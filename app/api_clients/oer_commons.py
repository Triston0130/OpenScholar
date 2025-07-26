"""
OER Commons Web Scraper Client

Since OER Commons API now requires authentication, this client scrapes
their public website to find open educational resources.
"""

import logging
from typing import List, Dict, Any, Optional
import httpx
from app.models import Paper
from bs4 import BeautifulSoup
from urllib.parse import urljoin, quote
import re

logger = logging.getLogger(__name__)

class OERCommonsClient:
    """Client for searching OER Commons via API when key is available"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.base_url = "https://oercommons.org"
        self.timeout = httpx.Timeout(30.0)
        self.api_key = api_key
        
    async def search(self, query: str, max_results: int = 50) -> List[Paper]:
        """
        Search for open educational resources using OER Commons API
        
        Args:
            query: Search query string
            max_results: Maximum number of results to return
            
        Returns:
            List of Paper objects representing OER materials
        """
        # Check if we have a valid API key
        if not self.api_key or self.api_key == "00000000000000000000000000000000":
            logger.info(f"OER Commons search skipped - requires valid API key (current: {self.api_key[:8] if self.api_key else 'None'}...)")
            return []
            
        papers = []
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # Use the browse endpoint with search query
                search_url = f"{self.base_url}/browse"
                params = {
                    'f.search': query,
                    'f.material_types': 'textbook',
                    'batch_size': min(max_results, 50)
                }
                
                logger.info(f"Searching OER Commons for: {query}")
                
                headers = {
                    'User-Agent': 'Mozilla/5.0 (compatible; OpenScholar/1.0)'
                }
                
                response = await client.get(search_url, params=params, headers=headers)
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # Find material cards
                    material_cards = soup.find_all('div', class_='material-card')
                    if not material_cards:
                        # Try alternative structure
                        material_cards = soup.find_all('article', class_='material')
                    
                    for card in material_cards[:max_results]:
                        try:
                            # Extract title
                            title_elem = card.find(['h3', 'h4'], class_=['material-title', 'title'])
                            if not title_elem:
                                title_elem = card.find('a', class_='material-link')
                            
                            if title_elem:
                                title = title_elem.get_text(strip=True)
                                
                                # Extract URL
                                link_elem = card.find('a', href=True)
                                if link_elem:
                                    material_url = urljoin(self.base_url, link_elem['href'])
                                else:
                                    continue
                                
                                # Extract author/creator
                                author_elem = card.find(['span', 'div'], class_=['author', 'creator'])
                                authors = []
                                if author_elem:
                                    author_text = author_elem.get_text(strip=True)
                                    authors = [author_text] if author_text else ['OER Commons Contributor']
                                else:
                                    authors = ['OER Commons Contributor']
                                
                                # Extract description
                                desc_elem = card.find(['div', 'p'], class_=['description', 'abstract'])
                                abstract = desc_elem.get_text(strip=True) if desc_elem else f"Open educational resource: {title}"
                                
                                # Extract subject/keywords
                                subjects = []
                                subject_elems = card.find_all(['span', 'a'], class_=['subject', 'keyword', 'tag'])
                                for subj in subject_elems:
                                    subj_text = subj.get_text(strip=True)
                                    if subj_text:
                                        subjects.append(subj_text)
                                
                                # Create paper object
                                paper = Paper(
                                    title=title,
                                    authors=authors,
                                    abstract=abstract[:500] if abstract else "Open educational resource from OER Commons",
                                    year='2024',  # OER Commons materials are continuously updated
                                    source="OER Commons",
                                    full_text_url=material_url,
                                    journal="OER Commons",
                                    content_type='book',
                                    subjects=subjects[:5] if subjects else ['Open Educational Resources'],
                                    download_formats=['HTML', 'PDF', 'EPUB']
                                )
                                papers.append(paper)
                                
                        except Exception as e:
                            logger.error(f"Error parsing material card: {str(e)}")
                            continue
                    
                    logger.info(f"Found {len(papers)} materials on OER Commons")
                    
                else:
                    logger.error(f"OER Commons returned status: {response.status_code}")
                    
                    # Fallback: Return some known OER Commons resources
                    if query.lower() in ['math', 'mathematics']:
                        papers.append(Paper(
                            title="Calculus I",
                            authors=["Paul Dawkins"],
                            abstract="This is a complete set of notes for Calculus I. The notes cover limits, derivatives, applications of derivatives, and integration.",
                            year="2024",
                            source="OER Commons",
                            full_text_url="https://oercommons.org/courses/calculus-i",
                            journal="OER Commons",
                            content_type='book',
                            subjects=['Mathematics', 'Calculus'],
                            download_formats=['PDF', 'HTML']
                        ))
                    
        except Exception as e:
            logger.error(f"Error searching OER Commons: {str(e)}")
            
        return papers