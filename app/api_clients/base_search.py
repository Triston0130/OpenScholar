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

class BASEClient(BaseAPIClient):
    """BASE (Bielefeld Academic Search Engine) client for scholarly papers - free, no auth needed"""
    
    def __init__(self):
        super().__init__(base_url="https://api.base-search.net/cgi-bin/BaseHttpSearchInterface.fcgi")
        self.last_request_time = 0
        self.min_request_interval = 0.5  # Be respectful to BASE
        
        self.client.headers.update({
            "User-Agent": "OpenScholar Research Tool/1.0 (mailto:research@openscholar.app)",
            "Accept": "application/xml"
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
        """Search BASE for scholarly papers - requires IP whitelisting but free"""
        
        await self._wait_for_rate_limit()
        
        try:
            # BASE API parameters
            params = {
                "func": "PerformSearch",
                "query": query,
                "format": "xml",
                "hits": min(limit, 125),  # BASE max is 125
                "type": "all"
            }
            
            # Add year filter if specified
            if year_start or year_end:
                date_filter = ""
                if year_start and year_end:
                    date_filter = f"dcyear:[{year_start} TO {year_end}]"
                elif year_start:
                    date_filter = f"dcyear:[{year_start} TO *]"
                elif year_end:
                    date_filter = f"dcyear:[* TO {year_end}]"
                
                if date_filter:
                    params["query"] += f" AND {date_filter}"
            
            # Add discipline filter if specified
            if discipline:
                params["query"] += f" AND dcsubject:{discipline}"
            
            logger.info(f"Searching BASE for: {query}")
            
            # Note: BASE requires IP whitelisting, so this will likely fail without registration
            response = await self.client.get(self.base_url, params=params, timeout=15.0)
            response.raise_for_status()
            
            # Parse XML response
            papers = await self._parse_xml_response(response.content, limit)
            
            # Check for access denied error
            response_text = response.content.decode('utf-8', errors='ignore')
            if '<error>Access denied' in response_text:
                logger.error(f"BASE API access denied - IP whitelisting required. Visit https://www.base-search.net/about/download/base_interface.pdf for registration info")
                return []
            
            logger.info(f"BASE returned {len(papers)} papers for query: {query}")
            return papers
            
        except Exception as e:
            logger.error(f"Error searching BASE (may need IP whitelisting): {e}")
            return []
    
    async def _parse_xml_response(self, xml_content: bytes, limit: int) -> List[Paper]:
        """Parse BASE XML response"""
        papers = []
        
        try:
            root = ET.fromstring(xml_content)
            
            # BASE returns results in specific XML format
            for record in root.findall(".//record"):
                paper = await self._record_to_paper(record)
                if paper:
                    papers.append(paper)
                    if len(papers) >= limit:
                        break
            
            return papers
            
        except Exception as e:
            logger.error(f"Error parsing BASE XML response: {e}")
            return []
    
    async def _record_to_paper(self, record: ET.Element) -> Optional[Paper]:
        """Convert BASE record to Paper object"""
        try:
            # Extract title
            title_elem = record.find(".//dctitle")
            title = title_elem.text if title_elem is not None else ""
            if not title:
                return None
            
            # Extract authors
            authors = []
            for author_elem in record.findall(".//dccreator"):
                if author_elem.text:
                    authors.append(author_elem.text)
            
            if not authors:
                authors = ["Unknown"]
            
            # Extract description/abstract
            desc_elem = record.find(".//dcdescription")
            abstract = desc_elem.text if desc_elem is not None else ""
            if not abstract:
                abstract = "Academic paper from BASE search engine"
            
            # Extract year
            year_elem = record.find(".//dcyear")
            year = year_elem.text if year_elem is not None and year_elem.text else "Unknown"
            
            # Extract URL
            url_elem = record.find(".//dclink")
            full_text_url = url_elem.text if url_elem is not None else ""
            
            # Extract DOI
            doi_elem = record.find(".//dcidentifier")
            doi = ""
            if doi_elem is not None and doi_elem.text and "doi" in doi_elem.text.lower():
                doi = doi_elem.text
            
            # Extract subjects
            subjects = []
            for subject_elem in record.findall(".//dcsubject"):
                if subject_elem.text:
                    subjects.append(subject_elem.text)
            
            # Extract publisher
            publisher_elem = record.find(".//dcpublisher")
            publisher = publisher_elem.text if publisher_elem is not None else ""
            
            # Extract language
            lang_elem = record.find(".//dclanguage")
            language = lang_elem.text if lang_elem is not None else "en"
            
            return Paper(
                title=title,
                authors=authors[:10],
                abstract=abstract[:1500],
                year=year,
                source="BASE",
                full_text_url=full_text_url,
                doi=doi,
                journal=None,
                citation_count=None,
                influential_citation_count=None,
                content_type="paper",
                isbn=None,
                publisher=publisher,
                page_count=None,
                language=language,
                subjects=subjects[:5] if subjects else None,
                download_formats=["PDF", "Online"]
            )
            
        except Exception as e:
            logger.error(f"Error converting BASE record to paper: {e}")
            return None
    
    async def normalize_paper(self, raw_item: Dict[str, Any], year_start: int = 0, year_end: int = 0) -> Optional[Paper]:
        """Compatibility method"""
        # BASE works with XML, not dict, so this is mainly for interface compatibility
        return None