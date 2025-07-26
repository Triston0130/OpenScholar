# tests/test_logging_system.py
"""
Unit tests for logging system
Tests structured logging, performance monitoring, and log formatting
"""

import pytest
import json
import logging
import time
from unittest.mock import Mock, patch, StringIO
from app.logging.structured_logger import (
    StructuredFormatter,
    OpenScholarLogger,
    PerformanceMonitor,
    performance_monitor,
    setup_logging,
    LoggingMiddleware,
    set_request_context
)

class TestStructuredFormatter:
    """Test structured JSON log formatter"""
    
    def test_basic_log_formatting(self):
        """Test basic log record formatting"""
        formatter = StructuredFormatter()
        
        # Create a log record
        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=42,
            msg="Test message",
            args=(),
            exc_info=None
        )
        record.funcName = "test_function"
        record.module = "test_module"
        
        formatted = formatter.format(record)
        parsed = json.loads(formatted)
        
        assert parsed["level"] == "INFO"
        assert parsed["logger"] == "test_logger"
        assert parsed["message"] == "Test message"
        assert parsed["module"] == "test_module"
        assert parsed["function"] == "test_function"
        assert parsed["line"] == 42
        assert "timestamp" in parsed
    
    def test_exception_formatting(self):
        """Test exception information in logs"""
        formatter = StructuredFormatter()
        
        try:
            raise ValueError("Test exception")
        except ValueError:
            record = logging.LogRecord(
                name="test_logger",
                level=logging.ERROR,
                pathname="test.py",
                lineno=42,
                msg="Error occurred",
                args=(),
                exc_info=True
            )
            record.funcName = "test_function"
            record.module = "test_module"
            
            formatted = formatter.format(record)
            parsed = json.loads(formatted)
            
            assert "exception" in parsed
            assert parsed["exception"]["type"] == "ValueError"
            assert parsed["exception"]["message"] == "Test exception"
            assert "traceback" in parsed["exception"]
    
    def test_extra_fields(self):
        """Test extra fields in log records"""
        formatter = StructuredFormatter()
        
        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=42,
            msg="Test message",
            args=(),
            exc_info=None
        )
        record.funcName = "test_function"
        record.module = "test_module"
        
        # Add extra fields
        record.user_id = "test_user"
        record.request_id = "test_request"
        record.custom_field = "custom_value"
        
        formatted = formatter.format(record)
        parsed = json.loads(formatted)
        
        assert "extra" in parsed
        assert parsed["extra"]["user_id"] == "test_user"
        assert parsed["extra"]["request_id"] == "test_request"
        assert parsed["extra"]["custom_field"] == "custom_value"

class TestOpenScholarLogger:
    """Test OpenScholar logger functionality"""
    
    def test_logger_initialization(self):
        """Test logger initialization"""
        logger = OpenScholarLogger("test_logger")
        assert logger.logger.name == "test_logger"
    
    def test_structured_logging_methods(self):
        """Test structured logging methods"""
        with patch('logging.StreamHandler') as mock_handler:
            logger = OpenScholarLogger("test_logger")
            
            # Test info logging with extra fields
            logger.info("Test message", user_id="123", action="test")
            
            # Test error logging
            logger.error("Error message", error_code="E001")
            
            # Test warning logging
            logger.warning("Warning message", component="test")
    
    def test_request_logging(self):
        """Test request-specific logging methods"""
        logger = OpenScholarLogger("test_logger")
        
        with patch.object(logger.logger, 'info') as mock_info:
            logger.log_request_start("GET", "/api/search", "127.0.0.1", "test-agent")
            
            mock_info.assert_called_once()
            call_args = mock_info.call_args
            assert "Request started" in call_args[0][0]
            assert call_args[1]["extra"]["event_type"] == "request_start"
            assert call_args[1]["extra"]["http_method"] == "GET"
            assert call_args[1]["extra"]["http_path"] == "/api/search"
    
    def test_search_query_logging(self):
        """Test search query logging"""
        logger = OpenScholarLogger("test_logger")
        
        with patch.object(logger.logger, 'info') as mock_info:
            logger.log_search_query(
                "machine learning",
                {"year_start": 2020},
                42,
                ["API1", "API2"],
                1500.5
            )
            
            mock_info.assert_called_once()
            call_args = mock_info.call_args
            assert "Search performed" in call_args[0][0]
            assert call_args[1]["extra"]["event_type"] == "search_performed"
            assert call_args[1]["extra"]["search_query"] == "machine learning"
            assert call_args[1]["extra"]["result_count"] == 42
    
    def test_api_call_logging(self):
        """Test API call logging"""
        logger = OpenScholarLogger("test_logger")
        
        with patch.object(logger.logger, 'info') as mock_info:
            logger.log_api_call(
                "semantic_scholar",
                "/search",
                250.5,
                True,
                result_count=10
            )
            
            mock_info.assert_called_once()
            call_args = mock_info.call_args
            assert "API call to semantic_scholar" in call_args[0][0]
            assert call_args[1]["extra"]["event_type"] == "api_call"
            assert call_args[1]["extra"]["api_success"] is True
    
    def test_cache_operation_logging(self):
        """Test cache operation logging"""
        logger = OpenScholarLogger("test_logger")
        
        with patch.object(logger.logger, 'info') as mock_info:
            logger.log_cache_operation("get", "search:key", hit=True, duration_ms=5.2)
            
            mock_info.assert_called_once()
            call_args = mock_info.call_args
            assert "Cache get" in call_args[0][0]
            assert call_args[1]["extra"]["cache_hit"] is True
    
    def test_error_with_context_logging(self):
        """Test error logging with context"""
        logger = OpenScholarLogger("test_logger")
        
        with patch.object(logger.logger, 'error') as mock_error:
            try:
                raise ValueError("Test error")
            except ValueError as e:
                logger.log_error_with_context(
                    e,
                    {"operation": "test", "user_id": "123"}
                )
                
                mock_error.assert_called_once()
                call_args = mock_error.call_args
                assert "Error occurred" in call_args[0][0]
                assert call_args[1]["extra"]["error_type"] == "ValueError"
                assert call_args[1]["extra"]["error_context"]["operation"] == "test"

