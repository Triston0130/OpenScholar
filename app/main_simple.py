# Simplified main.py without complex security features
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.models import SearchRequest, SearchResponse, ExportRequest
from app.services.search import SearchService
from app.export import ExportService
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create app
app = FastAPI(title="OpenScholar API")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Services
search_service = SearchService()
export_service = ExportService()

@app.get("/")
async def root():
    return {"status": "healthy", "service": "OpenScholar API"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.post("/search", response_model=SearchResponse)
async def search_papers(request: SearchRequest):
    """Search for papers"""
    try:
        papers, sources = await search_service.search(request)
        
        # Pagination
        total = len(papers)
        start = (request.page - 1) * request.per_page
        end = start + request.per_page
        
        return SearchResponse(
            total_results=total,
            papers=papers[start:end],
            sources_queried=sources
        )
    except Exception as e:
        logger.error(f"Search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/export")
async def export_papers(request: ExportRequest):
    """Export papers"""
    try:
        content, filename, mime_type = export_service.export_papers(request)
        from fastapi.responses import Response
        return Response(
            content=content,
            media_type=mime_type,
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except Exception as e:
        logger.error(f"Export error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)