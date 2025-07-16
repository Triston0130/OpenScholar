from typing import List, Dict, Any, Optional
import httpx
from app.api_clients.base import BaseAPIClient
from app.models import Paper
import logging

logger = logging.getLogger(__name__)

class ERICClient(BaseAPIClient):
    """ERIC API client for education research"""
    
    def __init__(self, api_key: Optional[str] = None):
        super().__init__(base_url="https://api.ies.ed.gov/eric")
        self.api_key = api_key
    
    async def search(self, query: str, year_start: int, year_end: int,
                    discipline: Optional[str] = None,
                    education_level: Optional[str] = None,
                    limit: int = 20) -> List[Paper]:
        """Search ERIC database for papers"""
        
        # Build search query
        search_query = f"{query}"
        
        # Add discipline filter if provided
        if discipline:
            discipline_mapping = {
                "education": "descriptor:education",
                "psychology": "descriptor:psychology",
                "child development": "descriptor:child development",
                "early childhood": "descriptor:early childhood education"
            }
            if discipline.lower() in discipline_mapping:
                search_query += f" AND {discipline_mapping[discipline.lower()]}"
        
        # Add education level filter
        if education_level:
            level_mapping = {
                "early childhood": "educationlevel:Early Childhood Education",
                "k-12": "educationlevel:Elementary Secondary Education",
                "higher ed": "educationlevel:Higher Education"
            }
            if education_level.lower() in level_mapping:
                search_query += f" AND {level_mapping[education_level.lower()]}"
        
        # Build parameters
        params = {
            "search": search_query,
            "format": "json",
            "rows": limit,
            "start": 0,
            "fields": "title,author,publicationdateyear,description,peerreviewed,url,isbn,sourceurl,publicationtype"
        }
        
        # Add year filter
        if year_start and year_end:
            params["publicationdateyear"] = f"[{year_start} TO {year_end}]"
        
        try:
            response = await self.client.get(
                f"{self.base_url}/",
                params=params
            )
            response.raise_for_status()
            
            data = response.json()
            papers = []
            
            if "response" in data and "docs" in data["response"]:
                for doc in data["response"]["docs"]:
                    # Only include peer-reviewed papers
                    if doc.get("peerreviewed", "F") == "T":
                        paper = self.normalize_paper(doc)
                        if paper:
                            papers.append(paper)
            
            return papers
            
        except Exception as e:
            logger.error(f"Error searching ERIC: {e}")
            return []
    
    def normalize_paper(self, raw_paper: Dict[str, Any]) -> Optional[Paper]:
        """Normalize ERIC response to Paper model - only return papers with full text"""
        try:
            # Get full text URL - only include papers with full text
            full_text_url = None
            if raw_paper.get("url"):
                full_text_url = raw_paper["url"]
            elif raw_paper.get("sourceurl"):
                full_text_url = raw_paper["sourceurl"]
            
            # Skip if no full text URL available
            if not full_text_url:
                return None
            
            # Extract authors
            authors = []
            if "author" in raw_paper and raw_paper["author"]:
                if isinstance(raw_paper["author"], list):
                    authors = [str(author).strip() for author in raw_paper["author"]]
                else:
                    authors = [author.strip() for author in str(raw_paper["author"]).split(";")]
            
            return Paper(
                title=raw_paper.get("title", "").strip(),
                authors=authors,
                abstract=raw_paper.get("description", "").strip(),
                year=str(raw_paper.get("publicationdateyear", "")),
                source="ERIC",
                full_text_url=full_text_url,
                doi=raw_paper.get("isbn"),  # ERIC sometimes uses ISBN in place of DOI
                journal=raw_paper.get("publicationtype", "")
            )
        except Exception as e:
            logger.error(f"Error normalizing ERIC paper: {e}")
            return None