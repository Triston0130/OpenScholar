"""
Open Textbook Library API Client

Uses the JSON API endpoint which doesn't require authentication.
"""

import logging
from typing import List, Dict, Any, Optional
import httpx
from app.models import Paper
import re

logger = logging.getLogger(__name__)

class OpenTextbookLibraryClient:
    """Client for searching Open Textbook Library using their JSON API"""
    
    def __init__(self):
        self.base_url = "https://open.umn.edu/opentextbooks"
        self.timeout = httpx.Timeout(30.0)
        
    async def search(self, query: str, max_results: int = 50) -> List[Paper]:
        """
        Search for open textbooks using the JSON API
        
        Args:
            query: Search query string
            max_results: Maximum number of results to return
            
        Returns:
            List of Paper objects representing textbooks
        """
        papers = []
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # Get all textbooks via JSON API
                url = f"{self.base_url}/textbooks.json"
                
                logger.info(f"Fetching Open Textbook Library catalog from {url}")
                
                response = await client.get(url)
                
                if response.status_code == 200:
                    data = response.json()
                    textbooks = data.get('data', [])
                    
                    # Search through textbooks
                    query_lower = query.lower()
                    matches = []
                    
                    for book in textbooks:
                        # Check if query matches title, description, or subjects
                        title = book.get('title', '').lower()
                        description = book.get('description', '').lower()
                        subjects = [s.get('name', '').lower() for s in book.get('subjects', [])]
                        
                        if (query_lower in title or 
                            query_lower in description or 
                            any(query_lower in subj for subj in subjects)):
                            matches.append(book)
                    
                    # Convert matches to Paper objects
                    for book in matches[:max_results]:
                        try:
                            # Extract authors from contributors
                            authors = []
                            for contributor in book.get('contributors', []):
                                if contributor.get('contribution') in ['Author', 'Editor']:
                                    authors.append(contributor.get('name', 'Unknown'))
                            
                            if not authors:
                                authors = ['Open Textbook Library']
                            
                            # Extract subjects
                            subjects_list = [s.get('name', '') for s in book.get('subjects', [])]
                            
                            # Get publication year
                            year = str(book.get('copyright_year', '2024'))
                            
                            # Build URL
                            book_id = book.get('id', '')
                            book_url = f"{self.base_url}/textbooks/{book_id}"
                            
                            # Get license
                            license_type = book.get('license', 'CC BY')
                            
                            paper = Paper(
                                title=book.get('title', 'Untitled'),
                                authors=authors,
                                abstract=book.get('description', 'No description available'),
                                year=year,
                                source="Open Textbook Library",
                                full_text_url=book_url,
                                journal="Open Textbook Library",
                                content_type='book',
                                subjects=subjects_list,
                                download_formats=['PDF', 'EPUB', 'HTML'],
                                license=license_type
                            )
                            papers.append(paper)
                            
                        except Exception as e:
                            logger.error(f"Error converting textbook to Paper: {str(e)}")
                            continue
                    
                    logger.info(f"Found {len(papers)} matching textbooks in Open Textbook Library")
                    
                else:
                    logger.error(f"Open Textbook Library API returned status: {response.status_code}")
                    
        except Exception as e:
            logger.error(f"Error searching Open Textbook Library: {str(e)}")
            
        return papers