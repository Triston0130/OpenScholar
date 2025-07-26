"""
Pressbooks Network API Client

Supports multiple Pressbooks-based networks:
- BCcampus Open Textbooks
- SUNY Open Textbooks
- Rebus Community
- eCampusOntario
- And others

All books are WordPress sites with REST API v2 enabled.
"""

import logging
from typing import List, Dict, Any, Optional
import httpx
from app.models import Paper
import asyncio

logger = logging.getLogger(__name__)

class PressbooksClient:
    """Client for fetching open textbooks from Pressbooks networks"""
    
    # Known Pressbooks networks with their catalog endpoints
    NETWORKS = {
        'BCcampus': {
            'base_url': 'https://open.bccampus.ca',
            'catalog_api': 'https://open.bccampus.ca/wp-json/pressbooks/v2/books',
            'name': 'BCcampus Open Textbooks'
        },
        'SUNY': {
            'base_url': 'https://textbooks.opensuny.org',
            'catalog_api': 'https://textbooks.opensuny.org/wp-json/pressbooks/v2/books',
            'name': 'SUNY Open Textbooks'
        },
        'Rebus': {
            'base_url': 'https://press.rebus.community',
            'catalog_api': 'https://press.rebus.community/wp-json/pressbooks/v2/books',
            'name': 'Rebus Community'
        },
        'eCampusOntario': {
            'base_url': 'https://ecampusontario.pressbooks.pub',
            'catalog_api': 'https://ecampusontario.pressbooks.pub/wp-json/pressbooks/v2/books',
            'name': 'eCampusOntario'
        }
    }
    
    def __init__(self):
        self.timeout = httpx.Timeout(30.0)
        
    async def search(self, query: str, max_results: int = 50) -> List[Paper]:
        """
        Search for open textbooks across all Pressbooks networks
        
        Args:
            query: Search query string
            max_results: Maximum number of results to return
            
        Returns:
            List of Paper objects representing open textbooks
        """
        all_papers = []
        results_per_network = max(10, max_results // len(self.NETWORKS))
        
        # Search all networks concurrently
        tasks = []
        for network_key, network_info in self.NETWORKS.items():
            task = self._search_network(
                network_key, 
                network_info, 
                query, 
                results_per_network
            )
            tasks.append(task)
        
        network_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Combine results from all networks
        for result in network_results:
            if isinstance(result, list):
                all_papers.extend(result)
            elif isinstance(result, Exception):
                logger.error(f"Error searching network: {result}")
        
        # Limit to max_results
        return all_papers[:max_results]
    
    async def _search_network(
        self, 
        network_key: str, 
        network_info: Dict[str, str], 
        query: str, 
        max_results: int
    ) -> List[Paper]:
        """Search a specific Pressbooks network"""
        papers = []
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # First, try to get the catalog
                catalog_url = network_info['catalog_api']
                logger.info(f"Searching {network_info['name']} catalog: {catalog_url}")
                
                # Add search parameter if the API supports it
                params = {
                    'per_page': 100,  # Get more books to search through
                    'search': query  # Some networks support search parameter
                }
                
                response = await client.get(catalog_url, params=params)
                
                if response.status_code == 200:
                    books = response.json()
                    
                    # If no search parameter support, filter manually
                    query_lower = query.lower()
                    for book in books:
                        if self._matches_query(book, query_lower):
                            paper = await self._convert_book_to_paper(
                                book, 
                                network_info['name'],
                                client
                            )
                            if paper:
                                papers.append(paper)
                                if len(papers) >= max_results:
                                    break
                else:
                    logger.warning(f"Failed to fetch catalog from {network_info['name']}: {response.status_code}")
                    
        except Exception as e:
            logger.error(f"Error searching {network_info['name']}: {str(e)}")
            
        return papers
    
    def _matches_query(self, book: Dict[str, Any], query_lower: str) -> bool:
        """Check if a book matches the search query"""
        # Check various fields
        title = book.get('title', {}).get('rendered', '').lower()
        author = book.get('author', '').lower()
        subject = book.get('subject', '').lower()
        
        return (query_lower in title or 
                query_lower in author or 
                query_lower in subject)
    
    async def _convert_book_to_paper(
        self, 
        book: Dict[str, Any], 
        network_name: str,
        client: httpx.AsyncClient
    ) -> Optional[Paper]:
        """Convert a Pressbooks book to a Paper object"""
        try:
            # Extract basic metadata
            title = book.get('title', {}).get('rendered', '').strip()
            if not title:
                return None
            
            # Get book URL and derive PDF URL
            book_url = book.get('link', '')
            if not book_url:
                return None
            
            # Pressbooks PDF export URL pattern
            pdf_url = f"{book_url}/open/download?type=pdf"
            
            # Try to get more metadata from the book's API
            book_api_url = f"{book_url}/wp-json/pressbooks/v2/metadata"
            try:
                metadata_response = await client.get(book_api_url)
                if metadata_response.status_code == 200:
                    metadata = metadata_response.json()
                else:
                    metadata = {}
            except:
                metadata = {}
            
            # Extract authors
            authors = []
            if 'author' in metadata:
                if isinstance(metadata['author'], list):
                    authors = [a.get('name', '') for a in metadata['author'] if a.get('name')]
                elif isinstance(metadata['author'], str):
                    authors = [metadata['author']]
            
            if not authors:
                authors = [book.get('author', 'Unknown')]
            
            # Extract year
            year = str(metadata.get('datePublished', {}).get('year', ''))
            if not year:
                year = str(book.get('date', '')[:4]) if book.get('date') else '2024'
            
            # Build abstract
            description = metadata.get('description', book.get('excerpt', {}).get('rendered', ''))
            if isinstance(description, dict):
                description = description.get('value', '')
            
            subjects = metadata.get('subject', [])
            if isinstance(subjects, str):
                subjects = [subjects]
            
            license_info = metadata.get('license', {})
            if isinstance(license_info, dict):
                license_name = license_info.get('name', 'CC')
            else:
                license_name = str(license_info)
            
            abstract_parts = []
            if description:
                # Clean HTML
                import re
                clean_desc = re.sub('<[^<]+?>', '', description).strip()
                abstract_parts.append(clean_desc[:500])
            if subjects:
                abstract_parts.append(f"Subjects: {', '.join(subjects)}")
            abstract_parts.append(f"License: {license_name}")
            abstract_parts.append(f"Network: {network_name}")
            
            abstract = ' | '.join(abstract_parts)
            
            return Paper(
                title=title,
                authors=authors,
                abstract=abstract,
                year=year,
                source=network_name,
                full_text_url=pdf_url,
                journal=metadata.get('publisher', {}).get('name', network_name),
                content_type='book',
                isbn=metadata.get('isbn', ''),
                publisher=metadata.get('publisher', {}).get('name', ''),
                subjects=subjects,
                download_formats=['PDF', 'EPUB', 'MOBI']  # Pressbooks supports multiple formats
            )
            
        except Exception as e:
            logger.error(f"Error converting Pressbooks book to Paper: {str(e)}")
            return None