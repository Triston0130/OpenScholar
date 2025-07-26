# app/main.py - Security Hardened Version
"""
OpenScholar FastAPI Application - Security Hardened & Performance Optimized
Addresses critical security and performance issues from audit
"""

import os
import logging
import time
from typing import Optional
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI, HTTPException, Depends, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse, Response
from pydantic import ValidationError
from dotenv import load_dotenv
import uvicorn

# Import our modules
from app.models import SearchRequest, SearchResponse, ExportRequest, ExternalPaperRequest
from app.services import SearchService
from app.export import ExportService
from app.external_papers import ExternalPaperFetcher
from app.api_clients.pdf_extractor import PDFExtractor

# Import for static file serving
from fastapi.staticfiles import StaticFiles

# Import security modules
from app.security.validation import (
    SecurityMiddleware, 
    validate_search_request, 
    sanitize_paper_data,
    sanitize_error_message,
    APIKeyValidator
)

# Import cache modules
from app.cache import initialize_cache, cleanup_cache, get_cache_manager

# Import database modules
from app.database import (
    initialize_database,
    create_tables,
    get_db,
    check_database_health,
    UserService,
    CollectionService,
    PaperService,
    SearchHistoryService
)

# Import API routers
from app.api.auth import router as auth_router
from app.api.collections import router as collections_router
from app.api import sharing
from app.api.ai_processing import router as ai_router
from app.api.ai_enhanced import router as ai_enhanced_router
from app.api.ai_textbook import router as ai_textbook_router

# Import logging modules
from app.app_logging import (
    setup_logging,
    get_logger,
    LoggingMiddleware,
    performance_monitor,
    PerformanceMonitor,
    set_request_context
)

# Load environment variables
load_dotenv()

# Setup comprehensive structured logging
app_logger = setup_logging(
    app_name="openscholar-api",
    log_level=os.getenv("LOG_LEVEL", "INFO")
)

# Module-level logger for exception handlers
logger = get_logger("main")

# Security middleware instance
security_middleware = SecurityMiddleware()
api_key_validator = APIKeyValidator()

