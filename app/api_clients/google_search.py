from typing import List, Dict, Any, Optional
import httpx
from app.api_clients.base import BaseAPIClient
from app.models import Paper
import logging
import asyncio
import time
import re
from urllib.parse import quote_plus, urlparse
import os

logger = logging.getLogger(__name__)

class GoogleSearchClient(BaseAPIClient):
    """Google Custom Search API client - searches for PDFs only across the web"""
    
    def __init__(self, api_key: str = None, search_engine_id: str = None):
        super().__init__(base_url="https://www.googleapis.com/customsearch/v1")
        
        # Get API credentials from environment or parameters
        self.api_key = api_key or os.getenv("GOOGLE_SEARCH_API_KEY")
        self.search_engine_id = search_engine_id or os.getenv("GOOGLE_SEARCH_ENGINE_ID")
        
        # Also try alternative environment variable name for backwards compatibility
        if not self.search_engine_id:
            self.search_engine_id = os.getenv("GOOGLE_CSE_ID")
        
        self.last_request_time = 0
        self.min_request_interval = 0.1  # Google allows 100 queries per second
        
        self.client.headers.update({
            "User-Agent": "OpenScholar Research Tool/1.0 (mailto:research@openscholar.app)",
            "Accept": "application/json"
        })
    
    async def _wait_for_rate_limit(self):
        """Rate limiting to respect Google's API limits"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.min_request_interval:
            wait_time = self.min_request_interval - time_since_last
            await asyncio.sleep(wait_time)
        
        self.last_request_time = time.time()
    
    async def search(self, query: str, year_start: int = None, year_end: int = None,
                    discipline: Optional[str] = None,
                    education_level: Optional[str] = None,
                    limit: int = 20) -> List[Paper]:
        """Search Google for PDF files only"""
        
        if not self.api_key or not self.search_engine_id:
            logger.warning("Google Search API credentials not configured")
            return []
        
        await self._wait_for_rate_limit()
        
        try:
            # Build search query with PDF filter - return ALL PDFs, not just academic
            search_query = f"{query} filetype:pdf"
            
            # Add discipline if specified
            if discipline:
                search_query += f" {discipline}"
            
            # Make multiple requests if needed (Google allows max 10 per request)
            papers = []
            requests_needed = min((limit + 9) // 10, 5)  # Max 5 requests to avoid quota issues
            
            for request_num in range(requests_needed):
                start_index = request_num * 10 + 1
                per_request = min(10, limit - len(papers))
                
                if per_request <= 0:
                    break
                
                # Build parameters for Google Custom Search
                params = {
                    "key": self.api_key,
                    "cx": self.search_engine_id,
                    "q": search_query,
                    "num": per_request,
                    "start": start_index,
                    "fileType": "pdf",  # Ensure we only get PDFs
                    "safe": "active",  # Safe search
                    "fields": "items(title,link,snippet,displayLink,pagemap,fileFormat)"
                }
                
                # Add date range if specified (Google format: after:YYYY-MM-DD before:YYYY-MM-DD)
                if year_start and year_end:
                    date_filter = f"after:{year_start}-01-01 before:{year_end}-12-31"
                    params["q"] += f" {date_filter}"
                
                logger.info(f"Searching Google for PDFs (request {request_num + 1}): {search_query}")
                
                response = await self.client.get(self.base_url, params=params, timeout=15.0)
                response.raise_for_status()
                
                data = response.json()
                items = data.get("items", [])
                
                if not items:
                    break  # No more results
                
                for item in items:
                    paper = await self._result_to_paper(item, discipline)
                    if paper:
                        # Google Search already filters for PDFs and excludes paywall domains
                        # So we can add all results without additional validation
                        papers.append(paper)
                
                # Rate limiting between requests
                if request_num < requests_needed - 1:
                    await self._wait_for_rate_limit()
            
            logger.info(f"Google Search returned {len(papers)} open access PDFs for query: {query}")
            return papers
            
        except Exception as e:
            logger.error(f"Error searching Google for PDFs: {e}")
            return []
    
    async def _result_to_paper(self, item: Dict[str, Any], discipline: Optional[str] = None) -> Optional[Paper]:
        """Convert Google search result to Paper object"""
        try:
            # Get title
            title = item.get("title", "").strip()
            if not title:
                return None
            
            # Clean title (remove [PDF] markers etc)
            title = re.sub(r'\[PDF\]|\(PDF\)|\.pdf$', '', title, flags=re.IGNORECASE).strip()
            
            # Get PDF URL
            pdf_url = item.get("link", "")
            if not pdf_url or not pdf_url.lower().endswith('.pdf'):
                return None
            
            # Validate URL
            if not self._is_valid_pdf_url(pdf_url):
                return None
            
            # Get snippet/abstract
            snippet = item.get("snippet", "")
            if not snippet:
                snippet = f"PDF document from {item.get('displayLink', 'Google Search')}: {title}"
            
            # Clean snippet
            snippet = re.sub(r'\s+', ' ', snippet).strip()
            
            # Extract basic metadata from title and snippet
            authors = self._extract_authors_from_text(title, snippet)
            year = self._extract_year_from_text(title, snippet)
            
            # Determine source domain
            display_link = item.get("displayLink", "")
            domain = urlparse(pdf_url).netloc if pdf_url else display_link
            
            # Try to extract additional metadata from pagemap
            pagemap = item.get("pagemap", {})
            meta_tags = pagemap.get("metatags", [{}])[0] if pagemap.get("metatags") else {}
            
            # Get author from meta tags if available
            if not authors:
                meta_author = meta_tags.get("author") or meta_tags.get("dc.creator")
                if meta_author:
                    authors = [meta_author]
            
            # Get date from meta tags if available
            if not year:
                meta_date = meta_tags.get("date") or meta_tags.get("dc.date") or meta_tags.get("publication_date")
                if meta_date:
                    year_match = re.search(r'(\d{4})', meta_date)
                    if year_match:
                        year = year_match.group(1)
            
            # Fallback values
            if not authors:
                authors = ["Unknown"]
            if not year:
                year = "Unknown"
            
            return Paper(
                title=title,
                authors=authors,
                abstract=snippet[:1500],  # Limit snippet length
                year=str(year),
                source="Google Search",
                full_text_url=pdf_url,
                doi=None,  # PDFs from Google usually don't have DOIs in results
                journal=None,
                citation_count=None,
                influential_citation_count=None,
                content_type="paper",
                download_formats=["PDF"],
                subjects=[discipline] if discipline else None
            )
            
        except Exception as e:
            logger.error(f"Error converting Google search result to paper: {e}")
            return None
    
    def _is_valid_pdf_url(self, url: str) -> bool:
        """Validate that the URL is a proper PDF URL"""
        if not url:
            return False
        
        # Must be HTTPS for security
        if not url.startswith('https://'):
            return False
        
        # Must end with .pdf
        if not url.lower().endswith('.pdf'):
            return False
        
        # Skip known problematic domains
        blocked_domains = [
            'researchgate.net',  # Often requires login
            'academia.edu',      # Often requires login
            'jstor.org',         # Paywall
            'springer.com',      # Often paywall
            'elsevier.com',      # Often paywall
            'wiley.com',         # Often paywall
            'nature.com',        # Often paywall
            'sciencedirect.com', # Paywall
        ]
        
        parsed_url = urlparse(url)
        domain = parsed_url.netloc.lower()
        
        # Check if domain contains any blocked domain
        for blocked in blocked_domains:
            if blocked in domain:
                return False
        
        return True
    
    def _extract_authors_from_text(self, title: str, snippet: str) -> List[str]:
        """Extract author names from title and snippet"""
        text = f"{title} {snippet}".lower()
        
        # Common author patterns
        author_patterns = [
            r'by\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',  # "by John Smith"
            r'author:?\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',  # "author: John Smith"
            r'([A-Z][a-z]+\s+[A-Z][a-z]+)\s+et\s+al',  # "Smith Jones et al"
        ]
        
        authors = []
        for pattern in author_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                if isinstance(match, str) and len(match.split()) <= 3:  # Reasonable name length
                    authors.append(match.title())
                    break  # Take first match only
        
        return authors[:3]  # Limit to 3 authors
    
    def _extract_year_from_text(self, title: str, snippet: str) -> Optional[str]:
        """Extract publication year from title and snippet"""
        text = f"{title} {snippet}"
        
        # Look for 4-digit years (1900-2030)
        year_pattern = r'\b(19\d{2}|20[0-3]\d)\b'
        matches = re.findall(year_pattern, text)
        
        if matches:
            # Return the most recent reasonable year
            years = [int(year) for year in matches]
            current_year = 2025
            reasonable_years = [year for year in years if 1900 <= year <= current_year]
            if reasonable_years:
                return str(max(reasonable_years))
        
        return None
    
    async def normalize_paper(self, raw_item: Dict[str, Any]) -> Optional[Paper]:
        """Compatibility method"""
        return await self._result_to_paper(raw_item)