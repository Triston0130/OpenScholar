from typing import List, Dict, Any, Optional
import httpx
from app.api_clients.base import BaseAPIClient
from app.models import Paper
import logging
import asyncio
import time
import re
import xml.etree.ElementTree as ET
from urllib.parse import quote

logger = logging.getLogger(__name__)

class NLMBookshelfClient(BaseAPIClient):
    """National Library of Medicine Bookshelf API client for medical textbooks"""
    
    def __init__(self):
        super().__init__(base_url="https://eutils.ncbi.nlm.nih.gov/entrez/eutils")
        self.last_request_time = 0
        self.min_request_interval = 0.4  # NCBI requires 3 requests per second max
        
        self.client.headers.update({
            "User-Agent": "OpenScholar Research Tool/1.0 (mailto:research@openscholar.app)",
            "Accept": "application/xml"
        })
    
    async def _wait_for_rate_limit(self):
        """Rate limiting for NCBI (3 requests per second)"""
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
        """Search NLM Bookshelf for medical textbooks"""
        
        await self._wait_for_rate_limit()
        
        try:
            # Step 1: Search for book IDs
            search_url = f"{self.base_url}/esearch.fcgi"
            
            # Build query for books database
            # Try to get full books rather than sections by adding filters
            query_terms = query.split()
            if len(query_terms) > 1:
                # Search for any of the terms
                search_query = " OR ".join([f"{term}[All Fields]" for term in query_terms])
                search_query = f"({search_query})"
            else:
                search_query = f"{query}[All Fields]"
            
            # Don't filter by object type as it's too restrictive
            
            # Add year filter
            if year_start and year_end:
                search_query += f" AND {year_start}:{year_end}[Publication Date]"
            elif year_start:
                search_query += f" AND {year_start}:3000[Publication Date]"
            elif year_end:
                search_query += f" AND 1900:{year_end}[Publication Date]"
            
            params = {
                "db": "books",
                "term": search_query,
                "retmax": min(limit, 100),
                "retmode": "xml",
                "sort": "relevance"
            }
            
            logger.info(f"Searching NLM Bookshelf for: {query}")
            
            response = await self.client.get(search_url, params=params, timeout=30.0)
            response.raise_for_status()
            
            # Parse XML response
            root = ET.fromstring(response.content)
            id_list = root.find("IdList")
            
            if id_list is None:
                return []
            
            book_ids = [id_elem.text for id_elem in id_list.findall("Id") if id_elem.text]
            
            if not book_ids:
                return []
            
            # Step 2: Fetch book details
            await self._wait_for_rate_limit()
            
            fetch_url = f"{self.base_url}/esummary.fcgi"
            fetch_params = {
                "db": "books",
                "id": ",".join(book_ids),
                "retmode": "xml"
            }
            
            response = await self.client.get(fetch_url, params=fetch_params, timeout=30.0)
            response.raise_for_status()
            
            # Parse book details
            books = []
            root = ET.fromstring(response.content)
            
            for doc_sum in root.findall(".//DocSum"):
                paper = await self._parse_book_summary(doc_sum, discipline)
                if paper:
                    books.append(paper)
            
            logger.info(f"NLM Bookshelf returned {len(books)} books for query: {query}")
            return books
            
        except Exception as e:
            logger.error(f"Error searching NLM Bookshelf: {e}")
            return []
    
    async def _parse_book_summary(self, doc_sum: ET.Element, discipline: Optional[str] = None) -> Optional[Paper]:
        """Parse book summary XML to Paper object"""
        try:
            # Helper to get item value
            def get_item(name: str) -> str:
                elem = doc_sum.find(f".//Item[@Name='{name}']")
                return elem.text if elem is not None and elem.text else ""
            
            # Get book ID
            book_id = doc_sum.find("Id")
            if book_id is None or not book_id.text:
                return None
            
            # Get title - check for book name first (for sections)
            title = get_item("Title")
            book_name = get_item("Book")
            
            # If we have a generic section title and a book name, use the book name
            if title and book_name and title.lower() in ["table", "methods", "references", "introduction", "background", "about the authors"]:
                title = book_name
            elif not title and book_name:
                title = book_name
            elif not title:
                return None
            
            # Clean up title if it's a book ID or abbreviated
            if title:
                # Replace common abbreviations
                title_replacements = {
                    "hiv_prep_len": "HIV Pre-Exposure Prophylaxis Guidelines",
                    "dmssa": "Disease Management and Social Services Administration",
                    "jatscon25": "JATS-Con Proceedings 2025",
                    "who_mhgap": "WHO Mental Health Gap Action Programme",
                    "ncbi_handbook": "NCBI Handbook",
                }
                
                # Check if title needs replacement
                title_lower = title.lower().replace("-", "_")
                for abbrev, full_name in title_replacements.items():
                    if abbrev in title_lower:
                        title = full_name
                        break
                
                # If still looks like an ID, try to make it more readable
                if title.startswith("NBK") or "_" in title or len(title) < 15:
                    # Try to get a better title from other fields
                    alt_title = get_item("Text") or get_item("Summary") or get_item("Description")
                    if alt_title and len(alt_title) > 10:
                        title = alt_title[:200]  # Limit length
                    else:
                        # Make the ID more readable
                        title = title.replace("_", " ").replace("-", " ").title()
            
            # Get authors
            authors = []
            author_list = get_item("AuthorList")
            if author_list:
                # Split by semicolon or comma
                authors = re.split(r'[;,]', author_list)
                authors = [a.strip() for a in authors if a.strip()]
            
            if not authors:
                authors = ["National Library of Medicine"]
            
            # Get year
            pubdate = get_item("PubDate")
            year = ""
            if pubdate:
                year_match = re.search(r'(\d{4})', pubdate)
                if year_match:
                    year = year_match.group(1)
            
            # Get publisher
            publisher = get_item("Publisher") or "National Library of Medicine"
            
            # Get description
            description = get_item("Description") or get_item("Summary")
            if not description:
                description = "Medical textbook from the National Library of Medicine Bookshelf"
            
            # Build URL - use PDF URL for the PDF viewer
            full_text_url = f"https://www.ncbi.nlm.nih.gov/books/{book_id.text}/pdf/"
            
            # Get subjects - medical books are specialized
            subjects = ["Medicine", "Health Sciences"]
            
            # Add specific medical subjects based on title/content
            title_lower = title.lower()
            if "anatomy" in title_lower:
                subjects.append("Anatomy")
            elif "physiology" in title_lower:
                subjects.append("Physiology")
            elif "pharmacology" in title_lower:
                subjects.append("Pharmacology")
            elif "genetics" in title_lower:
                subjects.append("Genetics")
            elif "biochemistry" in title_lower:
                subjects.append("Biochemistry")
            elif "pathology" in title_lower:
                subjects.append("Pathology")
            
            # Filter by discipline if specified
            if discipline and discipline.lower() not in ["medicine", "health", "biology", "life sciences"]:
                return None
            
            return Paper(
                title=title,
                authors=authors[:5],  # Limit authors
                abstract=description[:1000],
                year=year,
                source="NLM Bookshelf",
                full_text_url=full_text_url,
                doi=None,
                journal=None,
                citation_count=None,
                influential_citation_count=None,
                content_type="book",
                isbn=get_item("ISBN"),
                publisher=publisher,
                page_count=None,
                language="en",
                subjects=subjects,
                download_formats=["Online", "PDF", "EPUB"]
            )
            
        except Exception as e:
            logger.error(f"Error parsing NLM book summary: {e}")
            return None
    
    async def normalize_paper(self, raw_item: Dict[str, Any], year_start: int, year_end: int) -> Optional[Paper]:
        """Compatibility method"""
        # Not used for XML parsing
        return None