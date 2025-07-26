from typing import List, Dict, Any, Optional
import httpx
from app.api_clients.base import BaseAPIClient
from app.models import Paper
import logging
import asyncio
import time
import re
from urllib.parse import quote
import xml.etree.ElementTree as ET

logger = logging.getLogger(__name__)

class BioMedCentralClient(BaseAPIClient):
    """BioMed Central API client for open access biomedical research"""
    
    def __init__(self):
        super().__init__(base_url="https://www.biomedcentral.com")
        self.last_request_time = 0
        self.min_request_interval = 0.5
        self.api_key = None  # Will be set by search service if provided
        
        self.client.headers.update({
            "User-Agent": "Mozilla/5.0 (compatible; OpenScholar/1.0)",
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
        """Search BioMed Central for open access articles"""
        
        logger.info(f"BMC search called with query: {query}, api_key: {getattr(self, 'api_key', 'None')}")
        
        await self._wait_for_rate_limit()
        
        try:
            # BMC uses the Springer Nature API
            search_url = "https://api.springernature.com/openaccess/json"
            
            # Build query using keyword search format
            search_query = f"keyword:{query}"
            
            # Add year filters if specified
            if year_start and year_end:
                search_query += f" onlinedatefrom:{year_start}-01-01 onlinedateto:{year_end}-12-31"
            
            params = {
                "q": search_query,
                "s": 1,  # Start position
                "p": min(limit, 20)  # Page size
            }
            
            # Check if we have a valid API key
            if not hasattr(self, 'api_key') or not self.api_key or self.api_key == "00000000000000000000000000000000":
                logger.info(f"BMC search skipped - requires valid Springer Nature API key (current: {getattr(self, 'api_key', 'None')})")
                return []
                
            # Update the params with real API key
            params["api_key"] = self.api_key
            logger.info(f"BMC search using API key: {self.api_key[:8]}...{self.api_key[-4:]}")
                
            response = await self.client.get(search_url, params=params)
            
            # Log response status and headers for debugging
            logger.info(f"BMC API response status: {response.status_code}")
            if response.status_code == 403:
                logger.error(f"BMC API 403 response: {response.text[:500]}")
            
            response.raise_for_status()
            
            data = response.json()
            records = data.get("records", [])
            
            if not records:
                logger.info(f"Springer Nature API found no results for query: {query}")
                return []
            
            # Convert records to papers
            papers = []
            
            for record in records:
                # Only include open access articles
                if record.get("openAccess") == "true":
                    paper = await self._article_to_paper(record, discipline)
                    if paper:
                        papers.append(paper)
                        if len(papers) >= limit:
                            break
            
            logger.info(f"Springer Nature returned {len(papers)} open access articles for query: {query}")
            return papers
            
        except Exception as e:
            logger.error(f"Error searching BioMed Central: {e}")
            return []
    
    async def _article_to_paper(self, article: Dict[str, Any], discipline: Optional[str] = None) -> Optional[Paper]:
        """Convert BMC article to Paper object"""
        try:
            # Get title
            title = article.get("title", "")
            if not title:
                return None
            
            # Get authors
            creators = article.get("creators", [])
            authors = []
            for creator in creators:
                if isinstance(creator, dict):
                    name = creator.get("creator", "")
                    if name:
                        authors.append(name)
                elif isinstance(creator, str):
                    authors.append(creator)
            
            if not authors:
                authors = ["BioMed Central Authors"]
            
            # Get DOI
            doi = article.get("doi", "")
            
            # Get abstract
            abstract = article.get("abstract", "")
            
            # Handle abstract that might be a dict
            if isinstance(abstract, dict):
                # Extract text from dict structure
                abstract_text = abstract.get("p", "")
                if isinstance(abstract_text, list):
                    abstract = " ".join(abstract_text)
                else:
                    abstract = str(abstract_text)
            elif not abstract:
                abstract = "Open access biomedical research article from BioMed Central"
            else:
                abstract = str(abstract)
            
            # Clean abstract
            abstract = re.sub(r'<[^>]+>', '', abstract)
            abstract = re.sub(r'\s+', ' ', abstract).strip()
            
            # Get year
            pub_date = article.get("publicationDate", "") or article.get("onlineDate", "")
            year = ""
            if pub_date:
                year_match = re.search(r'(\d{4})', pub_date)
                if year_match:
                    year = year_match.group(1)
                else:
                    year = "Unknown"
            else:
                year = "Unknown"
            
            # Get journal
            journal = article.get("publicationName", "")
            
            # Get subjects
            subjects = []
            
            # Add subjects from various fields
            subject_fields = ["subjects", "keyword", "disciplines"]
            for field in subject_fields:
                field_data = article.get(field, [])
                if isinstance(field_data, list):
                    for item in field_data:
                        if isinstance(item, str):
                            subjects.append(item)
                        elif isinstance(item, dict) and 'term' in item:
                            subjects.append(item['term'])
                elif isinstance(field_data, str):
                    subjects.append(field_data)
            
            # Default subjects for BMC
            if not subjects:
                subjects = ["Biomedical Research", "Life Sciences"]
            
            # Filter by discipline if specified
            if discipline and discipline.lower() not in ["biology", "medicine", "life sciences", "biomedical"]:
                # Skip if not biomedical discipline
                return None
            
            # Build URL
            if doi:
                full_text_url = f"https://doi.org/{doi}"
            else:
                # Try to use URL field
                urls = article.get("url", [])
                if isinstance(urls, list) and urls:
                    url_obj = urls[0] if isinstance(urls[0], dict) else {"value": urls[0]}
                    full_text_url = url_obj.get("value", "")
                else:
                    full_text_url = f"https://www.biomedcentral.com/search?query={quote(title)}"
            
            # Publisher info
            publisher = article.get("publisher", "BioMed Central")
            
            # Article type
            content_type = article.get("contentType", "Article")
            
            return Paper(
                title=title,
                authors=authors[:10],  # Limit authors
                abstract=abstract[:1500],  # Limit abstract
                year=year,
                source="BioMed Central",
                full_text_url=full_text_url,
                doi=doi,
                journal=journal,
                citation_count=None,
                influential_citation_count=None,
                content_type="paper",
                isbn=None,
                publisher=publisher,
                page_count=None,
                language=article.get("language", "en"),
                subjects=subjects[:5] if subjects else None,
                download_formats=["PDF", "HTML", "ePub"]
            )
            
        except Exception as e:
            logger.error(f"Error converting BioMed Central article to paper: {e}")
            return None
    
    async def normalize_paper(self, raw_item: Dict[str, Any], year_start: int, year_end: int) -> Optional[Paper]:
        """Compatibility method"""
        return await self._article_to_paper(raw_item)