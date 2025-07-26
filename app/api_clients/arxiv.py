from typing import List, Dict, Any, Optional
import httpx
import xml.etree.ElementTree as ET
from app.api_clients.base import BaseAPIClient
from app.models import Paper
from app.utils.open_access_validator import open_access_validator
import logging
import asyncio
import time

logger = logging.getLogger(__name__)

class ArxivClient(BaseAPIClient):
    """arXiv API client for preprints and scientific papers"""
    
    def __init__(self, api_key: Optional[str] = None):
        super().__init__(base_url="https://export.arxiv.org/api")
        self.api_key = api_key  # Not required for arXiv
        self.last_request_time = 0
        self.min_request_interval = 3.0  # arXiv recommends 3 seconds between requests
        
        # Add User-Agent as recommended by arXiv
        self.client.headers.update({
            "User-Agent": "OpenScholar Research Tool 1.0 (mailto:research@openscholar.app)"
        })
    
    async def _wait_for_rate_limit(self):
        """Ensure we respect arXiv's rate limits"""
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
        """Search arXiv database for papers"""
        
        await self._wait_for_rate_limit()
        
        # Build search query
        search_terms = [query]
        
        # Add discipline-specific categories for arXiv
        if discipline:
            discipline_categories = {
                "education": ["cs.CY", "stat.OT"],  # Computers and Society, Other Statistics
                "psychology": ["q-bio.NC", "stat.AP"],  # Neurons and Cognition, Applications
                "mathematics": ["math"],  # All math categories
                "computer science": ["cs"],  # All CS categories
                "physics": ["physics", "astro-ph", "cond-mat", "gr-qc", "hep-ex", "hep-lat", "hep-ph", "hep-th", "math-ph", "nlin", "nucl-ex", "nucl-th", "quant-ph"],
                "biology": ["q-bio"],  # All quantitative biology
                "statistics": ["stat"],  # All statistics categories
            }
            
            if discipline.lower() in discipline_categories:
                # Add category search to arXiv query
                categories = discipline_categories[discipline.lower()]
                if isinstance(categories, list) and len(categories) == 1:
                    search_terms.append(f"cat:{categories[0]}*")
                elif isinstance(categories, list):
                    cat_query = " OR ".join([f"cat:{cat}*" for cat in categories])
                    search_terms.append(f"({cat_query})")
        
        # arXiv doesn't have direct year filtering in API, we'll filter results
        search_query = " AND ".join(search_terms)
        
        params = {
            "search_query": search_query,
            "start": 0,
            "max_results": min(limit, 100),  # arXiv recommends max 100
            "sortBy": "relevance",
            "sortOrder": "descending"
        }
        
        try:
            response = await self.client.get(
                f"{self.base_url}/query",
                params=params,
                timeout=30.0  # arXiv can be slow
            )
            response.raise_for_status()
            
            # Parse XML response
            papers = self._parse_arxiv_xml(response.text, year_start, year_end)
            
            # arXiv papers are inherently open access - minimal validation needed
            validated_papers = []
            for paper in papers:
                # Simple validation: must have title, authors, and valid PDF URL
                if (paper.title and 
                    paper.authors and 
                    paper.full_text_url and 
                    "arxiv.org/pdf/" in paper.full_text_url):
                    validated_papers.append(paper)
                    logger.debug(f"arXiv paper accepted: {paper.title[:50]}... (arXiv preprint - inherently OA)")
                else:
                    logger.debug(f"arXiv paper rejected: {paper.title[:50]}... (incomplete metadata)")
            
            logger.info(f"arXiv returned {len(validated_papers)} papers for query: {query}")
            return validated_papers
            
        except Exception as e:
            logger.error(f"Error searching arXiv: {e}")
            return []
    
    def _parse_arxiv_xml(self, xml_content: str, year_start: Optional[int], year_end: Optional[int]) -> List[Paper]:
        """Parse arXiv XML response into Paper objects"""
        papers = []
        
        try:
            # Parse XML with namespace handling
            root = ET.fromstring(xml_content)
            
            # Define namespaces
            namespaces = {
                'atom': 'http://www.w3.org/2005/Atom',
                'arxiv': 'http://arxiv.org/schemas/atom'
            }
            
            # Find all entry elements
            entries = root.findall('atom:entry', namespaces)
            
            for entry in entries:
                try:
                    # Extract basic information
                    title = entry.find('atom:title', namespaces)
                    title = title.text.strip() if title is not None else ""
                    
                    # Extract summary (abstract)
                    summary = entry.find('atom:summary', namespaces)
                    abstract = summary.text.strip() if summary is not None else ""
                    
                    # Extract authors
                    authors = []
                    author_elements = entry.findall('atom:author', namespaces)
                    for author_elem in author_elements:
                        name_elem = author_elem.find('atom:name', namespaces)
                        if name_elem is not None:
                            authors.append(name_elem.text.strip())
                    
                    # Extract published date and year
                    published = entry.find('atom:published', namespaces)
                    year = ""
                    if published is not None:
                        # Format: 2023-01-15T09:00:00Z
                        year_str = published.text[:4]
                        year = year_str
                        
                        # Filter by year if specified
                        if year_start or year_end:
                            try:
                                paper_year = int(year_str)
                                if year_start and paper_year < year_start:
                                    continue
                                if year_end and paper_year > year_end:
                                    continue
                            except ValueError:
                                continue
                    
                    # Extract arXiv ID and construct URLs
                    arxiv_id = ""
                    pdf_url = ""
                    doi = None
                    
                    id_elem = entry.find('atom:id', namespaces)
                    if id_elem is not None:
                        # Extract arXiv ID from URL like http://arxiv.org/abs/2301.12345v1
                        arxiv_url = id_elem.text
                        if '/abs/' in arxiv_url:
                            arxiv_id = arxiv_url.split('/abs/')[-1]
                            # Remove version number if present
                            if 'v' in arxiv_id:
                                arxiv_id = arxiv_id.split('v')[0]
                            
                            # Construct PDF URL
                            pdf_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"
                    
                    # Extract DOI if available
                    doi_elem = entry.find('arxiv:doi', namespaces)
                    if doi_elem is not None:
                        doi = doi_elem.text.strip()
                    
                    # Extract categories for journal field
                    categories = []
                    category_elements = entry.findall('atom:category', namespaces)
                    for cat_elem in category_elements:
                        term = cat_elem.get('term')
                        if term:
                            categories.append(term)
                    
                    journal = f"arXiv preprint ({', '.join(categories[:3])})" if categories else "arXiv preprint"
                    
                    # Create Paper object
                    if title and pdf_url:
                        paper = Paper(
                            title=title,
                            authors=authors if authors else ["Unknown"],
                            abstract=abstract or "No abstract available",
                            year=year,
                            source="arXiv",
                            full_text_url=pdf_url,
                            doi=doi,
                            journal=journal,
                            citation_count=None  # arXiv doesn't provide citation counts
                        )
                        papers.append(paper)
                        
                except Exception as e:
                    logger.debug(f"Error parsing arXiv entry: {e}")
                    continue
            
        except Exception as e:
            logger.error(f"Error parsing arXiv XML: {e}")
        
        return papers