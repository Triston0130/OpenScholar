"""
PDF URL Extractor - Extracts direct PDF URLs from textbook landing pages
"""

import logging
import httpx
from bs4 import BeautifulSoup
import re
from typing import Optional

logger = logging.getLogger(__name__)

class PDFExtractor:
    """Extract PDF URLs from various textbook sources"""
    
    async def extract_pdf_url(self, landing_page_url: str) -> Optional[str]:
        """Extract PDF URL from a landing page"""
        if "open.umn.edu/opentextbooks" in landing_page_url:
            return await self._extract_otl_pdf(landing_page_url)
        elif "libretexts.org" in landing_page_url:
            return await self._extract_libretexts_pdf(landing_page_url)
        else:
            # For other sources, return the original URL
            return landing_page_url
    
    def _libretexts_to_pdf(self, url: str) -> str:
        """Convert LibreTexts Bookshelves URL to PDF print URL"""
        import re
        from urllib.parse import urlparse, urlunparse
        
        if re.match(r'^https://[^/]*libretexts\.org/Bookshelves/', url):
            parsed = urlparse(url)
            # Remove trailing slash and add /print with pdf format
            clean_path = parsed.path.rstrip('/')
            new_path = clean_path + '/print'
            new_query = 'format=pdf'
            
            return urlunparse((
                parsed.scheme,
                parsed.netloc, 
                new_path,
                parsed.params,
                new_query,
                parsed.fragment
            ))
        
        return url
    
    async def _extract_otl_pdf(self, landing_page_url: str) -> Optional[str]:
        """Extract PDF URL from Open Textbook Library page"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.get(landing_page_url)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # Look for consistent OTL PDF button patterns
                    # Try 1: button with data-format="pdf"
                    pdf_button = soup.find('a', {'class': 'button', 'data-format': 'pdf'})
                    if pdf_button and pdf_button.get('href'):
                        format_url = pdf_button['href']
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
                                
                                # Special handling for MIT OCW
                                if 'ocw.mit.edu' in str(format_response.url):
                                    logger.info(f"Detected MIT OCW redirect from OTL: {format_response.url}")
                                    # MIT OCW uses links like "complete textbook (PDF)"
                                    # Look for links containing "complete" and "textbook" or "PDF"
                                    for link in format_soup.find_all('a'):
                                        link_text = link.get_text(strip=True).lower()
                                        if ('complete' in link_text and 'textbook' in link_text) or \
                                           ('complete' in link_text and 'pdf' in link_text):
                                            href = link.get('href')
                                            if href:
                                                # MIT OCW often has intermediate pages, follow them
                                                if not href.startswith('http'):
                                                    href = f"https://ocw.mit.edu{href}"
                                                    
                                                    # Follow the link to get the actual PDF
                                                    try:
                                                        pdf_response = await client.get(href, follow_redirects=True)
                                                        if 'application/pdf' in pdf_response.headers.get('content-type', ''):
                                                            return str(pdf_response.url)
                                                        elif pdf_response.status_code == 200:
                                                            # Look for PDF link on the intermediate page
                                                            pdf_soup = BeautifulSoup(pdf_response.text, 'html.parser')
                                                            
                                                            # MIT OCW has PDF links in resource-thumbnail elements
                                                            resource_link = pdf_soup.find('a', {'class': 'resource-thumbnail'})
                                                            if resource_link and resource_link.get('href', '').endswith('.pdf'):
                                                                pdf_url = resource_link['href']
                                                                if not pdf_url.startswith('http'):
                                                                    pdf_url = f"https://ocw.mit.edu{pdf_url}"
                                                                logger.info(f"Successfully extracted MIT OCW PDF: {pdf_url}")
                                                                return pdf_url
                                                            
                                                            # Fallback: look for any link ending in .pdf
                                                            for link in pdf_soup.find_all('a', href=True):
                                                                if link['href'].endswith('.pdf'):
                                                                    pdf_url = link['href']
                                                                    if not pdf_url.startswith('http'):
                                                                        pdf_url = f"https://ocw.mit.edu{pdf_url}"
                                                                    return pdf_url
                                                    except Exception as e:
                                                        logger.debug(f"Error following MIT OCW link: {e}")
                                    
                                # Special handling for LibreTexts
                                elif 'libretexts.org' in str(format_response.url):
                                    logger.info(f"Detected LibreTexts redirect from OTL: {format_response.url}")
                                    
                                    # LibreTexts has a "Download Full Book (PDF)" option
                                    # The downloadfull parameter needs to be accessed from the book's context
                                        current_url = str(format_response.url)
                                        base_url = f"{format_response.url.scheme}://{format_response.url.host}"
                                        
                                        # Try the downloadfull parameter on the current book URL
                                        full_book_url = f"{current_url}?downloadfull"
                                        
                                        try:
                                            # This may return HTML with a download link, not direct PDF
                                            full_book_response = await client.get(full_book_url)
                                            if 'application/pdf' in full_book_response.headers.get('content-type', ''):
                                                logger.info(f"Found LibreTexts full book PDF: {full_book_response.url}")
                                                return str(full_book_response.url)
                                            else:
                                                # Parse the download page for actual PDF link
                                                dl_soup = BeautifulSoup(full_book_response.text, 'html.parser')
                                                for link in dl_soup.find_all('a', href=True):
                                                    href = link.get('href', '')
                                                    if '@api/deki/pages/' in href and '/pdf/' in href and href.endswith('.pdf'):
                                                        if not href.startswith('http'):
                                                            href = f"{base_url}{href}"
                                                        # This might be the full book PDF via API
                                                        logger.info(f"Found LibreTexts full book API PDF: {href}")
                                                        return href
                                                        
                                        except Exception as e:
                                            logger.debug(f"Error getting LibreTexts full book: {e}")
                                        
                                        # Fallback: Look for "Download Full Book" links in the page
                                        for link in format_soup.find_all('a'):
                                            link_text = link.get_text(strip=True).lower()
                                            if ('download' in link_text and 'full' in link_text and 'book' in link_text) or \
                                               ('complete' in link_text and 'book' in link_text):
                                                href = link.get('href')
                                                if href:
                                                    if not href.startswith('http'):
                                                        href = f"{base_url}{href}"
                                                    try:
                                                        download_response = await client.get(href, follow_redirects=True)
                                                        if 'application/pdf' in download_response.headers.get('content-type', ''):
                                                            logger.info(f"LibreTexts full book link: {download_response.url}")
                                                            return str(download_response.url)
                                                    except Exception as e:
                                                        logger.debug(f"Error following LibreTexts download link: {e}")
                                        
                                        # Last resort: Look for API PDF URLs (but these might be incomplete)
                                        for link in format_soup.find_all('a', href=True):
                                            href = link.get('href', '')
                                            if '@api/deki/pages/' in href and '/pdf/' in href and href.endswith('.pdf'):
                                                if not href.startswith('http'):
                                                    href = f"{base_url}{href}"
                                                logger.info(f"Found LibreTexts PDF API link (may be incomplete): {href}")
                                                return href
                                    
                                    # Look for complete/full book PDF (general case)
                                    full_book_link = format_soup.find('a', string=re.compile(r'complete.*textbook.*PDF|full.*book.*PDF|complete.*pdf', re.IGNORECASE))
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
                    
                    # Try 2: Look for format section with PDF link text (fallback)
                    if not pdf_button:
                        format_section = soup.find('section', id='Formats')
                        if format_section:
                            pdf_link = format_section.find('a', string='PDF')
                            if pdf_link and pdf_link.get('href'):
                                format_url = pdf_link['href']
                                if not format_url.startswith('http'):
                                    format_url = f"https://open.umn.edu{format_url}"
                                
                                try:
                                    format_response = await client.get(format_url, follow_redirects=True)
                                    if 'application/pdf' in format_response.headers.get('content-type', ''):
                                        return str(format_response.url)
                                except Exception as e:
                                    logger.debug(f"Error following format section link: {e}")
                    
                    # Try 3: Look for direct PDF links on the page
                    pdf_links = soup.find_all('a', href=re.compile(r'\.pdf$', re.IGNORECASE))
                    if pdf_links:
                        pdf_url = pdf_links[0]['href']
                        if not pdf_url.startswith('http'):
                            pdf_url = f"https://open.umn.edu{pdf_url}"
                        return pdf_url
                            
            except Exception as e:
                logger.error(f"Error extracting OTL PDF URL: {e}")
        
        return None
    
    async def _extract_libretexts_pdf(self, landing_page_url: str) -> Optional[str]:
        """Extract PDF URL from LibreTexts page"""
        # For Bookshelves URLs, convert to print PDF format
        if '/Bookshelves/' in landing_page_url:
            pdf_url = self._libretexts_to_pdf(landing_page_url)
            logger.info(f"Converted LibreTexts Bookshelves URL to PDF: {pdf_url}")
            return pdf_url
        
        # For other LibreTexts URLs, return as-is
        return landing_page_url