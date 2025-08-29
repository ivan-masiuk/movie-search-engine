"""Command Line Interface application."""

import sys
import argparse
import logging
from typing import List

from ..config.settings import get_settings
from ..core.services import MovieSearchService
from ..domain.models import SearchResult


class MovieSearchCLI:
    """Command line interface for movie search."""
    
    def __init__(self):
        self.settings = get_settings()
        self.search_service = MovieSearchService(self.settings)
    
    def initialize(self) -> bool:
        """Initialize the CLI application."""
        print("Initializing movie search engine...")
        
        # Configure logging
        logging.basicConfig(
            level=getattr(logging, self.settings.logging.level),
            format=self.settings.logging.format
        )
        
        if not self.search_service.initialize():
            print("❌ Failed to initialize search service")
            return False
        
        print(f"✅ Search engine initialized with {self.search_service.get_movie_count()} movies")
        return True
    
    def search_movies(self, query: str, limit: int = 10) -> List[SearchResult]:
        """Search for movies using natural language query."""
        if not self.search_service.is_ready():
            if not self.initialize():
                return []
        
        try:
            response = self.search_service.search(query, limit=limit)
            return response.results
        except Exception as e:
            print(f"❌ Search failed: {e}")
            return []
    
    def display_results(self, results: List[SearchResult], query: str, execution_time: float = 0):
        """Display search results in a formatted way."""
        if not results:
            print("No movies found matching your query.")
            return
        
        print(f"\n🎬 Search Results for: '{query}'")
        if execution_time > 0:
            print(f"⏱️  Search completed in {execution_time:.2f}ms")
        print("=" * 60)
        
        for i, search_result in enumerate(results, 1):
            movie = search_result.movie
            print(f"\n{i}. {movie.title}")
            
            if movie.year:
                print(f"   📅 Year: {movie.year}")
            
            if movie.genres:
                print(f"   🎭 Genres: {', '.join(movie.genres)}")
            
            if movie.directors:
                print(f"   🎬 Director(s): {', '.join(movie.directors)}")
            
            if movie.actors:
                print(f"   🎭 Cast: {', '.join(movie.actors[:5])}")  # Show top 5
            
            if movie.overview:
                overview = movie.overview[:200] + '...' if len(movie.overview) > 200 else movie.overview
                print(f"   📝 Overview: {overview}")
            
            print(f"   ⭐ Relevance: {search_result.relevance_score}%")
            print("-" * 60)
    
    def interactive_mode(self):
        """Run interactive search mode."""
        print("🎬 Movie Search Engine - Interactive Mode")
        print("Type 'quit' or 'exit' to stop, 'help' for commands")
        print("=" * 50)
        
        if not self.initialize():
            print("Failed to initialize search engine. Exiting.")
            return
        
        while True:
            try:
                query = input("\n🔍 Enter your movie search query: ").strip()
                
                if query.lower() in ['quit', 'exit', 'q']:
                    print("Goodbye! 👋")
                    break
                
                if query.lower() == 'help':
                    self.show_help()
                    continue
                
                if not query:
                    print("Please enter a search query.")
                    continue
                
                print("Searching...")
                response = self.search_service.search(query)
                self.display_results(response.results, query, response.execution_time_ms)
                
            except KeyboardInterrupt:
                print("\n\nGoodbye! 👋")
                break
            except Exception as e:
                print(f"An error occurred: {e}")
    
    def show_help(self):
        """Show help information."""
        help_text = """
🎬 Movie Search Engine Help

Example queries you can try:
• "sci-fi movies from the 90s"
• "comedy films with Tom Hanks"
• "war movies about love"
• "horror films from early 2000s"
• "action movies directed by Steven Spielberg"
• "animated movies for family"

Features:
• Natural language understanding
• Genre recognition (sci-fi, rom-com, etc.)
• Year range parsing (90s, early 2000s, etc.)
• Actor and director search
• Fuzzy matching for names

Commands:
• help - Show this help
• quit/exit/q - Exit the program
"""
        print(help_text)
    
    def run_single_search(self, query: str, limit: int = 10):
        """Run a single search query."""
        if not self.initialize():
            sys.exit(1)
        
        response = self.search_service.search(query, limit=limit)
        self.display_results(response.results, query, response.execution_time_ms)
    
    def show_status(self):
        """Show system status."""
        if not self.initialize():
            print("❌ Search service not available")
            return
        
        print(f"✅ Search service ready")
        print(f"📊 Total movies: {self.search_service.get_movie_count()}")
        print(f"🔧 Environment: {self.settings.environment}")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description="Movie Search Engine CLI v2.0")
    parser.add_argument('query', nargs='*', help='Search query')
    parser.add_argument('-l', '--limit', type=int, default=10, help='Maximum number of results')
    parser.add_argument('-i', '--interactive', action='store_true', help='Run in interactive mode')
    parser.add_argument('--status', action='store_true', help='Show system status')
    parser.add_argument('-v', '--verbose', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    cli = MovieSearchCLI()
    
    if args.verbose:
        # Override logging level for verbose mode
        logging.getLogger().setLevel(logging.DEBUG)
    
    if args.status:
        cli.show_status()
        return
    
    if args.interactive or not args.query:
        cli.interactive_mode()
    else:
        query = ' '.join(args.query)
        cli.run_single_search(query, args.limit)


if __name__ == "__main__":
    main()
