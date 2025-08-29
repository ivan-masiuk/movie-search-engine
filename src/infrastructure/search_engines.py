"""Search engine implementations."""

import os
import logging
from typing import List, Dict, Any, Protocol
from abc import ABC, abstractmethod

import pandas as pd
import whoosh.index
from whoosh.fields import Schema, TEXT, ID, NUMERIC
from whoosh.qparser import QueryParser
from whoosh.query import Or, Term
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from ..domain.models import Movie, SearchQuery
from ..config.settings import SearchConfig, DatabaseConfig


class SearchEngineInterface(Protocol):
    """Search engine interface."""
    
    def build_index(self, movies: List[Movie]) -> None:
        """Build search index from movies."""
        ...
    
    def search(self, query: SearchQuery, limit: int) -> List[Dict[str, Any]]:
        """Search movies and return results with scores."""
        ...
    
    def is_ready(self) -> bool:
        """Check if search engine is ready."""
        ...


class WhooshSearchEngine:
    """Whoosh full-text search engine."""
    
    def __init__(self, config: SearchConfig, db_config: DatabaseConfig):
        self.config = config
        self.db_config = db_config
        self.index = None
        self.movies_df = None
        self.logger = logging.getLogger(__name__)
    
    def build_index(self, movies: List[Movie]) -> None:
        """Build Whoosh search index."""
        try:
            os.makedirs(self.db_config.index_dir, exist_ok=True)
            
            schema = Schema(
                id=ID(stored=True),
                title=TEXT(stored=True),
                overview=TEXT(stored=True),
                genres=TEXT(stored=True),
                cast=TEXT(stored=True),
                director=TEXT(stored=True),
                year=NUMERIC(stored=True),
                search_text=TEXT(stored=True)
            )
            
            self.index = whoosh.index.create_in(self.db_config.index_dir, schema)
            writer = self.index.writer()
            
            for movie in movies:
                writer.add_document(
                    id=movie.id,
                    title=movie.title,
                    overview=movie.overview,
                    genres=' '.join(movie.genres),
                    cast=' '.join(movie.actors),
                    director=' '.join(movie.directors),
                    year=movie.year or 0,
                    search_text=movie.search_text
                )
            
            writer.commit()
            self.logger.info("Whoosh index built successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to build Whoosh index: {e}")
            raise
    
    def load_index(self) -> None:
        """Load existing Whoosh index."""
        try:
            self.index = whoosh.index.open_dir(self.db_config.index_dir)
            self.logger.info("Whoosh index loaded successfully")
        except Exception as e:
            self.logger.error(f"Failed to load Whoosh index: {e}")
            raise
    
    def search(self, query: SearchQuery, limit: int) -> List[Dict[str, Any]]:
        """Search using Whoosh index."""
        if not self.is_ready():
            raise RuntimeError("Whoosh search engine not ready")
        
        with self.index.searcher() as searcher:
            query_parts = []
            
            # Add text search
            if query.keywords:
                text_query = ' '.join(query.keywords)
                parser = QueryParser("search_text", self.index.schema)
                query_parts.append(parser.parse(text_query))
            
            # Add genre filters
            for genre in query.genres:
                query_parts.append(Term("genres", genre))
            
            # Add actor filters
            for actor in query.actors:
                query_parts.append(Term("cast", actor))
            
            # Combine queries
            if query_parts:
                combined_query = Or(query_parts) if len(query_parts) > 1 else query_parts[0]
            else:
                # Fallback to searching all text
                parser = QueryParser("search_text", self.index.schema)
                combined_query = parser.parse(query.original_query)
            
            results = searcher.search(combined_query, limit=limit * self.config.whoosh_limit_multiplier)
            
            whoosh_results = []
            for result in results:
                # Apply year filter if specified
                if query.year_range:
                    year_start, year_end = query.year_range
                    movie_year = result['year']
                    if movie_year and not (year_start <= movie_year <= year_end):
                        continue
                
                whoosh_results.append({
                    'id': result['id'],
                    'score': result.score,
                    'source': 'whoosh'
                })
            
            return whoosh_results[:limit]
    
    def is_ready(self) -> bool:
        """Check if Whoosh engine is ready."""
        return self.index is not None


class TFIDFSearchEngine:
    """TF-IDF semantic search engine."""
    
    def __init__(self, config: SearchConfig):
        self.config = config
        self.vectorizer = None
        self.tfidf_matrix = None
        self.movies = None
        self.logger = logging.getLogger(__name__)
    
    def build_index(self, movies: List[Movie]) -> None:
        """Build TF-IDF index."""
        try:
            self.movies = movies
            
            # Create TF-IDF vectorizer
            self.vectorizer = TfidfVectorizer(
                max_features=self.config.tfidf_max_features,
                stop_words='english',
                ngram_range=self.config.tfidf_ngram_range,
                min_df=self.config.tfidf_min_df
            )
            
            # Build matrix from search texts
            search_texts = [movie.search_text for movie in movies]
            self.tfidf_matrix = self.vectorizer.fit_transform(search_texts)
            
            self.logger.info("TF-IDF index built successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to build TF-IDF index: {e}")
            raise
    
    def search(self, query: SearchQuery, limit: int) -> List[Dict[str, Any]]:
        """Search using TF-IDF similarity."""
        if not self.is_ready():
            raise RuntimeError("TF-IDF search engine not ready")
        
        # Create query vector
        search_query = ' '.join(
            query.keywords + query.genres + query.actors + query.directors
        )
        if not search_query:
            search_query = query.original_query
        
        query_vector = self.vectorizer.transform([search_query])
        
        # Calculate similarities
        similarities = cosine_similarity(query_vector, self.tfidf_matrix).flatten()
        
        # Get top results
        top_indices = similarities.argsort()[-limit * self.config.tfidf_limit_multiplier:][::-1]
        
        tfidf_results = []
        for idx in top_indices:
            if similarities[idx] > 0:  # Only include relevant results
                movie = self.movies[idx]
                
                # Apply year filter if specified
                if query.year_range:
                    year_start, year_end = query.year_range
                    if movie.year and not (year_start <= movie.year <= year_end):
                        continue
                
                tfidf_results.append({
                    'id': movie.id,
                    'score': similarities[idx],
                    'source': 'tfidf'
                })
        
        return tfidf_results[:limit]
    
    def is_ready(self) -> bool:
        """Check if TF-IDF engine is ready."""
        return (self.vectorizer is not None and 
                self.tfidf_matrix is not None and 
                self.movies is not None)
