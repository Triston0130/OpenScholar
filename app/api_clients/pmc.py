from typing import List, Dict, Any, Optional
import httpx
from app.api_clients.base import BaseAPIClient
from app.models import Paper
import logging

logger = logging.getLogger(__name__)

class PMCClient(BaseAPIClient):
    """PubMed Central Open Access client via Europe PMC"""
    
    def __init__(self, api_key: Optional[str] = None):
        super().__init__(base_url="https://www.ebi.ac.uk/europepmc/webservices/rest")
        self.api_key = api_key
    
    async def search(self, query: str, year_start: int, year_end: int,
                    discipline: Optional[str] = None,
                    education_level: Optional[str] = None,
                    limit: int = 20) -> List[Paper]:
        """Search PubMed Central subset via Europe PMC"""
        
        # Build search query parts
        query_parts = [query]
        
        # Restrict to PMC (PubMed Central) sources only
        query_parts.append("SRC:PMC")
        
        # Add open access filter
        query_parts.append("OPEN_ACCESS:y")
        
        # Add year range filter
        if year_start and year_end:
            query_parts.append(f"PUB_YEAR:[{year_start} TO {year_end}]")
        
        # Add discipline-specific terms if provided
        if discipline:
            discipline_mapping = {
                "education": "education OR learning OR pedagogy",
                "psychology": "psychology OR cognitive OR behavioral",
                "child development": "child development OR pediatric OR developmental",
                "early childhood": "early childhood OR infant OR toddler OR preschool"
            }
            if discipline.lower() in discipline_mapping:
                query_parts.append(f"({discipline_mapping[discipline.lower()]})")
        
        # Add education level terms if provided
        if education_level:
            level_mapping = {
                "early childhood": "infant OR toddler OR preschool OR early childhood",
                "k-12": "school age OR adolescent OR K-12 OR elementary OR secondary",
                "higher ed": "university OR college OR adult learning"
            }
            if education_level.lower() in level_mapping:
                query_parts.append(f"({level_mapping[education_level.lower()]})")
        
        # Combine query parts with AND
        search_query = " AND ".join(query_parts)
        
        params = {
            "query": search_query,
            "format": "json",
            "pageSize": limit,
            "resultType": "core"
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
                    # Only process if it has a PMC ID (confirming it's from PMC)
                    if result.get("pmcid"):
                        paper = self.normalize_paper(result)
                        if paper:
                            papers.append(paper)
            
            return papers
            
        except Exception as e:
            logger.error(f"Error searching PMC: {e}")
            return []
    
    def normalize_paper(self, raw_paper: Dict[str, Any]) -> Optional[Paper]:
        """Normalize PMC response to Paper model"""
        try:
            # Extract authors
            authors = []
            if "authorString" in raw_paper and raw_paper["authorString"]:
                # Split by comma and clean up
                authors = [author.strip() for author in raw_paper["authorString"].split(",")]
            
            # Construct PMC full text URL
            full_text_url = None
            pmcid = raw_paper.get("pmcid")
            if pmcid:
                # PMC articles are available in full text at this pattern
                full_text_url = f"https://www.ncbi.nlm.nih.gov/pmc/articles/{pmcid}/"
            
            # Alternative: Check fullTextUrlList
            if not full_text_url and "fullTextUrlList" in raw_paper:
                url_list = raw_paper["fullTextUrlList"].get("fullTextUrl", [])
                for url_obj in url_list:
                    if "pmc" in url_obj.get("url", "").lower():
                        full_text_url = url_obj.get("url")
                        break
                # If no PMC URL found, use the first available
                if not full_text_url and url_list:
                    full_text_url = url_list[0].get("url")
            
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
                source="PubMed Central",
                full_text_url=full_text_url,
                doi=doi,
                journal=journal,
                citation_count=raw_paper.get("citedByCount")
            )
        except Exception as e:
            logger.error(f"Error normalizing PMC paper: {e}")
            return None