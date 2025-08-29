# Movie Search Engine

A sophisticated movie search engine that understands natural language queries and provides intelligent search results from a large dataset of movies.

## Features

- **Natural Language Processing**: Understand queries like "sci-fi movies from the 90s with Tom Hanks"
- **Smart Query Parsing**: Handles synonyms, date ranges, celebrity names, and genres
- **Hybrid Search**: Combines Whoosh full-text search with TF-IDF semantic search
- **Multiple Interfaces**: Web UI and Command Line Interface
- **Fast Performance**: Sub-2 second response times
- **Intelligent Ranking**: Context-aware result scoring and boosting

## Quick Start

### Prerequisites

- Python 3.11+
- Docker (optional)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd movie-search-engine
   ```

2. **Install dependencies**
   ```bash
   # Using uv (recommended)
   uv sync
   
   # Or using pip
   pip install -r requirements.txt
   ```

3. **Download the dataset**
   ```bash
   # The application will automatically download the MSRD dataset on first run
   # Or manually download from: https://github.com/metarank/msrd
   ```

### Running the Application

#### Web Interface
```bash
python app.py
```
Visit `http://localhost:5000` in your browser.

#### Command Line Interface
```bash
# Interactive mode
python cli.py -i

# Single search
python cli.py "sci-fi movies from the 90s"

# With custom limit
python cli.py "comedy films with Tom Hanks" -l 20
```

#### Docker
```bash
# Build and run with Docker Compose
docker-compose up --build

# Or build and run manually
docker build -t movie-search-engine .
docker run -p 5000:5000 movie-search-engine
```

## Usage Examples

### Natural Language Queries

The search engine understands various query formats:

- **Genre + Year**: "sci-fi movies from the 90s"
- **Actor Search**: "comedy films with Tom Hanks"
- **Director Search**: "action movies directed by Steven Spielberg"
- **Complex Queries**: "war movies about love from early 2000s"
- **Synonym Support**: "rom-com" → "romantic comedy"

### CLI Commands

```bash
# Show system status
python cli.py --status

# Interactive mode with verbose logging
python cli.py -i -v

# Search with custom result limit
python cli.py "horror films from early 2000s" -l 15
```

### API Endpoints

- `GET /api/search?q=<query>&limit=<number>` - Search movies
- `GET /api/status` - System status and movie count

## Architecture

The application follows a clean architecture pattern with clear separation of concerns:

- **Domain Layer**: Core business models and entities
- **Core Layer**: Business logic and query parsing
- **Infrastructure Layer**: Data access and search engines
- **API Layer**: Web and CLI interfaces

### Search Engines

1. **Whoosh Engine**: Full-text search with exact matching
2. **TF-IDF Engine**: Semantic similarity search
3. **Hybrid Ranking**: Intelligent combination of both approaches

## Performance

- **Dataset**: ~9,700 movies from MSRD
- **Response Time**: < 2 seconds for complex queries
- **Memory Usage**: Optimized for efficient processing
- **Indexing**: Automatic index building and caching

##  Configuration

Environment variables:

```bash
SESSION_SECRET=your-secret-key
LOG_LEVEL=INFO
ENVIRONMENT=production
```

Configuration files:
- `pyproject.toml` - Dependencies and project metadata
- `src/config/settings.py` - Application settings

## Testing

```bash
# Run unit tests
python -m pytest tests/unit/

# Run integration tests
python -m pytest tests/integration/
```

## Project Structure

```
├── app.py # Web application entry point
├── cli.py # CLI application entry point
├── src/
│ ├── api/ # Web and CLI interfaces
│ ├── config/ # Configuration management
│ ├── core/ # Business logic and query parsing
│ ├── domain/ # Domain models
│ └── infrastructure/ # Data access and search engines
├── templates/ # HTML templates
├── static/ # CSS and static assets
├── data/ # Dataset storage
├── index/ # Search indices
└── tests/ # Test suite
```

## Development

### Adding New Features

1. **Query Parser**: Extend `src/core/query_parser.py` for new query types
2. **Search Engines**: Implement new engines in `src/infrastructure/search_engines.py`
3. **Models**: Add new domain models in `src/domain/models.py`

### Code Style

- Follow PEP 8 guidelines
- Use type hints throughout
- Document public methods and classes
- Write unit tests for new features

## Deployment

### Production Setup

1. **Environment Variables**
   ```bash
   export SESSION_SECRET=your-production-secret
   export ENVIRONMENT=production
   export LOG_LEVEL=WARNING
   ```

2. **Gunicorn (Recommended)**
   ```bash
   gunicorn -w 4 -b 0.0.0.0:5000 app:app
   ```

3. **Docker Production**
   ```bash
   docker-compose -f docker-compose.prod.yml up -d
   ```

## Monitoring

- **Health Check**: `GET /api/status`
- **Logging**: Structured logging with configurable levels
- **Performance**: Query execution time tracking

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

##  License

This project is licensed under the MIT License.

## Acknowledgments

- [MSRD Dataset](https://github.com/metarank/msrd) for the movie data
- [Whoosh](https://whoosh.readthedocs.io/) for full-text search
- [spaCy](https://spacy.io/) for natural language processing
- [scikit-learn](https://scikit-learn.org/) for TF-IDF implementation
