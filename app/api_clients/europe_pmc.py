from typing import List, Dict, Any, Optional
import httpx
from app.api_clients.base import BaseAPIClient
from app.models import Paper
import logging

logger = logging.getLogger(__name__)

class EuropePMCClient(BaseAPIClient):
    """Europe PMC API client for biomedical and life sciences research"""
    
    def __init__(self, api_key: Optional[str] = None):
        super().__init__(base_url="https://www.ebi.ac.uk/europepmc/webservices/rest")
        self.api_key = api_key
    
    async def search(self, query: str, year_start: int, year_end: int,
                    discipline: Optional[str] = None,
                    education_level: Optional[str] = None,
                    limit: int = 20) -> List[Paper]:
        """Search Europe PMC database for papers"""
        
        # Build search query parts
        query_parts = [query]
        
        # Add open access filter
        query_parts.append("OPEN_ACCESS:y")
        
        # Add year range filter
        if year_start and year_end:
            query_parts.append(f"PUB_YEAR:[{year_start} TO {year_end}]")
        
        # Add discipline-specific terms if provided
        if discipline:
            discipline_mapping = {
                "education": "education OR pedagogy",
                "psychology": "psychology OR cognitive",
                "child development": "child development OR pediatric development",
                "early childhood": "early childhood OR preschool"
            }
            if discipline.lower() in discipline_mapping:
                query_parts.append(f"({discipline_mapping[discipline.lower()]})")
        
        # Add education level terms if provided
        if education_level:
            level_mapping = {
                "early childhood": "early childhood OR preschool OR kindergarten",
                "k-12": "K-12 OR elementary OR secondary education",
                "higher ed": "higher education OR university OR college"
            }
            if education_level.lower() in level_mapping:
                query_parts.append(f"({level_mapping[education_level.lower()]})")
        
        # Combine query parts with AND
        search_query = " AND ".join(query_parts)
        
        params = {
            "query": search_query,
            "format": "json",
            "pageSize": limit,
            "resultType": "core"  # Get core metadata
        }
        
        try:
            response = await self.client.get(
                f"{self.base_url}/search",
                params=params
            )
            response.raise_for_status()
            
            data = response.json()
            papers = []
            
            if "resultList" in data and "result" in data["resultList"]:
                for result in data["resultList"]["result"]:
                    paper = self.normalize_paper(result)
                    if paper:
                        papers.append(paper)
            
            return papers
            
        except Exception as e:
            logger.error(f"Error searching Europe PMC: {e}")
            return []
    
    def normalize_paper(self, raw_paper: Dict[str, Any]) -> Optional[Paper]:
        """Normalize Europe PMC response to Paper model - only return papers with full text"""
        try:
            # Get full text URL - only include papers with full text
            full_text_url = None
            if "fullTextUrlList" in raw_paper and raw_paper["fullTextUrlList"]:
                url_list = raw_paper["fullTextUrlList"].get("fullTextUrl", [])
                if url_list and len(url_list) > 0:
                    full_text_url = url_list[0].get("url")
            
            # Alternative: Check if PMC ID exists and construct URL
            if not full_text_url and raw_paper.get("pmcid"):
                full_text_url = f"https://www.ncbi.nlm.nih.gov/pmc/articles/{raw_paper['pmcid']}/"
            
            # Skip if no full text available
            if not full_text_url:
                return None
            
            # Extract authors
            authors = []
            if "authorString" in raw_paper and raw_paper["authorString"]:
                # Split by comma and clean up
                authors = [author.strip() for author in raw_paper["authorString"].split(",")]
            
            # Get abstract
            abstract = raw_paper.get("abstractText", "")
            if not abstract:
                abstract = raw_paper.get("abstract", "")
            
            # Get DOI
            doi = raw_paper.get("doi")
            
            # Get journal
            journal = raw_paper.get("journalTitle", "")
            if not journal:
                journal = raw_paper.get("journal", {}).get("title", "")
            
            return Paper(
                title=raw_paper.get("title", "").strip(),
                authors=authors,
                abstract=abstract.strip(),
                year=str(raw_paper.get("pubYear", "")),
                source="Europe PMC",
                full_text_url=full_text_url,
                doi=doi,
                journal=journal
            )
        except Exception as e:
            logger.error(f"Error normalizing Europe PMC paper: {e}")
            return None