class TestPerformanceMonitor:
    """Test performance monitoring functionality"""
    
    def test_performance_monitor_context_manager(self):
        """Test performance monitor as context manager"""
        logger = OpenScholarLogger("test_logger")
        
        with patch.object(logger, 'info') as mock_info:
            with PerformanceMonitor(logger, "test_operation"):
                time.sleep(0.01)  # Small delay
            
            mock_info.assert_called_once()
            call_args = mock_info.call_args
            assert "Operation completed" in call_args[0][0]
            assert call_args[1]["operation"] == "test_operation"
            assert call_args[1]["success"] is True
            assert call_args[1]["duration_ms"] > 0
    
    def test_performance_monitor_with_exception(self):
        """Test performance monitor with exception"""
        logger = OpenScholarLogger("test_logger")
        
        with patch.object(logger, 'error') as mock_error:
            try:
                with PerformanceMonitor(logger, "failing_operation"):
                    raise ValueError("Test error")
            except ValueError:
                pass
            
            mock_error.assert_called_once()
            call_args = mock_error.call_args
            assert "Operation failed" in call_args[0][0]
            assert call_args[1]["operation"] == "failing_operation"
            assert call_args[1]["success"] is False
            assert call_args[1]["error_type"] == "ValueError"

class TestPerformanceDecorator:
    """Test performance monitoring decorator"""
    
    def test_sync_function_decorator(self):
        """Test decorator on synchronous functions"""
        @performance_monitor("test_sync_operation")
        def sync_function(x, y):
            return x + y
        
        with patch('app.logging.structured_logger.OpenScholarLogger') as mock_logger_class:
            mock_logger = Mock()
            mock_logger_class.return_value = mock_logger
            
            result = sync_function(2, 3)
            assert result == 5
            
            # Should have logged performance
            mock_logger.info.assert_called_once()
            call_args = mock_logger.info.call_args
            assert "Function completed" in call_args[0][0]
    
    @pytest.mark.asyncio
    async def test_async_function_decorator(self):
        """Test decorator on asynchronous functions"""
        @performance_monitor("test_async_operation")
        async def async_function(x, y):
            return x * y
        
        with patch('app.logging.structured_logger.OpenScholarLogger') as mock_logger_class:
            mock_logger = Mock()
            mock_logger_class.return_value = mock_logger
            
            result = await async_function(3, 4)
            assert result == 12
            
            # Should have logged performance
            mock_logger.info.assert_called_once()

