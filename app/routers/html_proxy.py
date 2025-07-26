"""
HTML proxy router for fetching and processing HTML content from external URLs
"""
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse
import httpx
import logging
from bs4 import BeautifulSoup
import re
from urllib.parse import urlparse, urljoin
import os

logger = logging.getLogger(__name__)

router = APIRouter()

# Development mode flag
DEV_MODE = os.getenv("DEV_MODE", "true").lower() == "true"

# List of allowed domains for proxy (expanded for HTML content)
ALLOWED_DOMAINS = [
    # Educational and research domains
    '.edu', '.ac.', '.org', '.gov',
    # Specific allowed domains
    'eric.ed.gov', 'files.eric.ed.gov',
    'ncbi.nlm.nih.gov', 'pubmed.ncbi.nlm.nih.gov',
    'europepmc.org', 'pmc.ncbi.nlm.nih.gov',
    'arxiv.org', 'export.arxiv.org',
    'doaj.org', 'core.ac.uk',
    'handle.net', 'doi.org',
    'plos.org', 'biomedcentral.com',
    'nature.com', 'springer.com',
    'nih.gov', 'nlm.nih.gov',
    'biodiversitylibrary.org',
    'archive.org', 'openlibrary.org',
    'gutenberg.org', 'oapen.org',
    'library.oapen.org', 'doab.org',
    'directory.doabooks.org',
    'openstax.org', 'cnx.org',
    'iteaconnect.org',  # Allow ITEA Connect
    'libretexts.org',   # LibreTexts educational content
    'sciencedirect.com', 'elsevier.com',
    'wiley.com', 'tandfonline.com',
    'sagepub.com', 'jstor.org',
    'cambridge.org', 'oup.com',
    'crossref.org', 'unpaywall.org',
    'semanticscholar.org', 'openalex.org',
    'researchgate.net', 'academia.edu',
    'repository', 'digital', 'scholar'
]

@router.get("/proxy-html")
async def proxy_html(url: str = Query(..., description="URL to fetch HTML from")):
    """
    Proxy HTML content from external URLs and clean it for display
    """
    try:
        # Validate URL
        if not url.startswith(('http://', 'https://')):
            raise HTTPException(status_code=400, detail="Invalid URL scheme")
        
        # Parse URL
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        
        # Check if domain is allowed (skip in dev mode for testing)
        if not DEV_MODE and not any(allowed in domain for allowed in ALLOWED_DOMAINS):
            logger.warning(f"Domain not in allowed list for HTML proxy: {domain}")
            raise HTTPException(
                status_code=403, 
                detail=f"Domain '{domain}' not allowed for proxy."
            )
        
        logger.info(f"[proxy-html] Fetching HTML from: {url}")
        
        # Fetch the HTML content
        async with httpx.AsyncClient(follow_redirects=True, timeout=30.0) as client:
            response = await client.get(url, headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
                "Accept-Encoding": "gzip, deflate, br",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1"
            })
            response.raise_for_status()
            
            # Get content type and encoding
            content_type = response.headers.get("content-type", "text/html")
            encoding = response.encoding or 'utf-8'
            
            # Special handling for LibreTexts encoding issues
            if 'libretexts.org' in domain:
                try:
                    # Try to detect encoding from content
                    raw_content = response.content
                    # Try UTF-8 first
                    html_content = raw_content.decode('utf-8', errors='ignore')
                    logger.info(f"[proxy-html] LibreTexts content decoded with UTF-8")
                except Exception as e:
                    logger.warning(f"[proxy-html] LibreTexts encoding issue: {e}")
                    html_content = response.text
            else:
                # Decode content normally
                html_content = response.text
            
            # Parse and clean HTML
            try:
                soup = BeautifulSoup(html_content, 'html.parser')
            except Exception as e:
                logger.error(f"[proxy-html] BeautifulSoup parsing error for {url}: {e}")
                # Try with a more robust parser
                soup = BeautifulSoup(html_content, 'lxml', from_encoding='utf-8')
            
            # Extract title
            try:
                title = soup.title.string.strip() if soup.title and soup.title.string else "Document"
            except Exception:
                title = "Document"
            
            # Remove scripts and styles
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Convert relative URLs to absolute
            base_url = f"{parsed.scheme}://{parsed.netloc}"
            
            # Fix links
            for tag in soup.find_all(['a', 'link']):
                if tag.get('href'):
                    tag['href'] = urljoin(url, tag['href'])
            
            # Fix images
            for tag in soup.find_all(['img', 'source']):
                if tag.get('src'):
                    tag['src'] = urljoin(url, tag['src'])
            
            # Fix forms
            for tag in soup.find_all('form'):
                if tag.get('action'):
                    tag['action'] = urljoin(url, tag['action'])
            
            # Add base tag if not present
            if not soup.find('base'):
                base_tag = soup.new_tag('base', href=url)
                if soup.head:
                    soup.head.insert(0, base_tag)
            
            # Add responsive viewport
            if soup.head and not soup.find('meta', attrs={'name': 'viewport'}):
                viewport_tag = soup.new_tag('meta', attrs={
                    'name': 'viewport',
                    'content': 'width=device-width, initial-scale=1.0'
                })
                soup.head.append(viewport_tag)
            
            # Add custom styles for better readability
            style_tag = soup.new_tag('style')
            style_tag.string = """
                body {
                    max-width: 1200px;
                    margin: 0 auto;
                    padding: 20px;
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    line-height: 1.6;
                    color: #333;
                }
                img {
                    max-width: 100%;
                    height: auto;
                }
                pre {
                    overflow-x: auto;
                    background: #f4f4f4;
                    padding: 10px;
                    border-radius: 4px;
                }
                table {
                    border-collapse: collapse;
                    width: 100%;
                    margin: 1em 0;
                }
                table, th, td {
                    border: 1px solid #ddd;
                }
                th, td {
                    padding: 8px;
                    text-align: left;
                }
                /* Hide navigation and sidebars that might interfere */
                nav, aside, .sidebar, .navigation, .header-nav {
                    display: none !important;
                }
            """
            if soup.head:
                soup.head.append(style_tag)
            
            # Convert back to string
            cleaned_html = str(soup)
            
            # Final sanitization to remove any problematic characters
            try:
                # Ensure clean UTF-8 encoding
                cleaned_html = cleaned_html.encode('utf-8', errors='ignore').decode('utf-8')
                # Remove any null bytes or other problematic characters
                cleaned_html = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', cleaned_html)
            except Exception as e:
                logger.warning(f"[proxy-html] Character sanitization error: {e}")
            
            return JSONResponse({
                "success": True,
                "url": url,
                "title": title,
                "content": cleaned_html,
                "contentType": "html"
            })
            
    except httpx.TimeoutException:
        logger.error(f"Timeout fetching HTML from: {url}")
        raise HTTPException(status_code=504, detail="HTML fetch timeout")
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error fetching HTML: {e.response.status_code} - {url}")
        raise HTTPException(
            status_code=e.response.status_code, 
            detail=f"HTTP error: {e.response.status_code}"
        )
    except httpx.RequestError as e:
        logger.error(f"Error fetching HTML: {str(e)} - {url}")
        raise HTTPException(status_code=502, detail=f"Error fetching HTML: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error in HTML proxy: {str(e)} - {url}")
        raise HTTPException(status_code=500, detail="Internal server error")