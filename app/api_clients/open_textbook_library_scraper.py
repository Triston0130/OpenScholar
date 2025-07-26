"""
Open Textbook Library Scraper
Scrapes the full catalog since API is limited
"""

import logging
from typing import List, Optional
import httpx
from bs4 import BeautifulSoup
from app.models import Paper
import asyncio
import re

logger = logging.getLogger(__name__)

class OpenTextbookLibraryScraper:
    """Scraper for Open Textbook Library full catalog"""
    
    BASE_URL = "https://open.umn.edu/opentextbooks"
    
    async def _fetch_pdf_url(self, landing_page_url: str, client: httpx.AsyncClient) -> Optional[str]:
        """Fetch direct PDF URL from landing page"""
        try:
            response = await client.get(landing_page_url)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Look for format section
                format_section = soup.find('section', id='Formats')
                if format_section:
                    pdf_link = format_section.find('a', string='PDF')
                    if pdf_link and pdf_link.get('href'):
                        format_url = pdf_link['href']
                        if not format_url.startswith('http'):
                            format_url = f"https://open.umn.edu{format_url}"
                        
                        # Follow the format link to get the actual PDF
                        try:
                            format_response = await client.get(format_url, follow_redirects=True)
                            
                            # Check if it's already a PDF
                            if 'application/pdf' in format_response.headers.get('content-type', ''):
                                return str(format_response.url)
                            
                            # If redirected to another site, look for PDF links there
                            if format_response.status_code == 200:
                                format_soup = BeautifulSoup(format_response.text, 'html.parser')
                                
                                # Look for complete/full book PDF
                                full_book_link = format_soup.find('a', string=re.compile(r'complete.*textbook.*PDF|full.*book.*PDF', re.IGNORECASE))
                                if full_book_link and full_book_link.get('href'):
                                    pdf_url = full_book_link['href']
                                    # Handle relative URLs from the redirected domain
                                    if not pdf_url.startswith('http'):
                                        base_url = f"{format_response.url.scheme}://{format_response.url.host}"
                                        pdf_url = base_url + pdf_url
                                    return pdf_url
                                
                                # Fallback: look for any PDF link
                                pdf_links = format_soup.find_all('a', href=re.compile(r'\.pdf|\/pdf\/|resources.*pdf', re.IGNORECASE))
                                if pdf_links:
                                    pdf_url = pdf_links[0]['href']
                                    if not pdf_url.startswith('http'):
                                        base_url = f"{format_response.url.scheme}://{format_response.url.host}"
                                        pdf_url = base_url + pdf_url
                                    return pdf_url
                                    
                        except Exception as e:
                            logger.debug(f"Error following format link: {e}")
                
                # Fallback: Look for direct PDF links on the page
                pdf_links = soup.find_all('a', href=re.compile(r'\.pdf$', re.IGNORECASE))
                if pdf_links:
                    pdf_url = pdf_links[0]['href']
                    if not pdf_url.startswith('http'):
                        pdf_url = f"https://open.umn.edu{pdf_url}"
                    return pdf_url
                        
        except Exception as e:
            logger.debug(f"Error fetching PDF URL from {landing_page_url}: {e}")
        
        return None
    
    async def search(self, query: str, max_results: int = 100) -> List[Paper]:
        """Search the full OTL catalog"""
        papers = []
        query_lower = query.lower()
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                # Search directly using their search endpoint
                search_url = f"{self.BASE_URL}/textbooks"
                params = {
                    'term': query,
                    'commit': 'Search'
                }
                headers = {
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
                }
                
                response = await client.get(search_url, params=params, headers=headers)
                if response.status_code != 200:
                    logger.error(f"OTL search failed with status {response.status_code}")
                    return []
                
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Find all book entries - they use 'row short-description' for each book
                book_items = soup.find_all('div', class_='row short-description')
                
                logger.info(f"Found {len(book_items)} book entries for query: {query}")
                
                for item in book_items[:max_results]:
                    try:
                        # Extract title from h2 tag
                        title_elem = item.find('h2')
                        if not title_elem:
                            continue
                            
                        title_link = title_elem.find('a')
                        if not title_link:
                            continue
                            
                        title = title_link.get_text(strip=True)
                        book_url = title_link['href']
                        if not book_url.startswith('http'):
                            book_url = f"https://open.umn.edu{book_url}"
                        
                        # Extract metadata from p tags
                        info_div = item.find('div', class_='info')
                        if not info_div:
                            info_div = item.find('div', class_='col-sm-9')
                        
                        # Extract authors (from Contributor field) and publisher
                        authors = ["Open Textbook Library"]
                        contributor_p = None
                        publisher = ""
                        for p in info_div.find_all('p'):
                            text = p.get_text(strip=True)
                            if text.startswith('Contributor:'):
                                contributor_text = text.replace('Contributor:', '').strip()
                                authors = [a.strip() for a in re.split(r'[,;&]|and', contributor_text) if a.strip()]
                            elif text.startswith('Publisher:'):
                                publisher = text.replace('Publisher:', '').strip()
                        
                        # Extract year
                        year = "2024"
                        time_elem = info_div.find('time')
                        if time_elem:
                            year = time_elem.get('datetime', '2024')
                        
                        # Extract description (look for paragraph without specific markers)
                        description = f"Open textbook on {title}"
                        for p in info_div.find_all('p'):
                            text = p.get_text(strip=True)
                            # Skip metadata paragraphs
                            if not any(text.startswith(prefix) for prefix in ['Copyright Year:', 'Contributor:', 'Publisher:', 'License:', '(']):
                                if len(text) > 20 and not text.count('star') > 2:  # Skip rating paragraphs
                                    description = text
                                    break
                        
                        # Skip LibreTexts books - we have a dedicated client for those
                        if ('libretexts' in description.lower() or 
                            'libretexts' in str(book_url).lower() or
                            'libretexts' in publisher.lower()):
                            logger.debug(f"Skipping LibreTexts book from OTL: {title}")
                            continue
                        
                        # Create paper with landing page URL
                        paper = Paper(
                            title=title,
                            authors=authors,
                            abstract=description[:500],  # Limit description length
                            year=year,
                            source="Open Textbook Library",
                            full_text_url=book_url,  # Landing page URL - PDF extraction happens on click
                            content_type="book",
                            subjects=None,  # Could extract from breadcrumbs if needed
                            download_formats=["PDF", "EPUB", "Online"],
                            publisher=publisher if publisher else None
                        )
                        
                        papers.append(paper)
                        
                    except Exception as e:
                        logger.warning(f"Error parsing OTL book item: {e}")
                        continue
                
                # If no results from search, try browsing by subject
                if not papers and len(query_lower.split()) == 1:
                    # Try subject browse
                    papers = await self._browse_by_subject(query_lower, max_results, client)
                
                # Check if we need more results via pagination
                if len(papers) < max_results:
                    # Look for pagination
                    pagination_nav = soup.find('nav', class_='pagination')
                    if pagination_nav:
                        # Get total pages
                        last_page_link = pagination_nav.find('a', string=re.compile(r'Last'))
                        if last_page_link:
                            href = last_page_link.get('href', '')
                            match = re.search(r'page=(\d+)', href)
                            if match:
                                total_pages = int(match.group(1))
                                logger.info(f"Found {total_pages} total pages of results")
                                
                                # Fetch additional pages (limit to reasonable number)
                                pages_to_fetch = min(total_pages, max(5, max_results // 10))
                                
                                for page in range(2, pages_to_fetch + 1):
                                    if len(papers) >= max_results:
                                        break
                                        
                                    try:
                                        page_params = params.copy()
                                        page_params['page'] = page
                                        
                                        page_response = await client.get(search_url, params=page_params, headers=headers)
                                        if page_response.status_code == 200:
                                            page_soup = BeautifulSoup(page_response.text, 'html.parser')
                                            page_books = page_soup.find_all('div', class_='row short-description')
                                            
                                            for item in page_books:
                                                if len(papers) >= max_results:
                                                    break
                                                    
                                                # Same parsing logic as above
                                                try:
                                                    title_elem = item.find('h2')
                                                    if not title_elem:
                                                        continue
                                                        
                                                    title_link = title_elem.find('a')
                                                    if not title_link:
                                                        continue
                                                        
                                                    title = title_link.get_text(strip=True)
                                                    book_url = title_link['href']
                                                    if not book_url.startswith('http'):
                                                        book_url = f"https://open.umn.edu{book_url}"
                                                    
                                                    info_div = item.find('div', class_='info')
                                                    if not info_div:
                                                        info_div = item.find('div', class_='col-sm-9')
                                                    
                                                    authors = ["Open Textbook Library"]
                                                    publisher = ""
                                                    for p in info_div.find_all('p'):
                                                        text = p.get_text(strip=True)
                                                        if text.startswith('Contributor:'):
                                                            contributor_text = text.replace('Contributor:', '').strip()
                                                            authors = [a.strip() for a in re.split(r'[,;&]|and', contributor_text) if a.strip()]
                                                        elif text.startswith('Publisher:'):
                                                            publisher = text.replace('Publisher:', '').strip()
                                                    
                                                    year = "2024"
                                                    time_elem = info_div.find('time')
                                                    if time_elem:
                                                        year = time_elem.get('datetime', '2024')
                                                    
                                                    description = f"Open textbook on {title}"
                                                    for p in info_div.find_all('p'):
                                                        text = p.get_text(strip=True)
                                                        if not any(text.startswith(prefix) for prefix in ['Copyright Year:', 'Contributor:', 'Publisher:', 'License:', '(']):
                                                            if len(text) > 20 and not text.count('star') > 2:
                                                                description = text
                                                                break
                                                    
                                                    # Skip LibreTexts books - we have a dedicated client for those
                                                    if ('libretexts' in description.lower() or 
                                                        'libretexts' in str(book_url).lower() or
                                                        'libretexts' in publisher.lower()):
                                                        logger.debug(f"Skipping LibreTexts book from OTL: {title}")
                                                        continue
                                                    
                                                    paper = Paper(
                                                        title=title,
                                                        authors=authors,
                                                        abstract=description[:500],
                                                        year=year,
                                                        source="Open Textbook Library",
                                                        full_text_url=book_url,  # Landing page URL
                                                        content_type="book",
                                                        subjects=None,
                                                        download_formats=["PDF", "EPUB", "Online"],
                                                        publisher=publisher if publisher else None
                                                    )
                                                    
                                                    papers.append(paper)
                                                    
                                                except Exception as e:
                                                    logger.debug(f"Error parsing book on page {page}: {e}")
                                                    continue
                                                    
                                    except Exception as e:
                                        logger.warning(f"Error fetching page {page}: {e}")
                                        break
                
                logger.info(f"Returning {len(papers)} papers from OTL")
                return papers
                
            except Exception as e:
                logger.error(f"OTL scraper error: {e}")
                return []
    
    async def _browse_by_subject(self, subject: str, max_results: int, client: httpx.AsyncClient) -> List[Paper]:
        """Browse books by subject"""
        papers = []
        
        # Map common subjects to OTL categories
        subject_map = {
            'math': 'Mathematics',
            'mathematics': 'Mathematics',
            'calculus': 'Mathematics',
            'algebra': 'Mathematics',
            'statistics': 'Mathematics',
            'biology': 'Biology',
            'chemistry': 'Chemistry',
            'physics': 'Physics',
            'business': 'Business',
            'psychology': 'Social Sciences',
            'sociology': 'Social Sciences',
            'history': 'Humanities',
            'english': 'Languages',
            'computer': 'Computer Science',
            'engineering': 'Engineering'
        }
        
        otl_subject = subject_map.get(subject.lower(), subject.title())
        
        browse_url = f"{self.BASE_URL}/textbooks?subject={otl_subject}"
        
        try:
            response = await client.get(browse_url)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Similar parsing as search results
                book_items = soup.find_all('div', class_='cover-book-info')
                
                for item in book_items[:max_results]:
                    # Parse book item (same as above)
                    # ... (similar parsing code)
                    pass
                    
        except Exception as e:
            logger.warning(f"Error browsing OTL by subject: {e}")
        
        return papers