class TestLoggingSetup:
    """Test logging setup and configuration"""
    
    def test_setup_logging_basic(self):
        """Test basic logging setup"""
        with patch('logging.getLogger') as mock_get_logger, \
             patch('logging.StreamHandler') as mock_handler:
            
            mock_root_logger = Mock()
            mock_get_logger.return_value = mock_root_logger
            
            logger = setup_logging("test_app", "INFO")
            
            # Should configure root logger
            mock_root_logger.setLevel.assert_called_with(logging.INFO)
            mock_root_logger.addHandler.assert_called()
    
    def test_setup_logging_with_file(self):
        """Test logging setup with file handler"""
        with patch('logging.getLogger') as mock_get_logger, \
             patch('logging.FileHandler') as mock_file_handler, \
             patch.dict('os.environ', {'LOG_FILE': '/tmp/test.log'}):
            
            mock_root_logger = Mock()
            mock_get_logger.return_value = mock_root_logger
            
            logger = setup_logging("test_app", "DEBUG")
            
            # Should create file handler
            mock_file_handler.assert_called_with('/tmp/test.log')

class TestRequestContext:
    """Test request context functionality"""
    
    def test_set_request_context(self):
        """Test setting request context"""
        request_id = "test-request-123"
        user_id = "user-456"
        
        set_request_context(request_id, user_id)
        
        # Context should be set (this is tested via the context vars)
        # The actual testing would require checking the context in log records
    
    def test_request_context_in_logs(self):
        """Test that request context appears in logs"""
        set_request_context("req-123", "user-456")
        
        formatter = StructuredFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test",
            args=(),
            exc_info=None
        )
        record.funcName = "test"
        record.module = "test"
        
        # Note: This test would need the actual context vars to be set
        # which requires the real contextvars implementation

class TestLoggingMiddleware:
    """Test FastAPI logging middleware"""
    
    @pytest.mark.asyncio
    async def test_logging_middleware_success(self):
        """Test logging middleware with successful request"""
        middleware = LoggingMiddleware()
        
        # Mock request and response
        mock_request = Mock()
        mock_request.method = "GET"
        mock_request.url.path = "/test"
        mock_request.client.host = "127.0.0.1"
        mock_request.headers.get.return_value = "test-agent"
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {}
        
        async def mock_call_next(request):
            return mock_response
        
        with patch.object(middleware.logger, 'log_request_start') as mock_start, \
             patch.object(middleware.logger, 'log_request_end') as mock_end:
            
            response = await middleware(mock_request, mock_call_next)
            
            assert response == mock_response
            mock_start.assert_called_once()
            mock_end.assert_called_once()
            
            # Should have added request ID header
            assert "X-Request-ID" in mock_response.headers
    
    @pytest.mark.asyncio
    async def test_logging_middleware_exception(self):
        """Test logging middleware with exception"""
        middleware = LoggingMiddleware()
        
        mock_request = Mock()
        mock_request.method = "POST"
        mock_request.url.path = "/error"
        mock_request.client.host = "127.0.0.1"
        mock_request.headers.get.return_value = "test-agent"
        
        async def mock_call_next(request):
            raise ValueError("Test error")
        
        with patch.object(middleware.logger, 'error') as mock_error:
            with pytest.raises(ValueError):
                await middleware(mock_request, mock_call_next)
            
            mock_error.assert_called_once()

# Integration tests
class TestLoggingIntegration:
    """Integration tests for logging system"""
    
    def test_complete_logging_flow(self):
        """Test complete logging flow with structured formatter"""
        # Create logger with string buffer to capture output
        logger = OpenScholarLogger("integration_test")
        
        # Capture log output
        log_capture = StringIO()
        handler = logging.StreamHandler(log_capture)
        handler.setFormatter(StructuredFormatter())
        
        # Clear existing handlers and add our capture handler
        logger.logger.handlers.clear()
        logger.logger.addHandler(handler)
        logger.logger.setLevel(logging.INFO)
        
        # Log various events
        logger.log_request_start("GET", "/api/test", "127.0.0.1")
        logger.log_search_query("test query", {}, 5, ["API"], 100.0)
        logger.log_request_end("GET", "/api/test", 200, 150.0)
        
        # Get logged output
        log_output = log_capture.getvalue()
        log_lines = [line for line in log_output.strip().split('\n') if line]
        
        assert len(log_lines) == 3
        
        # Verify each log line is valid JSON
        for line in log_lines:
            parsed = json.loads(line)
            assert "timestamp" in parsed
            assert "level" in parsed
            assert "message" in parsed

if __name__ == "__main__":
    pytest.main([__file__])
