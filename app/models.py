from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class SearchRequest(BaseModel):
    query: str
    year_start: Optional[int] = Field(default=2000, ge=1900, le=datetime.now().year)
    year_end: Optional[int] = Field(default=datetime.now().year, ge=1900, le=datetime.now().year)
    discipline: Optional[str] = None
    education_level: Optional[str] = None
    
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
                "papers": [
                    {
                        "title": "Early Language Development in Children",
                        "authors": ["Smith, J.", "Jones, M."],
                        "abstract": "This study examines early language development...",
                        "year": "2023",
                        "source": "ERIC",
                        "full_text_url": "https://example.com/paper.pdf",
                        "doi": "10.1234/example",
                        "journal": "Journal of Child Development"
                    }
                ],
                "format": "bib"
            }
        }