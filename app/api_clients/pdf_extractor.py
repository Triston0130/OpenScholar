"""
PDF URL Extractor - Extracts direct PDF URLs from textbook landing pages
"""

import logging
import httpx
from bs4 import BeautifulSoup
import re
from typing import Optional
from urllib.parse import urlparse, urlunparse, quote

logger = logging.getLogger(__name__)

class PDFExtractor:
    """Extract PDF URLs from various textbook sources"""
    
    async def extract_pdf_url(self, landing_page_url: str) -> Optional[str]:
        """Extract PDF URL from a landing page"""
        
        if "open.umn.edu/opentextbooks" in landing_page_url:
            result = await self._extract_otl_pdf(landing_page_url)
            return result if result else landing_page_url
        elif "libretexts.org" in landing_page_url:
            result = await self._extract_libretexts_pdf(landing_page_url)
            return result if result else landing_page_url
        elif "doabooks.org/handle" in landing_page_url:
            result = await self._extract_doab_pdf(landing_page_url)
            return result if result else landing_page_url
        else:
            # For other sources, return the original URL
            return landing_page_url
    
    def _libretexts_to_pdf(self, url: str) -> str:
        """Convert LibreTexts Bookshelves URL to PDF download URL"""
        # This method is no longer used since we extract the actual PDF URL from the page
        return url
    
    async def _extract_otl_pdf(self, landing_page_url: str) -> Optional[str]:
        """Extract PDF URL from Open Textbook Library page"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.get(landing_page_url)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # Try 1: Look for button with data-format="pdf" (old format)
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
                                                        for pdf_link in pdf_soup.find_all('a', href=True):
                                                            if pdf_link['href'].endswith('.pdf'):
                                                                pdf_url = pdf_link['href']
                                                                if not pdf_url.startswith('http'):
                                                                    pdf_url = f"https://ocw.mit.edu{pdf_url}"
                                                                return pdf_url
                                                except Exception as e:
                                                    logger.debug(f"Error following MIT OCW link: {e}")
                                
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
                    
                    # Try 2: Look for formats list with PDF link  
                    if not pdf_button:
                        # First try the ul#book-types structure (new format)
                        book_types = soup.find('ul', id='book-types')
                        if book_types:
                            pdf_link = book_types.find('a', string='PDF')
                            if pdf_link and pdf_link.get('href'):
                                format_url = pdf_link['href']
                                if not format_url.startswith('http'):
                                    format_url = f"https://open.umn.edu{format_url}"
                                
                                try:
                                    format_response = await client.get(format_url, follow_redirects=True)
                                    if 'application/pdf' in format_response.headers.get('content-type', ''):
                                        return str(format_response.url)
                                    
                                    # If redirected to another site, look for PDF links there
                                    if format_response.status_code == 200:
                                        format_soup = BeautifulSoup(format_response.text, 'html.parser')
                                        
                                        # Special handling for LibreTexts
                                        if 'libretexts.org' in str(format_response.url):
                                            # Look for "Download Full Book (PDF)" link
                                            full_book_link = format_soup.find('a', id='download_pdf_full')
                                            if full_book_link and full_book_link.get('href'):
                                                # This usually points to /?downloadfull, need to get actual PDF
                                                # Look for the actual PDF API link
                                                pdf_export = format_soup.find('a', href=re.compile(r'/@api/deki/pages/\d+/pdf/'))
                                                if pdf_export:
                                                    pdf_url = pdf_export['href']
                                                    if not pdf_url.startswith('http'):
                                                        pdf_url = f"{format_response.url.scheme}://{format_response.url.host}{pdf_url}"
                                                    return pdf_url
                                        
                                        # Look for any link with "PDF" in the text that points to a .pdf file
                                        pdf_links = format_soup.find_all('a')
                                        for link in pdf_links:
                                            link_text = link.get_text(strip=True).lower()
                                            link_href = link.get('href', '')
                                            
                                            # Prioritize "complete" or "full" book PDFs
                                            if ('complete' in link_text or 'full' in link_text or 'download full book' in link_text) and 'pdf' in link_text and link_href:
                                                if not link_href.startswith('http'):
                                                    base_url = f"{format_response.url.scheme}://{format_response.url.host}"
                                                    pdf_url = base_url + link_href
                                                else:
                                                    pdf_url = link_href
                                                return pdf_url
                                        
                                        # If no "complete" PDF found, take any PDF
                                        for link in pdf_links:
                                            link_href = link.get('href', '')
                                            if link_href and ('.pdf' in link_href.lower() or '/pdf/' in link_href):
                                                if not link_href.startswith('http'):
                                                    base_url = f"{format_response.url.scheme}://{format_response.url.host}"
                                                    pdf_url = base_url + link_href
                                                else:
                                                    pdf_url = link_href
                                                return pdf_url
                                except Exception as e:
                                    logger.debug(f"Error following book-types PDF link: {e}")
                        
                        # Fallback to old format section structure
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
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                # Fetch the LibreTexts page
                response = await client.get(landing_page_url)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # Method 0: Look for the direct PDF API link (if it exists on the page)
                    pdf_api_link = soup.find('a', href=re.compile(r'/@api/deki/pages/\d+/pdf/.*\.pdf'))
                    if pdf_api_link:
                        pdf_url = pdf_api_link['href']
                        if not pdf_url.startswith('http'):
                            parsed = urlparse(landing_page_url)
                            pdf_url = f"{parsed.scheme}://{parsed.netloc}{pdf_url}"
                        logger.info(f"Found LibreTexts direct PDF API link: {pdf_url}")
                        return pdf_url
                    
                    # Method 1: Look for pageId in JavaScript globals
                    script_tag = soup.find('script', id='mt-global-settings')
                    if script_tag and script_tag.string:
                        import json
                        try:
                            settings = json.loads(script_tag.string)
                            page_id = settings.get('pageId')
                            if page_id and page_id != 0:
                                # Extract library prefix from URL (e.g., math, chem, bio)
                                parsed = urlparse(landing_page_url)
                                library_match = re.match(r'^([^.]+)\.libretexts\.org', parsed.netloc)
                                
                                if library_match:
                                    library = library_match.group(1)
                                    
                                    # Try batch PDF URL first (full book PDF)
                                    batch_url = f"https://batch.libretexts.org/print/Letter/Finished/{library}-{page_id}/Full.pdf"
                                    
                                    # Check if batch PDF exists
                                    try:
                                        head_response = await client.head(batch_url, follow_redirects=False)
                                        if head_response.status_code == 200:
                                            logger.info(f"Found LibreTexts batch PDF (full book): {batch_url}")
                                            return batch_url
                                    except:
                                        logger.debug(f"Batch PDF not available for {library}-{page_id}")
                                
                                # Fallback to MindTouch API URL (table of contents only)
                                # Extract title from URL or page
                                path_parts = [p for p in parsed.path.split('/') if p]
                                if path_parts:
                                    title = path_parts[-1].replace(' ', '+')
                                else:
                                    # Fallback to page title
                                    title = settings.get('pageName', 'document').replace(' ', '+')
                                
                                # Construct MindTouch PDF API URL
                                pdf_url = f"{parsed.scheme}://{parsed.netloc}/@api/deki/pages/{page_id}/pdf/{title}.pdf?stylesheet=default"
                                logger.info(f"Using LibreTexts MindTouch PDF URL (TOC only): {pdf_url}")
                                return pdf_url
                        except json.JSONDecodeError:
                            logger.debug("Failed to parse mt-global-settings JSON")
                    
                    # Method 2: Look for PDF export link
                    pdf_link = soup.find('a', {'class': 'elm-pdf-export'})
                    if not pdf_link:
                        pdf_link = soup.find('a', href=re.compile(r'/@api/deki/pages/\d+/pdf/'))
                    
                    if pdf_link and pdf_link.get('href'):
                        pdf_href = pdf_link['href']
                        if not pdf_href.startswith('http'):
                            parsed = urlparse(landing_page_url)
                            pdf_href = f"{parsed.scheme}://{parsed.netloc}{pdf_href}"
                        logger.info(f"Found LibreTexts PDF link: {pdf_href}")
                        return pdf_href
                    
            except Exception as e:
                logger.error(f"Error extracting LibreTexts PDF URL: {e}")
        
        # If we can't extract the PDF URL, return the original
        return landing_page_url
    
    async def _extract_doab_pdf(self, landing_page_url: str) -> Optional[str]:
        """Extract PDF URL from DOAB handle page"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.get(landing_page_url)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # Look for PDF download links in the file section
                    # DOAB usually has links like "Download (PDF)"
                    pdf_links = soup.find_all('a', href=True)
                    for link in pdf_links:
                        link_text = link.get_text(strip=True).lower()
                        link_href = link['href']
                        
                        # Look for PDF download links
                        if ('download' in link_text and 'pdf' in link_text) or link_href.endswith('.pdf'):
                            if not link_href.startswith('http'):
                                # DOAB uses full URLs, but just in case
                                parsed = urlparse(landing_page_url)
                                link_href = f"{parsed.scheme}://{parsed.netloc}{link_href}"
                            logger.info(f"Found DOAB PDF link: {link_href}")
                            return link_href
                    
                    # Alternative: Look for links in the files/bitstream section
                    bitstream_links = soup.find_all('a', href=re.compile(r'/bitstream/'))
                    for link in bitstream_links:
                        if link['href'].endswith('.pdf'):
                            pdf_url = link['href']
                            if not pdf_url.startswith('http'):
                                parsed = urlparse(landing_page_url)
                                pdf_url = f"{parsed.scheme}://{parsed.netloc}{pdf_url}"
                            logger.info(f"Found DOAB bitstream PDF: {pdf_url}")
                            return pdf_url
                            
            except Exception as e:
                logger.error(f"Error extracting DOAB PDF URL: {e}")
        
        return None