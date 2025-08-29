"""Repository implementations for data access."""

import os
import pandas as pd
import logging
from typing import List, Optional, Protocol
from abc import ABC, abstractmethod

from ..domain.models import Movie
from ..config.settings import DatabaseConfig


class MovieRepositoryInterface(Protocol):
    """Movie repository interface."""
    
    def load_movies(self) -> List[Movie]:
        """Load all movies from data source."""
        ...
    
    def get_movie_by_id(self, movie_id: str) -> Optional[Movie]:
        """Get movie by ID."""
        ...
    
    def get_movies_count(self) -> int:
        """Get total number of movies."""
        ...


class MovieRepository:
    """CSV-based movie repository implementation."""
    
    def __init__(self, config: DatabaseConfig):
        self.config = config
        self._movies_df: Optional[pd.DataFrame] = None
        self._movies: Optional[List[Movie]] = None
        self.logger = logging.getLogger(__name__)
    
    def load_movies(self) -> List[Movie]:
        """Load all movies from CSV file."""
        if self._movies is not None:
            return self._movies
        
        if not os.path.exists(self.config.movies_path):
            raise FileNotFoundError(f"Movies dataset not found at {self.config.movies_path}")
        
        self.logger.info("Loading movies from CSV...")
        
        try:
            self._movies_df = pd.read_csv(
                self.config.movies_path,
                sep='\t',
                quoting=3,
                encoding='utf-8',
                on_bad_lines='skip',
                engine='python'
            )
            
            # Clean column names and data
            self._movies_df.columns = self._movies_df.columns.str.strip('"')
            
            for col in self._movies_df.columns:
                if self._movies_df[col].dtype == 'object':
                    self._movies_df[col] = self._movies_df[col].astype(str).str.strip('"')
            
            # Convert DataFrame to Movie objects
            self._movies = self._convert_dataframe_to_movies(self._movies_df)
            
            self.logger.info(f"Loaded {len(self._movies)} movies")
            return self._movies
            
        except Exception as e:
            self.logger.error(f"Failed to load movies: {e}")
            raise
    
    def get_movie_by_id(self, movie_id: str) -> Optional[Movie]:
        """Get movie by ID."""
        movies = self.load_movies()
        for movie in movies:
            if movie.id == movie_id:
                return movie
        return None
    
    def get_movies_count(self) -> int:
        """Get total number of movies."""
        return len(self.load_movies())
    
    def get_movies_dataframe(self) -> pd.DataFrame:
        """Get movies as pandas DataFrame (for search engines)."""
        if self._movies_df is None:
            self.load_movies()
        return self._movies_df
    
    def _convert_dataframe_to_movies(self, df: pd.DataFrame) -> List[Movie]:
        """Convert pandas DataFrame to list of Movie objects."""
        movies = []
        
        for idx, row in df.iterrows():
            movie = Movie(
                id=str(idx),
                title=self._safe_get_string(row, 'title'),
                overview=self._safe_get_string(row, 'overview'),
                genres=self._parse_comma_separated(self._safe_get_string(row, 'genres')),
                actors=self._parse_comma_separated(self._safe_get_string(row, 'actors')),
                directors=self._parse_directors(self._safe_get_string(row, 'director')),
                year=self._safe_get_int(row, 'year'),
                rating=self._safe_get_float(row, 'rating'),
                popularity=self._safe_get_float(row, 'popularity')
            )
            movies.append(movie)
        
        return movies
    
    def _safe_get_string(self, row: pd.Series, column: str, default: str = "") -> str:
        """Safely get string value from row."""
        if column not in row:
            return default
        value = row[column]
        if pd.isna(value):
            return default
        return str(value).strip()
    
    def _safe_get_int(self, row: pd.Series, column: str, default: Optional[int] = None) -> Optional[int]:
        """Safely get integer value from row."""
        if column not in row:
            return default
        value = row[column]
        if pd.isna(value):
            return default
        try:
            return int(value)
        except (ValueError, TypeError):
            return default
    
    def _safe_get_float(self, row: pd.Series, column: str, default: Optional[float] = None) -> Optional[float]:
        """Safely get float value from row."""
        if column not in row:
            return default
        value = row[column]
        if pd.isna(value):
            return default
        try:
            return float(value)
        except (ValueError, TypeError):
            return default
    
    def _parse_comma_separated(self, field_str: str) -> List[str]:
        """Parse comma-separated string field."""
        if not field_str or field_str.strip() == '':
            return []
        return [item.strip() for item in field_str.split(',') if item.strip()]
    
    def _parse_directors(self, director_str: str) -> List[str]:
        """Parse director string (single director or comma-separated)."""
        if not director_str or director_str.strip() == '':
            return []
        return [director_str.strip()]
