"""
LibreTexts Enhanced Client
Properly searches across all 3000+ LibreTexts books
"""

import logging
from typing import List, Dict, Any, Optional
import httpx
from app.models import Paper
from bs4 import BeautifulSoup
import asyncio
import re

logger = logging.getLogger(__name__)

class LibreTextsEnhanced:
    """Enhanced client that actually searches LibreTexts content"""
    
    async def _get_pdf_url(self, page_url: str) -> str:
        """Convert LibreTexts page URL to PDF download URL"""
        # LibreTexts PDF URLs follow a pattern:
        # Page: https://math.libretexts.org/Bookshelves/Calculus/Book%3A_Calculus_(OpenStax)
        # PDF:  https://math.libretexts.org/@api/deki/pages/4610/pdf/Book%253A_Calculus_(OpenStax).pdf
        
        # For now, return the page URL as LibreTexts PDFs require special handling
        # Users can use the "Download PDF" button on the page
        return page_url
    
    # All LibreTexts libraries
    LIBRARIES = {
        'biology': 'https://bio.libretexts.org',
        'business': 'https://biz.libretexts.org',
        'chemistry': 'https://chem.libretexts.org',
        'engineering': 'https://eng.libretexts.org',
        'español': 'https://espanol.libretexts.org',
        'geosciences': 'https://geo.libretexts.org',
        'humanities': 'https://human.libretexts.org',
        'k12': 'https://k12.libretexts.org',
        'mathematics': 'https://math.libretexts.org',
        'medicine': 'https://med.libretexts.org',
        'physics': 'https://phys.libretexts.org',
        'social_sciences': 'https://socialsci.libretexts.org',
        'spanish': 'https://espanol.libretexts.org',
        'statistics': 'https://stats.libretexts.org',
        'workforce': 'https://workforce.libretexts.org',
        'portuguese': 'https://pt.libretexts.org',
        'italian': 'https://it.libretexts.org'
    }
    
    async def search(self, query: str, max_results: int = 100) -> List[Paper]:
        """Search across all LibreTexts libraries"""
        papers = []
        query_lower = query.lower()
        
        # Determine which libraries to search
        libraries_to_search = self._select_libraries(query_lower)
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Search each library
            tasks = []
            for discipline, base_url in libraries_to_search:
                if len(papers) < max_results:
                    task = self._search_library(client, discipline, base_url, query, max_results - len(papers))
                    tasks.append(task)
            
            # Run searches in parallel
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Combine results
            for result in results:
                if isinstance(result, list):
                    papers.extend(result)
                    if len(papers) >= max_results:
                        papers = papers[:max_results]
                        break
                elif isinstance(result, Exception):
                    logger.warning(f"Search error: {result}")
        
        logger.info(f"LibreTexts returned {len(papers)} books for query: {query}")
        return papers
    
    def _select_libraries(self, query_lower: str) -> List[tuple]:
        """Select which libraries to search based on query"""
        # Keywords to library mapping
        keyword_map = {
            'math': ['mathematics', 'statistics'],
            'calculus': ['mathematics'],
            'algebra': ['mathematics'],
            'statistics': ['statistics', 'mathematics'],
            'biology': ['biology', 'medicine'],
            'chemistry': ['chemistry'],
            'physics': ['physics'],
            'engineering': ['engineering'],
            'computer': ['engineering', 'mathematics'],
            'psychology': ['social_sciences'],
            'sociology': ['social_sciences'],
            'history': ['humanities', 'social_sciences'],
            'literature': ['humanities'],
            'business': ['business'],
            'economics': ['business', 'social_sciences'],
            'medicine': ['medicine', 'biology'],
            'spanish': ['español', 'spanish'],
            'science': ['biology', 'chemistry', 'physics', 'geosciences']
        }
        
        selected = set()
        
        # Check for keyword matches
        for keyword, libraries in keyword_map.items():
            if keyword in query_lower:
                for lib in libraries:
                    if lib in self.LIBRARIES:
                        selected.add((lib, self.LIBRARIES[lib]))
        
        # If no matches, search core STEM libraries
        if not selected:
            default_libs = ['mathematics', 'biology', 'chemistry', 'physics', 'humanities', 'social_sciences']
            for lib in default_libs:
                if lib in self.LIBRARIES:
                    selected.add((lib, self.LIBRARIES[lib]))
        
        return list(selected)[:6]  # Limit to 6 libraries to avoid too many requests
    
    async def _search_library(self, client: httpx.AsyncClient, discipline: str, base_url: str, 
                             query: str, max_results: int) -> List[Paper]:
        """Search a specific LibreTexts library"""
        papers = []
        
        try:
            # First try the search endpoint
            search_url = f"{base_url}/Special:Search"
            params = {
                'search': query,
                'fulltext': 'Search'
            }
            
            response = await client.get(search_url, params=params)
            
            if response.status_code == 200:
                papers.extend(await self._parse_search_results(response.text, discipline, base_url, max_results))
            
            # If few results, also check the Bookshelves
            if len(papers) < max_results // 2:
                bookshelf_papers = await self._browse_bookshelves(client, discipline, base_url, query, max_results - len(papers))
                papers.extend(bookshelf_papers)
                
        except Exception as e:
            logger.warning(f"Error searching {discipline} library: {e}")
        
        return papers
    
    async def _parse_search_results(self, html: str, discipline: str, base_url: str, max_results: int) -> List[Paper]:
        """Parse search results page"""
        papers = []
        soup = BeautifulSoup(html, 'html.parser')
        
        # We'll use the client passed from the calling method
        async with httpx.AsyncClient(timeout=httpx.Timeout(30.0)) as client:
            # Find search results
            results = soup.find_all('div', class_='searchresult')
            if not results:
                results = soup.find_all('li', class_='mw-search-result')
        
            for result in results[:max_results]:
                try:
                    # Extract title and URL
                    title_elem = result.find('a')
                    if not title_elem:
                        continue
                    
                    title = title_elem.get_text(strip=True)
                    href = title_elem.get('href', '')
                    
                    # Build full URL first
                    if href.startswith('/'):
                        full_url = base_url + href
                    else:
                        full_url = href
                    
                    # If this is a category page, we need to drill into it
                    if '/Bookshelves/' in full_url and not ('(' in title and ')' in title):
                        # This is a category - fetch it and extract books
                        try:
                            category_response = await client.get(full_url)
                            if category_response.status_code == 200:
                                category_soup = BeautifulSoup(category_response.text, 'html.parser')
                                
                                # Extract all books from this category
                                book_items = category_soup.find_all('li', class_='mt-sortable-listing')
                                for book_item in book_items:
                                    book_link = book_item.find('a', class_='mt-sortable-listing-link')
                                    if book_link:
                                        book_title = book_link.find('span', class_='mt-sortable-listing-title')
                                        book_title_text = book_title.get_text(strip=True) if book_title else book_link.get('title', '').split(':')[0]
                                        
                                        # Only add if it's a book (has parentheses)
                                        if '(' in book_title_text and ')' in book_title_text:
                                            book_href = book_link.get('href', '')
                                            if not book_href.startswith('http'):
                                                book_url = base_url + book_href if book_href.startswith('/') else base_url + '/' + book_href
                                            else:
                                                book_url = book_href
                                                
                                            # Create paper for this book
                                            paper = Paper(
                                                title=book_title_text,
                                                authors=['LibreTexts Contributors'],
                                                abstract=description[:500] if 'description' in locals() else f"Open textbook from LibreTexts {discipline} library",
                                                year='2024',
                                                source='LibreTexts',
                                                full_text_url=book_url,
                                                content_type='book',
                                                subjects=[discipline.title()],
                                                download_formats=['PDF', 'Online'],
                                                publisher=f'LibreTexts {discipline.title()}'
                                            )
                                            papers.append(paper)
                        except Exception as e:
                            logger.debug(f"Error drilling into category: {e}")
                        
                        # Skip to next result - we've handled this category
                        continue
                    
                    # Extract snippet/description
                    snippet_elem = result.find('div', class_='searchresulttext')
                    if not snippet_elem:
                        snippet_elem = result.find('span', class_='searchmatch')
                    
                    description = snippet_elem.get_text(strip=True) if snippet_elem else f"LibreTexts {discipline} textbook"
                    
                    # Create paper with landing page URL
                    paper = Paper(
                        title=title,
                        authors=['LibreTexts Contributors'],
                        abstract=description[:500],
                        year='2024',
                        source='LibreTexts',
                        full_text_url=full_url,  # Landing page URL
                        content_type='book',
                        subjects=[discipline.title()],
                        download_formats=['PDF', 'Online'],
                        publisher=f'LibreTexts {discipline.title()}'
                    )
                    
                    papers.append(paper)
                    
                except Exception as e:
                    logger.debug(f"Error parsing search result: {e}")
                    continue
        
        return papers
    
    async def _browse_bookshelves(self, client: httpx.AsyncClient, discipline: str, 
                                 base_url: str, query: str, max_results: int) -> List[Paper]:
        """Browse the Bookshelves section for books"""
        papers = []
        query_lower = query.lower()
        
        try:
            bookshelf_url = f"{base_url}/Bookshelves"
            response = await client.get(bookshelf_url)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Find all book links
                book_links = soup.find_all('a', href=lambda h: h and '/Bookshelves/' in h)
                
                for link in book_links[:max_results * 2]:  # Check more links since we'll filter
                    try:
                        title = link.get_text(strip=True)
                        href = link.get('href', '')
                        
                        # Skip navigation links
                        if len(title) < 5 or title.lower() in ['bookshelves', 'home', 'back']:
                            continue
                        
                        # Check if this is an individual book (has author in parentheses) vs a category
                        is_book = '(' in title and ')' in title
                        
                        # Skip category pages - we only want individual books
                        if not is_book:
                            continue
                        
                        # Check if relevant to query (more flexible matching)
                        title_lower = title.lower()
                        query_words = query_lower.split()
                        
                        # Match if any query word is in title
                        if any(word in title_lower for word in query_words if len(word) > 2):
                            # Build full URL
                            if not href.startswith('http'):
                                full_url = base_url + href if href.startswith('/') else base_url + '/' + href
                            else:
                                full_url = href
                            
                            paper = Paper(
                                title=title,
                                authors=['LibreTexts Contributors'],
                                abstract=f"Open textbook from LibreTexts {discipline.title()} library. Free, peer-reviewed instructional material.",
                                year='2024',
                                source='LibreTexts',
                                full_text_url=full_url,  # Landing page URL
                                content_type='book',
                                subjects=[discipline.title()],
                                download_formats=['PDF', 'Online'],
                                publisher=f'LibreTexts {discipline.title()}'
                            )
                            
                            papers.append(paper)
                            
                            if len(papers) >= max_results:
                                break
                    
                    except Exception as e:
                        logger.debug(f"Error parsing bookshelf link: {e}")
                        continue
                
        except Exception as e:
            logger.warning(f"Error browsing {discipline} bookshelves: {e}")
        
        return papers