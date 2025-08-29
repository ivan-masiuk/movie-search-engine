"""Flask web application."""

import logging
from flask import Flask, render_template, request, jsonify

from ..config.settings import get_settings
from ..core.services import MovieSearchService


def create_app() -> Flask:
    """Create and configure Flask application."""
    app = Flask(__name__, 
                template_folder='../../templates',
                static_folder='../../static')
    
    # Load settings
    settings = get_settings()
    
    # Configure Flask app
    app.secret_key = settings.server.secret_key
    
    # Configure logging
    logging.basicConfig(
        level=getattr(logging, settings.logging.level),
        format=settings.logging.format
    )
    
    # Initialize search service (lazy loading)
    search_service = None
    
    def get_search_service() -> MovieSearchService:
        """Get search service instance (lazy initialization)."""
        nonlocal search_service
        if search_service is None:
            search_service = MovieSearchService(settings)
            if not search_service.initialize():
                logging.error("Failed to initialize search service")
                return None
        return search_service
    
    @app.route('/')
    def index():
        """Home page."""
        return render_template('index.html')
    
    @app.route('/search', methods=['GET', 'POST'])
    def search():
        """Search page."""
        if request.method == 'GET':
            return render_template('index.html')
        
        query = request.form.get('query', '').strip()
        if not query:
            return render_template('index.html', error="Please enter a search query")
        
        service = get_search_service()
        if not service:
            return render_template(
                'index.html', 
                error="Search service not available. Please ensure the dataset is downloaded."
            )
        
        try:
            response = service.search(query, limit=20)
            
            # Convert SearchResult objects to dictionaries for template
            results = []
            for search_result in response.results:
                movie = search_result.movie
                results.append({
                    'title': movie.title,
                    'year': movie.year,
                    'genres': movie.genres,
                    'overview': movie.overview[:300] + '...' if len(movie.overview) > 300 else movie.overview,
                    'cast': movie.actors[:5],  # Show top 5 actors
                    'directors': movie.directors,
                    'relevance_score': search_result.relevance_score
                })
            
            return render_template(
                'results.html', 
                query=query, 
                results=results,
                total_found=response.total_found,
                execution_time=response.execution_time_ms
            )
            
        except Exception as e:
            logging.error(f"Search error: {e}")
            return render_template('index.html', error=f"Search failed: {str(e)}")
    
    @app.route('/api/search')
    def api_search():
        """API search endpoint."""
        query = request.args.get('q', '').strip()
        if not query:
            return jsonify({'error': 'Query parameter q is required'}), 400
        
        service = get_search_service()
        if not service:
            return jsonify({'error': 'Search service not available'}), 503
        
        try:
            limit = int(request.args.get('limit', 10))
            response = service.search(query, limit=limit)
            
            return jsonify(response.to_dict())
            
        except ValueError:
            return jsonify({'error': 'Invalid limit parameter'}), 400
        except Exception as e:
            logging.error(f"API search error: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/status')
    def api_status():
        """API status endpoint."""
        service = get_search_service()
        if service and service.is_ready():
            return jsonify({
                'status': 'ready',
                'movie_count': service.get_movie_count(),
                'version': '2.0.0'
            })
        else:
            return jsonify({
                'status': 'not_ready',
                'message': 'Search service not initialized'
            })
    
    @app.route('/status')
    def status():
        """Legacy status endpoint for compatibility."""
        return api_status()
    
    @app.errorhandler(404)
    def not_found(error):
        """Handle 404 errors."""
        return jsonify({'error': 'Not found'}), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        """Handle 500 errors."""
        logging.error(f"Internal server error: {error}")
        return jsonify({'error': 'Internal server error'}), 500
    
    return app
