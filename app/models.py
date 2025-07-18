from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class SearchRequest(BaseModel):
    query: str
    year_start: Optional[int] = Field(default=2000, ge=1900, le=datetime.now().year)
    year_end: Optional[int] = Field(default=datetime.now().year, ge=1900, le=datetime.now().year)
    discipline: Optional[str] = None
    education_level: Optional[str] = None
    publication_type: Optional[str] = None  # journal, conference, book, etc.
    study_type: Optional[str] = None       # experimental, survey, review, meta-analysis
    min_citations: Optional[int] = Field(default=None, ge=0)  # minimum citation count filter
    sort_by: Optional[str] = Field(default="relevance", pattern="^(relevance|newest|oldest|citations)$")
    page: Optional[int] = Field(default=1, ge=1)
    per_page: Optional[int] = Field(default=20, ge=10, le=50)
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": "language development",
                "year_start": 2015,
                "year_end": 2025,
                "discipline": "child development",
                "education_level": "early childhood"
            }
        }

class Paper(BaseModel):
    title: str
    authors: List[str]
    abstract: str
    year: str
    source: str
    full_text_url: Optional[str] = None
    doi: Optional[str] = None
    journal: Optional[str] = None
    citation_count: Optional[int] = None
    influential_citation_count: Optional[int] = None
    
class SearchResponse(BaseModel):
    total_results: int
    papers: List[Paper]
    sources_queried: List[str]

class ExportRequest(BaseModel):
    papers: List[Paper]
    format: str = Field(..., pattern="^(csv|json|bib)$")
    
    class Config:
        json_schema_extra = {
            "example": {
                "format": "csv",
                "papers": []
            }
        }

class ExternalPaperRequest(BaseModel):
    doi: str = Field(..., description="DOI of the paper to fetch")
    
    class Config:
        json_schema_extra = {
            "example": {
                "doi": "10.1234/example.2023.001"
            }
        }