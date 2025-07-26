from typing import List, Dict, Any, Optional
import httpx
from app.api_clients.base import BaseAPIClient
from app.models import Paper
import logging
import asyncio
import time
import re
from urllib.parse import quote_plus
import xml.etree.ElementTree as ET

logger = logging.getLogger(__name__)

class OAPENClient(BaseAPIClient):
    """OAPEN (Open Access Publishing in European Networks) API client for academic books"""
    
    def __init__(self):
        super().__init__(base_url="https://library.oapen.org")
        self.last_request_time = 0
        self.min_request_interval = 0.5
        
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
        """Search OAPEN books using OAI-PMH protocol"""
        
        await self._wait_for_rate_limit()
        
        try:
            # Use OAPEN's OAI-PMH endpoint which is more reliable
            oai_url = f"{self.base_url}/oai/request"
            
            # Build OAI-PMH parameters
            params = {
                "verb": "ListRecords",
                "metadataPrefix": "oai_dc"
            }
            
            # Add date filter
            if year_start:
                params["from"] = f"{year_start}-01-01"
            if year_end:
                params["until"] = f"{year_end}-12-31"
            
            logger.info(f"Searching OAPEN OAI-PMH for: {query}")
            
            # Update headers for XML response
            headers = {
                "User-Agent": "OpenScholar Research Tool/1.0 (mailto:research@openscholar.app)",
                "Accept": "application/xml, text/xml"
            }
            
            response = await self.client.get(oai_url, params=params, headers=headers, timeout=30.0)
            response.raise_for_status()
            
            # Parse XML response
            root = ET.fromstring(response.content)
            
            # Debug: Log response structure
            logger.info(f"OAPEN OAI-PMH response root tag: {root.tag}")
            
            # Define namespaces
            ns = {
                'oai': 'http://www.openarchives.org/OAI/2.0/',
                'dc': 'http://purl.org/dc/elements/1.1/',
                'oai_dc': 'http://www.openarchives.org/OAI/2.0/oai_dc/'
            }
            
            books = []
            records = root.findall('.//oai:record', ns)
            logger.info(f"OAPEN found {len(records)} records total")
            
            for record in records:
                # Check if record matches query
                metadata = record.find('.//oai_dc:dc', ns)
                if metadata is None:
                    continue
                
                # Extract all text content for query matching - be more lenient
                all_text = " ".join([elem.text or "" for elem in metadata])
                # Split query into words and check if ANY word matches (not exact phrase)
                query_words = query.lower().split()
                text_lower = all_text.lower()
                if not any(word in text_lower for word in query_words):
                    continue
                
                paper = await self._parse_oai_record(record, ns, discipline)
                if paper:
                    books.append(paper)
                    if len(books) >= limit:
                        break
            
            logger.info(f"OAPEN returned {len(books)} books for query: {query}")
            return books
            
        except Exception as e:
            logger.error(f"Error searching OAPEN OAI-PMH: {e}")
            return []
    
    async def _parse_oai_record(self, record: ET.Element, ns: Dict[str, str], 
                               discipline: Optional[str]) -> Optional[Paper]:
        """Parse OAI-PMH record to Paper object"""
        try:
            metadata = record.find('.//oai_dc:dc', ns)
            if metadata is None:
                return None
            
            # Helper to get DC field
            def get_dc_field(field: str, multiple: bool = False):
                elements = metadata.findall(f'.//dc:{field}', ns)
                if multiple:
                    return [elem.text for elem in elements if elem.text]
                return elements[0].text if elements and elements[0].text else ""
            
            # Get title
            title = get_dc_field("title")
            if not title:
                return None
            
            # Get authors/creators
            authors = get_dc_field("creator", multiple=True)
            if not authors:
                authors = ["OAPEN Authors"]
            
            # Get abstract/description
            descriptions = get_dc_field("description", multiple=True)
            abstract = descriptions[0] if descriptions else "Open access academic book from OAPEN"
            
            # Get year from date
            dates = get_dc_field("date", multiple=True)
            year = ""
            for date in dates:
                year_match = re.search(r'(\d{4})', date)
                if year_match:
                    year = year_match.group(1)
                    break
            
            # Get subjects
            subjects = get_dc_field("subject", multiple=True)
            
            # Get identifier (URL)
            identifiers = get_dc_field("identifier", multiple=True)
            full_text_url = None
            
            for identifier in identifiers:
                if identifier.startswith("http") and "oapen.org" in identifier:
                    full_text_url = identifier
                    break
            
            if not full_text_url:
                return None
            
            # Get publisher
            publishers = get_dc_field("publisher", multiple=True)
            publisher = publishers[0] if publishers else "OAPEN"
            
            # Get language
            languages = get_dc_field("language", multiple=True)
            language = languages[0] if languages else "en"
            
            # Filter by discipline if specified
            if discipline and subjects:
                discipline_match = any(discipline.lower() in subj.lower() for subj in subjects)
                if not discipline_match:
                    return None
            
            return Paper(
                title=title,
                authors=authors[:5],
                abstract=abstract[:1000],
                year=year,
                source="OAPEN",
                full_text_url=full_text_url,
                doi=None,
                journal=None,
                citation_count=None,
                influential_citation_count=None,
                content_type="book",
                isbn=None,
                publisher=publisher,
                page_count=None,
                language=language,
                subjects=subjects[:5] if subjects else ["Academic"],
                download_formats=["PDF", "EPUB"]
            )
            
        except Exception as e:
            logger.error(f"Error parsing OAPEN OAI record: {e}")
            return None
    
    async def _book_to_paper(self, book: Dict[str, Any], year_start: int, year_end: int) -> Optional[Paper]:
        """Convert OAPEN book to Paper object"""
        try:
            # Extract metadata
            metadata = book.get("metadata", {})
            
            # Get title
            title = metadata.get("title", [""])[0] if isinstance(metadata.get("title"), list) else metadata.get("title", "")
            if not title:
                return None
            
            # Get authors/contributors
            authors = []
            contributors = metadata.get("contributor", [])
            if isinstance(contributors, list):
                authors = [c for c in contributors if c]
            elif contributors:
                authors = [contributors]
            
            if not authors:
                authors = ["Unknown"]
            
            # Get abstract/description
            descriptions = metadata.get("description", [])
            if isinstance(descriptions, list) and descriptions:
                abstract = descriptions[0]
            else:
                abstract = descriptions if descriptions else "Open access academic book from OAPEN"
            
            # Get year
            dates = metadata.get("date", [])
            year = None
            if isinstance(dates, list) and dates:
                year_match = re.search(r'(\d{4})', str(dates[0]))
                if year_match:
                    year = int(year_match.group(1))
            
            # Apply year filter
            if year:
                if year_start and year < year_start:
                    return None
                if year_end and year > year_end:
                    return None
            
            # Get subjects
            subjects = metadata.get("subject", [])
            if not isinstance(subjects, list):
                subjects = [subjects] if subjects else []
            
            # Get publisher
            publishers = metadata.get("publisher", [])
            publisher = publishers[0] if isinstance(publishers, list) and publishers else "OAPEN"
            
            # Get identifiers
            identifiers = metadata.get("identifier", [])
            isbn = None
            full_text_url = None
            
            for identifier in identifiers if isinstance(identifiers, list) else [identifiers]:
                if isinstance(identifier, dict):
                    id_type = identifier.get("type", "")
                    id_value = identifier.get("value", "")
                    if id_type == "isbn":
                        isbn = id_value
                    elif id_type == "uri" and "oapen.org" in id_value:
                        full_text_url = id_value
                elif isinstance(identifier, str):
                    if identifier.startswith("http"):
                        full_text_url = identifier
                    elif re.match(r'^\d{13}$', identifier):
                        isbn = identifier
            
            # Get handle for URL if not found
            handle = book.get("handle")
            if not full_text_url and handle:
                full_text_url = f"https://library.oapen.org/handle/{handle}"
            
            # Get languages
            languages = metadata.get("language", [])
            language = languages[0] if isinstance(languages, list) and languages else "en"
            
            return Paper(
                title=title,
                authors=authors[:5],  # Limit authors
                abstract=abstract[:1000] if abstract else "",  # Limit abstract length
                year=str(year) if year else "Unknown",
                source="OAPEN",
                full_text_url=full_text_url,
                doi=None,
                journal=None,
                citation_count=None,
                influential_citation_count=None,
                content_type="book",
                isbn=isbn,
                publisher=publisher,
                page_count=None,
                language=language,
                subjects=subjects[:5] if subjects else None,  # Limit subjects
                download_formats=["PDF", "EPUB"]
            )
            
        except Exception as e:
            logger.error(f"Error converting OAPEN book to paper: {e}")
            return None
    
    async def normalize_paper(self, raw_item: Dict[str, Any], year_start: int, year_end: int) -> Optional[Paper]:
        """Compatibility method"""
        return await self._book_to_paper(raw_item, year_start, year_end)