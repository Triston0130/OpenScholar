# app/security/validation.py
"""
Input validation and security middleware for OpenScholar API
Addresses critical security issues identified in audit
"""

import re
import bleach
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, validator, ValidationError
from fastapi import HTTPException, status
import logging

logger = logging.getLogger(__name__)

class SearchQueryValidator(BaseModel):
    """Validate and sanitize search queries"""
    query: str
    limit: Optional[int] = 50
    year_start: Optional[int] = None
    year_end: Optional[int] = None
    publication_type: Optional[str] = None
    study_type: Optional[str] = None
    page: Optional[int] = 1
    per_page: Optional[int] = 20
    require_authors: Optional[bool] = True
    sources: Optional[List[str]] = None
    
    @validator('query')
    def validate_query(cls, v):
        if not v or not v.strip():
            raise ValueError("Query cannot be empty")
        
        # Remove any potential SQL injection patterns
        forbidden_patterns = [
            r'[;\'\"\\]',  # SQL injection chars
            r'<script[^>]*>.*?</script>',  # XSS scripts
            r'javascript:',  # JavaScript URLs
            r'vbscript:',   # VBScript URLs
        ]
        
        for pattern in forbidden_patterns:
            if re.search(pattern, v, re.IGNORECASE):
                raise ValueError(f"Query contains forbidden characters or patterns")
        
        # Sanitize HTML/XML tags but allow academic symbols
        cleaned = bleach.clean(v, tags=[], attributes={}, strip=True)
        
        # Limit length
        if len(cleaned) > 500:
            raise ValueError("Query too long (max 500 characters)")
            
        return cleaned.strip()
    
    @validator('limit')
    def validate_limit(cls, v):
        if v is not None:
            if v < 1 or v > 200:
                raise ValueError("Limit must be between 1 and 200")
        return v
    
    @validator('year_start', 'year_end')
    def validate_years(cls, v):
        if v is not None:
            current_year = 2025
            if v < 1700 or v > current_year + 1:
                raise ValueError(f"Year must be between 1700 and {current_year + 1}")
        return v
    
    @validator('publication_type')
    def validate_publication_type(cls, v):
        if v is not None:
            allowed_types = [
                'journal-article', 'conference-paper', 'book-chapter', 
                'book', 'preprint', 'thesis', 'report', 'review'
            ]
            if v not in allowed_types:
                raise ValueError(f"Invalid publication type. Allowed: {allowed_types}")
        return v
    
    @validator('study_type')
    def validate_study_type(cls, v):
        if v is not None:
            allowed_types = [
                'experimental', 'observational', 'review', 'meta-analysis',
                'case-study', 'survey', 'theoretical'
            ]
            if v not in allowed_types:
                raise ValueError(f"Invalid study type. Allowed: {allowed_types}")
        return v
    
    @validator('sources')
    def validate_sources(cls, v):
        if v is not None:
            # Allow all known academic and book sources
            allowed_sources = [
                'ERIC', 'CORE', 'DOAJ', 'Europe PMC', 'PubMed Central', 'PubMed', 
                'Semantic Scholar', 'OpenAlex', 'arXiv', 'Crossref',
                'DOAB', 'Project Gutenberg', 'Internet Archive', 'Open Library', 'OpenStax',
                'OAPEN', 'BHL', 'NLM Bookshelf', 'PLOS', 'BioMed Central', 
                'Unpaywall', 'BASE', 'Google Books', 'Google Search',
                # OER sources
                'Open Textbook Library', 'Pressbooks', 'LibreTexts', 'MERLOT', 
                'OER Commons', 'MIT OpenCourseWare'
            ]
            
            if not isinstance(v, list):
                raise ValueError("Sources must be a list")
            
            for source in v:
                if source not in allowed_sources:
                    raise ValueError(f"Invalid source '{source}'. Allowed: {allowed_sources}")
            
            if len(v) > 29:  # Maximum number of sources
                raise ValueError("Too many sources selected (max 29)")
        
        return v

class APIKeyValidator:
    """Validate and manage API keys securely"""
    
    def __init__(self):
        self.required_keys = [
            'CORE_API_KEY',
        ]
        self.optional_keys = [
            'SEMANTIC_SCHOLAR_API_KEY',
            'CROSSREF_EMAIL',
            'PUBMED_API_KEY',
        ]
    
    def validate_api_keys(self, config: Dict[str, Any]) -> Dict[str, str]:
        """Validate that required API keys are present and properly formatted"""
        errors = []
        validated_keys = {}
        
        # Check required keys
        for key in self.required_keys:
            value = config.get(key)
            if not value:
                errors.append(f"Missing required API key: {key}")
            else:
                validated_keys[key] = self._sanitize_api_key(value)
        
        # Check optional keys
        for key in self.optional_keys:
            value = config.get(key)
            if value:
                validated_keys[key] = self._sanitize_api_key(value)
        
        if errors:
            logger.error(f"API key validation failed: {errors}")
            # Don't raise in production, just log warnings
            for error in errors:
                logger.warning(error)
        
        return validated_keys
    
    def _sanitize_api_key(self, key: str) -> str:
        """Basic sanitization of API keys"""
        if not isinstance(key, str):
            raise ValueError("API key must be a string")
        
        # Remove whitespace
        key = key.strip()
        
        # Basic format validation (alphanumeric + common special chars)
        if not re.match(r'^[a-zA-Z0-9\-_\.@]+$', key):
            raise ValueError("API key contains invalid characters")
        
        if len(key) < 5:  # More lenient for email addresses
            raise ValueError("API key too short (minimum 5 characters)")
        
        return key

