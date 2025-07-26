#!/usr/bin/env python3
"""
Simplified OpenScholar API for testing
"""
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.models import SearchRequest, SearchResponse
from app.services.search import SearchService
import logging

# Setup basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(title="OpenScholar API (Simplified)")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for testing
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize search service
search_service = SearchService()

@app.get("/")
async def root():
    return {"status": "healthy", "service": "OpenScholar API (Simplified)"}

@app.post("/search")
async def search_papers(request: SearchRequest):
    """Search for academic papers"""
    try:
        logger.info(f"Search request: {request}")
        papers, sources = await search_service.search(request)
        
        # Pagination
        total_results = len(papers)
        start_idx = (request.page - 1) * request.per_page
        end_idx = start_idx + request.per_page
        paginated_papers = papers[start_idx:end_idx]
        
        return SearchResponse(
            total_results=total_results,
            papers=paginated_papers,
            sources_queried=sources
        )
    except Exception as e:
        logger.error(f"Search error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8002, reload=True)