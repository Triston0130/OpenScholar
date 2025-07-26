from typing import List, Dict, Any, Optional
import httpx
from app.api_clients.base import BaseAPIClient
from app.models import Paper
import logging
import asyncio
import time
import re
from urllib.parse import quote_plus

logger = logging.getLogger(__name__)

class GoogleBooksClient(BaseAPIClient):
    """Google Books API client - free access, no authentication needed"""
    
    def __init__(self):
        super().__init__(base_url="https://www.googleapis.com/books/v1")
        self.last_request_time = 0
        self.min_request_interval = 0.2  # Be polite to Google
        
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
        """Search Google Books for academic books and texts"""
        
        await self._wait_for_rate_limit()
        
        try:
            # Build search query - require ALL terms to match
            # Split query into terms and join with + for Google Books (requires all terms)
            query_terms = query.split()
            search_terms = "+".join(query_terms)
            
            # Add academic filters
            if discipline:
                search_terms += f"+{discipline}"
            
            # Focus on academic books by adding academic keywords
            search_terms += "+academic OR research OR study"
            
            # Build parameters
            params = {
                "q": search_terms,
                "maxResults": min(limit, 40),  # Google Books max is 40
                "orderBy": "relevance",
                "printType": "books",
                "projection": "full"
            }
            
            # Add subject filter if discipline specified
            if discipline:
                # Map disciplines to Google Books subject categories
                subject_map = {
                    "science": "subject:Science",
                    "medicine": "subject:Medical",
                    "psychology": "subject:Psychology", 
                    "education": "subject:Education",
                    "history": "subject:History",
                    "philosophy": "subject:Philosophy",
                    "literature": "subject:Literary+Criticism",
                    "mathematics": "subject:Mathematics",
                    "biology": "subject:Science",
                    "chemistry": "subject:Science",
                    "physics": "subject:Science"
                }
                
                subject_filter = subject_map.get(discipline.lower())
                if subject_filter:
                    params["q"] += f" {subject_filter}"
            
            logger.info(f"Searching Google Books for: {query}")
            
            response = await self.client.get(f"{self.base_url}/volumes", params=params, timeout=15.0)
            response.raise_for_status()
            
            data = response.json()
            items = data.get("items", [])
            
            papers = []
            for item in items:
                paper = await self._book_to_paper(item, year_start, year_end, discipline)
                if paper:
                    papers.append(paper)
                    if len(papers) >= limit:
                        break
            
            logger.info(f"Google Books returned {len(papers)} books for query: {query}")
            return papers
            
        except Exception as e:
            logger.error(f"Error searching Google Books: {e}")
            return []
    
    async def _book_to_paper(self, item: Dict[str, Any], year_start: int, year_end: int, discipline: Optional[str] = None) -> Optional[Paper]:
        """Convert Google Books item to Paper object"""
        try:
            volume_info = item.get("volumeInfo", {})
            
            # Get title
            title = volume_info.get("title", "")
            if not title:
                return None
            
            # Get authors
            authors = volume_info.get("authors", [])
            if not authors:
                authors = ["Unknown"]
            
            # Get description/abstract
            description = volume_info.get("description", "")
            if not description:
                description = f"Book from Google Books: {title}"
            
            # Clean HTML from description
            description = re.sub(r'<[^>]+>', '', description)
            description = re.sub(r'\s+', ' ', description).strip()
            
            # Get publication year
            published_date = volume_info.get("publishedDate", "")
            year = ""
            if published_date:
                year_match = re.search(r'(\d{4})', published_date)
                if year_match:
                    year = year_match.group(1)
            
            # If no year found, skip this book
            if not year:
                return None
            
            # Apply year filter
            if year and year_start and year_end:
                try:
                    year_int = int(year)
                    if year_int < year_start or year_int > year_end:
                        return None
                except ValueError:
                    pass
            
            # Get publisher
            publisher = volume_info.get("publisher", "")
            
            # Get page count
            page_count = volume_info.get("pageCount")
            
            # Get language
            language = volume_info.get("language", "en")
            
            # Get categories/subjects
            categories = volume_info.get("categories", [])
            subjects = categories[:5] if categories else []
            
            # Get identifiers for ISBN
            isbn = None
            identifiers = volume_info.get("industryIdentifiers", [])
            for identifier in identifiers:
                if identifier.get("type") in ["ISBN_13", "ISBN_10"]:
                    isbn = identifier.get("identifier")
                    break
            
            # Include books with reasonable access
            access_info = item.get("accessInfo", {})
            
            # Check if book has some view access (not just ALL_PAGES)
            viewability = access_info.get("viewability", "")
            if viewability in ["NO_PAGES", "NOT_ACCESSIBLE"]:
                return None  # Skip completely inaccessible books
            
            # Get full text URL - prefer web reader, fallback to preview
            web_reader_link = access_info.get("webReaderLink")
            preview_link = access_info.get("previewLink")
            info_link = volume_info.get("infoLink")
            
            full_text_url = web_reader_link or preview_link or info_link
            if not full_text_url:
                return None  # Must have some kind of link
            
            # Determine download formats based on access
            download_formats = ["Online"]
            if access_info.get("pdf", {}).get("isAvailable"):
                download_formats.append("PDF")
            if access_info.get("epub", {}).get("isAvailable"):
                download_formats.append("EPUB")
            
            return Paper(
                title=title,
                authors=authors[:10],  # Limit authors
                abstract=description[:1500],  # Limit description length
                year=str(year) if year is not None else "Unknown",
                source="Google Books",
                full_text_url=full_text_url,
                doi=None,
                journal=None,
                citation_count=None,
                influential_citation_count=None,
                content_type="book",
                isbn=isbn,
                publisher=publisher,
                page_count=page_count,
                language=language,
                subjects=subjects if subjects else None,
                download_formats=download_formats
            )
            
        except Exception as e:
            logger.error(f"Error converting Google Books item to paper: {e}")
            return None
    
    async def normalize_paper(self, raw_item: Dict[str, Any], year_start: int = 0, year_end: int = 0) -> Optional[Paper]:
        """Compatibility method"""
        return await self._book_to_paper(raw_item, year_start, year_end)