from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from contextlib import asynccontextmanager
import logging
import os
from dotenv import load_dotenv

from app.models import SearchRequest, SearchResponse, ExportRequest, ExternalPaperRequest
from app.services import SearchService
from app.export import ExportService
from app.external_papers import ExternalPaperFetcher

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global service instances
search_service = None
export_service = None
external_paper_fetcher = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle"""
    global search_service, export_service, external_paper_fetcher
    
    # Startup
    logger.info("Starting OpenScholar API...")
    core_api_key = os.getenv("CORE_API_KEY")
    search_service = SearchService(core_api_key=core_api_key)
    export_service = ExportService()
    external_paper_fetcher = ExternalPaperFetcher()
    
    yield
    
    # Shutdown
    logger.info("Shutting down OpenScholar API...")
    if search_service:
        await search_service.close()

# Create FastAPI app
app = FastAPI(
    title="OpenScholar API",
    description="Search for peer-reviewed, open-access research papers in education and child development",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS for production
allowed_origins = [
    "http://localhost:3000",  # Local React dev
    "http://localhost:3001",  # Alternative React dev
    "https://*.vercel.app",   # Vercel deployments
    "https://*.netlify.app",  # Netlify deployments
]

# Add production origins from environment
if production_origins := os.getenv("ALLOWED_ORIGINS"):
    allowed_origins.extend(production_origins.split(","))

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins if not os.getenv("RENDER") else ["*"],  # Allow all in Render for now
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

@app.get("/", tags=["Health"])
async def root():
    """Root endpoint - API health check"""
    return {
        "status": "healthy",
        "service": "OpenScholar API",
        "version": "1.0.0",
        "environment": "production" if os.getenv("RENDER") else "development",
        "endpoints": ["/search", "/export", "/external-paper"]
    }

@app.get("/health", tags=["Health"])
async def health_check():
    """Detailed health check endpoint"""
    global search_service, export_service, external_paper_fetcher
    
    health_status = {
        "status": "healthy",
        "timestamp": "2024-01-01T00:00:00Z",
        "services": {
            "search": "healthy" if search_service else "unhealthy",
            "export": "healthy" if export_service else "unhealthy",
            "external_paper": "healthy" if external_paper_fetcher else "unhealthy"
        },
        "environment": {
            "python_version": f"{os.sys.version_info.major}.{os.sys.version_info.minor}.{os.sys.version_info.micro}",
            "render_deployment": bool(os.getenv("RENDER")),
            "core_api_configured": bool(os.getenv("CORE_API_KEY"))
        }
    }
    
    # Update timestamp
    from datetime import datetime
    health_status["timestamp"] = datetime.utcnow().isoformat() + "Z"
    
    # Overall status
    if not search_service or not export_service or not external_paper_fetcher:
        health_status["status"] = "degraded"
    
    return health_status

@app.post("/search", response_model=SearchResponse, tags=["Search"])
async def search_papers(request: SearchRequest):
    """
    Search for academic papers across multiple open-access databases.
    
    - **query**: Search keywords
    - **year_start**: Start year for publication date filter
    - **year_end**: End year for publication date filter
    - **discipline**: Academic discipline (e.g., "education", "psychology", "child development")
    - **education_level**: Education level (e.g., "early childhood", "k-12", "higher ed")
    
    Returns deduplicated results from ERIC, CORE, and DOAJ.
    """
    global search_service
    
    if not search_service:
        raise HTTPException(status_code=503, detail="Search service not initialized")
    
    try:
        # Validate year range
        if request.year_start > request.year_end:
            raise HTTPException(
                status_code=400, 
                detail="year_start cannot be greater than year_end"
            )
        
        # Perform search
        logger.info(f"Searching for: {request.query} (page {request.page})")
        all_papers, sources_queried = await search_service.search(request)
        
        # Calculate pagination
        total_results = len(all_papers)
        start_idx = (request.page - 1) * request.per_page
        end_idx = start_idx + request.per_page
        
        # Get papers for current page
        paginated_papers = all_papers[start_idx:end_idx]
        
        return SearchResponse(
            total_results=total_results,
            papers=paginated_papers,
            sources_queried=sources_queried
        )
        
    except Exception as e:
        logger.error(f"Search error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

@app.post("/export", tags=["Export"])
async def export_papers(request: ExportRequest):
    """
    Export papers to CSV, JSON, or BibTeX format.
    
    - **papers**: List of Paper objects to export
    - **format**: Export format - "csv", "json", or "bib"
    
    Returns a downloadable file in the specified format.
    """
    global export_service
    
    if not export_service:
        raise HTTPException(status_code=503, detail="Export service not initialized")
    
    try:
        # Validate input
        if not request.papers:
            raise HTTPException(status_code=400, detail="No papers provided for export")
        
        if request.format not in ["csv", "json", "bib"]:
            raise HTTPException(status_code=400, detail="Invalid format. Must be 'csv', 'json', or 'bib'")
        
        # Perform export
        logger.info(f"Exporting {len(request.papers)} papers in {request.format} format")
        content, filename, mime_type = export_service.export_papers(request)
        
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
        logger.error(f"Export validation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    
    except Exception as e:
        logger.error(f"Export error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")

@app.post("/external-paper", response_model=dict, tags=["External Papers"])
async def fetch_external_paper(request: ExternalPaperRequest):
    """
    Fetch paper metadata from external sources using DOI.
    
    - **doi**: DOI of the paper to fetch metadata for
    
    Returns paper metadata in OpenScholar format from Crossref and Unpaywall APIs.
    """
    global external_paper_fetcher
    
    if not external_paper_fetcher:
        raise HTTPException(status_code=503, detail="External paper service not initialized")
    
    try:
        # Fetch paper metadata
        logger.info(f"Fetching external paper for DOI: {request.doi}")
        paper_data = external_paper_fetcher.fetch_paper_from_doi(request.doi)
        
        return {
            "status": "success",
            "paper": paper_data
        }
        
    except Exception as e:
        logger.error(f"External paper fetch error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch paper: {str(e)}")

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle uncaught exceptions"""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "An unexpected error occurred"}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )