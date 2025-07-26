from typing import List, Dict, Any, Optional
import httpx
from app.api_clients.base import BaseAPIClient
from app.models import Paper
import logging
import asyncio
import time
import re

logger = logging.getLogger(__name__)

class OpenStaxClient(BaseAPIClient):
    """OpenStax API client for free textbooks"""
    
    def __init__(self):
        super().__init__(base_url="https://openstax.org")
        self.last_request_time = 0
        self.min_request_interval = 0.5
        
        self.client.headers.update({
            "User-Agent": "OpenScholar Research Tool/1.0 (mailto:research@openscholar.app)",
            "Accept": "application/json"
        })
        
        # Set follow_redirects=True for httpx client
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=30.0,
            follow_redirects=True,
            headers=self.client.headers
        )
    
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
        """Search OpenStax textbooks"""
        
        await self._wait_for_rate_limit()
        
        try:
            # OpenStax books API endpoint
            api_url = f"{self.base_url}/apps/cms/api/books/"
            
            params = {
                "format": "json"
            }
            
            logger.info(f"Searching OpenStax for: {query}")
            
            response = await self.client.get(api_url, params=params, timeout=30.0)
            response.raise_for_status()
            
            data = response.json()
            books = []
            
            # OpenStax API returns a dict with "books" array
            book_list = data.get("books", [])
            for item in book_list:
                # Filter books that match the query
                if self._matches_query(item, query, discipline):
                    paper = await self._book_to_paper(item)
                    if paper:
                        # Apply year filtering
                        if self._matches_year_filter(paper, year_start, year_end):
                            books.append(paper)
                            if len(books) >= limit:
                                break
            
            logger.info(f"OpenStax returned {len(books)} books for query: {query}")
            return books
            
        except Exception as e:
            logger.error(f"Error searching OpenStax: {e}")
            return []
    
    def _matches_query(self, book: Dict[str, Any], query: str, discipline: Optional[str] = None) -> bool:
        """Check if book matches search query"""
        try:
            # Skip non-live books
            book_state = book.get("book_state", "")
            if book_state != "live":
                return False
            
            query_lower = query.lower()
            
            # Build searchable text from OpenStax book fields
            searchable_parts = [
                book.get("title", ""),
                " ".join(book.get("subjects", [])),
                " ".join(book.get("k12subject", [])),
            ]
            
            # Add book content description if available
            if book.get("content_warning_text"):
                searchable_parts.append(book.get("content_warning_text", ""))
            
            searchable_text = " ".join(searchable_parts).lower()
            
            # Check if query terms match
            query_terms = query_lower.split()
            if not any(term in searchable_text for term in query_terms):
                return False
            
            # Discipline filtering based on subjects
            if discipline:
                subjects = book.get("subjects", []) + book.get("k12subject", [])
                subjects_text = " ".join(subjects).lower()
                
                discipline_keywords = {
                    "psychology": ["psychology", "behavioral", "cognitive", "mental health"],
                    "biology": ["biology", "life science", "anatomy", "physiology"],
                    "chemistry": ["chemistry", "chemical", "organic", "inorganic"],
                    "physics": ["physics", "mechanics", "thermodynamics", "quantum"],
                    "mathematics": ["mathematics", "calculus", "algebra", "statistics", "math"],
                    "history": ["history", "historical", "civilization"],
                    "literature": ["literature", "english", "writing", "composition"],
                    "economics": ["economics", "business", "finance", "accounting"],
                    "sociology": ["sociology", "social", "anthropology"],
                    "education": ["education", "teaching", "learning", "pedagogy"]
                }
                
                keywords = discipline_keywords.get(discipline.lower(), [])
                if keywords and not any(keyword in subjects_text for keyword in keywords):
                    return False
            
            return True
            
        except Exception as e:
            logger.warning(f"Error matching query: {e}")
            return False
    
    def _matches_year_filter(self, paper: Paper, year_start: int, year_end: int) -> bool:
        """Apply year filtering"""
        if not year_start and not year_end:
            return True
        
        if not paper.year or not paper.year.isdigit():
            return True  # Include books without clear years
        
        paper_year = int(paper.year)
        
        if year_start and paper_year < year_start:
            return False
        if year_end and paper_year > year_end:
            return False
        
        return True
    
    async def _book_to_paper(self, book: Dict[str, Any]) -> Optional[Paper]:
        """Convert OpenStax book to Paper object"""
        try:
            title = book.get("title", "").strip()
            if not title:
                return None
            
            # OpenStax books typically don't list individual authors - they're created by OpenStax
            authors = ["OpenStax"]
            
            # Use title as abstract since OpenStax doesn't provide detailed descriptions in API
            abstract = f"OpenStax free textbook: {title}"
            
            # Extract subjects from both subjects and k12subject fields
            subjects = list(set(book.get("subjects", []) + book.get("k12subject", [])))
            
            # Most OpenStax books are modern (2010s+)
            year = "2015"  # Default year for OpenStax books
            
            # Build URLs - prefer PDF for direct viewing
            webview_link = book.get("webview_rex_link")
            pdf_url = book.get("high_resolution_pdf_url") 
            
            # Prefer PDF URL for direct viewing in PDF viewer
            full_text_url = pdf_url or webview_link
            if not full_text_url:
                book_id = book.get("id", "")
                full_text_url = f"https://openstax.org/details/books/{book_id}" if book_id else None
            
            # Determine download formats
            download_formats = ["Online"]
            if pdf_url:
                download_formats.append("PDF")
            
            # Only include live books
            if book.get("book_state") != "live":
                return None
            
            return Paper(
                title=title,
                authors=authors,
                abstract=abstract,
                year=year,
                source="OpenStax",
                full_text_url=full_text_url,
                doi=None,
                journal=None,
                citation_count=None,
                influential_citation_count=None,
                content_type="book",
                isbn=None,
                publisher="OpenStax",
                page_count=None,
                language="en",
                subjects=subjects if subjects else None,
                download_formats=download_formats
            )
            
        except Exception as e:
            logger.error(f"Error converting OpenStax book to paper: {e}")
            return None
    
    async def normalize_paper(self, raw_item: Dict[str, Any], year_start: int, year_end: int) -> Optional[Paper]:
        """Compatibility method"""
        return await self._book_to_paper(raw_item)