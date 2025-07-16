from typing import List, Dict, Any, Optional
import httpx
from app.api_clients.base import BaseAPIClient
from app.models import Paper
import logging

logger = logging.getLogger(__name__)

class DOAJClient(BaseAPIClient):
    """DOAJ API client for open access journals"""
    
    def __init__(self, api_key: Optional[str] = None):
        super().__init__(base_url="https://doaj.org/api/v2")
        self.api_key = api_key
    
    async def search(self, query: str, year_start: int, year_end: int,
                    discipline: Optional[str] = None,
                    education_level: Optional[str] = None,
                    limit: int = 20) -> List[Paper]:
        """Search DOAJ database for papers"""
        
        # Build search query
        search_parts = [query]
        
        # Add subject filters for discipline
        if discipline:
            discipline_mapping = {
                "education": "Education",
                "psychology": "Psychology",
                "child development": "Psychology OR Education",
                "early childhood": "Education"
            }
            if discipline.lower() in discipline_mapping:
                search_parts.append(f'bibjson.subject.term:"{discipline_mapping[discipline.lower()]}"')
        
        # DOAJ doesn't have education level, so include it in general search
        if education_level:
            search_parts.append(education_level)
        
        # Add year filter
        if year_start and year_end:
            search_parts.append(f"bibjson.year:[{year_start} TO {year_end}]")
        
        search_query = " AND ".join(search_parts)
        
        params = {
            "search": search_query,
            "pageSize": limit,
            "page": 1
        }
        
        headers = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        
        try:
            response = await self.client.get(
                f"{self.base_url}/search/articles",
                headers=headers,
                params=params
            )
            response.raise_for_status()
            
            data = response.json()
            papers = []
            
            if "results" in data:
                for result in data["results"]:
                    paper = self.normalize_paper(result)
                    if paper:
                        papers.append(paper)
            
            return papers
            
        except Exception as e:
            logger.error(f"Error searching DOAJ: {e}")
            return []
    
    def normalize_paper(self, raw_paper: Dict[str, Any]) -> Optional[Paper]:
        """Normalize DOAJ response to Paper model - only return papers with full text"""
        try:
            bibjson = raw_paper.get("bibjson", {})
            
            # Get full text URL - only include papers with full text
            full_text_url = None
            if "link" in bibjson:
                for link in bibjson["link"]:
                    if link.get("type") == "fulltext":
                        full_text_url = link.get("url")
                        break
            
            # Skip if no full text available
            if not full_text_url:
                return None
            
            # Extract authors
            authors = []
            if "author" in bibjson:
                for author in bibjson["author"]:
                    name = author.get("name", "")
                    if name:
                        authors.append(name)
            
            # Get DOI
            doi = None
            if "identifier" in bibjson:
                for identifier in bibjson["identifier"]:
                    if identifier.get("type") == "doi":
                        doi = identifier.get("id")
                        break
            
            # Get journal
            journal = ""
            if "journal" in bibjson:
                journal = bibjson["journal"].get("title", "")
            
            return Paper(
                title=bibjson.get("title", "").strip(),
                authors=authors,
                abstract=bibjson.get("abstract", "").strip(),
                year=str(bibjson.get("year", "")),
                source="DOAJ",
                full_text_url=full_text_url,
                doi=doi,
                journal=journal
            )
        except Exception as e:
            logger.error(f"Error normalizing DOAJ paper: {e}")
            return None