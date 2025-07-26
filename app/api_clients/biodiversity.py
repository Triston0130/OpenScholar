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

class BiodiversityClient(BaseAPIClient):
    """Biodiversity Heritage Library API client for natural history literature"""
    
    def __init__(self, api_key: Optional[str] = None):
        super().__init__(base_url="https://www.biodiversitylibrary.org")
        self.last_request_time = 0
        self.min_request_interval = 0.5
        
        self.client.headers.update({
            "User-Agent": "OpenScholar Research Tool/1.0 (mailto:research@openscholar.app)",
            "Accept": "application/json"
        })
        
        # BHL API key (free registration required for production)
        self.api_key = api_key or "00000000-0000-0000-0000-000000000000"  # Use demo key if none provided
    
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
        """Search Biodiversity Heritage Library"""
        
        await self._wait_for_rate_limit()
        
        try:
            # BHL API v3 search endpoint
            search_url = f"{self.base_url}/api3"
            
            params = {
                "op": "PublicationSearchAdvanced",
                "title": query,  # PublicationSearchAdvanced uses 'title' not 'searchterm'
                "searchtype": "F",  # Full text search
                "apikey": self.api_key,
                "format": "json",
                "limit": min(limit * 2, 200)  # Get more results to filter
            }
            
            # Add year filter if provided
            if year_start:
                params["startdate"] = year_start
            if year_end:
                params["enddate"] = year_end
            
            # Check if we have an API key
            if not self.api_key:
                logger.info("BHL search skipped - requires API key")
                return []
                
            response = await self.client.get(search_url, params=params)
            response.raise_for_status()
            
            data = response.json()
            results = data.get("Result", [])
            
            if not results:
                logger.info(f"BHL found no results for query: {query}")
                return []
            
            # Convert results to papers
            books = []
            
            for item in results:
                paper = await self._book_to_paper(item, discipline, query)
                if paper:
                    books.append(paper)
                    if len(books) >= limit:
                        break
            
            logger.info(f"BHL returned {len(books)} books for query: {query}")
            return books
            
        except Exception as e:
            logger.error(f"Error searching Biodiversity Heritage Library: {e}")
            return []
    
    async def _book_to_paper(self, book: Dict[str, Any], discipline: Optional[str] = None, query: str = "") -> Optional[Paper]:
        """Convert BHL record to Paper object"""
        try:
            # Get title
            title = book.get("Title", "") or book.get("FullTitle", "")
            if not title:
                return None
            
            # Clean title
            title = re.sub(r'\s+', ' ', title).strip()
            
            # Get authors
            authors = []
            author_names = book.get("Authors", [])
            if isinstance(author_names, list):
                for author in author_names:
                    if isinstance(author, dict):
                        name = author.get("Name", "")
                        if name:
                            authors.append(name)
                    elif isinstance(author, str):
                        authors.append(author)
            
            if not authors:
                # Try to extract from PublisherName
                publisher = book.get("PublisherName", "")
                if publisher and not publisher.lower().startswith(("publisher", "published")):
                    authors = [publisher]
                else:
                    authors = ["Unknown"]
            
            # Get year
            year = book.get("Year") or book.get("PublicationDate") or book.get("Date")
            if year:
                year_match = re.search(r'(\d{4})', str(year))
                if year_match:
                    year = year_match.group(1)
                else:
                    year = "Unknown"
            else:
                year = "Unknown"
            
            # Filter by discipline if specified
            if discipline and discipline.lower() not in ["biology", "natural history", "botany", "zoology", "ecology"]:
                # BHL is specialized in natural history, skip if looking for other disciplines
                return None
            
            # Get subjects
            subjects = []
            subject_list = book.get("Subjects", [])
            if isinstance(subject_list, list):
                subjects = [s.get("SubjectText", "") if isinstance(s, dict) else str(s) 
                           for s in subject_list if s]
            
            # Add default subjects for BHL
            if not subjects:
                subjects = ["Natural History", "Biodiversity", "Biology"]
            
            # Build URLs
            title_id = book.get("TitleID")
            item_id = book.get("ItemID")
            
            # For BHL, we want to provide the PDF URL as full_text_url for the PDF viewer
            if item_id:
                # Direct PDF URL using ItemID
                full_text_url = f"https://www.biodiversitylibrary.org/itempdf/{item_id}"
            elif title_id:
                # Fallback to bibliography page if no ItemID
                full_text_url = f"https://www.biodiversitylibrary.org/bibliography/{title_id}"
            else:
                full_text_url = f"https://www.biodiversitylibrary.org/search?SearchTerm={quote(query)}"
            
            # Get publisher info
            publisher_name = book.get("PublisherName", "")
            publisher_place = book.get("PublisherPlace", "")
            publisher = f"{publisher_place}: {publisher_name}" if publisher_place and publisher_name else publisher_name or "Biodiversity Heritage Library"
            
            # Volume/edition info
            volume = book.get("Volume", "")
            edition = book.get("Edition", "")
            
            abstract = f"Historical natural history literature from the Biodiversity Heritage Library. "
            if volume:
                abstract += f"Volume: {volume}. "
            if edition:
                abstract += f"Edition: {edition}. "
            if subjects:
                abstract += f"Subjects: {', '.join(subjects[:3])}"
            
            return Paper(
                title=title,
                authors=authors[:5],  # Limit authors
                abstract=abstract,
                year=str(year) if year and year != "" else "Unknown",
                source="BHL",
                full_text_url=full_text_url,
                doi=None,
                journal=None,
                citation_count=None,
                influential_citation_count=None,
                content_type="book",
                isbn=None,
                publisher=publisher,
                page_count=book.get("PageCount"),
                language=book.get("Language", "en"),
                subjects=subjects[:5] if subjects else ["Natural History"],
                download_formats=["PDF", "Online"]
            )
            
        except Exception as e:
            logger.error(f"Error converting BHL book to paper: {e}")
            return None
    
    async def normalize_paper(self, raw_item: Dict[str, Any], year_start: int, year_end: int) -> Optional[Paper]:
        """Compatibility method"""
        return await self._book_to_paper(raw_item)