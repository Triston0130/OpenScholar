# tests/test_security_validation.py
"""
Unit tests for security validation module
Tests input validation, sanitization, and API key management
"""

import pytest
from pydantic import ValidationError
from app.security.validation import (
    SearchQueryValidator,
    APIKeyValidator,
    validate_search_request,
    sanitize_paper_data,
    sanitize_error_message,
    SecurityMiddleware
)

class TestSearchQueryValidator:
    """Test search query validation"""
    
    def test_valid_query(self):
        """Test validation of valid search queries"""
        valid_data = {
            "query": "machine learning education",
            "limit": 50,
            "year_start": 2020,
            "year_end": 2024
        }
        validator = SearchQueryValidator(**valid_data)
        assert validator.query == "machine learning education"
        assert validator.limit == 50
        assert validator.year_start == 2020
        assert validator.year_end == 2024
    
    def test_empty_query_validation(self):
        """Test that empty queries are rejected"""
        with pytest.raises(ValidationError) as exc_info:
            SearchQueryValidator(query="")
        
        errors = exc_info.value.errors()
        assert any("empty" in str(error["msg"]).lower() for error in errors)
    
    def test_xss_prevention(self):
        """Test XSS attack prevention"""
        malicious_queries = [
            "<script>alert('xss')</script>",
            "javascript:alert('xss')",
            "vbscript:alert('xss')",
            "search term'; DROP TABLE papers; --"
        ]
        
        for malicious_query in malicious_queries:
            with pytest.raises(ValidationError) as exc_info:
                SearchQueryValidator(query=malicious_query)
            
            errors = exc_info.value.errors()
            assert any("forbidden" in str(error["msg"]).lower() for error in errors)
    
    def test_query_length_limit(self):
        """Test query length limitations"""
        long_query = "a" * 501  # Over 500 character limit
        
        with pytest.raises(ValidationError) as exc_info:
            SearchQueryValidator(query=long_query)
        
        errors = exc_info.value.errors()
        assert any("too long" in str(error["msg"]).lower() for error in errors)
    
    def test_limit_validation(self):
        """Test search limit validation"""
        # Test valid limits
        validator = SearchQueryValidator(query="test", limit=10)
        assert validator.limit == 10
        
        # Test invalid limits
        with pytest.raises(ValidationError):
            SearchQueryValidator(query="test", limit=0)
        
        with pytest.raises(ValidationError):
            SearchQueryValidator(query="test", limit=201)
    
    def test_year_validation(self):
        """Test year range validation"""
        # Valid years
        validator = SearchQueryValidator(query="test", year_start=2000, year_end=2024)
        assert validator.year_start == 2000
        assert validator.year_end == 2024
        
        # Invalid years
        with pytest.raises(ValidationError):
            SearchQueryValidator(query="test", year_start=1800)  # Too old
        
        with pytest.raises(ValidationError):
            SearchQueryValidator(query="test", year_end=2030)  # Too far in future
    
    def test_publication_type_validation(self):
        """Test publication type validation"""
        valid_types = ['journal-article', 'conference-paper', 'book-chapter']
        
        for pub_type in valid_types:
            validator = SearchQueryValidator(query="test", publication_type=pub_type)
            assert validator.publication_type == pub_type
        
        # Invalid type
        with pytest.raises(ValidationError):
            SearchQueryValidator(query="test", publication_type="invalid-type")

class TestAPIKeyValidator:
    """Test API key validation"""
    
    def test_valid_api_keys(self):
        """Test validation of valid API keys"""
        validator = APIKeyValidator()
        config = {
            'CORE_API_KEY': 'valid-api-key-123',
            'CROSSREF_EMAIL': 'test@example.com',
            'SEMANTIC_SCHOLAR_API_KEY': 'another-valid-key'
        }
        
        validated = validator.validate_api_keys(config)
        assert 'CORE_API_KEY' in validated
        assert validated['CORE_API_KEY'] == 'valid-api-key-123'
    
    def test_missing_required_keys(self):
        """Test handling of missing required API keys"""
        validator = APIKeyValidator()
        config = {}  # No keys provided
        
        # Should not raise exception but should log warnings
        validated = validator.validate_api_keys(config)
        assert len(validated) == 0
    
    def test_invalid_api_key_format(self):
        """Test rejection of invalid API key formats"""
        validator = APIKeyValidator()
        
        invalid_keys = [
            'key with spaces',
            'key@#$%^&*()',
            'x',  # Too short
            '',   # Empty
        ]
        
        for invalid_key in invalid_keys:
            with pytest.raises(ValueError):
                validator._sanitize_api_key(invalid_key)

