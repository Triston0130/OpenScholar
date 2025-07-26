# app/logging/structured_logger.py
"""
Comprehensive structured logging system for OpenScholar
Includes request tracking, performance monitoring, and error tracking
"""

import json
import logging
import time
import traceback
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, Union
from contextvars import ContextVar
from functools import wraps
import os

# Context variables for request tracking
request_id: ContextVar[str] = ContextVar('request_id', default='')
user_id: ContextVar[str] = ContextVar('user_id', default='')

class StructuredFormatter(logging.Formatter):
    """Custom formatter that outputs structured JSON logs"""
    
    def format(self, record: logging.LogRecord) -> str:
        # Create base log entry
        log_entry = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
        }
        
        # Add request context if available
        req_id = request_id.get('')
        if req_id:
            log_entry['request_id'] = req_id
            
        user = user_id.get('')
        if user:
            log_entry['user_id'] = user
        
        # Add exception info if present
        if record.exc_info:
            log_entry['exception'] = {
                'type': record.exc_info[0].__name__ if record.exc_info[0] else None,
                'message': str(record.exc_info[1]) if record.exc_info[1] else None,
                'traceback': traceback.format_exception(*record.exc_info)
            }
        
        # Add extra fields from the log record
        extra_fields = {}
        for key, value in record.__dict__.items():
            if key not in ['name', 'msg', 'args', 'levelname', 'levelno', 'pathname', 
                          'filename', 'module', 'exc_info', 'exc_text', 'stack_info',
                          'lineno', 'funcName', 'created', 'msecs', 'relativeCreated',
                          'thread', 'threadName', 'processName', 'process', 'getMessage',
                          'message']:
                extra_fields[key] = value
        
        if extra_fields:
            log_entry['extra'] = extra_fields
        
        return json.dumps(log_entry, default=str, separators=(',', ':'))

