# Movie Search Engine Architecture

## Overview

The Movie Search Engine is built using a clean architecture pattern that separates concerns into distinct layers, enabling maintainability, testability, and scalability. The system processes natural language queries and returns relevant movie results using a hybrid search approach.

## Architecture Layers

### 1. Domain Layer (`src/domain/`)

**Purpose**: Contains core business entities and models that represent the domain concepts.

**Key Components**:
- `Movie`: Core entity representing a movie with metadata
- `SearchQuery`: Structured representation of parsed user queries
- `SearchResult`: Individual search result with scoring
- `SearchResponse`: Complete search response with metadata

**Design Principles**:
- Pure domain models without external dependencies
- Immutable data structures using dataclasses
- Clear separation between domain logic and infrastructure concerns

### 2. Core Layer (`src/core/`)

**Purpose**: Contains business logic, query parsing, and orchestration services.

**Key Components**:
- `QueryParser`: Natural language query understanding
- `MovieSearchService`: Main orchestration service
- Query processing and result ranking logic

**Responsibilities**:
- Natural language query parsing
- Search engine coordination
- Result ranking and boosting
- Business rule enforcement

### 3. Infrastructure Layer (`src/infrastructure/`)

**Purpose**: Handles data access, external services, and technical implementations.

**Key Components**:
- `DataLoader`: Dataset management and loading
- `MovieRepository`: Data access abstraction
- `WhooshSearchEngine`: Full-text search implementation
- `TFIDFSearchEngine`: Semantic search implementation

**Design Patterns**:
- Repository pattern for data access
- Strategy pattern for search engines
- Factory pattern for component creation

### 4. API Layer (`src/api/`)

**Purpose**: Provides interfaces for different user interaction methods.

**Key Components**:
- `web_app.py`: Flask web application
- `cli_app.py`: Command line interface
- REST API endpoints
- Template rendering

## 🔍 Search Architecture

### Hybrid Search Approach

The system uses a sophisticated hybrid search strategy combining multiple search engines:

#### 1. Whoosh Full-Text Search
- **Purpose**: Exact keyword matching and structured queries
- **Strengths**: Fast exact matches, boolean queries, field-specific search
- **Use Cases**: Genre filters, actor names, exact title matches

#### 2. TF-IDF Semantic Search
- **Purpose**: Semantic similarity and content-based search
- **Strengths**: Understanding context, handling synonyms, content relevance
- **Use Cases**: Plot descriptions, thematic searches, fuzzy matching

#### 3. Intelligent Result Combination
- **Weighted Scoring**: Configurable weights for each engine
- **Boosting System**: Additional scores for exact matches
- **Deduplication**: Smart result merging and ranking

### Query Processing Pipeline

User Query → Query Parser → Search Engines → Result Combination → Ranking → Response

1. **Query Parsing**: Extract entities, dates, genres, keywords
2. **Parallel Search**: Execute searches on both engines
3. **Result Merging**: Combine and deduplicate results
4. **Score Calculation**: Apply weights and boosting
5. **Final Ranking**: Sort by relevance score

## Natural Language Processing

### Query Understanding

The system employs advanced NLP techniques for query understanding:

#### Entity Extraction
- **Named Entity Recognition**: Using spaCy for person names
- **Genre Recognition**: Synonym mapping and fuzzy matching
- **Date Parsing**: Intelligent decade and year range parsing

#### Context Understanding
- **Director vs Actor**: Context-based classification
- **Genre Synonyms**: "sci-fi" → "science fiction"
- **Temporal Expressions**: "early 2000s" → 2000-2004

### Parsing Patterns

```python
# Year patterns
"90s" → (1990, 1999)
"early 2000s" → (2000, 2004)
"late 90s" → (1995, 1999)

# Genre synonyms
"sci-fi" → "science fiction"
"rom-com" → "romantic comedy"

# Person classification
"movies with Tom Hanks" → Actor
"movies directed by Spielberg" → Director
```

## Data Management

### Dataset Structure

The system uses the Movie Search Ranking Dataset (MSRD) with rich metadata:

