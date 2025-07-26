from typing import List, Dict, Any, Optional
import httpx
from app.api_clients.base import BaseAPIClient
from app.models import Paper
import logging
import asyncio
import time
import re
from urllib.parse import quote

logger = logging.getLogger(__name__)

class UnpaywallClient(BaseAPIClient):
    """Unpaywall API client for finding free versions of academic papers"""
    
    def __init__(self):
        super().__init__(base_url="https://api.unpaywall.org/v2")
        self.last_request_time = 0
        self.min_request_interval = 0.1  # Unpaywall allows 100k requests per day
        
        self.client.headers.update({
            "User-Agent": "OpenScholar Research Tool/1.0 (mailto:research@openscholar.app)",
            "Accept": "application/json"
        })
        
        # Email is required for Unpaywall API
        self.email = "research@openscholar.app"
    
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
        """Search for papers using Unpaywall (requires DOIs or uses Crossref first)"""
        
        # Since Unpaywall doesn't have a search endpoint, we'll use Crossref to find DOIs
        # then check Unpaywall for free versions
        
        try:
            # First, search Crossref for papers
            crossref_papers = await self._search_crossref(query, year_start, year_end, discipline, limit * 2)
            
            papers = []
            for crossref_paper in crossref_papers:
                if not crossref_paper.get("DOI"):
                    continue
                
                # Check if this paper is available free via Unpaywall
                unpaywall_paper = await self._check_unpaywall(crossref_paper["DOI"])
                if unpaywall_paper:
                    paper = await self._unpaywall_to_paper(unpaywall_paper, crossref_paper)
                    if paper:
                        papers.append(paper)
                        if len(papers) >= limit:
                            break
                
                await self._wait_for_rate_limit()
            
            logger.info(f"Unpaywall found {len(papers)} free papers for query: {query}")
            return papers
            
        except Exception as e:
            logger.error(f"Error searching with Unpaywall: {e}")
            return []
    
    async def _search_crossref(self, query: str, year_start: int, year_end: int, 
                              discipline: Optional[str], limit: int) -> List[Dict[str, Any]]:
        """Search Crossref for papers to check in Unpaywall"""
        try:
            crossref_url = "https://api.crossref.org/works"
            
            # Convert multi-word query to use OR
            query_terms = query.split()
            if len(query_terms) > 1:
                # Join with + for OR behavior in Crossref
                search_query = "+".join(query_terms)
            else:
                search_query = query
            
            params = {
                "query": search_query,
                "rows": limit,
                "select": "DOI,title,author,published-print,publisher,container-title,abstract,subject,type"
            }
            
            # Add year filter
            if year_start and year_end:
                params["filter"] = f"from-pub-date:{year_start},until-pub-date:{year_end}"
            elif year_start:
                params["filter"] = f"from-pub-date:{year_start}"
            elif year_end:
                params["filter"] = f"until-pub-date:{year_end}"
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    crossref_url, 
                    params=params,
                    headers={"User-Agent": "OpenScholar/1.0 (mailto:research@openscholar.app)"},
                    timeout=30.0
                )
                response.raise_for_status()
                
                data = response.json()
                return data.get("message", {}).get("items", [])
                
        except Exception as e:
            logger.error(f"Error searching Crossref: {e}")
            return []
    
    async def _check_unpaywall(self, doi: str) -> Optional[Dict[str, Any]]:
        """Check if a paper is available free via Unpaywall"""
        try:
            await self._wait_for_rate_limit()
            
            url = f"{self.base_url}/{doi}"
            params = {"email": self.email}
            
            response = await self.client.get(url, params=params, timeout=10.0)
            
            if response.status_code == 404:
                return None  # Not found in Unpaywall
                
            response.raise_for_status()
            data = response.json()
            
            # Check if there's an OA location
            if data.get("is_oa") and data.get("oa_locations"):
                return data
            
            return None
            
        except Exception as e:
            logger.debug(f"Error checking Unpaywall for {doi}: {e}")
            return None
    
    async def _unpaywall_to_paper(self, unpaywall_data: Dict[str, Any], 
                                 crossref_data: Dict[str, Any]) -> Optional[Paper]:
        """Convert Unpaywall + Crossref data to Paper object"""
        try:
            # Get the best OA location
            oa_locations = unpaywall_data.get("oa_locations", [])
            if not oa_locations:
                return None
            
            # Prefer publisher versions, then repositories
            best_location = None
            for loc in oa_locations:
                if loc.get("host_type") == "publisher":
                    best_location = loc
                    break
            if not best_location:
                best_location = oa_locations[0]
            
            # Get URL for full text
            full_text_url = best_location.get("url_for_pdf") or best_location.get("url")
            if not full_text_url:
                return None
            
            # Extract metadata (prefer Unpaywall, fallback to Crossref)
            title = unpaywall_data.get("title") or crossref_data.get("title", [""])[0]
            if not title:
                return None
            
            # Authors
            authors = []
            if unpaywall_data.get("z_authors"):
                for author in unpaywall_data["z_authors"]:
                    if author.get("given") and author.get("family"):
                        authors.append(f"{author['given']} {author['family']}")
            elif crossref_data.get("author"):
                for author in crossref_data["author"]:
                    if author.get("given") and author.get("family"):
                        authors.append(f"{author['given']} {author['family']}")
            
            if not authors:
                authors = ["Unknown"]
            
            # Year
            year = str(unpaywall_data.get("year", ""))
            if not year and crossref_data.get("published-print"):
                date_parts = crossref_data["published-print"].get("date-parts", [[]])[0]
                if date_parts:
                    year = str(date_parts[0])
            
            # Journal
            journal = unpaywall_data.get("journal_name") or crossref_data.get("container-title", [""])[0]
            
            # Abstract from Crossref
            abstract = ""
            if crossref_data.get("abstract"):
                abstract = crossref_data["abstract"]
                # Clean abstract
                abstract = re.sub(r'<[^>]+>', '', abstract)
                abstract = re.sub(r'\s+', ' ', abstract).strip()
            if not abstract:
                abstract = f"Open access version found via Unpaywall"
            
            # DOI
            doi = unpaywall_data.get("doi") or crossref_data.get("DOI")
            
            # Publisher
            publisher = unpaywall_data.get("publisher") or crossref_data.get("publisher")
            
            # Subjects from Crossref
            subjects = crossref_data.get("subject", [])
            
            # OA status info
            oa_status = unpaywall_data.get("oa_status", "")
            if oa_status:
                abstract += f" (OA Status: {oa_status})"
            
            # Repository info
            repo_name = best_location.get("repository_institution")
            if repo_name:
                abstract += f" Available from: {repo_name}"
            
            paper = Paper(
                title=title,
                authors=authors[:10],
                abstract=abstract[:1500],
                year=year,
                source="Unpaywall",
                full_text_url=full_text_url,
                doi=doi,
                journal=journal,
                citation_count=None,
                influential_citation_count=None,
                content_type="paper",
                isbn=None,
                publisher=publisher,
                page_count=None,
                language="en",
                subjects=subjects[:5] if subjects else None,
                download_formats=["PDF"] if best_location.get("url_for_pdf") else ["Online"]
            )
            
            # Validate open access
            is_oa, reason = await self.validate_open_access(paper)
            if is_oa:
                return paper
            else:
                logger.debug(f"Unpaywall paper rejected - {reason}: {paper.title[:50]}...")
                return None
            
        except Exception as e:
            logger.error(f"Error converting Unpaywall data to paper: {e}")
            return None
    
    async def normalize_paper(self, raw_item: Dict[str, Any], year_start: int, year_end: int) -> Optional[Paper]:
        """Compatibility method"""
        return None  # Not used directly