class OpenScholarLogger:
    """Enhanced logger with structured logging and performance monitoring"""
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        self._setup_logger()
    
    def _setup_logger(self):
        """Setup structured logging configuration"""
        if not self.logger.handlers:
            # Console handler with structured formatting
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(StructuredFormatter())
            self.logger.addHandler(console_handler)
            
            # File handler for production (if configured)
            log_file = os.getenv('LOG_FILE')
            if log_file:
                file_handler = logging.FileHandler(log_file)
                file_handler.setFormatter(StructuredFormatter())
                self.logger.addHandler(file_handler)
            
            # Set log level from environment
            log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
            self.logger.setLevel(getattr(logging, log_level, logging.INFO))
    
    def info(self, message: str, **kwargs):
        """Log info message with extra context"""
        self.logger.info(message, extra=kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log warning message with extra context"""
        self.logger.warning(message, extra=kwargs)
    
    def error(self, message: str, **kwargs):
        """Log error message with extra context"""
        self.logger.error(message, extra=kwargs)
    
    def debug(self, message: str, **kwargs):
        """Log debug message with extra context"""
        self.logger.debug(message, extra=kwargs)
    
    def critical(self, message: str, **kwargs):
        """Log critical message with extra context"""
        self.logger.critical(message, extra=kwargs)
    
    def log_request_start(self, method: str, path: str, client_ip: str, user_agent: str = None):
        """Log incoming request"""
        self.info(
            f"Request started: {method} {path}",
            event_type="request_start",
            http_method=method,
            http_path=path,
            client_ip=client_ip,
            user_agent=user_agent
        )
    
    def log_request_end(self, method: str, path: str, status_code: int, duration_ms: float):
        """Log request completion"""
        self.info(
            f"Request completed: {method} {path} - {status_code} ({duration_ms:.2f}ms)",
            event_type="request_end",
            http_method=method,
            http_path=path,
            http_status=status_code,
            duration_ms=duration_ms
        )
    
    def log_search_query(self, query: str, filters: Dict[str, Any], result_count: int, 
                        sources: list, duration_ms: float):
        """Log search queries for analytics"""
        self.info(
            f"Search performed: '{query}' returned {result_count} results",
            event_type="search_performed",
            search_query=query,
            search_filters=filters,
            result_count=result_count,
            sources_queried=sources,
            search_duration_ms=duration_ms
        )
    
    def log_api_call(self, api_name: str, endpoint: str, duration_ms: float, 
                    success: bool, result_count: int = None, error: str = None):
        """Log external API calls"""
        self.info(
            f"API call to {api_name}: {endpoint} - {'success' if success else 'failed'} ({duration_ms:.2f}ms)",
            event_type="api_call",
            api_name=api_name,
            api_endpoint=endpoint,
            api_duration_ms=duration_ms,
            api_success=success,
            api_result_count=result_count,
            api_error=error
        )
    
    def log_cache_operation(self, operation: str, key: str, hit: bool = None, 
                           duration_ms: float = None):
        """Log cache operations"""
        if hit is not None:
            message = f"Cache {operation}: {key} - {'hit' if hit else 'miss'}"
        else:
            message = f"Cache {operation}: {key}"
        
        self.info(
            message,
            event_type="cache_operation",
            cache_operation=operation,
            cache_key=key,
            cache_hit=hit,
            cache_duration_ms=duration_ms
        )
    
    def log_authentication(self, event: str, user_email: str = None, success: bool = None):
        """Log authentication events"""
        self.info(
            f"Authentication {event}: {user_email if user_email else 'unknown'}",
            event_type="authentication",
            auth_event=event,
            auth_user=user_email,
            auth_success=success
        )
    
    def log_error_with_context(self, error: Exception, context: Dict[str, Any] = None):
        """Log errors with full context"""
        self.error(
            f"Error occurred: {str(error)}",
            event_type="error",
            error_type=type(error).__name__,
            error_context=context or {}
        )

class PerformanceMonitor:
    """Performance monitoring decorator and context manager"""
    
    def __init__(self, logger: OpenScholarLogger, operation_name: str):
        self.logger = logger
        self.operation_name = operation_name
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time:
            duration_ms = (time.time() - self.start_time) * 1000
            
            if exc_type:
                self.logger.error(
                    f"Operation failed: {self.operation_name} ({duration_ms:.2f}ms)",
                    event_type="performance",
                    operation=self.operation_name,
                    duration_ms=duration_ms,
                    success=False,
                    error_type=exc_type.__name__ if exc_type else None
                )
            else:
                self.logger.info(
                    f"Operation completed: {self.operation_name} ({duration_ms:.2f}ms)",
                    event_type="performance",
                    operation=self.operation_name,
                    duration_ms=duration_ms,
                    success=True
                )

def performance_monitor(operation_name: str):
    """Decorator for monitoring function performance"""
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            logger = OpenScholarLogger(func.__module__)
            start_time = time.time()
            
            try:
                result = await func(*args, **kwargs)
                duration_ms = (time.time() - start_time) * 1000
                
                logger.info(
                    f"Function completed: {operation_name} ({duration_ms:.2f}ms)",
                    event_type="performance",
                    function=func.__name__,
                    operation=operation_name,
                    duration_ms=duration_ms,
                    success=True
                )
                return result
            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                logger.error(
                    f"Function failed: {operation_name} ({duration_ms:.2f}ms)",
                    event_type="performance",
                    function=func.__name__,
                    operation=operation_name,
                    duration_ms=duration_ms,
                    success=False,
                    error_type=type(e).__name__,
                    exc_info=True
                )
                raise
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            logger = OpenScholarLogger(func.__module__)
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                duration_ms = (time.time() - start_time) * 1000
                
                logger.info(
                    f"Function completed: {operation_name} ({duration_ms:.2f}ms)",
                    event_type="performance",
                    function=func.__name__,
                    operation=operation_name,
                    duration_ms=duration_ms,
                    success=True
                )
                return result
            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                logger.error(
                    f"Function failed: {operation_name} ({duration_ms:.2f}ms)",
                    event_type="performance",
                    function=func.__name__,
                    operation=operation_name,
                    duration_ms=duration_ms,
                    success=False,
                    error_type=type(e).__name__,
                    exc_info=True
                )
                raise
        
        # Return appropriate wrapper based on function type
        return async_wrapper if hasattr(func, '__code__') and func.__code__.co_flags & 0x80 else sync_wrapper
    
    return decorator

def set_request_context(req_id: str, user: str = None):
    """Set request context for logging"""
    request_id.set(req_id)
    if user:
        user_id.set(user)

def get_logger(name: str) -> OpenScholarLogger:
    """Get a configured logger instance"""
    return OpenScholarLogger(name)

# Request middleware for FastAPI
class LoggingMiddleware:
    """FastAPI middleware for request logging"""
    
    def __init__(self):
        self.logger = get_logger("middleware")
    
    async def __call__(self, request, call_next):
        # Generate request ID
        req_id = str(uuid.uuid4())
        set_request_context(req_id)
        
        # Log request start
        start_time = time.time()
        client_ip = request.client.host
        user_agent = request.headers.get("user-agent", "")
        
        self.logger.log_request_start(
            request.method, 
            str(request.url.path), 
            client_ip, 
            user_agent
        )
        
        # Process request
        try:
            response = await call_next(request)
            duration_ms = (time.time() - start_time) * 1000
            
            # Log request completion
            self.logger.log_request_end(
                request.method,
                str(request.url.path),
                response.status_code,
                duration_ms
            )
            
            # Add request ID to response headers
            response.headers["X-Request-ID"] = req_id
            
            return response
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            
            self.logger.error(
                f"Request failed: {request.method} {request.url.path} ({duration_ms:.2f}ms)",
                event_type="request_error",
                http_method=request.method,
                http_path=str(request.url.path),
                duration_ms=duration_ms,
                error_type=type(e).__name__
            )
            raise

# Configuration helper
def setup_logging(app_name: str = "openscholar", log_level: str = "INFO"):
    """Setup application-wide logging configuration"""
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    
    # Remove default handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Add structured handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(StructuredFormatter())
    root_logger.addHandler(console_handler)
    
    # File logging in production
    log_file = os.getenv('LOG_FILE')
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(StructuredFormatter())
        root_logger.addHandler(file_handler)
    
    # Get application logger
    app_logger = get_logger(app_name)
    app_logger.info(
        f"Logging initialized for {app_name}",
        event_type="logging_initialized",
        log_level=log_level,
        log_file=log_file
    )
    
    return app_logger