- **Core Fields**: Title, overview, genres, cast, directors
- **Metadata**: Year, rating, popularity, tags
- **Searchable Text**: Combined text representation for indexing

### Index Management

#### Whoosh Index Schema
```python
Schema(
    id=ID(stored=True),
    title=TEXT(stored=True),
    overview=TEXT(stored=True),
    genres=TEXT(stored=True),
    cast=TEXT(stored=True),
    director=TEXT(stored=True),
    year=NUMERIC(stored=True),
    search_text=TEXT(stored=True)
)
```

#### TF-IDF Vectorization
- **Features**: 5000 max features with n-gram range (1,2)
- **Preprocessing**: Stop word removal, stemming
- **Similarity**: Cosine similarity for semantic matching

## Performance Optimization

### Caching Strategy
- **Index Caching**: Persistent Whoosh indices
- **Model Caching**: TF-IDF vectorizer and matrices
- **Result Caching**: Query result caching (future enhancement)

### Memory Management
- **Lazy Loading**: Components initialized on demand
- **Efficient Data Structures**: Optimized for search operations
- **Resource Cleanup**: Proper cleanup of search engine resources

### Scalability Considerations
- **Horizontal Scaling**: Stateless design enables multiple instances
- **Database Separation**: Search indices separate from application
- **Load Balancing**: Ready for load balancer deployment

## Configuration Management

### Settings Architecture

The configuration system uses a hierarchical approach:

```python
@dataclass
class Settings:
    database: DatabaseConfig
    search: SearchConfig
    server: ServerConfig
    logging: LoggingConfig
```

### Environment-Based Configuration
- **Development**: Debug mode, verbose logging
- **Production**: Optimized settings, minimal logging
- **Docker**: Container-optimized configuration

## Testing Strategy

### Test Architecture

```
tests/
├── unit/ # Unit tests for individual components
├── integration/ # Integration tests for workflows
└── fixtures/ # Test data and mocks
```

### Testing Patterns
- **Unit Tests**: Isolated component testing
- **Integration Tests**: End-to-end workflow testing
- **Mock Testing**: External dependency mocking
- **Performance Testing**: Query response time validation

## Security Considerations

### Input Validation
- **Query Sanitization**: Prevent injection attacks
- **Rate Limiting**: Protect against abuse (future enhancement)
- **Authentication**: API key support (future enhancement)

### Data Protection
- **Secure Headers**: HTTPS and security headers
- **Error Handling**: Safe error messages
- **Logging**: Sensitive data exclusion

## Deployment Architecture

### Container Strategy
- **Multi-Stage Builds**: Optimized Docker images
- **Health Checks**: Application health monitoring
- **Volume Management**: Persistent data storage

### Production Considerations
- **Load Balancing**: Multiple application instances
- **Database Scaling**: Separate search index storage
- **Monitoring**: Application metrics and logging
- **Backup Strategy**: Index and data backup procedures

## Future Enhancements

### Planned Improvements
1. **Advanced NLP**: BERT-based semantic search
2. **Recommendation Engine**: Collaborative filtering
3. **Real-time Updates**: Live index updates
4. **Advanced Analytics**: Search pattern analysis
5. **Mobile API**: RESTful API for mobile applications

### Scalability Roadmap
1. **Microservices**: Service decomposition
2. **Event-Driven**: Asynchronous processing
3. **Cloud Native**: Kubernetes deployment
4. **Global Distribution**: CDN and edge computing

## Performance Metrics

### Key Performance Indicators
- **Query Response Time**: < 2 seconds target
- **Search Accuracy**: Relevance score validation
- **System Throughput**: Queries per second
- **Resource Utilization**: CPU and memory usage

### Monitoring Strategy
- **Application Metrics**: Response times, error rates
- **Infrastructure Metrics**: Resource utilization
- **Business Metrics**: Search patterns, user behavior
- **Alerting**: Proactive issue detection

This architecture provides a solid foundation for a production-ready movie search engine with clear separation of concerns, excellent testability, and room for future enhancements.
