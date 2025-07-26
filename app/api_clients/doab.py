from typing import List, Dict, Any, Optional
import httpx
from app.api_clients.base import BaseAPIClient
from app.models import Paper
import logging
import asyncio
import time
import re
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

class DOABClient(BaseAPIClient):
    """DOAB (Directory of Open Access Books) API client"""
    
    def __init__(self):
        super().__init__(base_url="https://directory.doabooks.org/rest")
        self.last_request_time = 0
        self.min_request_interval = 0.5  # Be respectful to DOAB
        
        self.client.headers.update({
            "User-Agent": "OpenScholar Research Tool/1.0 (mailto:research@openscholar.app)",
            "Accept": "application/json"
        })
    
    async def _wait_for_rate_limit(self):
        """Ensure we don't overwhelm DOAB API"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.min_request_interval:
            wait_time = self.min_request_interval - time_since_last
            await asyncio.sleep(wait_time)
        
        self.last_request_time = time.time()
    
    async def extract_pdf_url_from_handle(self, handle_url: str) -> Optional[str]:
        """Extract PDF download URL from DOAB handle page"""
        try:
            # Fetch the handle page
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(handle_url)
                response.raise_for_status()
                
                # Parse HTML
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Look for download links
                # DOAB pages typically have download links in a specific pattern
                # Look for links containing "bitstream" and ending with ".pdf"
                for link in soup.find_all('a', href=True):
                    href = link['href']
                    if 'bitstream' in href and href.endswith('.pdf'):
                        # Convert relative URLs to absolute
                        if href.startswith('http'):
                            return href
                        elif href.startswith('/'):
                            # Extract base URL from handle_url
                            base_url = '/'.join(handle_url.split('/')[:3])
                            return base_url + href
                        else:
                            # Relative to current directory
                            base_path = '/'.join(handle_url.split('/')[:-1])
                            return base_path + '/' + href
                
                # Alternative: Look for links with "Download" text
                for link in soup.find_all('a', string=re.compile(r'Download.*PDF', re.I)):
                    href = link.get('href', '')
                    if href:
                        if href.startswith('http'):
                            return href
                        elif href.startswith('/'):
                            base_url = '/'.join(handle_url.split('/')[:3])
                            return base_url + href
                
                logger.warning(f"No PDF URL found on handle page: {handle_url}")
                return None
                
        except Exception as e:
            logger.error(f"Error extracting PDF URL from {handle_url}: {e}")
            return None
    
    async def search(self, query: str, year_start: int, year_end: int,
                    discipline: Optional[str] = None,
                    education_level: Optional[str] = None,
                    limit: int = 20) -> List[Paper]:
        """Search DOAB for open access books"""
        
        await self._wait_for_rate_limit()
        
        # Build search parameters for DOAB API
        params = {
            "query": query,
            "size": min(limit, 20),  # Reduce to avoid timeouts
            "expand": "metadata"  # Only metadata, bitstreams cause timeouts
        }
        
        # Skip year filtering for DOAB as it causes timeouts
        # We'll filter by year in post-processing instead
        
        # Add discipline-specific terms to query
        if discipline:
            discipline_terms = {
                "education": "education OR educational OR teaching OR learning OR pedagogy",
                "psychology": "psychology OR psychological OR cognitive OR behavioral",
                "child development": "child development OR developmental psychology OR early childhood",
                "computer science": "computer science OR programming OR software OR algorithms",
                "mathematics": "mathematics OR math OR statistics OR calculus OR algebra",
                "physics": "physics OR quantum OR mechanics OR thermodynamics",
                "biology": "biology OR biological OR life sciences OR ecology"
            }
            
            if discipline.lower() in discipline_terms:
                params["query"] = f"{query} AND ({discipline_terms[discipline.lower()]})"
        
        try:
            logger.info(f"DOAB query: {params}")
            response = await self.client.get(
                f"{self.base_url}/search",
                params=params,
                timeout=30.0  # Increase timeout for DOAB
            )
            response.raise_for_status()
            
            data = response.json()
            logger.info(f"DOAB response type: {type(data)}, length: {len(data) if isinstance(data, list) else 'N/A'}")
            books = []
            
            # DOAB returns an array directly, not wrapped in "results"
            if isinstance(data, list):
                for item in data:
                    book = await self.normalize_paper(item, year_start, year_end)
                    if book:
                        books.append(book)
            elif "results" in data:
                for item in data["results"]:
                    book = await self.normalize_paper(item, year_start, year_end)
                    if book:
                        books.append(book)
            
            logger.info(f"DOAB returned {len(books)} books for query: {query}")
            return books
            
        except Exception as e:
            logger.error(f"Error searching DOAB: {e}", exc_info=True)
            return []
    
    async def normalize_paper(self, raw_book: Dict[str, Any], year_start: Optional[int] = None, year_end: Optional[int] = None) -> Optional[Paper]:
        """Normalize DOAB response to Paper model"""
        try:
            # Extract title from name field (DOAB uses "name" not "title")
            title = raw_book.get("name", "") or ""
            title = title.strip() if title else ""
            if not title:
                title = raw_book.get("title", "") or ""
                title = title.strip() if title else ""
            if not title:
                return None
            
            # Extract authors from metadata (DOAB metadata structure)
            authors = []
            metadata = raw_book.get("metadata", [])
            for meta in metadata:
                if meta.get("key") == "dc.contributor.author":
                    authors.append(meta.get("value", ""))
                elif meta.get("key") == "dc.creator":
                    authors.append(meta.get("value", ""))
            
            # Extract abstract/description from metadata
            abstract = "No description available"
            for meta in metadata:
                if meta.get("key") in ["dc.description.abstract", "dc.description"]:
                    abstract = meta.get("value", "")
                    break
            
            # Clean up abstract (remove HTML tags if present)
            abstract = re.sub(r'<[^>]+>', '', abstract)
            abstract = abstract.strip() or "No description available"
            
            # Extract publication year from metadata
            year = ""
            for meta in metadata:
                if meta.get("key") in ["dc.date.issued", "dc.date.published", "dc.date"]:
                    date_val = meta.get("value", "")
                    year_match = re.search(r'\d{4}', date_val)
                    if year_match:
                        year = year_match.group()
                        break
            
            # Apply year filtering if specified
            if year and (year_start or year_end):
                try:
                    year_int = int(year)
                    if year_start and year_int < year_start:
                        return None
                    if year_end and year_int > year_end:
                        return None
                except ValueError:
                    pass  # Continue if year is not a valid integer
            
            # Extract publisher from metadata
            publisher = ""
            for meta in metadata:
                if meta.get("key") == "dc.publisher":
                    publisher = meta.get("value", "")
                    break
            
            # Extract language from metadata
            language = "en"
            for meta in metadata:
                if meta.get("key") == "dc.language.iso":
                    language = meta.get("value", "en")
                    break
            
            # Extract subjects/keywords from metadata
            subjects = []
            for meta in metadata:
                if meta.get("key") in ["dc.subject", "dc.subject.classification"]:
                    subjects.append(meta.get("value", ""))
            
            # Extract ISBN from metadata
            isbn = ""
            for meta in metadata:
                if meta.get("key") == "dc.identifier.isbn":
                    isbn = meta.get("value", "")
                    break
            
            # Extract DOI from metadata
            doi = ""
            for meta in metadata:
                if meta.get("key") == "dc.identifier.doi":
                    doi = meta.get("value", "")
                    break
            
            # Look for PDF URL in metadata
            download_formats = ["PDF", "HTML"]  # DOAB books typically have these formats
            full_text_url = None
            pdf_url = None
            
            # Check metadata for direct PDF links
            for meta in metadata:
                key = meta.get("key", "")
                value = meta.get("value", "")
                
                # Look for PDF URLs in various metadata fields
                if value and isinstance(value, str) and value.endswith('.pdf'):
                    pdf_url = value
                    logger.info(f"Found PDF URL in metadata for '{title}': {pdf_url}")
                    break
                elif key in ["dc.identifier.uri", "dc.identifier.url"] and "oapen.org/bitstream" in value:
                    pdf_url = value
                    logger.info(f"Found OAPEN URL in metadata for '{title}': {pdf_url}")
                    break
            
            # Use PDF if found, otherwise try to extract from handle page
            if pdf_url:
                full_text_url = pdf_url
            else:
                handle = raw_book.get("handle", "")
                if handle:
                    # Just use the handle URL directly - PDF extraction will happen in frontend
                    full_text_url = f"https://directory.doabooks.org/handle/{handle}"
                elif doi:
                    full_text_url = f"https://doi.org/{doi}"
            
            # Ensure we have a full_text_url
            if not full_text_url:
                logger.warning(f"No full text URL found for DOAB book: {title}")
                return None
            
            # Extract page count from metadata
            page_count = None
            for meta in metadata:
                if meta.get("key") in ["dc.format.extent", "dc.format"]:
                    extent = meta.get("value", "")
                    # Try to extract number from various formats like "250 p.", "xviii, 345 p.", etc.
                    page_match = re.search(r'(\d+)', str(extent))
                    if page_match:
                        page_count = int(page_match.group(1))
                        break
            
            return Paper(
                title=title,
                authors=authors if authors else ["Unknown"],
                abstract=abstract,
                year=year,
                source="DOAB",
                full_text_url=full_text_url,
                doi=doi,
                journal=None,  # Books don't have journals
                citation_count=None,  # DOAB doesn't provide citation counts
                influential_citation_count=None,
                content_type="book",
                isbn=isbn,
                publisher=publisher,
                page_count=page_count,
                language=language,
                subjects=subjects if subjects else None,
                download_formats=download_formats if download_formats else None
            )
            
        except Exception as e:
            logger.error(f"Error normalizing DOAB book: {e}")
            return None