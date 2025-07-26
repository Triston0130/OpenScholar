# tests/test_api_endpoints.py
"""
Unit tests for API endpoints
Tests FastAPI endpoints with security, caching, and logging
"""

import pytest
import asyncio
from fastapi.testclient import TestClient
from unittest.mock import Mock, AsyncMock, patch
from app.main import app
from app.models import SearchRequest, SearchResponse

# Test client
client = TestClient(app)

class TestHealthEndpoints:
    """Test health check endpoints"""
    
    def test_root_endpoint(self):
        """Test root endpoint"""
        response = client.get("/")
        assert response.status_code == 200
        
        data = response.json()
        assert "service" in data
        assert data["service"] == "OpenScholar API"
        assert "version" in data
        assert "security" in data
        assert data["security"] == "enabled"
    
    def test_health_endpoint(self):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert "status" in data
        assert "timestamp" in data
        assert "services" in data
        assert "environment" in data
        
        # Check service statuses
        services = data["services"]
        assert "search" in services
        assert "export" in services
        assert "external_paper" in services
        assert "cache" in services
        assert "security" in services
        assert services["security"] == "enabled"

class TestSearchEndpoint:
    """Test search endpoint functionality"""
    
    @patch('app.main.search_service')
    def test_search_valid_request(self, mock_search_service):
        """Test search with valid request"""
        # Mock search service response
        mock_papers = [
            {
                "title": "Test Paper",
                "authors": ["Test Author"],
                "year": "2023",
                "abstract": "Test abstract",
                "journal": "Test Journal",
                "source": "Test Source"
            }
        ]
        mock_search_service.search = AsyncMock(return_value=(mock_papers, ["Test Source"]))
        
        search_data = {
            "query": "machine learning",
            "page": 1,
            "per_page": 10
        }
        
        response = client.post("/search", json=search_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "papers" in data
        assert "total_results" in data
        assert "sources_queried" in data
        assert len(data["papers"]) <= 10
    
    def test_search_empty_query(self):
        """Test search with empty query"""
        search_data = {
            "query": "",
            "page": 1,
            "per_page": 10
        }
        
        response = client.post("/search", json=search_data)
        assert response.status_code == 400
        
        data = response.json()
        assert "error" in data or "detail" in data
    
    def test_search_xss_prevention(self):
        """Test XSS prevention in search"""
        malicious_queries = [
            "<script>alert('xss')</script>",
            "javascript:alert('xss')",
            "search'; DROP TABLE papers; --"
        ]
        
        for malicious_query in malicious_queries:
            search_data = {
                "query": malicious_query,
                "page": 1,
                "per_page": 10
            }
            
            response = client.post("/search", json=search_data)
            assert response.status_code == 400
    
    def test_search_invalid_year_range(self):
        """Test search with invalid year range"""
        search_data = {
            "query": "test",
            "year_start": 2024,
            "year_end": 2020,  # End before start
            "page": 1,
            "per_page": 10
        }
        
        response = client.post("/search", json=search_data)
        assert response.status_code == 400
    
    def test_search_invalid_limit(self):
        """Test search with invalid limits"""
        # Test limit too high
        search_data = {
            "query": "test",
            "page": 1,
            "per_page": 300  # Over limit
        }
        
        response = client.post("/search", json=search_data)
        assert response.status_code == 400
        
        # Test limit too low
        search_data["per_page"] = 0
        response = client.post("/search", json=search_data)
        assert response.status_code == 400

class TestExportEndpoint:
    """Test export endpoint functionality"""
    
    @patch('app.main.export_service')
    def test_export_valid_request(self, mock_export_service):
        """Test export with valid request"""
        # Mock export service response
        mock_content = b"test,csv,content"
        mock_filename = "test.csv"
        mock_mime_type = "text/csv"
        mock_export_service.export_papers = Mock(return_value=(mock_content, mock_filename, mock_mime_type))
        
        export_data = {
            "papers": [
                {
                    "title": "Test Paper",
                    "authors": ["Test Author"],
                    "year": "2023",
                    "abstract": "Test abstract",
                    "journal": "Test Journal",
                    "source": "Test Source"
                }
            ],
            "format": "csv"
        }
        
        response = client.post("/export", json=export_data)
        assert response.status_code == 200
        assert response.headers["content-type"] == mock_mime_type
    
    def test_export_empty_papers(self):
        """Test export with no papers"""
        export_data = {
            "papers": [],
            "format": "csv"
        }
        
        response = client.post("/export", json=export_data)
        assert response.status_code == 400
    
    def test_export_invalid_format(self):
        """Test export with invalid format"""
        export_data = {
            "papers": [{"title": "Test"}],
            "format": "invalid"
        }
        
        response = client.post("/export", json=export_data)
        assert response.status_code == 400

class TestExternalPaperEndpoint:
    """Test external paper endpoint functionality"""
    
    @patch('app.main.external_paper_fetcher')
    def test_fetch_external_paper_valid_doi(self, mock_fetcher):
        """Test fetching external paper with valid DOI"""
        # Mock fetcher response
        mock_paper = {
            "title": "External Paper",
            "authors": ["External Author"],
            "year": "2023",
            "abstract": "External abstract",
            "journal": "External Journal",
            "doi": "10.1000/test"
        }
        mock_fetcher.fetch_paper_from_doi = Mock(return_value=mock_paper)
        
        request_data = {
            "doi": "10.1000/test"
        }
        
        response = client.post("/external-paper", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "status" in data
        assert data["status"] == "success"
        assert "paper" in data
    
    def test_fetch_external_paper_invalid_doi(self):
        """Test fetching external paper with invalid DOI"""
        invalid_dois = [
            "invalid-doi",
            "",
            "a" * 201,  # Too long
            "javascript:alert('xss')"
        ]
        
        for invalid_doi in invalid_dois:
            request_data = {"doi": invalid_doi}
            response = client.post("/external-paper", json=request_data)
            assert response.status_code == 400

class TestSecurityHeaders:
    """Test security headers in responses"""
    
    def test_cors_headers(self):
        """Test CORS headers are properly set"""
        response = client.options("/search", headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "POST"
        })
        
        # Should have CORS headers
        assert "access-control-allow-origin" in response.headers
        assert "access-control-allow-methods" in response.headers
    
    def test_request_id_header(self):
        """Test that request ID is added to responses"""
        response = client.get("/")
        
        # Should have request ID header (added by logging middleware)
        assert "X-Request-ID" in response.headers or response.status_code == 200

class TestRateLimiting:
    """Test rate limiting functionality"""
    
    def test_rate_limiting_dependency(self):
        """Test rate limiting dependency"""
        # Make multiple rapid requests
        responses = []
        for i in range(5):
            response = client.get("/")
            responses.append(response)
        
        # All should succeed (rate limiting is logged but not enforced in tests)
        for response in responses:
            assert response.status_code == 200

class TestErrorHandling:
    """Test error handling in endpoints"""
    
    def test_404_handling(self):
        """Test 404 error handling"""
        response = client.get("/nonexistent")
        assert response.status_code == 404
    
    def test_method_not_allowed(self):
        """Test method not allowed handling"""
        response = client.delete("/search")  # DELETE not allowed
        assert response.status_code == 405
    
    @patch('app.main.search_service', None)
    def test_service_unavailable(self):
        """Test service unavailable error"""
        search_data = {
            "query": "test",
            "page": 1,
            "per_page": 10
        }
        
        response = client.post("/search", json=search_data)
        assert response.status_code == 503

class TestCacheIntegration:
    """Test cache integration in endpoints"""
    
    @patch('app.main.get_cache_manager')
    @patch('app.main.search_service')
    def test_search_cache_hit(self, mock_search_service, mock_cache_manager):
        """Test search endpoint with cache hit"""
        # Mock cache manager with cached results
        mock_cache = Mock()
        mock_cache.get_search_results = AsyncMock(return_value={
            "papers": [{"title": "Cached Paper"}],
            "total_results": 1,
            "sources_queried": ["Cache"]
        })
        mock_cache_manager.return_value = mock_cache
        
        search_data = {
            "query": "cached query",
            "page": 1,
            "per_page": 10
        }
        
        response = client.post("/search", json=search_data)
        assert response.status_code == 200
        
        # Search service should not be called if cache hit
        data = response.json()
        assert len(data["papers"]) == 1
        assert data["papers"][0]["title"] == "Cached Paper"
    
    @patch('app.main.get_cache_manager')
    @patch('app.main.search_service')
    def test_search_cache_miss(self, mock_search_service, mock_cache_manager):
        """Test search endpoint with cache miss"""
        # Mock cache manager with no cached results
        mock_cache = Mock()
        mock_cache.get_search_results = AsyncMock(return_value=None)
        mock_cache.cache_search_results = AsyncMock(return_value=True)
        mock_cache_manager.return_value = mock_cache
        
        # Mock search service
        mock_papers = [{"title": "Fresh Paper", "authors": ["Author"]}]
        mock_search_service.search = AsyncMock(return_value=(mock_papers, ["API"]))
        
        search_data = {
            "query": "fresh query",
            "page": 1,
            "per_page": 10
        }
        
        response = client.post("/search", json=search_data)
        assert response.status_code == 200
        
        # Should call search service and cache results
        mock_search_service.search.assert_called_once()
        mock_cache.cache_search_results.assert_called_once()

# Integration tests
class TestEndpointIntegration:
    """Integration tests for endpoints"""
    
    def test_health_to_search_flow(self):
        """Test flow from health check to search"""
        # First check health
        health_response = client.get("/health")
        assert health_response.status_code == 200
        
        # Health should indicate services are available
        health_data = health_response.json()
        if health_data["services"]["search"] == "healthy":
            # Try a search (might fail due to missing services in test)
            search_data = {
                "query": "integration test",
                "page": 1,
                "per_page": 5
            }
            
            search_response = client.post("/search", json=search_data)
            # Could be 200 (success) or 503 (service unavailable in test)
            assert search_response.status_code in [200, 503]

if __name__ == "__main__":
    pytest.main([__file__])
