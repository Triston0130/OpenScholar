from typing import List, Dict, Any, Optional
import httpx
from app.api_clients.base import BaseAPIClient
from app.models import Paper
from app.utils.open_access_validator import open_access_validator
import logging
import asyncio
import time

logger = logging.getLogger(__name__)

class CrossrefClient(BaseAPIClient):
    """Crossref API client for scholarly metadata and DOI information"""
    
    def __init__(self, api_key: Optional[str] = None):
        super().__init__(base_url="https://api.crossref.org")
        self.api_key = api_key  # Not required for public tier
        self.last_request_time = 0
        self.min_request_interval = 1.0  # Be polite to Crossref
        
        # Add polite contact info as recommended by Crossref
        self.client.headers.update({
            "User-Agent": "OpenScholar Research Tool/1.0 (mailto:research@openscholar.app)"
        })
    
    async def _wait_for_rate_limit(self):
        """Ensure we don't overwhelm Crossref API"""
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
        """Search Crossref database for papers"""
        
        await self._wait_for_rate_limit()
        
        # Build query parameters with better query construction
        # Use query.bibliographic for full-text search across all fields
        params = {
            "query.bibliographic": query,  # Searches title, abstract, authors, etc.
            "rows": min(limit, 100),  # Crossref allows up to 1000, but we'll be conservative
            "sort": "relevance",
            "order": "desc",
            "filter": []
        }
        
        # Add year filter
        if year_start and year_end:
            params["filter"].append(f"from-pub-date:{year_start}")
            params["filter"].append(f"until-pub-date:{year_end}")
        elif year_start:
            params["filter"].append(f"from-pub-date:{year_start}")
        elif year_end:
            params["filter"].append(f"until-pub-date:{year_end}")
        
        # Add content type filter to focus on journal articles
        params["filter"].append("type:journal-article")
        
        # Don't filter by license - too restrictive
        # params["filter"].append("has-license:true")
        
        # Add discipline-specific filters
        if discipline:
            # Crossref doesn't have direct discipline filtering, but we can enhance the query
            discipline_terms = {
                "education": "education OR educational OR teaching OR learning OR pedagogy",
                "psychology": "psychology OR psychological OR cognitive OR behavioral",
                "child development": "child development OR developmental psychology OR early childhood",
                "early childhood": "early childhood OR preschool OR kindergarten",
                "stem": "science OR technology OR engineering OR mathematics OR STEM"
            }
            
            if discipline.lower() in discipline_terms:
                params["query"] = f"{query} AND ({discipline_terms[discipline.lower()]})"
        
        # Join filters
        if params["filter"]:
            params["filter"] = ",".join(params["filter"])
        else:
            del params["filter"]
        
        try:
            response = await self.client.get(
                f"{self.base_url}/works",
                params=params,
                timeout=30.0  # Increased timeout
            )
            response.raise_for_status()
            
            data = response.json()
            papers = []
            
            if "message" in data and "items" in data["message"]:
                logger.info(f"Crossref API returned {len(data['message']['items'])} items for query: {query}")
                for item in data["message"]["items"]:
                    paper = await self.normalize_paper(item)
                    if paper:
                        papers.append(paper)
                    else:
                        logger.debug(f"Paper rejected during normalization")
            else:
                logger.warning(f"Unexpected Crossref response structure: {list(data.keys())}")
            
            logger.info(f"Crossref normalized {len(papers)} papers for query: {query}")
            
            # Enhance with Unpaywall URLs for papers with DOIs
            try:
                enhanced_papers = await self._enhance_with_unpaywall(papers)
                return enhanced_papers
            except Exception as e:
                logger.error(f"Error enhancing with Unpaywall, returning original papers: {e}")
                return papers
            
        except Exception as e:
            logger.error(f"Error searching Crossref: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return []
    
    async def normalize_paper(self, raw_paper: Dict[str, Any]) -> Optional[Paper]:
        """Normalize Crossref response to Paper model"""
        try:
            # Extract title
            title = ""
            if "title" in raw_paper and raw_paper["title"]:
                title = raw_paper["title"][0].strip()
            
            if not title:
                logger.debug("Crossref paper rejected - no title")
                return None
            
            logger.debug(f"Processing Crossref paper: {title[:50]}...")
            
            # Extract authors
            authors = []
            if "author" in raw_paper:
                for author in raw_paper["author"]:
                    given = author.get("given", "")
                    family = author.get("family", "")
                    if family:
                        if given:
                            authors.append(f"{given} {family}")
                        else:
                            authors.append(family)
            
            # Extract abstract
            abstract = raw_paper.get("abstract", "")
            if not abstract:
                abstract = "No abstract available"
            
            # Extract publication year
            year = ""
            if "published-print" in raw_paper:
                date_parts = raw_paper["published-print"].get("date-parts", [[]])
                if date_parts and date_parts[0]:
                    year = str(date_parts[0][0])
            elif "published-online" in raw_paper:
                date_parts = raw_paper["published-online"].get("date-parts", [[]])
                if date_parts and date_parts[0]:
                    year = str(date_parts[0][0])
            
            # Extract DOI
            doi = raw_paper.get("DOI", "")
            
            # Extract journal name
            journal = ""
            if "container-title" in raw_paper and raw_paper["container-title"]:
                journal = raw_paper["container-title"][0]
            
            # Construct full text URL
            full_text_url = None
            
            # STRICT OA validation for Crossref
            
            # Step 1: Check for Creative Commons or other open licenses
            license_info = None
            has_open_license = False
            if "license" in raw_paper:
                licenses = raw_paper["license"]
                if licenses:
                    license_urls = []
                    for lic in licenses:
                        license_url = lic.get("URL", "")
                        if license_url:
                            license_urls.append(license_url)
                            # Check for open licenses
                            if any(cc in license_url.lower() for cc in ["creativecommons.org", "cc-by", "cc0"]):
                                has_open_license = True
                    license_info = "; ".join(license_urls)
            
            # Step 2: Must have either open license OR be from known OA publisher
            known_oa_publishers = [
                "plos", "frontiers", "mdpi", "hindawi", "bmj", "nature communications",
                "scientific reports", "springeropen", "biomed central", "ieee access",
                "royal society open", "f1000research", "elife", "wellcome open"
            ]
            
            is_from_oa_publisher = False
            if journal:
                journal_lower = journal.lower()
                is_from_oa_publisher = any(pub in journal_lower for pub in known_oa_publishers)
            
            # Must meet at least one OA criteria - but be less strict
            # Comment out for now to see what we're getting
            # if not has_open_license and not is_from_oa_publisher:
            #     logger.debug(f"Crossref paper rejected - no open license or OA publisher: {title[:50]}...")
            #     return None
            
            # Step 3: Get full text URL - prefer direct PDF links
            if "link" in raw_paper:
                for link in raw_paper["link"]:
                    if link.get("content-type") == "application/pdf":
                        full_text_url = link.get("URL")
                        break
                    elif link.get("content-type") == "text/html" and "intended-application" in link:
                        if link["intended-application"] == "text-mining":
                            full_text_url = link.get("URL")
                            break
            
            # If no direct link but has DOI, use DOI URL
            # Note: We're being less strict here - any paper with a DOI should be accessible somehow
            if not full_text_url and doi:
                full_text_url = f"https://doi.org/{doi}"
                logger.debug(f"Using DOI URL for paper: {title[:50]}...")
            
            # Skip only if no URL at all (no direct link AND no DOI)
            if not full_text_url:
                logger.debug(f"Crossref paper rejected - no accessible URL or DOI: {title[:50]}...")
                return None
            
            # Get citation count
            citation_count = raw_paper.get("is-referenced-by-count")
            
            # Validate open access status - but be less strict for Crossref
            # Since many Crossref papers don't have explicit license info, we'll be more permissive
            is_oa = True
            reason = "Crossref paper with DOI"
            
            # Only reject if it's from a known paywall domain
            if full_text_url:
                is_oa, reason = await open_access_validator.validate_paper(
                    title=title,
                    journal=journal,
                    doi=doi,
                    license_info=license_info,
                    abstract=abstract,
                    full_text_url=full_text_url,
                    check_url_accessibility=False
                )
                
                # For Crossref, we'll accept papers even without explicit OA indicators
                # as long as they're not from known paywall domains
                if not is_oa and "paywall domain" in reason.lower():
                    logger.debug(f"Crossref paper rejected: {title[:50]}... ({reason})")
                    return None
            
            logger.debug(f"Crossref paper accepted: {title[:50]}... (DOI: {doi})")
            return Paper(
                title=title,
                authors=authors if authors else ["Unknown"],
                abstract=abstract,
                year=year,
                source="Crossref",
                full_text_url=full_text_url,
                doi=doi,
                journal=journal,
                citation_count=citation_count
            )
            
        except Exception as e:
            logger.error(f"Error normalizing Crossref paper: {e}")
            return None
    
    async def _enhance_with_unpaywall(self, papers: List[Paper]) -> List[Paper]:
        """Enhance papers with direct PDF URLs from Unpaywall"""
        try:
            # Only check papers with DOIs
            papers_to_check = [p for p in papers if p.doi][:10]  # Limit to first 10 to avoid too many API calls
            
            if not papers_to_check:
                return papers
            
            logger.info(f"Enhancing {len(papers_to_check)} papers with Unpaywall URLs...")
            
            # Check each paper with Unpaywall
            async def check_paper(paper: Paper) -> Paper:
                try:
                    url = f"https://api.unpaywall.org/v2/{paper.doi}"
                    params = {"email": "research@openscholar.app"}
                    
                    async with httpx.AsyncClient() as client:
                        response = await client.get(url, params=params, timeout=5.0)
                        
                        if response.status_code == 200:
                            data = response.json()
                            
                            # If OA version found, update the URL
                            if data.get("is_oa") and data.get("oa_locations"):
                                # Get best OA location
                                best_location = None
                                for loc in data["oa_locations"]:
                                    if loc.get("url_for_pdf"):
                                        best_location = loc
                                        break
                                    elif not best_location and loc.get("url"):
                                        best_location = loc
                                
                                if best_location:
                                    pdf_url = best_location.get("url_for_pdf") or best_location.get("url")
                                    if pdf_url:
                                        paper.full_text_url = pdf_url
                                        logger.debug(f"Found Unpaywall URL for: {paper.title[:50]}...")
                                        
                                        # Add OA location info to abstract
                                        location_type = best_location.get("host_type", "")
                                        if location_type:
                                            paper.abstract += f"\n\n[Open Access: {location_type}]"
                
                except Exception as e:
                    logger.debug(f"Error checking Unpaywall for DOI {paper.doi}: {e}")
                
                return paper
            
            # Check papers concurrently but with rate limiting
            enhanced_papers = []
            for i in range(0, len(papers_to_check), 3):  # Process 3 at a time
                batch = papers_to_check[i:i+3]
                batch_results = await asyncio.gather(*[check_paper(p) for p in batch])
                enhanced_papers.extend(batch_results)
                
                if i + 3 < len(papers_to_check):
                    await asyncio.sleep(0.5)  # Small delay between batches
            
            # Combine enhanced papers with the rest
            enhanced_dois = {p.doi for p in enhanced_papers}
            for paper in papers:
                if paper.doi not in enhanced_dois:
                    enhanced_papers.append(paper)
            
            return enhanced_papers[:len(papers)]  # Return same number as input
            
        except Exception as e:
            logger.error(f"Error enhancing with Unpaywall: {e}")
            return papers  # Return original papers on error