# Global service instances
search_service = None
export_service = None
external_paper_fetcher = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events with security validation, caching, and comprehensive logging"""
    global search_service, export_service, external_paper_fetcher
    
    # Startup
    app_logger.info(
        "Starting OpenScholar API with security validation and comprehensive logging",
        event_type="application_startup",
        environment=environment
    )
    
    # Initialize cache system
    with PerformanceMonitor(app_logger, "cache_initialization"):
        await initialize_cache()
    
    # Initialize database system
    with PerformanceMonitor(app_logger, "database_initialization"):
        database_url = os.getenv("DATABASE_URL")
        db_echo = os.getenv("DB_ECHO", "false").lower() == "true"
        initialize_database(database_url, db_echo)
        
        # Create tables if they don't exist
        try:
            create_tables()
            app_logger.info(
                "Database tables created/verified",
                event_type="database_tables_ready"
            )
        except Exception as e:
            app_logger.error(
                f"Failed to create database tables: {e}",
                event_type="database_error"
            )
    
    # Validate API keys on startup
    try:
        config = dict(os.environ)
        validated_keys = api_key_validator.validate_api_keys(config)
        app_logger.info(
            f"Validated {len(validated_keys)} API keys successfully",
            event_type="api_key_validation",
            validated_count=len(validated_keys),
            required_keys=api_key_validator.required_keys
        )
    except Exception as e:
        app_logger.warning(
            f"API key validation warnings: {e}",
            event_type="api_key_validation_warning"
        )
        # Continue startup even with validation warnings
    
    # Initialize services with validated configuration
    with PerformanceMonitor(app_logger, "services_initialization"):
        core_api_key = os.getenv("CORE_API_KEY")
        search_service = SearchService(core_api_key=core_api_key, use_advanced_ranking=False)
        export_service = ExportService()
        external_paper_fetcher = ExternalPaperFetcher()
    
    app_logger.info(
        "All services initialized successfully",
        event_type="services_ready",
        services=["search", "export", "external_paper"]
    )
    
    yield
    
    # Shutdown
    app_logger.info(
        "Shutting down OpenScholar API",
        event_type="application_shutdown"
    )
    
    # Cleanup services
    if search_service:
        await search_service.close()
    
    # Cleanup cache
    await cleanup_cache()
    
    app_logger.info(
        "Shutdown complete",
        event_type="application_shutdown_complete"
    )

# Create FastAPI app with security settings
environment = os.getenv("ENVIRONMENT", "development")
app = FastAPI(
    title="OpenScholar API",
    description="Secure academic research search API",
    version="1.1.0",
    docs_url="/docs" if environment == "development" else None,
    redoc_url="/redoc" if environment == "development" else None,
    lifespan=lifespan
)

# Include API routers
app.include_router(auth_router)
app.include_router(collections_router)
app.include_router(sharing.router)
app.include_router(ai_router)
app.include_router(ai_enhanced_router)
app.include_router(ai_textbook_router)

# Include user settings router
from app.api.user_settings import router as user_settings_router
app.include_router(user_settings_router)

# Import and include PDF proxy router
from app.routers.pdf_proxy import router as pdf_proxy_router
app.include_router(pdf_proxy_router, prefix="/api")

# Import and include HTML proxy router
from app.routers.html_proxy import router as html_proxy_router
app.include_router(html_proxy_router, prefix="/api")

# Import and include annotations router
from app.routers.annotations import router as annotations_router
app.include_router(annotations_router)

# Import and include PDF upload router
from app.routers.pdf_upload import router as pdf_upload_router
app.include_router(pdf_upload_router)

# Import and include test OER router (for debugging)
from app.routers.test_oer import router as test_oer_router
app.include_router(test_oer_router)

# Import and include external lookup router
from app.api.external import router as external_router
app.include_router(external_router)

# Mount static files for uploaded PDFs
from pathlib import Path
uploads_dir = Path("uploads/pdfs")
uploads_dir.mkdir(parents=True, exist_ok=True)
app.mount("/uploads/pdfs", StaticFiles(directory=str(uploads_dir)), name="uploads")

# Security Middleware Configuration
allowed_origins = security_middleware.get_cors_origins(environment)

# Add custom origins from environment
if production_origins := os.getenv("ALLOWED_ORIGINS"):
    allowed_origins.extend(production_origins.split(","))

# CORS Middleware - Fixed security configuration (NO MORE WILDCARDS!)
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,  # Specific origins only
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    max_age=600,  # Cache preflight requests for 10 minutes
)

# Add comprehensive logging middleware
logging_middleware = LoggingMiddleware()
app.middleware("http")(logging_middleware)

# Trusted Host Middleware for additional security in production
if environment == "production":
    app.add_middleware(
        TrustedHostMiddleware, 
        allowed_hosts=[
            "openscholar-nsc1.onrender.com",
            "api.openscholar.app",
            "www.api.openscholar.app"
        ]
    )

# Rate limiting check (simplified version)
async def rate_limit_check(request: Request):
    """Basic rate limiting check"""
    # For now, just pass through - no rate limiting
    return True

# Custom Exception Handlers
@app.exception_handler(ValidationError)
async def validation_exception_handler(request: Request, exc: ValidationError):
    sanitized_error = sanitize_error_message(str(exc))
    logger.warning(f"Validation error from {request.client.host}: {sanitized_error}")
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "error": "Validation Error",
            "message": "Please check your request parameters",
            "details": exc.errors()[:3]  # Limit details to prevent info leakage
        }
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    sanitized_detail = sanitize_error_message(exc.detail)
    logger.warning(f"HTTP error {exc.status_code} from {request.client.host}: {sanitized_detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": sanitized_detail,
            "status_code": exc.status_code
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    sanitized_error = sanitize_error_message(str(exc))
    logger.error(f"Unhandled error from {request.client.host}: {sanitized_error}")
    
    # In production, don't leak internal error details
    if environment == "production":
        error_message = "An internal server error occurred"
    else:
        error_message = sanitized_error
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal server error",
            "message": error_message
        }
    )

# Health Check Endpoints
@app.get("/", tags=["Health"])
async def root():
    """Root endpoint - API health check"""
    db_health = check_database_health()
    
    return {
        "status": "healthy" if db_health["status"] == "healthy" else "degraded",
        "service": "OpenScholar API",
        "version": "1.1.0",
        "environment": environment,
        "security": "enabled",
        "cache": "enabled" if get_cache_manager() else "disabled",
        "database": db_health["status"],
        "endpoints": ["/search", "/export", "/external-paper", "/health"]
    }

@app.post("/test-search", tags=["Test"])
async def test_search(request: SearchRequest):
    """Simple test endpoint without complex validation"""
    return {"message": f"Received search for: {request.query}", "request": request.dict()}

@app.get("/health", tags=["Health"])
async def health_check():
    """Comprehensive health check with database, cache and security status"""
    global search_service, export_service, external_paper_fetcher
    
    # Check database health
    db_health = check_database_health()
    
    # Check cache status
    cache_manager = get_cache_manager()
    cache_status = "disabled"
    if cache_manager and cache_manager.cache:
        if await cache_manager.cache.is_connected():
            cache_status = "redis" if hasattr(cache_manager.cache, 'redis_client') else "memory"
        else:
            cache_status = "error"
    
    health_status = {
        "status": "healthy" if db_health["status"] == "healthy" else "degraded",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "services": {
            "search": "healthy" if search_service else "unhealthy",
            "export": "healthy" if export_service else "unhealthy",
            "external_paper": "healthy" if external_paper_fetcher else "unhealthy",
            "database": db_health["status"],
            "cache": cache_status,
            "security": "enabled"
        },
        "environment": {
            "mode": environment,
            "cors_origins": len(allowed_origins),
            "api_keys_configured": len([k for k in os.environ.keys() if k.endswith('_API_KEY') and os.environ[k]]),
            "database_engine": db_health.get("engine", "unknown")
        }
    }
    
    # Overall status check
    if not search_service or not export_service or not external_paper_fetcher or db_health["status"] != "healthy":
        health_status["status"] = "degraded"
    
    return health_status

# Test PDF extractor endpoint (development only)
@app.get("/test-pdf-extractor", tags=["Development"])
async def test_pdf_extractor():
    """Test PDF extractor directly"""
    if environment == "production":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Endpoint not available in production"
        )
    
    from app.api_clients.pdf_extractor import PDFExtractor
    extractor = PDFExtractor()
    test_url = "https://human.libretexts.org/Bookshelves/History"
    result = await extractor.extract_pdf_url(test_url)
    
    return {
        "test_url": test_url,
        "result": result,
        "module_file": PDFExtractor.__module__,
        "changed": result != test_url
    }

# Cache statistics endpoint (development only)
@app.get("/cache-stats", tags=["Development"])
async def cache_stats():
    """Get cache statistics (development only)"""
    if environment == "production":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Endpoint not available in production"
        )
    
    cache_manager = get_cache_manager()
    if not cache_manager:
        return {"status": "cache not initialized"}
    
    return {
        "cache_type": "redis" if hasattr(cache_manager.cache, 'redis_client') else "memory",
        "connected": await cache_manager.cache.is_connected() if cache_manager.cache else False,
        "status": "operational" if cache_manager.cache else "disabled"
    }

# Main Search Endpoint with Security, Caching, and Comprehensive Logging
@app.post("/search", response_model=SearchResponse, tags=["Search"])
async def search_papers(
    request: SearchRequest,
    rate_limited = Depends(rate_limit_check)
):
    """
    Search for academic papers across multiple databases with security validation, caching, and logging
    """
    print(f"DEBUG: Search endpoint called with query: {request.query}")
    global search_service
    
    # Get logger for this request
    logger = get_logger("search_endpoint")
    print("DEBUG: Logger obtained")
    
    if not search_service:
        logger.error(
            "Search service not available",
            event_type="service_error",
            service="search"
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Search service not available"
        )
    
    search_start_time = time.time()
    
    try:
        # Validate and sanitize the search request
        request_dict = request.dict()
        logger.info(f"Raw request dict: {request_dict}")
        validated_request = validate_search_request(request_dict)
        logger.info(f"Validated request: {validated_request}")
        
        logger.info(
            f"Search request validated: {request.query}",
            event_type="search_validation",
            query=request.query,
            filters={
                "year_start": request.year_start,
                "year_end": request.year_end,
                "page": request.page,
                "per_page": request.per_page
            }
        )
        
        # Check cache first
        cache_manager = get_cache_manager()
        cached_results = None
        
        if cache_manager:
            with PerformanceMonitor(logger, "cache_lookup"):
                cached_results = await cache_manager.get_search_results(
                    request.query,
                    year_start=request.year_start,
                    year_end=request.year_end,
                    page=request.page,
                    per_page=request.per_page,
                    sources=request.sources
                )
            
            if cached_results:
                cache_duration = (time.time() - search_start_time) * 1000
                logger.log_cache_operation(
                    "search_results_get", 
                    f"search:{request.query[:50]}", 
                    hit=True,
                    duration_ms=cache_duration
                )
                logger.info(
                    f"Returning cached search results for: {request.query}",
                    event_type="search_cache_hit",
                    query=request.query,
                    result_count=len(cached_results.get('papers', [])),
                    cache_duration_ms=cache_duration
                )
                return SearchResponse(**cached_results)
            else:
                logger.log_cache_operation(
                    "search_results_get", 
                    f"search:{request.query[:50]}", 
                    hit=False
                )
        
        # Validate year range
        if request.year_start and request.year_end and request.year_start > request.year_end:
            logger.warning(
                "Invalid year range in search request",
                event_type="validation_error",
                year_start=request.year_start,
                year_end=request.year_end
            )
            raise HTTPException(
                status_code=400, 
                detail="year_start cannot be greater than year_end"
            )
        
        # Perform search with performance monitoring
        with PerformanceMonitor(logger, "search_execution"):
            search_results = await search_service.search(request)
            
        # Handle both old and new return formats
        if len(search_results) == 5:
            # Advanced ranking with metrics
            paginated_papers, sources_queried, total_results, source_counts, search_metrics = search_results
        else:
            # Basic ranking without metrics
            paginated_papers, sources_queried, total_results, source_counts = search_results
            search_metrics = None
        
        # Sanitize paginated paper data before returning
        sanitized_papers = []
        for paper in paginated_papers:
            if hasattr(paper, 'dict'):
                sanitized_data = sanitize_paper_data(paper.dict())
            else:
                sanitized_data = sanitize_paper_data(paper)
            sanitized_papers.append(sanitized_data)
        
        # Create response
        response_data = {
            "total_results": total_results,
            "papers": sanitized_papers,
            "sources_queried": sources_queried,
            "source_counts": source_counts
        }
        
        # Add search metrics if available (from advanced ranking)
        if search_metrics:
            response_data["search_metrics"] = search_metrics
        
        # Cache the results
        if cache_manager:
            with PerformanceMonitor(logger, "cache_store"):
                await cache_manager.cache_search_results(
                    request.query,
                    response_data,
                    year_start=request.year_start,
                    year_end=request.year_end,
                    page=request.page,
                    per_page=request.per_page,
                    sources=request.sources
                )
        
        # Log successful search
        search_duration = (time.time() - search_start_time) * 1000
        logger.log_search_query(
            request.query,
            {
                "year_start": request.year_start,
                "year_end": request.year_end,
                "page": request.page,
                "per_page": request.per_page
            },
            total_results,
            sources_queried,
            search_duration
        )
        
        return SearchResponse(**response_data)
        
    except ValidationError as e:
        sanitized_error = sanitize_error_message(str(e))
        logger.warning(
            f"Search validation failed: {sanitized_error}",
            event_type="validation_error",
            query=getattr(request, 'query', 'unknown'),
            error_type="ValidationError"
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid search parameters: {sanitized_error}"
        )
    except Exception as e:
        sanitized_error = sanitize_error_message(str(e))
        search_duration = (time.time() - search_start_time) * 1000
        logger.log_error_with_context(
            e,
            {
                "query": getattr(request, 'query', 'unknown'),
                "search_duration_ms": search_duration,
                "endpoint": "search_papers"
            }
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Search service error"
        )

# Export Endpoint with Security
@app.post("/export", tags=["Export"])
async def export_papers(
    request: ExportRequest,
    rate_limited = Depends(rate_limit_check)
):
    """Export papers to CSV, JSON, or BibTeX format with security validation"""
    global export_service
    
    if not export_service:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Export service not available"
        )
    
    try:
        # Validate input
        if not request.papers:
            raise HTTPException(status_code=400, detail="No papers provided for export")
        
        if request.format not in ["csv", "json", "bib"]:
            raise HTTPException(status_code=400, detail="Invalid format. Must be 'csv', 'json', or 'bib'")
        
        # Sanitize all paper data before export
        sanitized_papers = []
        for paper in request.papers:
            if hasattr(paper, 'dict'):
                sanitized_data = sanitize_paper_data(paper.dict())
            else:
                sanitized_data = sanitize_paper_data(paper)
            sanitized_papers.append(sanitized_data)
        
        # Create sanitized request
        sanitized_request = ExportRequest(
            papers=sanitized_papers,
            format=request.format
        )
        
        # Perform export
        logger.info(f"Exporting {len(sanitized_papers)} papers in {request.format} format")
        content, filename, mime_type = export_service.export_papers(sanitized_request)
        
        # Return file response
        return Response(
            content=content,
            media_type=mime_type,
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "Content-Type": mime_type
            }
        )
        
    except ValueError as e:
        sanitized_error = sanitize_error_message(str(e))
        logger.error(f"Export validation error: {sanitized_error}")
        raise HTTPException(status_code=400, detail=sanitized_error)
    
    except Exception as e:
        sanitized_error = sanitize_error_message(str(e))
        logger.error(f"Export error: {sanitized_error}")
        raise HTTPException(status_code=500, detail="Export service error")

# External Paper Endpoint with Security
@app.post("/external-paper", response_model=dict, tags=["External Papers"])
async def fetch_external_paper(
    request: ExternalPaperRequest,
    rate_limited = Depends(rate_limit_check)
):
    """Fetch paper metadata from external sources using DOI with security validation"""
    global external_paper_fetcher
    
    if not external_paper_fetcher:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="External paper service not available"
        )
    
    try:
        # Validate DOI format
        if not request.doi or len(request.doi) > 200:
            raise HTTPException(status_code=400, detail="Invalid DOI format")
        
        # Basic DOI sanitization
        sanitized_doi = request.doi.strip()
        if not sanitized_doi.startswith(('10.', 'doi:', 'DOI:')):
            raise HTTPException(status_code=400, detail="Invalid DOI format")
        
        # Check cache first
        cache_manager = get_cache_manager()
        if cache_manager:
            cached_paper = await cache_manager.get_paper_details(sanitized_doi)
            if cached_paper:
                logger.info(f"Returning cached paper data for DOI: {sanitized_doi}")
                return {
                    "status": "success",
                    "paper": cached_paper,
                    "cached": True
                }
        
        # Fetch paper metadata
        logger.info(f"Fetching external paper for DOI: {sanitized_doi}")
        paper_data = external_paper_fetcher.fetch_paper_from_doi(sanitized_doi)
        
        # Sanitize paper data
        if paper_data:
            sanitized_paper_data = sanitize_paper_data(paper_data)
            
            # Cache the result
            if cache_manager:
                await cache_manager.cache_paper_details(sanitized_doi, sanitized_paper_data)
        else:
            sanitized_paper_data = None
        
        return {
            "status": "success",
            "paper": sanitized_paper_data,
            "cached": False
        }
        
    except Exception as e:
        sanitized_error = sanitize_error_message(str(e))
        logger.error(f"External paper fetch error: {sanitized_error}")
        raise HTTPException(
            status_code=500, 
            detail="Failed to fetch paper metadata"
        )

# PDF URL Extraction Endpoint
@app.post("/extract-pdf-url", response_model=dict, tags=["PDF"])
async def extract_pdf_url(
    request: dict,
    rate_limited = Depends(rate_limit_check)
):
    """Extract direct PDF URL from a textbook landing page"""
    landing_url = request.get('url', '').strip()
    
    if not landing_url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="URL is required"
        )
    
    # Basic URL validation
    if not landing_url.startswith(('http://', 'https://')):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid URL format"
        )
    
    try:
        pdf_extractor = PDFExtractor()
        pdf_url = await pdf_extractor.extract_pdf_url(landing_url)
        
        logger.info(f"PDF extraction: {landing_url} -> {pdf_url}")
        
        return {
            "original_url": landing_url,
            "pdf_url": pdf_url or landing_url,
            "extracted": pdf_url != landing_url  # True if URL actually changed
        }
        
    except Exception as e:
        logger.error(f"PDF extraction error: {e}")
        # Return original URL on error
        return {
            "original_url": landing_url,
            "pdf_url": landing_url,
            "extracted": False
        }

# PDF Text Extraction Endpoint
@app.post("/api/extract-pdf-text", response_model=dict, tags=["PDF"])
async def extract_pdf_text(
    request: dict,
    rate_limited = Depends(rate_limit_check)
):
    """Extract text content from a PDF for TTS"""
    logger.info(
        "PDF text extraction requested",
        event_type="pdf_text_extraction_request",
        pdf_url=request.get("pdf_url")
    )
    
    try:
        pdf_url = request.get("pdf_url")
        max_pages = request.get("max_pages", 50)
        
        if not pdf_url:
            return {"success": False, "error": "No PDF URL provided"}
        
        # Import PDF extractor
        from app.utils.pdf_extractor import extract_text_from_pdf_url
        
        # Extract text
        result = await extract_text_from_pdf_url(pdf_url, max_pages=max_pages)
        
        if result['success']:
            logger.info(
                "PDF text extraction successful",
                event_type="pdf_text_extraction_success",
                text_length=len(result['text']),
                page_count=result['page_count']
            )
            return {
                "success": True,
                "text": result['text'],
                "page_count": result['page_count']
            }
        else:
            logger.warning(
                "PDF text extraction failed",
                event_type="pdf_text_extraction_failed",
                error=result['error']
            )
            return {
                "success": False,
                "error": result['error']
            }
            
    except Exception as e:
        logger.exception(f"Unexpected error in PDF text extraction: {e}")
        return {
            "success": False,
            "error": f"Server error: {str(e)}"
        }

if __name__ == "__main__":
    # Development server configuration
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=port,
        reload=environment == "development",
        access_log=True,
        log_level="info"
    )
