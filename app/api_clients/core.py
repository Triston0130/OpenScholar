from typing import List, Dict, Any, Optional
import httpx
from app.api_clients.base import BaseAPIClient
from app.models import Paper
import logging

logger = logging.getLogger(__name__)

class COREClient(BaseAPIClient):
    """CORE API client for open access research"""
    
    def __init__(self, api_key: Optional[str] = None):
        super().__init__(base_url="https://api.core.ac.uk/v3")
        self.api_key = api_key
    
    async def search(self, query: str, year_start: int, year_end: int,
                    discipline: Optional[str] = None,
                    education_level: Optional[str] = None,
                    limit: int = 20) -> List[Paper]:
        """Search CORE database for papers"""
        
        # Build search query
        search_query = query
        
        # Add discipline to query if provided
        if discipline:
            search_query += f" AND {discipline}"
        
        if education_level:
            search_query += f" AND {education_level}"
        
        # Add year filter to query
        if year_start and year_end:
            search_query += f" AND yearPublished:[{year_start} TO {year_end}]"
        
        headers = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        
        params = {
            "q": search_query,
            "limit": limit,
            "fullText": "true"  # Only return papers with full text
        }
        
        try:
            response = await self.client.get(
                f"{self.base_url}/search/works",
                headers=headers,
                params=params
            )
            response.raise_for_status()
            
            data = response.json()
            papers = []
            
            if "results" in data:
                for result in data["results"]:
                    paper = await self.normalize_paper(result)
                    if paper:
                        papers.append(paper)
            
            return papers
            
        except Exception as e:
            logger.error(f"Error searching CORE: {e}")
            return []
    
    async def normalize_paper(self, raw_paper: Dict[str, Any]) -> Optional[Paper]:
        """Normalize CORE response to Paper model - only return papers with full PDFs"""
        try:
            # Only include papers with downloadable PDFs
            if not raw_paper.get("downloadUrl"):
                return None
            
            # Extract authors
            authors = []
            if "authors" in raw_paper and raw_paper["authors"]:
                authors = [author.get("name", "") for author in raw_paper["authors"] if author.get("name")]
            
            # Get full text URL (guaranteed to exist due to check above)
            full_text_url = raw_paper["downloadUrl"]
            
            # Get abstract
            abstract = raw_paper.get("abstract", "")
            if not abstract and raw_paper.get("description"):
                abstract = raw_paper["description"]
            
            paper = Paper(
                title=raw_paper.get("title", "").strip(),
                authors=authors,
                abstract=abstract.strip(),
                year=str(raw_paper.get("yearPublished", "Unknown")) if raw_paper.get("yearPublished") else "Unknown",
                source="CORE",
                full_text_url=full_text_url,
                doi=raw_paper.get("doi"),
                journal=raw_paper.get("publisher", "")
            )
            
            # Validate open access
            is_oa, reason = await self.validate_open_access(paper)
            if is_oa:
                return paper
            else:
                logger.debug(f"CORE paper rejected - {reason}: {paper.title[:50]}...")
                return None
        except Exception as e:
            logger.error(f"Error normalizing CORE paper: {e}")
            return None