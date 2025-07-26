from typing import List, Dict, Any, Optional
import httpx
from app.api_clients.base import BaseAPIClient
from app.models import Paper
from app.utils.open_access_validator import open_access_validator
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
        
        # Build search query - use OR for multiple terms
        query_terms = query.split()
        if len(query_terms) > 1:
            search_query = " OR ".join(query_terms)
        else:
            search_query = query
        
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
        
        # Build parameters - less restrictive filters for more results
        params = {
            "search": search_query,
            "format": "json",
            "rows": limit * 3,  # Request more to account for filtering
            "start": 0,
            "fields": "id,title,author,publicationdateyear,description,peerreviewed,url,isbn,sourceurl,publicationtype,audience,subject,institutionauthor,sponsor,e_fulltextauth",
            # Basic filters
            "fq": []
        }
        
        # Add year filter to fq
        if year_start and year_end:
            params["fq"].append(f"publicationdateyear:[{year_start} TO {year_end}]")
        
        # Join fq filters
        if params["fq"]:
            params["fq"] = " AND ".join(params["fq"])
        
        try:
            response = await self.client.get(
                f"{self.base_url}/",
                params=params,
                timeout=15.0
            )
            response.raise_for_status()
            
            data = response.json()
            papers = []
            
            if "response" in data and "docs" in data["response"]:
                for doc in data["response"]["docs"]:
                    # Include all papers with URLs, not just peer-reviewed
                    paper = await self.normalize_paper(doc)
                    if paper:
                        papers.append(paper)
                        if len(papers) >= limit:
                            break
            
            return papers
            
        except Exception as e:
            logger.error(f"Error searching ERIC: {e}")
            return []
    
    async def normalize_paper(self, raw_paper: Dict[str, Any]) -> Optional[Paper]:
        """Normalize ERIC response to Paper model - STRICT open access validation for education research"""
        try:
            title = raw_paper.get("title", "").strip()
            if not title:
                return None
            
            # Check if full text is available (e_fulltextauth is 0 or 1, not boolean)
            fulltext_auth = raw_paper.get("e_fulltextauth", 0)
            # Log what we're getting but don't filter yet
            logger.debug(f"ERIC paper e_fulltextauth={fulltext_auth} for: {title[:50]}...")
            
            # ERIC-specific open access validation
            # Step 1: Get URL or construct it from ID
            full_text_url = None
            eric_id = raw_paper.get("id", "")
            
            if raw_paper.get("url"):
                full_text_url = raw_paper["url"]
            elif raw_paper.get("sourceurl"):
                full_text_url = raw_paper["sourceurl"]
            elif eric_id:
                # If no URL but we have an ID, construct the ERIC landing page URL
                full_text_url = f"https://eric.ed.gov/?id={eric_id}"
                logger.debug(f"Constructed ERIC URL from ID: {full_text_url}")
            
            if not full_text_url:
                logger.debug(f"ERIC paper rejected - no URL or ID: {title[:50]}...")
                return None
            
            # Convert ERIC landing page URL to direct PDF URL
            if "eric.ed.gov/?id=" in full_text_url:
                # Extract ERIC ID from URL if not already have it
                if not eric_id:
                    eric_id = full_text_url.split("?id=")[-1].split("&")[0]
                
                # ED documents with fulltext_auth=1 have PDFs on ERIC servers
                if eric_id.startswith("ED") and fulltext_auth == 1:
                    full_text_url = f"https://files.eric.ed.gov/fulltext/{eric_id}.pdf"
                    logger.debug(f"Converted ERIC URL to direct PDF: {full_text_url}")
                elif eric_id.startswith("ED") and fulltext_auth != 1:
                    # ED without full text should be rejected
                    logger.debug(f"ERIC ED paper rejected - no full text available: {title[:50]}...")
                    return None
                elif eric_id.startswith("EJ"):
                    # EJ documents are journal articles
                    # If fulltext_auth=0 and we have an external URL, it might be paywalled
                    if fulltext_auth != 1 and not raw_paper.get("url"):
                        logger.debug(f"ERIC EJ paper rejected - no full text access: {title[:50]}...")
                        return None
                    logger.debug(f"ERIC EJ paper: {eric_id} - fulltext_auth={fulltext_auth}")
            
            # Step 2: Check for educational/institutional URLs (typically open access)
            url_lower = full_text_url.lower()
            
            # Known open access domains for ERIC
            open_access_domains = [
                'eric.ed.gov', 'files.eric.ed.gov', 'ies.ed.gov',
                'repository', 'digital', 'scholar', 'research',
                'ojs.', 'journal', 'archive', 'dspace', 'escholarship',
                'open', 'free', 'public'
            ]
            
            # Educational domains that MAY be open access (need additional checks)
            educational_domains = ['.edu/', '.ac.', '.org/', '.gov/']
            
            # Check for known paywall/restricted domains
            paywall_domains = [
                'jstor.org', 'sciencedirect.com', 'elsevier.com', 
                'springer.com', 'wiley.com', 'tandfonline.com',
                'sagepub.com', 'nature.com', 'ieee.org',
                'acm.org', 'apa.org', 'cambridge.org'
            ]
            
            # Reject if from known paywall domain
            if any(domain in url_lower for domain in paywall_domains):
                logger.debug(f"ERIC paper rejected - paywall domain: {title[:50]}...")
                return None
            
            # Check if URL has open access indicators
            is_open_access_url = any(domain in url_lower for domain in open_access_domains)
            is_educational_url = any(domain in url_lower for domain in educational_domains)
            
            # Step 3: Check publication source/sponsor for known open access publishers
            sponsor = raw_paper.get("sponsor", "")
            institution = raw_paper.get("institutionauthor", "")
            pub_type = raw_paper.get("publicationtype", "")
            
            known_oa_sources = [
                "department of education", "institute of education sciences",
                "national science foundation", "national institutes",
                "eric", "government", "university", "college",
                "open access", "creative commons", "public domain"
            ]
            
            is_from_oa_source = False
            for field in [sponsor, institution, pub_type]:
                if field and isinstance(field, str):
                    field_lower = field.lower()
                    if any(source in field_lower for source in known_oa_sources):
                        is_from_oa_source = True
                        break
                elif field and isinstance(field, list):
                    for item in field:
                        if isinstance(item, str):
                            item_lower = item.lower()
                            if any(source in item_lower for source in known_oa_sources):
                                is_from_oa_source = True
                                break
            
            # Step 4: Must meet strong open access criteria
            # If it's a known OA URL, accept it
            if is_open_access_url:
                pass  # Will accept below
            # If from OA source AND educational URL, likely OA
            elif is_from_oa_source and is_educational_url:
                pass  # Will accept below
            # If only educational URL without OA indicators, reject
            else:
                logger.debug(f"ERIC paper rejected - insufficient OA evidence: {title[:50]}...")
                return None
            
            # Extract authors
            authors = []
            if "author" in raw_paper and raw_paper["author"]:
                if isinstance(raw_paper["author"], list):
                    authors = [str(author).strip() for author in raw_paper["author"]]
                else:
                    authors = [author.strip() for author in str(raw_paper["author"]).split(";")]
            
            # Handle publication type/journal
            journal = ""
            if isinstance(pub_type, list):
                journal = ", ".join(str(t) for t in pub_type)
            else:
                journal = str(pub_type) if pub_type else "ERIC Education Database"
            
            # Get other metadata
            doi = raw_paper.get("isbn")  # ERIC sometimes uses ISBN
            abstract = raw_paper.get("description", "").strip()
            
            # Try to get citation count
            citation_count = None
            if doi:
                citation_count = await self._get_citation_count_from_europe_pmc(doi)
            
            logger.debug(f"ERIC paper accepted: {title[:50]}... (Educational OA source)")
            return Paper(
                title=title,
                authors=authors,
                abstract=abstract,
                year=str(raw_paper.get("publicationdateyear", "Unknown")) if raw_paper.get("publicationdateyear") else "Unknown",
                source="ERIC",
                full_text_url=full_text_url,
                doi=doi,
                journal=journal,
                citation_count=citation_count
            )
            
        except Exception as e:
            logger.error(f"Error normalizing ERIC paper: {e}")
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