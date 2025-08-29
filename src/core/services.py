"""Core business logic services."""

import time
import logging
from typing import List, Dict, Any, Optional

from ..domain.models import Movie, SearchQuery, SearchResult, SearchResponse
from ..infrastructure.repositories import MovieRepository
from ..infrastructure.search_engines import WhooshSearchEngine, TFIDFSearchEngine
from ..infrastructure.data_loader import DataLoader
from ..config.settings import Settings
from .query_parser import QueryParser


class MovieSearchService:
    """Main service for movie search functionality."""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.logger = logging.getLogger(__name__)
        
        # Initialize components
        self.data_loader = DataLoader(settings.database)
        self.movie_repository = MovieRepository(settings.database)
        self.whoosh_engine = WhooshSearchEngine(settings.search, settings.database)
        self.tfidf_engine = TFIDFSearchEngine(settings.search)
        self.query_parser = QueryParser()
        
        self._movies: Optional[List[Movie]] = None
        self._is_initialized = False
    
    def initialize(self) -> bool:
        """Initialize the search service."""
        if self._is_initialized:
            return True
        
        try:
            # Ensure dataset is available
            if not self.data_loader.ensure_dataset_available():
                self.logger.error("Failed to ensure dataset availability")
                return False
            
            # Load movies
            self.logger.info("Loading movies...")
            self._movies = self.movie_repository.load_movies()
            
            # Build or load search indices
            self._initialize_search_engines()
            
            self._is_initialized = True
            self.logger.info(f"Movie search service initialized with {len(self._movies)} movies")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize search service: {e}")
            return False
    
    def _initialize_search_engines(self):
        """Initialize search engines with indices."""
        import os
        
        # Check if Whoosh index exists
        if os.path.exists(self.settings.database.index_dir):
            try:
                self.logger.info("Loading existing search indices...")
                self.whoosh_engine.load_index()
                self.tfidf_engine.build_index(self._movies)  # TF-IDF is quick to rebuild
                return
            except Exception as e:
                self.logger.warning(f"Failed to load existing indices: {e}")
        
        # Build new indices
        self.logger.info("Building search indices...")
        self.whoosh_engine.build_index(self._movies)
        self.tfidf_engine.build_index(self._movies)
    
    def search(self, query: str, limit: int = 10) -> SearchResponse:
        """Search for movies using natural language query."""
        start_time = time.time()
        
        if not self._is_initialized:
            if not self.initialize():
                return SearchResponse(
                    query=query,
                    results=[],
                    total_found=0,
                    execution_time_ms=0.0
                )
        
        try:
            # Parse the query
            parsed_query = self.query_parser.parse(query)
            
            # Get results from both search engines
            whoosh_results = self._search_with_whoosh(parsed_query, limit)
            tfidf_results = self._search_with_tfidf(parsed_query, limit)
            
            # Combine and rank results
            combined_results = self._combine_results(
                whoosh_results, tfidf_results, parsed_query
            )
            
            # Convert to SearchResult objects
            search_results = self._convert_to_search_results(combined_results[:limit])
            
            execution_time = (time.time() - start_time) * 1000  # Convert to milliseconds
            
            return SearchResponse(
                query=query,
                results=search_results,
                total_found=len(combined_results),
                execution_time_ms=execution_time
            )
            
        except Exception as e:
            self.logger.error(f"Search failed: {e}")
            return SearchResponse(
                query=query,
                results=[],
                total_found=0,
                execution_time_ms=0.0
            )
    
    def _search_with_whoosh(self, query: SearchQuery, limit: int) -> List[Dict[str, Any]]:
        """Search using Whoosh engine."""
        try:
            return self.whoosh_engine.search(query, limit)
        except Exception as e:
            self.logger.error(f"Whoosh search failed: {e}")
            return []
    
    def _search_with_tfidf(self, query: SearchQuery, limit: int) -> List[Dict[str, Any]]:
        """Search using TF-IDF engine."""
        try:
            return self.tfidf_engine.search(query, limit)
        except Exception as e:
            self.logger.error(f"TF-IDF search failed: {e}")
            return []
    
    def _combine_results(
        self, 
        whoosh_results: List[Dict[str, Any]], 
        tfidf_results: List[Dict[str, Any]],
        query: SearchQuery
    ) -> List[Dict[str, Any]]:
        """Combine and rank results from different search methods."""
        combined_scores = {}
        
        # Add Whoosh results
        for result in whoosh_results:
            movie_id = result['id']
            combined_scores[movie_id] = combined_scores.get(movie_id, {'whoosh': 0, 'tfidf': 0})
            combined_scores[movie_id]['whoosh'] = result['score']
        
        # Add TF-IDF results
        for result in tfidf_results:
            movie_id = result['id']
            combined_scores[movie_id] = combined_scores.get(movie_id, {'whoosh': 0, 'tfidf': 0})
            combined_scores[movie_id]['tfidf'] = result['score']
        
        # Calculate final scores and prepare results
        final_results = []
        for movie_id, scores in combined_scores.items():
            movie = self._get_movie_by_id(movie_id)
            if not movie:
                continue
            
            # Weighted combination of scores
            combined_score = (
                self.settings.search.whoosh_weight * scores['whoosh'] + 
                self.settings.search.tfidf_weight * scores['tfidf']
            )
            
            # Add boost for exact matches
            boost = self._calculate_boost(movie, query)
            combined_score += boost
            
            final_results.append({
                'movie': movie,
                'score': combined_score,
                'relevance_score': min(combined_score * 100, 100),
                'source': 'combined'
            })
        
        # Sort by score
        final_results.sort(key=lambda x: x['score'], reverse=True)
        return final_results
    
    def _calculate_boost(self, movie: Movie, query: SearchQuery) -> float:
        """Calculate boost score for exact matches."""
        boost = 0.0
        
        # Boost for genre matches
        if query.genres:
            movie_genres = [g.lower() for g in movie.genres]
            for genre in query.genres:
                if genre.lower() in movie_genres:
                    boost += self.settings.search.genre_boost
        
        # Boost for actor matches
        if query.actors:
            movie_actors = [a.lower() for a in movie.actors]
            for actor in query.actors:
                if any(actor.lower() in movie_actor for movie_actor in movie_actors):
                    boost += self.settings.search.actor_boost
        
        # Boost for director matches
        if query.directors:
            movie_directors = [d.lower() for d in movie.directors]
            for director in query.directors:
                if any(director.lower() in movie_director for movie_director in movie_directors):
                    boost += self.settings.search.actor_boost  # Same boost as actors
        
        # Boost for year matches
        if query.year_range and movie.year:
            year_start, year_end = query.year_range
            if year_start <= movie.year <= year_end:
                boost += self.settings.search.year_boost
        
        return boost
    
    def _get_movie_by_id(self, movie_id: str) -> Optional[Movie]:
        """Get movie by ID from loaded movies."""
        if not self._movies:
            return None
        
        for movie in self._movies:
            if movie.id == movie_id:
                return movie
        return None
    
    def _convert_to_search_results(self, combined_results: List[Dict[str, Any]]) -> List[SearchResult]:
        """Convert combined results to SearchResult objects."""
        search_results = []
        
        for result in combined_results:
            search_result = SearchResult(
                movie=result['movie'],
                score=result['score'],
                relevance_score=round(result['relevance_score'], 1),
                source=result['source']
            )
            search_results.append(search_result)
        
        return search_results
    
    def get_movie_count(self) -> int:
        """Get total number of movies."""
        if not self._is_initialized:
            self.initialize()
        return len(self._movies) if self._movies else 0
    
    def is_ready(self) -> bool:
        """Check if service is ready to handle requests."""
        return (self._is_initialized and 
                self.whoosh_engine.is_ready() and 
                self.tfidf_engine.is_ready())
