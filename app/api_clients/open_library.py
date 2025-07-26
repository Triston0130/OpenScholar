from typing import List, Dict, Any, Optional
import httpx
from app.api_clients.base import BaseAPIClient
from app.models import Paper
import logging
import asyncio
import time
import re

logger = logging.getLogger(__name__)

class OpenLibraryClient(BaseAPIClient):
    """Open Library API client for book metadata and free access"""
    
    def __init__(self):
        super().__init__(base_url="https://openlibrary.org")
        self.last_request_time = 0
        self.min_request_interval = 0.4  # Be respectful to Open Library
        
        self.client.headers.update({
            "User-Agent": "OpenScholar Research Tool/1.0 (mailto:research@openscholar.app)",
            "Accept": "application/json"
        })
    
    async def _wait_for_rate_limit(self):
        """Ensure we don't overwhelm Open Library API"""
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
        """Search Open Library for books with available text"""
        
        await self._wait_for_rate_limit()
        
        # Build query with focus on freely available texts
        # Add textbook-specific terms to improve results
        textbook_terms = ["textbook", "introduction", "fundamentals", "principles", "college", "university"]
        
        # Convert multi-word query to OR search
        query_terms = query.split()
        if len(query_terms) > 1:
            query_str = " OR ".join(query_terms)
        else:
            query_str = query
        
        # Add textbook terms to increase relevance
        textbook_query = " OR ".join([f'"{term}"' for term in textbook_terms])
        query_str = f"({query_str}) AND ({textbook_query})"
            
        search_params = {
            "q": query_str,
            "limit": min(limit * 2, 100),  # Increase limit to get more results
            "fields": "key,title,author_name,first_publish_year,publisher,language,subject,ia,has_fulltext,ebook_count_i,isbn,number_of_pages_median,publish_year",
            "sort": "rating desc"  # Sort by rating/popularity
        }
        
        # Add year filter
        if year_start and year_end:
            search_params["q"] = f"({search_params['q']}) AND first_publish_year:[{year_start} TO {year_end}]"
        elif year_start:
            search_params["q"] = f"({search_params['q']}) AND first_publish_year:[{year_start} TO *]"
        elif year_end:
            search_params["q"] = f"({search_params['q']}) AND first_publish_year:[* TO {year_end}]"
        
        # Focus on books with full text available
        search_params["q"] = f"({search_params['q']}) AND has_fulltext:true"
        
        # Add discipline-specific keywords
        if discipline:
            discipline_keywords = {
                "education": "education OR educational OR teaching OR learning OR pedagogy",
                "psychology": "psychology OR psychological OR cognitive OR behavioral",
                "computer science": "computer science OR programming OR software OR algorithms",
                "mathematics": "mathematics OR math OR statistics OR calculus OR algebra",
                "physics": "physics OR quantum OR mechanics OR scientific",
                "biology": "biology OR biological OR life sciences OR natural history",
                "history": "history OR historical OR civilization OR culture",
                "literature": "literature OR poetry OR fiction OR novel OR writing",
                "philosophy": "philosophy OR philosophical OR ethics OR logic",
                "science": "science OR scientific OR research OR study"
            }
            
            if discipline.lower() in discipline_keywords:
                search_params["q"] += f" AND ({discipline_keywords[discipline.lower()]})"
        
        try:
            response = await self.client.get(
                f"{self.base_url}/search.json",
                params=search_params,
                timeout=15.0
            )
            response.raise_for_status()
            
            data = response.json()
            books = []
            
            if "docs" in data:
                for item in data["docs"]:
                    # Only process books that have full text or Internet Archive links
                    if item.get("has_fulltext") or item.get("ia") or item.get("ebook_count_i", 0) > 0:
                        book = await self.normalize_paper(item)
                        if book:
                            books.append(book)
            
            logger.info(f"Open Library returned {len(books)} books for query: {query}")
            return books
            
        except Exception as e:
            logger.error(f"Error searching Open Library: {e}")
            return []
    
    async def normalize_paper(self, raw_book: Dict[str, Any]) -> Optional[Paper]:
        """Normalize Open Library response to Paper model"""
        try:
            # Extract title
            title = raw_book.get("title", "").strip()
            if not title:
                return None
            
            # Extract authors
            authors = []
            author_names = raw_book.get("author_name", [])
            if author_names:
                authors = [name.strip() for name in author_names if name and name.strip()]
            
            # Extract key for URL construction
            key = raw_book.get("key", "")
            if not key:
                return None
            
            # Extract Internet Archive identifier if available
            ia_identifier = None
            ia_list = raw_book.get("ia", [])
            if ia_list:
                ia_identifier = ia_list[0] if isinstance(ia_list, list) else ia_list
            
            # Construct full text URL
            full_text_url = None
            
            # Prefer Internet Archive links for full text
            if ia_identifier:
                full_text_url = f"https://archive.org/details/{ia_identifier}"
            else:
                # Use Open Library reader if available
                full_text_url = f"https://openlibrary.org{key}"
            
            # Extract first publish year
            year = ""
            first_publish_year = raw_book.get("first_publish_year")
            if first_publish_year:
                year = str(first_publish_year)
            
            # Create abstract from available metadata
            abstract_parts = []
            
            # Add subjects as description
            subjects = raw_book.get("subject", [])
            if subjects:
                subject_list = subjects[:5] if len(subjects) > 5 else subjects
                abstract_parts.append(f"Subjects: {', '.join(subject_list)}")
            
            # Add publisher info
            publishers = raw_book.get("publisher", [])
            if publishers:
                publisher_name = publishers[0] if isinstance(publishers, list) else publishers
                abstract_parts.append(f"Publisher: {publisher_name}")
            
            # Add publication years if available
            publish_years = raw_book.get("publish_year", [])
            if publish_years and len(publish_years) > 1:
                years_range = f"{min(publish_years)}-{max(publish_years)}"
                abstract_parts.append(f"Published: {years_range}")
            
            abstract = ". ".join(abstract_parts) if abstract_parts else "No description available"
            
            # Extract publisher
            publisher = ""
            publishers = raw_book.get("publisher", [])
            if publishers:
                publisher = publishers[0] if isinstance(publishers, list) else publishers
            
            # Extract language
            languages = raw_book.get("language", [])
            language = "en"  # Default
            if languages:
                language = languages[0] if isinstance(languages, list) else languages
            
            # Extract ISBN
            isbn = None
            isbns = raw_book.get("isbn", [])
            if isbns:
                isbn = isbns[0] if isinstance(isbns, list) else isbns
            
            # Extract page count
            page_count = raw_book.get("number_of_pages_median")
            
            # Determine available formats
            download_formats = []
            ebook_count = raw_book.get("ebook_count_i", 0)
            
            if ebook_count > 0 or ia_identifier:
                # Common formats available through Internet Archive
                download_formats = ["PDF", "EPUB", "TXT"]
            
            if raw_book.get("has_fulltext"):
                if "HTML" not in download_formats:
                    download_formats.append("HTML")
            
            return Paper(
                title=title,
                authors=authors if authors else ["Unknown"],
                abstract=abstract,
                year=year,
                source="Open Library",
                full_text_url=full_text_url,
                doi=None,  # Open Library doesn't use DOIs
                journal=None,  # Books don't have journals
                citation_count=None,  # Open Library doesn't provide citation counts
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
            logger.error(f"Error normalizing Open Library book: {e}")
            return None