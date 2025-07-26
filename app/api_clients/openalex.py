from typing import List, Dict, Any, Optional
import httpx
from app.api_clients.base import BaseAPIClient
from app.models import Paper
from app.utils.open_access_validator import open_access_validator
import logging
import asyncio
import time

logger = logging.getLogger(__name__)

class OpenAlexClient(BaseAPIClient):
    """OpenAlex API client for open access scholarly papers"""
    
    def __init__(self):
        super().__init__(base_url="https://api.openalex.org")
        self.last_request_time = 0
        self.min_request_interval = 0.1  # OpenAlex is generous with rate limits
        
        # OpenAlex requires email in User-Agent
        self.client.headers.update({
            "User-Agent": "OpenScholar Research Tool/1.0 (mailto:research@openscholar.app)",
            "Accept": "application/json"
        })
    
    async def _wait_for_rate_limit(self):
        """Rate limiting"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.min_request_interval:
            wait_time = self.min_request_interval - time_since_last
            await asyncio.sleep(wait_time)
        
        self.last_request_time = time.time()
    
    async def search(self, query: str, year_start: int, year_end: int,
                    discipline: Optional[str] = None,
                    education_level: Optional[str] = None,
                    limit: int = 20) -> List[Paper]:
        """Search OpenAlex for open access papers"""
        
        await self._wait_for_rate_limit()
        
        try:
            # Build search query
            # OpenAlex uses filter syntax: https://docs.openalex.org/api-entities/works/filter-works
            filters = []
            
            # Only get open access works
            filters.append("is_oa:true")
            
            # Year filter
            if year_start and year_end:
                filters.append(f"publication_year:{year_start}-{year_end}")
            elif year_start:
                filters.append(f"publication_year:>{year_start-1}")
            elif year_end:
                filters.append(f"publication_year:<{year_end+1}")
            
            # Build the filter string
            filter_str = ",".join(filters) if filters else None
            
            # Search parameters
            params = {
                "search": query,
                "filter": filter_str,
                "per_page": min(limit, 200),  # OpenAlex allows up to 200 per page
                "sort": "relevance_score:desc",
                "select": "id,title,display_name,authorships,publication_year,doi,open_access,primary_location,locations,abstract_inverted_index,cited_by_count,concepts"
            }
            
            # Remove None values
            params = {k: v for k, v in params.items() if v is not None}
            
            logger.info(f"Searching OpenAlex for: {query} with filters: {filter_str}")
            
            response = await self.client.get(
                f"{self.base_url}/works",
                params=params,
                timeout=30.0
            )
            response.raise_for_status()
            
            data = response.json()
            papers = []
            
            if "results" in data:
                for item in data["results"]:
                    paper = await self.normalize_paper(item)
                    if paper:
                        papers.append(paper)
            
            logger.info(f"OpenAlex returned {len(papers)} papers for query: {query}")
            return papers[:limit]
            
        except Exception as e:
            logger.error(f"Error searching OpenAlex: {e}")
            return []
    
    async def normalize_paper(self, raw_paper: Dict[str, Any]) -> Optional[Paper]:
        """Normalize OpenAlex response to Paper model"""
        try:
            # Extract title
            title = raw_paper.get("display_name", "").strip()
            if not title:
                return None
            
            # Only process if it's open access
            oa_info = raw_paper.get("open_access", {})
            if not oa_info.get("is_oa", False):
                logger.debug(f"OpenAlex paper rejected - not open access: {title[:50]}...")
                return None
            
            # Get the best OA URL - start with oa_url from oa_info
            oa_url = oa_info.get("oa_url")
            
            # If oa_url is a paywall domain, try to find a better one
            if oa_url and open_access_validator.is_paywall_domain(oa_url):
                logger.debug(f"OpenAlex oa_url is paywall domain: {oa_url}, searching for alternative...")
                oa_url = None
            
            # If no good oa_url, check all locations for truly open access URLs
            if not oa_url:
                # Try primary location first
                primary_location = raw_paper.get("primary_location", {})
                if primary_location and primary_location.get("is_oa"):
                    pdf_url = primary_location.get("pdf_url")
                    landing_url = primary_location.get("landing_page_url")
                    
                    # Check PDF URL first
                    if pdf_url and not open_access_validator.is_paywall_domain(pdf_url):
                        oa_url = pdf_url
                    # Then landing page URL
                    elif landing_url and not open_access_validator.is_paywall_domain(landing_url):
                        oa_url = landing_url
                
                # If still no good URL, check all locations
                if not oa_url:
                    all_locations = raw_paper.get("locations", [])
                    for location in all_locations:
                        if location.get("is_oa"):
                            pdf_url = location.get("pdf_url")
                            landing_url = location.get("landing_page_url")
                            
                            # Check PDF URL first
                            if pdf_url and not open_access_validator.is_paywall_domain(pdf_url):
                                oa_url = pdf_url
                                break
                            # Then landing page URL
                            elif landing_url and not open_access_validator.is_paywall_domain(landing_url):
                                oa_url = landing_url
                                break
            
            if not oa_url:
                logger.debug(f"OpenAlex paper rejected - no non-paywall OA URL found: {title[:50]}...")
                return None
            
            # Extract DOI first for validation
            doi = raw_paper.get("doi", "").replace("https://doi.org/", "") if raw_paper.get("doi") else None
            
            # Check if DOI is from a known paywall publisher
            if doi and not open_access_validator.is_doi_likely_open_access(doi):
                logger.debug(f"OpenAlex paper rejected - paywall DOI pattern: {doi} for {title[:50]}...")
                return None
            
            # Final validation of the URL
            is_oa, reason = open_access_validator.validate_paper_metadata(
                title=title,
                full_text_url=oa_url,
                doi=doi,
                journal=None  # Will extract journal later
            )
            
            if not is_oa:
                logger.debug(f"OpenAlex paper rejected - {reason}: {title[:50]}...")
                return None
            
            # Extract authors
            authors = []
            authorships = raw_paper.get("authorships", [])
            for authorship in authorships[:10]:  # Limit to 10 authors
                author_info = authorship.get("author", {})
                name = author_info.get("display_name")
                if name:
                    authors.append(name)
            
            # Extract abstract
            abstract = ""
            # OpenAlex provides inverted index for abstract, need to reconstruct
            abstract_inverted = raw_paper.get("abstract_inverted_index")
            if abstract_inverted:
                # Reconstruct abstract from inverted index
                words = [""] * (max(max(positions) for positions in abstract_inverted.values()) + 1)
                for word, positions in abstract_inverted.items():
                    for pos in positions:
                        words[pos] = word
                abstract = " ".join(word for word in words if word)
            
            if not abstract:
                abstract = "No abstract available"
            
            # Extract other fields
            year = str(raw_paper.get("publication_year", "Unknown"))
            # doi already extracted above for validation
            
            # Get journal from primary location
            journal = ""
            primary_location = raw_paper.get("primary_location", {})
            if primary_location:
                source = primary_location.get("source", {})
                if source:
                    journal = source.get("display_name", "")
            
            # Citation count
            citation_count = raw_paper.get("cited_by_count", 0)
            
            # Extract concepts/subjects
            subjects = []
            concepts = raw_paper.get("concepts", [])
            for concept in concepts[:5]:  # Limit to 5 concepts
                if concept.get("score", 0) > 0.3:  # Only high-relevance concepts
                    subjects.append(concept.get("display_name", ""))
            
            logger.debug(f"OpenAlex paper accepted: {title[:50]}... (OA URL: {oa_url})")
            
            return Paper(
                title=title,
                authors=authors if authors else ["Unknown"],
                abstract=abstract[:1500],  # Limit abstract length
                year=year,
                source="OpenAlex",
                full_text_url=oa_url,
                doi=doi,
                journal=journal,
                citation_count=citation_count,
                subjects=subjects if subjects else None
            )
            
        except Exception as e:
            logger.error(f"Error normalizing OpenAlex paper: {e}")
            return None