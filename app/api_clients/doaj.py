from typing import List, Dict, Any, Optional
import httpx
from app.api_clients.base import BaseAPIClient
from app.models import Paper
from app.utils.open_access_validator import open_access_validator
import logging

logger = logging.getLogger(__name__)

class DOAJClient(BaseAPIClient):
    """DOAJ API client for open access journals"""
    
    def __init__(self, api_key: Optional[str] = None):
        super().__init__(base_url="https://doaj.org/api")
        self.api_key = api_key
    
    async def search(self, query: str, year_start: int, year_end: int,
                    discipline: Optional[str] = None,
                    education_level: Optional[str] = None,
                    limit: int = 20) -> List[Paper]:
        """Search DOAJ database for papers"""
        
        # For DOAJ, use simple query in URL path with parameters for filtering
        # URL encode the query to handle spaces and special characters
        import urllib.parse
        encoded_query = urllib.parse.quote(query)
        
        params = {
            "pageSize": limit,
            "page": 1
        }
        
        # Add year filter as parameter if needed
        # Note: DOAJ API may not support all these filters directly
        
        headers = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        
        try:
            response = await self.client.get(
                f"{self.base_url}/search/articles/{encoded_query}",
                headers=headers,
                params=params,
                timeout=15.0  # Shorter timeout for DOAJ
            )
            
            # If 404, the API endpoint might not be available
            if response.status_code == 404:
                logger.warning("DOAJ API endpoint not available (404), skipping DOAJ search")
                return []
                
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
            logger.error(f"Error searching DOAJ: {e}")
            return []
    
    async def normalize_paper(self, raw_paper: Dict[str, Any]) -> Optional[Paper]:
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
            
            # Try to get citation count using Europe PMC lookup
            citation_count = None
            if doi:
                citation_count = await self._get_citation_count_from_europe_pmc(doi)
            
            title = bibjson.get("title", "").strip()
            abstract = bibjson.get("abstract", "").strip()
            
            # DOAJ is inherently open access - minimal validation needed
            # Just ensure we have valid metadata
            if not title or not full_text_url:
                logger.debug(f"DOAJ paper rejected: {title[:50]}... (incomplete metadata)")
                return None
            
            logger.debug(f"DOAJ paper accepted: {title[:50]}... (DOAJ - inherently OA)")
            return Paper(
                title=title,
                authors=authors,
                abstract=abstract,
                year=str(bibjson.get("year", "Unknown")) if bibjson.get("year") else "Unknown",
                source="DOAJ",
                full_text_url=full_text_url,
                doi=doi,
                journal=journal,
                citation_count=citation_count
            )
        except Exception as e:
            logger.error(f"Error normalizing DOAJ paper: {e}")
            return None
    
    async def _get_citation_count_from_europe_pmc(self, doi: str) -> Optional[int]:
        """Get citation count from Europe PMC using DOI"""
        if not doi:
            return None
        
        try:
            params = {
                "query": f'DOI:"{doi}"',
                "format": "json",
                "pageSize": 1,
                "resultType": "core"
            }
            
            response = await self.client.get(
                "https://www.ebi.ac.uk/europepmc/webservices/rest/search",
                params=params
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("resultList", {}).get("result"):
                    result = data["resultList"]["result"][0]
                    return result.get("citedByCount")
        except Exception as e:
            logger.debug(f"Citation count lookup failed for DOI {doi}: {e}")
        
        return None