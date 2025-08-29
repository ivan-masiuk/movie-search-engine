"""Natural language query parser."""

import re
import logging
from typing import Dict, Any, Optional, List, Tuple

try:
    import spacy
    from spacy.lang.en import English
except ImportError:
    spacy = None

from ..domain.models import SearchQuery


class QueryParser:
    """Parse natural language queries into structured search parameters."""
    
    def __init__(self):
        self.nlp = None
        self.logger = logging.getLogger(__name__)
        
        # Genre synonyms mapping
        self.genre_synonyms = {
            'sci-fi': 'science fiction',
            'scifi': 'science fiction',
            'rom-com': 'romantic comedy',
            'romcom': 'romantic comedy',
            'action': 'action',
            'thriller': 'thriller',
            'horror': 'horror',
            'comedy': 'comedy',
            'drama': 'drama',
            'adventure': 'adventure',
            'fantasy': 'fantasy',
            'crime': 'crime',
            'mystery': 'mystery',
            'war': 'war',
            'western': 'western',
            'musical': 'music',
            'animation': 'animation',
            'animated': 'animation',
            'documentary': 'documentary',
            'family': 'family',
            'biography': 'biography',
            'history': 'history',
            'sport': 'sport',
            'music': 'music'
        }
        
        # Year parsing patterns
        self.year_patterns = [
            (r"(\d{4})s", self._parse_decade),  # "90s", "2000s"
            (r"early (\d{4})s", self._parse_early_decade),  # "early 2000s"
            (r"late (\d{4})s", self._parse_late_decade),  # "late 90s"
            (r"mid (\d{4})s", self._parse_mid_decade),  # "mid 90s"
            (r"(\d{4})", self._parse_single_year),  # "1995"
        ]
        
        # Stop words for keyword extraction
        self.stop_words = {
            'with', 'from', 'in', 'the', 'and', 'or', 'by', 'about', 
            'movies', 'films', 'film', 'movie', 'starring', 'directed',
            'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been', 'being'
        }
        
        self._init_nlp()
    
    def _init_nlp(self):
        """Initialize spaCy NLP model."""
        if spacy is None:
            self.logger.warning("spaCy not available. Using basic text processing.")
            return
        
        try:
            self.nlp = spacy.load("en_core_web_sm")
            self.logger.info("spaCy English model loaded successfully")
        except OSError:
            self.logger.warning("spaCy English model not found. Using basic text processing.")
            self.nlp = None
    
    def parse(self, query: str) -> SearchQuery:
        """Parse natural language query into SearchQuery object."""
        query_info = SearchQuery(
            original_query=query,
            processed_query=query.lower(),
            genres=[],
            actors=[],
            directors=[],
            keywords=[]
        )
        
        # Extract year ranges
        query_info.year_range = self._extract_year_range(query)
        
        # Extract genres using synonyms
        query_info.genres = self._extract_genres(query)
        
        # Extract person names using spaCy if available
        if self.nlp:
            actors, directors = self._extract_persons_with_spacy(query)
            query_info.actors.extend(actors)
            query_info.directors.extend(directors)
        
        # Extract keywords (remove common words and detected entities)
        query_info.keywords = self._extract_keywords(query, query_info)
        
        self.logger.debug(f"Parsed query: {query_info}")
        return query_info
    
    def _extract_year_range(self, query: str) -> Optional[Tuple[int, int]]:
        """Extract year range from query."""
        for pattern, extractor in self.year_patterns:
            match = re.search(pattern, query)
            if match:
                return extractor(match)
        return None
    
    def _parse_decade(self, match: re.Match) -> Tuple[int, int]:
        """Parse decade like '90s' or '2000s'."""
        year_str = match.group(1)
        if len(year_str) == 2:  # "90s"
            if int(year_str) >= 20:  # Assume 20-99 means 1920-1999
                start_year = 1900 + int(year_str)
            else:  # 00-19 means 2000-2019
                start_year = 2000 + int(year_str)
        else:  # "2000s"
            start_year = int(year_str[:-1] + '0')
        
        return (start_year, start_year + 9)
    
    def _parse_early_decade(self, match: re.Match) -> Tuple[int, int]:
        """Parse 'early 2000s' etc."""
        year_str = match.group(1)
        decade_start = int(year_str[:-1] + '0')
        return (decade_start, decade_start + 4)
    
    def _parse_late_decade(self, match: re.Match) -> Tuple[int, int]:
        """Parse 'late 90s' etc."""
        year_str = match.group(1)
        decade_start = int(year_str[:-1] + '0')
        return (decade_start + 5, decade_start + 9)
    
    def _parse_mid_decade(self, match: re.Match) -> Tuple[int, int]:
        """Parse 'mid 90s' etc."""
        year_str = match.group(1)
        decade_start = int(year_str[:-1] + '0')
        return (decade_start + 3, decade_start + 7)
    
    def _parse_single_year(self, match: re.Match) -> Tuple[int, int]:
        """Parse single year like '1995'."""
        year = int(match.group(1))
        return (year, year)
    
    def _extract_genres(self, query: str) -> List[str]:
        """Extract genres from query using synonyms."""
        genres = []
        query_lower = query.lower()
        
        for synonym, genre in self.genre_synonyms.items():
            if synonym in query_lower:
                if genre not in genres:
                    genres.append(genre)
        
        return genres
    
    def _extract_persons_with_spacy(self, query: str) -> Tuple[List[str], List[str]]:
        """Extract person names using spaCy NER."""
        actors = []
        directors = []
        
        doc = self.nlp(query)
        
        for ent in doc.ents:
            if ent.label_ == "PERSON":
                person_name = ent.text.strip()
                # Simple heuristic: if "directed" appears near the name, it's likely a director
                if self._is_likely_director(query, person_name):
                    directors.append(person_name)
                else:
                    actors.append(person_name)
        
        return actors, directors
    
    def _is_likely_director(self, query: str, person_name: str) -> bool:
        """Check if person is likely a director based on context."""
        director_keywords = ['directed', 'director', 'by']
        query_lower = query.lower()
        person_lower = person_name.lower()
        
        # Find position of person name in query
        person_pos = query_lower.find(person_lower)
        if person_pos == -1:
            return False
        
        # Check words around the person name
        words_before = query_lower[:person_pos].split()[-3:]  # 3 words before
        words_after = query_lower[person_pos + len(person_lower):].split()[:3]  # 3 words after
        
        context_words = words_before + words_after
        
        return any(keyword in context_words for keyword in director_keywords)
    
    def _extract_keywords(self, query: str, query_info: SearchQuery) -> List[str]:
        """Extract keywords from query, excluding stop words and detected entities."""
        words = query.lower().split()
        keywords = []
        
        # Remove detected entities from consideration
        detected_entities = (
            query_info.genres + 
            query_info.actors + 
            query_info.directors
        )
        detected_entities_lower = [entity.lower() for entity in detected_entities]
        
        for word in words:
            # Clean word of punctuation
            clean_word = re.sub(r'[^\w]', '', word)
            
            if (clean_word and 
                clean_word not in self.stop_words and
                len(clean_word) > 2 and
                not clean_word.isdigit() and
                not any(clean_word in entity for entity in detected_entities_lower)):
                keywords.append(clean_word)
        
        return keywords
