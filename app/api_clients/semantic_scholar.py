from typing import List, Optional, Dict, Any
import httpx
from app.models import Paper, SearchRequest
from .base import BaseAPIClient

class SemanticScholarClient(BaseAPIClient):
    """Client for Semantic Scholar API - AI-powered academic search"""
    
    def __init__(self):
        super().__init__(base_url="https://api.semanticscholar.org/graph/v1/")
        # Add User-Agent header to avoid rate limiting
        self.client.headers.update({
            "User-Agent": "OpenScholar Research Tool (Educational Academic Search)"
        })
    
    async def search(self, query: str, year_start: Optional[int] = None, 
                    year_end: Optional[int] = None, discipline: Optional[str] = None,
                    education_level: Optional[str] = None) -> List[Paper]:
        """Search Semantic Scholar for papers"""
        
        # Build query with education focus
        search_query = self._build_query(query, discipline, education_level)
        
        params = {
            "query": search_query,
            "limit": 100,
            "fields": "title,authors,abstract,year,venue,publicationTypes,url,citationCount,influentialCitationCount,externalIds"
        }
        
        # Add year filter
        if year_start:
            params["year"] = f"{year_start}-{year_end if year_end else ''}"
        
        try:
            response = await self.client.get(f"{self.base_url}paper/search", params=params)
            data = response.json()
            
            
            papers = []
            for item in data.get("data", []):
                # Skip if not peer-reviewed
                pub_types = item.get("publicationTypes", [])
                if pub_types and not any(t in ["JournalArticle", "Conference"] for t in pub_types):
                    continue
                
                # Extract DOI from externalIds
                doi = None
                external_ids = item.get("externalIds", {})
                if external_ids and "DOI" in external_ids:
                    doi = external_ids["DOI"]
                
                # Prefer papers with DOI for full-text access
                if not doi:
                    continue
                
                # Extract authors
                authors = []
                for author in item.get("authors", []):
                    if author.get("name"):
                        authors.append(author["name"])
                
                # Use DOI link which often leads to full text, or fallback to URL
                if doi:
                    full_text_url = f"https://doi.org/{doi}"
                else:
                    full_text_url = item.get("url", "")
                
                paper = Paper(
                    title=item.get("title", ""),
                    authors=authors if authors else ["Unknown"],
                    abstract=item.get("abstract") or "No abstract available",
                    year=str(item.get("year", "2000")),
                    source="Semantic Scholar",
                    full_text_url=full_text_url,
                    doi=doi,
                    journal=item.get("venue", ""),
                    citation_count=item.get("citationCount"),
                    influential_citation_count=item.get("influentialCitationCount")
                )
                
                papers.append(paper)
            
            return papers
            
        except Exception as e:
            print(f"Semantic Scholar search error: {str(e)}")
            return []
    
    def _build_query(self, query: str, discipline: Optional[str], education_level: Optional[str]) -> str:
        """Build query with education/child development focus"""
        
        terms = [query]
        
        # Add discipline-specific terms
        if discipline:
            if "education" in discipline.lower():
                terms.append("education educational teaching learning")
            elif "child" in discipline.lower() or "development" in discipline.lower():
                terms.append("child development psychology pediatric")
            elif "psychology" in discipline.lower():
                terms.append("psychology cognitive behavioral")
        
        # Add education level terms
        if education_level:
            if "early" in education_level.lower():
                terms.append("early childhood preschool kindergarten")
            elif "k-12" in education_level.lower():
                terms.append("K-12 elementary secondary school")
            elif "higher" in education_level.lower():
                terms.append("higher education university college")
        
        return " ".join(terms)
    
    def normalize_paper(self, raw_paper: Dict[str, Any]) -> Optional[Paper]:
        """Normalize Semantic Scholar JSON response to Paper model"""
        try:
            # Extract authors
            authors = []
            for author in raw_paper.get("authors", []):
                if author.get("name"):
                    authors.append(author["name"])
            
            # Extract DOI from externalIds
            doi = None
            external_ids = raw_paper.get("externalIds", {})
            if external_ids and "DOI" in external_ids:
                doi = external_ids["DOI"]
            
            paper = Paper(
                title=raw_paper.get("title", ""),
                authors=authors if authors else ["Unknown"],
                abstract=raw_paper.get("abstract", "No abstract available"),
                year=str(raw_paper.get("year", "2000")),
                source="Semantic Scholar",
                full_text_url=raw_paper.get("url", ""),
                doi=doi,
                journal=raw_paper.get("venue", ""),
                citation_count=raw_paper.get("citationCount"),
                influential_citation_count=raw_paper.get("influentialCitationCount")
            )
            
            return paper
            
        except Exception as e:
            print(f"Error normalizing Semantic Scholar paper: {str(e)}")
            return None