"""
MERLOT Web Scraper Client

Since MERLOT API requires authentication, this client scrapes their public
website to find open educational resources.
"""

import logging
from typing import List, Dict, Any, Optional
import httpx
from app.models import Paper
from bs4 import BeautifulSoup
from urllib.parse import urljoin, quote
import re

logger = logging.getLogger(__name__)

class MERLOTClient:
    """Client for searching MERLOT via web scraping or API when key is available"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.base_url = "https://www.merlot.org"
        self.timeout = httpx.Timeout(30.0)
        self.api_key = api_key
        
    async def search(self, query: str, max_results: int = 50) -> List[Paper]:
        """
        Search for open educational resources using MERLOT API or web scraping
        
        Args:
            query: Search query string
            max_results: Maximum number of results to return
            
        Returns:
            List of Paper objects representing OER materials
        """
        # Check if we have a valid API key
        if not self.api_key or self.api_key == "00000000000000000000000000000000":
            logger.info(f"MERLOT search skipped - requires valid API key (current: {self.api_key[:8] if self.api_key else 'None'}...)")
            return []
            
        papers = []
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # Use the search materials endpoint
                search_url = f"{self.base_url}/merlot/searchMaterials.htm"
                
                # Search parameters
                params = {
                    'keywords': query,
                    'materialType': 'Open Textbook',  # Focus on textbooks
                    'hasCreativeCommons': 'true',     # Only CC licensed
                    'sort.property': 'relevance'
                }
                
                logger.info(f"Searching MERLOT for: {query}")
                
                headers = {
                    'User-Agent': 'Mozilla/5.0 (compatible; OpenScholar/1.0)',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
                }
                
                response = await client.get(search_url, params=params, headers=headers, follow_redirects=True)
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # Find search results
                    results_section = soup.find('div', id='searchResults')
                    if results_section:
                        # Find individual result items
                        result_items = results_section.find_all('div', class_='resultItem')
                        
                        for item in result_items[:max_results]:
                            try:
                                # Extract title
                                title_elem = item.find('a', class_='itemTitle')
                                if not title_elem:
                                    continue
                                
                                title = title_elem.get_text(strip=True)
                                material_url = urljoin(self.base_url, title_elem.get('href', ''))
                                
                                # Extract authors
                                author_elem = item.find('span', class_='author')
                                authors = []
                                if author_elem:
                                    author_text = author_elem.get_text(strip=True)
                                    # Clean up author text
                                    author_text = re.sub(r'^(Author:|By:)\s*', '', author_text, flags=re.IGNORECASE)
                                    authors = [a.strip() for a in author_text.split(',') if a.strip()]
                                
                                if not authors:
                                    authors = ['MERLOT Contributor']
                                
                                # Extract description
                                desc_elem = item.find('div', class_='description')
                                if not desc_elem:
                                    desc_elem = item.find('span', class_='description')
                                
                                abstract = ""
                                if desc_elem:
                                    abstract = desc_elem.get_text(strip=True)
                                
                                # Extract additional metadata
                                metadata_elem = item.find('div', class_='metadata')
                                subjects = []
                                
                                if metadata_elem:
                                    # Look for subject/category info
                                    category_elems = metadata_elem.find_all('a', href=re.compile(r'category'))
                                    for cat in category_elems:
                                        subjects.append(cat.get_text(strip=True))
                                
                                # Create paper object
                                paper = Paper(
                                    title=title,
                                    authors=authors,
                                    abstract=abstract[:500] if abstract else f"Open educational resource from MERLOT: {title}",
                                    year='2024',  # MERLOT materials are continuously updated
                                    source="MERLOT",
                                    full_text_url=material_url,
                                    journal="MERLOT",
                                    content_type='book',
                                    subjects=subjects[:5] if subjects else ['Open Educational Resources'],
                                    download_formats=['PDF', 'HTML']
                                )
                                papers.append(paper)
                                
                            except Exception as e:
                                logger.error(f"Error parsing MERLOT result item: {str(e)}")
                                continue
                    
                    # If no results found in expected structure, try fallback
                    if not papers:
                        # Look for alternative result structure
                        links = soup.find_all('a', href=re.compile(r'/merlot/viewMaterial\.htm'))
                        
                        for link in links[:max_results]:
                            try:
                                title = link.get_text(strip=True)
                                if title and len(title) > 5:  # Filter out empty or too short titles
                                    material_url = urljoin(self.base_url, link.get('href', ''))
                                    
                                    paper = Paper(
                                        title=title,
                                        authors=['MERLOT Contributor'],
                                        abstract=f"Open educational resource from MERLOT: {title}",
                                        year='2024',
                                        source="MERLOT",
                                        full_text_url=material_url,
                                        journal="MERLOT",
                                        content_type='book',
                                        subjects=['Open Educational Resources'],
                                        download_formats=['PDF', 'HTML']
                                    )
                                    papers.append(paper)
                            except Exception:
                                continue
                    
                    logger.info(f"Found {len(papers)} materials on MERLOT")
                    
                else:
                    logger.error(f"MERLOT returned status: {response.status_code}")
                    
        except Exception as e:
            logger.error(f"Error searching MERLOT: {str(e)}")
            
        return papers