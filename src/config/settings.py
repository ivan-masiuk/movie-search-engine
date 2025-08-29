"""Application configuration settings."""

import os
from typing import Optional
from dataclasses import dataclass, field
from functools import lru_cache


@dataclass
class DatabaseConfig:
    """Database configuration."""
    data_dir: str = "data"
    movies_file: str = "movies_metadata.csv"
    index_dir: str = "index"
    
    @property
    def movies_path(self) -> str:
        """Get full path to movies file."""
        return os.path.join(self.data_dir, self.movies_file)


@dataclass
class SearchConfig:
    """Search engine configuration."""
    tfidf_max_features: int = 5000
    tfidf_ngram_range: tuple = (1, 2)
    tfidf_min_df: int = 2
    whoosh_limit_multiplier: int = 2
    tfidf_limit_multiplier: int = 3
    whoosh_weight: float = 0.6
    tfidf_weight: float = 0.4
    
    # Boost scores
    genre_boost: float = 0.3
    actor_boost: float = 0.4
    year_boost: float = 0.2


@dataclass
class ServerConfig:
    """Server configuration."""
    host: str = "0.0.0.0"
    port: int = 5000
    debug: bool = False
    secret_key: str = field(default_factory=lambda: os.urandom(24).hex())
    
    def __post_init__(self):
        """Set secret key from environment if available."""
        env_secret = os.environ.get("SESSION_SECRET")
        if env_secret:
            self.secret_key = env_secret


@dataclass
class LoggingConfig:
    """Logging configuration."""
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    def __post_init__(self):
        """Set logging level from environment if available."""
        env_level = os.environ.get("LOG_LEVEL")
        if env_level:
            self.level = env_level.upper()


@dataclass
class Settings:
    """Application settings."""
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    search: SearchConfig = field(default_factory=SearchConfig)
    server: ServerConfig = field(default_factory=ServerConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    
    # Environment
    environment: str = field(default_factory=lambda: os.environ.get("ENVIRONMENT", "development"))
    
    @property
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.environment.lower() in ("development", "dev")
    
    @property
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.environment.lower() in ("production", "prod")


@lru_cache()
def get_settings() -> Settings:
    """Get application settings (cached)."""
    return Settings()