def validate_search_request(request_data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate incoming search request"""
    try:
        # Create validator with known fields
        validator_data = {
            'query': request_data.get('query'),
            'limit': request_data.get('limit', 50),
            'year_start': request_data.get('year_start'),
            'year_end': request_data.get('year_end'),
            'publication_type': request_data.get('publication_type'),
            'study_type': request_data.get('study_type'),
            'page': request_data.get('page', 1),
            'per_page': request_data.get('per_page', 20),
            'require_authors': request_data.get('require_authors', True),
            'sources': request_data.get('sources')
        }
        
        # Validate with SearchQueryValidator
        validated = SearchQueryValidator(**validator_data)
        
        # Return the original request data with validated fields
        request_data['query'] = validated.query
        if validated.sources is not None:
            request_data['sources'] = validated.sources
        
        return request_data
        
    except ValidationError as e:
        logger.warning(f"Search validation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid search parameters: {e}"
        )

def sanitize_paper_data(paper_data: Dict[str, Any]) -> Dict[str, Any]:
    """Sanitize paper data from external APIs before storing/returning"""
    
    # Fields that should be cleaned of HTML/scripts
    text_fields = ['title', 'abstract', 'journal', 'venue']
    
    # Fields that should be validated as URLs
    url_fields = ['url', 'pdf_url', 'doi_url']
    
    sanitized = paper_data.copy()
    
    for field in text_fields:
        if field in sanitized and sanitized[field]:
            # Clean HTML tags and dangerous content
            sanitized[field] = bleach.clean(
                str(sanitized[field]),
                tags=[],
                attributes={},
                strip=True
            )
    
    for field in url_fields:
        if field in sanitized and sanitized[field]:
            url = str(sanitized[field])
            # Basic URL validation
            if not re.match(r'^https?://', url, re.IGNORECASE):
                logger.warning(f"Invalid URL in {field}: {url}")
                sanitized[field] = None
    
    # Validate year
    if 'year' in sanitized:
        try:
            year = int(sanitized['year'])
            if year < 1700 or year > 2026:
                sanitized['year'] = str(year)  # Keep as string
            else:
                sanitized['year'] = str(year)
        except (ValueError, TypeError):
            # If year can't be parsed as int (like "Unknown"), keep it as is
            if sanitized['year'] and isinstance(sanitized['year'], str):
                sanitized['year'] = sanitized['year']
            else:
                sanitized['year'] = "Unknown"
    
    # Validate citation count
    if 'citation_count' in sanitized:
        try:
            citations = int(sanitized['citation_count'])
            if citations < 0:
                sanitized['citation_count'] = 0
        except (ValueError, TypeError):
            sanitized['citation_count'] = 0
    
    return sanitized

def sanitize_error_message(error: str) -> str:
    """Remove sensitive information from error messages"""
    if not isinstance(error, str):
        error = str(error)
    
    # Remove API keys and sensitive data
    sanitized = re.sub(r'api[_-]?key[s]?[=:]\s*[\w-]+', 'api_key=***', error, flags=re.IGNORECASE)
    sanitized = re.sub(r'token[s]?[=:]\s*[\w-]+', 'token=***', sanitized, flags=re.IGNORECASE)
    sanitized = re.sub(r'password[s]?[=:]\s*[\w-]+', 'password=***', sanitized, flags=re.IGNORECASE)
    
    return sanitized

# Security middleware class
class SecurityMiddleware:
    """Security middleware for FastAPI application"""
    
    def __init__(self):
        self.key_validator = APIKeyValidator()
    
    def get_cors_origins(self, environment: str = "development") -> List[str]:
        """Get appropriate CORS origins for environment"""
        
        if environment == "production":
            return [
                "https://openscholar.netlify.app",
                "https://www.openscholar.app",
                "https://openscholar.app"
            ]
        else:
            return [
                "http://localhost:3000",
                "http://localhost:3001", 
                "http://127.0.0.1:3000",
                "http://127.0.0.1:3001"
            ]
