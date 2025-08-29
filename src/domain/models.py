"""Domain models for the movie search engine."""

from dataclasses import dataclass
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime


@dataclass
class Movie:
    """Movie domain model."""
    id: str
    title: str
    overview: str
    genres: List[str]
    actors: List[str]
    directors: List[str]
    year: Optional[int] = None
    rating: Optional[float] = None
    popularity: Optional[float] = None
    
    @property
    def search_text(self) -> str:
        """Get searchable text representation."""
        return " ".join([
            self.title,
            self.overview,
            " ".join(self.genres),
            " ".join(self.actors),
            " ".join(self.directors)
        ])
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "title": self.title,
            "overview": self.overview,
            "genres": self.genres,
            "actors": self.actors,
            "directors": self.directors,
            "year": self.year,
            "rating": self.rating,
            "popularity": self.popularity
        }


@dataclass
class SearchQuery:
    """Search query domain model."""
    original_query: str
    processed_query: str
    genres: List[str]
    actors: List[str]
    directors: List[str]
    keywords: List[str]
    year_range: Optional[Tuple[int, int]] = None
    
    @classmethod
    def from_string(cls, query: str) -> "SearchQuery":
        """Create SearchQuery from string (will be processed by query parser)."""
        return cls(
            original_query=query,
            processed_query=query.lower(),
            genres=[],
            actors=[],
            directors=[],
            keywords=[]
        )


@dataclass
class SearchResult:
    """Search result domain model."""
    movie: Movie
    score: float
    relevance_score: float
    source: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        result = self.movie.to_dict()
        result.update({
            "score": self.score,
            "relevance_score": self.relevance_score,
            "source": self.source
        })
        return result


@dataclass
class SearchResponse:
    """Search response containing results and metadata."""
    query: str
    results: List[SearchResult]
    total_found: int
    execution_time_ms: float
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "query": self.query,
            "results": [result.to_dict() for result in self.results],
            "total_found": self.total_found,
            "execution_time_ms": self.execution_time_ms
        }
