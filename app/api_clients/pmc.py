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
        query_parts = []
        
        # Convert query to OR search for multiple terms
        query_terms = query.split()
        if len(query_terms) > 1:
            query_parts.append(f"({' OR '.join(query_terms)})")
        else:
            query_parts.append(query)
        
        # Restrict to PMC (PubMed Central) sources only
        query_parts.append("SRC:PMC")
        
        # Add open access filter - less restrictive
        query_parts.append("OPEN_ACCESS:y")
        # Don't require CC license - too restrictive
        # query_parts.append("LICENSE:cc*")
        query_parts.append("HAS_PDF:y")     # Only papers with PDF available
        
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
                        # Double-check open access status
                        if result.get("isOpenAccess") == "Y":
                            # Check if PDF is available
                            has_pdf = result.get("hasPDF")
                            if has_pdf == "Y":
                                # Check publication type
                                pub_type = result.get("pubType", "").lower()
                                if not pub_type or pub_type not in ["abstract", "editorial", "letter", "comment", "erratum"]:
                                    paper = await self.normalize_paper(result)
                                    if paper:
                                        papers.append(paper)
                                else:
                                    logger.debug(f"Skipping PMC paper - publication type: {pub_type}")
                            else:
                                logger.debug(f"Skipping PMC paper - no PDF available")
                        else:
                            logger.debug(f"Skipping PMC paper - not marked as open access: {result.get('title', 'Unknown')}")
            
            return papers
            
        except Exception as e:
            logger.error(f"Error searching PMC: {e}")
            return []
    
    async def normalize_paper(self, raw_paper: Dict[str, Any]) -> Optional[Paper]:
        """Normalize PMC response to Paper model - strict open access checking"""
        try:
            # Check license - only allow Creative Commons or explicit open access
            license_info = raw_paper.get("license")
            if license_info:
                if not (license_info.lower().startswith("cc") or "open access" in license_info.lower()):
                    logger.debug(f"Skipping PMC paper due to restrictive license: {license_info}")
                    return None
            # Extract authors
            authors = []
            if "authorString" in raw_paper and raw_paper["authorString"]:
                # Split by comma and clean up
                authors = [author.strip() for author in raw_paper["authorString"].split(",")]
            
            # Construct PMC full text URL - use Europe PMC direct PDF URL
            full_text_url = None
            pmcid = raw_paper.get("pmcid")
            if pmcid:
                # Use Europe PMC direct PDF download URL (returns PDF with filename in headers)
                full_text_url = f"https://europepmc.org/backend/ptpmcrender.fcgi?accid={pmcid}&blobtype=pdf"
            
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
            
            # Validate that URL points to a full article, not just abstract
            if full_text_url and self._is_abstract_only_url(full_text_url):
                logger.debug(f"Skipping PMC paper - URL appears to be abstract-only: {full_text_url}")
                return None
            
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
                year=str(raw_paper.get("pubYear", "Unknown")) if raw_paper.get("pubYear") else "Unknown",
                source="PubMed Central",
                full_text_url=full_text_url,
                doi=doi,
                journal=journal,
                citation_count=raw_paper.get("citedByCount")
            )
        except Exception as e:
            logger.error(f"Error normalizing PMC paper: {e}")
            return None
    
    def _is_abstract_only_url(self, url: str) -> bool:
        """Check if URL appears to be abstract-only rather than full text"""
        abstract_indicators = [
            "/abstract",
            "?abstract", 
            "&abstract",
            "/summary",
            "?summary",
            "&summary"
        ]
        
        # Check for abstract indicators in URL
        url_lower = url.lower()
        for indicator in abstract_indicators:
            if indicator in url_lower:
                return True
        
        # PMC URLs should have the full article path
        if "pmc/articles/" in url_lower and not url_lower.endswith("/"):
            return False
        
        return False