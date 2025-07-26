from typing import List, Dict, Any, Optional
import httpx
from app.api_clients.base import BaseAPIClient
from app.models import Paper
import logging
import re

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
        
        # Add open access filter - stricter filtering for true open access
        query_parts.append("OPEN_ACCESS:y")
        query_parts.append("LICENSE:cc*")  # Only Creative Commons licensed content
        query_parts.append("HAS_PDF:y")     # Only papers with PDF available
        query_parts.append("FIRST_PDATE:[2000-01-01 TO 2025-12-31]")  # Filter out very old partial records
        
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
            # Check license first - only allow Creative Commons or explicit open access
            license_info = raw_paper.get("license")
            if license_info:
                # Only allow Creative Commons licenses or explicit open access
                if not (license_info.lower().startswith("cc") or "open access" in license_info.lower()):
                    logger.debug(f"Skipping paper due to restrictive license: {license_info}")
                    return None
            
            # Double-check open access status
            if raw_paper.get("isOpenAccess") != "Y":
                logger.debug(f"Skipping paper - not marked as open access")
                return None
            
            # Check if PDF is available
            has_pdf = raw_paper.get("hasPDF")
            if has_pdf != "Y":
                logger.debug(f"Skipping paper - no PDF available")
                return None
            
            # Check if it's a full research article (not just abstract, editorial, etc.)
            publication_type = raw_paper.get("pubType", "").lower()
            if publication_type and publication_type in ["abstract", "editorial", "letter", "comment", "erratum"]:
                logger.debug(f"Skipping paper - publication type: {publication_type}")
                return None
            
            # Get full text URL - prioritize PDF URLs
            full_text_url = None
            if "fullTextUrlList" in raw_paper and raw_paper["fullTextUrlList"]:
                url_list = raw_paper["fullTextUrlList"].get("fullTextUrl", [])
                if url_list and len(url_list) > 0:
                    # First priority: Look for PDF URLs but convert to proper format
                    for url_obj in url_list:
                        doc_style = url_obj.get("documentStyle", "").lower()
                        if doc_style in ["pdf", "epdf"]:
                            url = url_obj.get("url", "")
                            # Convert NCBI URLs to Europe PMC direct PDF URLs
                            if "/pmc/articles/PMC" in url and "/pdf/" in url:
                                # Extract PMC ID from URL
                                pmc_match = re.search(r'/PMC(\d+)/', url)
                                if pmc_match:
                                    pmc_id = f"PMC{pmc_match.group(1)}"
                                    full_text_url = f"https://europepmc.org/backend/ptpmcrender.fcgi?accid={pmc_id}&blobtype=pdf"
                                    break
                            else:
                                full_text_url = url
                                break
                    
                    # Second priority: PMC URLs (if no PDF found)
                    if not full_text_url:
                        for url_obj in url_list:
                            url = url_obj.get("url", "")
                            if "pmc" in url.lower() or "europepmc.org" in url.lower():
                                # Extract PMC ID from various URL formats
                                pmc_id = None
                                if "/PMC" in url:
                                    pmc_id = "PMC" + url.split("/PMC")[1].split("/")[0].split("?")[0]
                                elif "pmcid=" in url:
                                    pmc_id = url.split("pmcid=")[1].split("&")[0]
                                
                                if pmc_id:
                                    # Use Europe PMC direct PDF download URL
                                    full_text_url = f"https://europepmc.org/backend/ptpmcrender.fcgi?accid={pmc_id}&blobtype=pdf"
                                    break
                    
                    # Third priority: use first available URL but convert if needed
                    if not full_text_url and url_list:
                        url = url_list[0].get("url", "")
                        # Check if it's an NCBI PMC URL that needs conversion
                        if "/pmc/articles/PMC" in url:
                            pmc_match = re.search(r'/PMC(\d+)', url)
                            if pmc_match:
                                pmc_id = f"PMC{pmc_match.group(1)}"
                                full_text_url = f"https://europepmc.org/backend/ptpmcrender.fcgi?accid={pmc_id}&blobtype=pdf"
                            else:
                                full_text_url = url
                        else:
                            full_text_url = url
            
            # Alternative: Check if PMC ID exists and construct PDF URL directly
            if not full_text_url and raw_paper.get("pmcid"):
                # Use Europe PMC direct PDF download URL
                full_text_url = f"https://europepmc.org/backend/ptpmcrender.fcgi?accid={raw_paper['pmcid']}&blobtype=pdf"
            
            # Skip if no full text available
            if not full_text_url:
                logger.debug(f"Skipping paper - no full text URL available")
                return None
            
            # Validate that URL points to a full article, not just abstract
            if self._is_abstract_only_url(full_text_url):
                logger.debug(f"Skipping paper - URL appears to be abstract-only: {full_text_url}")
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
                year=str(raw_paper.get("pubYear", "Unknown")) if raw_paper.get("pubYear") else "Unknown",
                source="Europe PMC",
                full_text_url=full_text_url,
                doi=doi,
                journal=journal,
                citation_count=raw_paper.get("citedByCount")
            )
        except Exception as e:
            logger.error(f"Error normalizing Europe PMC paper: {e}")
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