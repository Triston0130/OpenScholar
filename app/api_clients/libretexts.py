"""
LibreTexts Enhanced Client

Fetches actual books from LibreTexts libraries
"""

import logging
from typing import List, Dict, Any, Optional
import httpx
from app.models import Paper
from bs4 import BeautifulSoup
import asyncio

logger = logging.getLogger(__name__)

class LibreTextsClient:
    """Enhanced client for fetching LibreTexts books"""
    
    LIBRARIES = {
        'biology': 'https://bio.libretexts.org',
        'business': 'https://biz.libretexts.org', 
        'chemistry': 'https://chem.libretexts.org',
        'engineering': 'https://eng.libretexts.org',
        'geosciences': 'https://geo.libretexts.org',
        'humanities': 'https://human.libretexts.org',
        'mathematics': 'https://math.libretexts.org',
        'medicine': 'https://med.libretexts.org',
        'physics': 'https://phys.libretexts.org',
        'social_sciences': 'https://socialsci.libretexts.org',
        'statistics': 'https://stats.libretexts.org',
        'workforce': 'https://workforce.libretexts.org'
    }
    
    def __init__(self):
        self.timeout = httpx.Timeout(30.0)
        
    async def search(self, query: str, max_results: int = 20) -> List[Paper]:
        """Search for textbooks across LibreTexts libraries"""
        papers = []
        query_lower = query.lower()
        
        # Determine which libraries to search based on query
        libraries_to_search = []
        
        # Check for specific disciplines
        for discipline, url in self.LIBRARIES.items():
            if query_lower in discipline or discipline in query_lower:
                libraries_to_search.append((discipline, url))
        
        # If no specific match, search multiple libraries
        if not libraries_to_search:
            # Default to searching math, science, and humanities
            libraries_to_search = [
                ('mathematics', self.LIBRARIES['mathematics']),
                ('chemistry', self.LIBRARIES['chemistry']),
                ('biology', self.LIBRARIES['biology']),
                ('physics', self.LIBRARIES['physics'])
            ]
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            # Fetch bookshelves from each library
            for discipline, base_url in libraries_to_search:
                if len(papers) >= max_results:
                    break
                    
                try:
                    # Get the bookshelf page
                    bookshelf_url = f"{base_url}/Bookshelves"
                    response = await client.get(bookshelf_url)
                    
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.text, 'html.parser')
                        
                        # First check if there are any books directly on the bookshelf page
                        direct_books = soup.find_all('li', class_='mt-sortable-listing')
                        for book_item in direct_books:
                            if len(papers) >= max_results:
                                break
                            
                            book_link = book_item.find('a', class_='mt-sortable-listing-link')
                            if not book_link:
                                continue
                                
                            book_href = book_link.get('href', '')
                            book_title_span = book_link.find('span', class_='mt-sortable-listing-title')
                            book_title = book_title_span.get_text(strip=True) if book_title_span else book_link.get('title', '').split(':')[0]
                            
                            # Check if this book matches the query and is not a category page
                            # Books have author names in parentheses
                            is_individual_book = '(' in book_title and ')' in book_title
                            
                            if (book_href and book_title and query_lower in book_title.lower() and is_individual_book):
                                # Build full URL
                                if not book_href.startswith('http'):
                                    full_book_url = base_url + book_href if book_href.startswith('/') else base_url + '/' + book_href
                                else:
                                    full_book_url = book_href
                                
                                paper = Paper(
                                    title=book_title,
                                    authors=['LibreTexts Contributors'],
                                    abstract=f"Open textbook from LibreTexts {discipline.title()} library. Part of the LibreTexts project providing free, peer-reviewed instructional materials.",
                                    year='2024',
                                    source="LibreTexts",
                                    full_text_url=full_book_url,
                                    journal=f"LibreTexts {discipline.title()}",
                                    content_type='book',
                                    subjects=[discipline.title(), 'Open Textbook'],
                                    download_formats=['HTML', 'PDF', 'EPUB'],
                                    license='CC BY-NC-SA 4.0'
                                )
                                papers.append(paper)
                        
                        # Then find all category pages to search within
                        category_links = soup.find_all('a', href=True)
                        all_categories = []
                        
                        for link in category_links:
                            href = link.get('href', '')
                            title = link.get_text(strip=True)
                            
                            # Collect all category pages in Bookshelves
                            if '/Bookshelves/' in href and href.count('/') == base_url.count('/') + 2:
                                if not href.startswith('http'):
                                    full_url = base_url + href if href.startswith('/') else base_url + '/' + href
                                else:
                                    full_url = href
                                all_categories.append((title, full_url))
                        
                        # Second pass: drill down into each category to find books matching the query
                        for category_title, category_url in all_categories:  # Search all categories
                            if len(papers) >= max_results:
                                break
                                
                            try:
                                category_response = await client.get(category_url)
                                if category_response.status_code == 200:
                                    category_soup = BeautifulSoup(category_response.text, 'html.parser')
                                    
                                    # Look for mt-sortable-listing items which are actual books
                                    book_listings = category_soup.find_all('li', class_='mt-sortable-listing')
                                    
                                    for book_item in book_listings:
                                        if len(papers) >= max_results:
                                            break
                                            
                                        book_link = book_item.find('a', class_='mt-sortable-listing-link')
                                        if not book_link:
                                            continue
                                            
                                        book_href = book_link.get('href', '')
                                        book_title_span = book_link.find('span', class_='mt-sortable-listing-title')
                                        book_title = book_title_span.get_text(strip=True) if book_title_span else book_link.get('title', '').split(':')[0]
                                        
                                        # Filter for actual individual books that match query
                                        # Books have author names in parentheses
                                        is_individual_book = '(' in book_title and ')' in book_title
                                        
                                        if (book_href and book_title and 
                                            query_lower in book_title.lower() and is_individual_book):
                                            
                                            # Build full URL
                                            if not book_href.startswith('http'):
                                                full_book_url = base_url + book_href if book_href.startswith('/') else base_url + '/' + book_href
                                            else:
                                                full_book_url = book_href
                                            
                                            paper = Paper(
                                                title=book_title,
                                                authors=['LibreTexts Contributors'],
                                                abstract=f"Open textbook from LibreTexts {discipline.title()} library - {category_title}. Part of the LibreTexts project providing free, peer-reviewed instructional materials.",
                                                year='2024',
                                                source="LibreTexts",
                                                full_text_url=full_book_url,
                                                journal=f"LibreTexts {discipline.title()}",
                                                content_type='book',
                                                subjects=[discipline.title(), 'Open Textbook'],
                                                download_formats=['HTML', 'PDF', 'EPUB'],
                                                license='CC BY-NC-SA 4.0'
                                            )
                                            papers.append(paper)
                                            
                            except Exception as e:
                                logger.debug(f"Error fetching category {category_url}: {e}")
                                continue
                    
                except Exception as e:
                    logger.error(f"Error searching LibreTexts {discipline}: {str(e)}")
                    continue
        
        logger.info(f"LibreTexts: Found {len(papers)} results for '{query}'")
        return papers