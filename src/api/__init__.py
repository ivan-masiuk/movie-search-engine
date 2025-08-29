"""API layer for web and CLI interfaces."""

from .web_app import create_app
from .cli_app import MovieSearchCLI

__all__ = ["create_app", "MovieSearchCLI"]
