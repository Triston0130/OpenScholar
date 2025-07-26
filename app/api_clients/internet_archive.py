from typing import List, Dict, Any, Optional
import httpx
from app.api_clients.base import BaseAPIClient
from app.models import Paper
import logging
import asyncio
import time
import re
import urllib.parse

logger = logging.getLogger(__name__)

class InternetArchiveClient(BaseAPIClient):
    """Internet Archive API client for books and texts"""
    
    def __init__(self):
        super().__init__(base_url="https://archive.org")
        self.last_request_time = 0
        self.min_request_interval = 0.5  # Be respectful to Internet Archive
        
        self.client.headers.update({
            "User-Agent": "OpenScholar Research Tool/1.0 (mailto:research@openscholar.app)",
            "Accept": "application/json"
        })
    
    async def _wait_for_rate_limit(self):
        """Ensure we don't overwhelm Internet Archive API"""
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
        """Search Internet Archive for texts and books"""
        
        await self._wait_for_rate_limit()
        
        # Build query for Internet Archive Advanced Search
        search_query = f"({query})"
        
        # Add media type filter for texts/books
        search_query += " AND mediatype:(texts OR books)"
        
        # Add collection filters for freely accessible content (avoid restricted collections)
        search_query += " AND (collection:opensource OR collection:gutenberg OR collection:internetarchivebooks)"
        # Exclude restricted/preview-only collections
        search_query += " AND NOT collection:inlibrary"
        
        # Add year filter if specified
        if year_start and year_end:
            search_query += f" AND year:[{year_start} TO {year_end}]"
        elif year_start:
            search_query += f" AND year:[{year_start} TO *]"
        elif year_end:
            search_query += f" AND year:[* TO {year_end}]"
        
        # Add discipline-specific terms
        if discipline:
            discipline_terms = {
                "education": "education OR educational OR teaching OR learning OR pedagogy OR school",
                "psychology": "psychology OR psychological OR cognitive OR behavioral OR mental",
                "computer science": "computer OR programming OR software OR algorithm OR technology",
                "mathematics": "mathematics OR math OR statistics OR calculus OR algebra OR geometry",
                "physics": "physics OR quantum OR mechanics OR thermodynamics OR relativity",
                "biology": "biology OR biological OR life sciences OR ecology OR evolution",
                "history": "history OR historical OR civilization OR culture",
                "literature": "literature OR poetry OR novel OR fiction OR writing",
                "philosophy": "philosophy OR philosophical OR ethics OR logic OR metaphysics"
            }
            
            if discipline.lower() in discipline_terms:
                search_query += f" AND ({discipline_terms[discipline.lower()]})"
        
        # Build API parameters
        params = {
            "q": search_query,
            "fl": "identifier,title,creator,description,date,publisher,language,subject,format,downloads,avg_rating,num_reviews",
            "rows": min(limit, 50),  # Internet Archive allows up to 10000, but we'll be conservative
            "output": "json",
            "sort": "downloads desc"  # Sort by popularity
        }
        
        try:
            response = await self.client.get(
                f"{self.base_url}/advancedsearch.php",
                params=params,
                timeout=15.0
            )
            response.raise_for_status()
            
            data = response.json()
            books = []
            
            if "response" in data and "docs" in data["response"]:
                for item in data["response"]["docs"]:
                    book = await self.normalize_paper(item)
                    if book:
                        books.append(book)
            
            logger.info(f"Internet Archive returned {len(books)} books for query: {query}")
            return books
            
        except Exception as e:
            logger.error(f"Error searching Internet Archive: {e}")
            return []
    
    async def normalize_paper(self, raw_item: Dict[str, Any]) -> Optional[Paper]:
        """Normalize Internet Archive response to Paper model"""
        try:
            # Extract title
            title = raw_item.get("title", "").strip()
            if not title:
                return None
            
            # Clean title (remove extra whitespace and common prefixes)
            title = re.sub(r'\s+', ' ', title)
            title = title.strip()
            
            # Extract authors/creators
            authors = []
            creator = raw_item.get("creator", "")
            if creator:
                if isinstance(creator, list):
                    for auth in creator:
                        if auth and auth.strip():
                            # Clean up author names
                            clean_auth = re.sub(r'\s*\(\d{4}-?\d{0,4}\)', '', auth).strip()
                            authors.append(clean_auth)
                elif isinstance(creator, str) and creator.strip():
                    clean_auth = re.sub(r'\s*\(\d{4}-?\d{0,4}\)', '', creator).strip()
                    authors.append(clean_auth)
            
            # Extract description
            description = raw_item.get("description", "")
            if isinstance(description, list) and description:
                description = description[0]
            
            abstract = description if description else "No description available"
            
            # Clean abstract (remove HTML tags and excessive whitespace)
            abstract = re.sub(r'<[^>]+>', '', abstract)
            abstract = re.sub(r'\s+', ' ', abstract).strip()
            
            # Limit abstract length
            if len(abstract) > 500:
                abstract = abstract[:500] + "..."
            
            # Extract year
            year = ""
            date_field = raw_item.get("date", "")
            if date_field:
                if isinstance(date_field, list) and date_field:
                    date_field = date_field[0]
                
                # Extract year from various date formats
                year_match = re.search(r'\b(19|20)\d{2}\b', str(date_field))
                if year_match:
                    year = year_match.group()
            
            # Extract identifier for URL construction
            identifier = raw_item.get("identifier", "")
            if not identifier:
                return None
            
            # Construct URLs
            full_text_url = f"https://archive.org/details/{identifier}"
            
            # Extract publisher
            publisher = raw_item.get("publisher", "")
            if isinstance(publisher, list) and publisher:
                publisher = publisher[0]
            
            # Extract language
            language = raw_item.get("language", "en")
            if isinstance(language, list) and language:
                language = language[0]
            
            # Extract subjects
            subjects = []
            subject_field = raw_item.get("subject", [])
            if subject_field:
                if isinstance(subject_field, list):
                    subjects = [s.strip() for s in subject_field if s and s.strip()]
                elif isinstance(subject_field, str):
                    subjects = [subject_field.strip()]
            
            # Extract formats and validate full access
            formats = raw_item.get("format", [])
            download_formats = []
            
            # Check if item has downloadable text formats (indicating full access)
            has_full_text = False
            
            if formats:
                if isinstance(formats, list):
                    for fmt in formats:
                        fmt_upper = fmt.upper()
                        # Check for full-text readable formats
                        if any(x in fmt_upper for x in ["PDF", "EPUB", "MOBI", "TXT", "HTML", "DJVU"]):
                            has_full_text = True
                            if fmt_upper not in download_formats:
                                download_formats.append(fmt_upper)
                elif isinstance(formats, str):
                    fmt_upper = formats.upper()
                    if any(x in fmt_upper for x in ["PDF", "EPUB", "MOBI", "TXT", "HTML", "DJVU"]):
                        has_full_text = True
                        download_formats.append(fmt_upper)
            
            # Only return items with full text access
            if not has_full_text:
                return None
            
            # Extract download count and rating as popularity indicators
            downloads = raw_item.get("downloads", 0)
            avg_rating = raw_item.get("avg_rating", 0)
            num_reviews = raw_item.get("num_reviews", 0)
            
            # Calculate a popularity score
            popularity_score = int(downloads) if downloads else 0
            if avg_rating and num_reviews:
                popularity_score += int(float(avg_rating) * int(num_reviews))
            
            return Paper(
                title=title,
                authors=authors if authors else ["Unknown"],
                abstract=abstract,
                year=year if year else "Unknown",
                source="Internet Archive",
                full_text_url=full_text_url,
                doi=None,  # Internet Archive doesn't use DOIs
                journal=None,  # Books don't have journals
                citation_count=popularity_score if popularity_score > 0 else None,
                influential_citation_count=None,
                content_type="book",
                isbn=None,  # ISBN not consistently available
                publisher=publisher if publisher else "Internet Archive",
                page_count=None,  # Not consistently available
                language=language,
                subjects=subjects if subjects else None,
                download_formats=download_formats if download_formats else None
            )
            
        except Exception as e:
            logger.error(f"Error normalizing Internet Archive item: {e}")
            return None