#!/usr/bin/env python3
"""Test if we can make ANY search work"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any
import uvicorn

app = FastAPI()

# Add CORS - allow everything for testing
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class SearchRequest(BaseModel):
    query: str
    sources: List[str] = None
    limit: int = 20
    page: int = 1
    per_page: int = 20

class SearchResponse(BaseModel):
    total_results: int
    papers: List[Dict[str, Any]]
    sources_queried: List[str]
    source_counts: Dict[str, int] = {}

@app.get("/")
async def root():
    return {"status": "Test server running"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.post("/search")
async def search(request: SearchRequest):
    """Simple test search that returns dummy data"""
    print(f"Search called with query: {request.query}")
    
    # Return dummy data immediately
    return SearchResponse(
        total_results=2,
        papers=[
            {
                "title": f"Test Paper 1 about {request.query}",
                "authors": ["Test Author 1"],
                "year": "2023",
                "abstract": f"This is a test paper about {request.query}",
                "source": "Test Source",
                "url": "http://example.com/1",
                "id": "test-1"
            },
            {
                "title": f"Test Paper 2 about {request.query}",
                "authors": ["Test Author 2"],
                "year": "2024",
                "abstract": f"Another test paper about {request.query}",
                "source": "Test Source",
                "url": "http://example.com/2",
                "id": "test-2"
            }
        ],
        sources_queried=["Test Source"],
        source_counts={"Test Source": 2}
    )

@app.get("/api/auth/me")
async def auth_me():
    return {"user": {"username": "test", "email": "test@test.com"}}

@app.post("/api/auth/login")
async def login(data: dict):
    return {
        "access_token": "fake-token",
        "token_type": "bearer",
        "user": {"username": "test", "email": "test@test.com"}
    }

if __name__ == "__main__":
    print("Starting simple test server on port 8001...")
    uvicorn.run(app, host="0.0.0.0", port=8001)