class TestPaperDataSanitization:
    """Test paper data sanitization"""
    
    def test_sanitize_valid_paper_data(self):
        """Test sanitization of valid paper data"""
        paper_data = {
            'title': 'Valid Paper Title',
            'abstract': 'This is a valid abstract.',
            'year': 2023,
            'citation_count': 42,
            'url': 'https://example.com/paper'
        }
        
        sanitized = sanitize_paper_data(paper_data)
        assert sanitized['title'] == 'Valid Paper Title'
        assert sanitized['year'] == 2023
        assert sanitized['citation_count'] == 42
    
    def test_sanitize_malicious_content(self):
        """Test sanitization of malicious content in paper data"""
        malicious_data = {
            'title': '<script>alert("xss")</script>Malicious Title',
            'abstract': 'Abstract with <img src="x" onerror="alert()"> content',
            'year': 'invalid_year',
            'citation_count': -5,
            'url': 'javascript:alert("xss")'
        }
        
        sanitized = sanitize_paper_data(malicious_data)
        
        # HTML should be stripped
        assert '<script>' not in sanitized['title']
        assert '<img' not in sanitized['abstract']
        
        # Invalid year should be set to None
        assert sanitized['year'] is None
        
        # Negative citation count should be set to 0
        assert sanitized['citation_count'] == 0
        
        # Invalid URL should be set to None
        assert sanitized['url'] is None
    
    def test_sanitize_edge_cases(self):
        """Test sanitization edge cases"""
        edge_cases = {
            'title': None,
            'year': '2023',  # String year should be converted
            'citation_count': '42',  # String citation count
            'url': 'http://valid-url.com'  # Valid HTTP URL
        }
        
        sanitized = sanitize_paper_data(edge_cases)
        assert sanitized['year'] == 2023
        assert sanitized['citation_count'] == 42
        assert sanitized['url'] == 'http://valid-url.com'

class TestErrorMessageSanitization:
    """Test error message sanitization"""
    
    def test_sanitize_api_keys_in_errors(self):
        """Test that API keys are removed from error messages"""
        error_with_key = "API error: api_key=abc123secret failed to authenticate"
        sanitized = sanitize_error_message(error_with_key)
        assert "abc123secret" not in sanitized
        assert "api_key=***" in sanitized
    
    def test_sanitize_tokens_in_errors(self):
        """Test that tokens are removed from error messages"""
        error_with_token = "Authentication failed: token=xyz789secret"
        sanitized = sanitize_error_message(error_with_token)
        assert "xyz789secret" not in sanitized
        assert "token=***" in sanitized
    
    def test_sanitize_passwords_in_errors(self):
        """Test that passwords are removed from error messages"""
        error_with_password = "Login failed: password=mypassword123"
        sanitized = sanitize_error_message(error_with_password)
        assert "mypassword123" not in sanitized
        assert "password=***" in sanitized

class TestSecurityMiddleware:
    """Test security middleware functionality"""
    
    def test_cors_origins_development(self):
        """Test CORS origins for development environment"""
        middleware = SecurityMiddleware()
        origins = middleware.get_cors_origins("development")
        
        assert "http://localhost:3000" in origins
        assert "http://localhost:3001" in origins
        assert "https://openscholar.netlify.app" not in origins
    
    def test_cors_origins_production(self):
        """Test CORS origins for production environment"""
        middleware = SecurityMiddleware()
        origins = middleware.get_cors_origins("production")
        
        assert "https://openscholar.netlify.app" in origins
        assert "https://www.openscholar.app" in origins
        assert "http://localhost:3000" not in origins

# Integration tests
class TestValidationIntegration:
    """Integration tests for validation components"""
    
    def test_search_request_validation_flow(self):
        """Test complete search request validation flow"""
        valid_request = {
            "query": "education technology",
            "limit": 25,
            "year_start": 2020,
            "year_end": 2024,
            "publication_type": "journal-article"
        }
        
        # Should not raise any exceptions
        validated = validate_search_request(valid_request)
        assert validated.query == "education technology"
        assert validated.limit == 25
    
    def test_search_request_validation_with_invalid_data(self):
        """Test search request validation with invalid data"""
        invalid_request = {
            "query": "<script>alert('xss')</script>",
            "limit": 500,  # Too high
            "year_start": 2025,
            "year_end": 2020  # Invalid range
        }
        
        with pytest.raises(Exception):  # Should raise HTTPException or ValidationError
            validate_search_request(invalid_request)

if __name__ == "__main__":
    pytest.main([__file__])
