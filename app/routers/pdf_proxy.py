"""
PDF and HTML Proxy router to handle CORS issues
"""
from fastapi import APIRouter, HTTPException, Response
from fastapi.responses import StreamingResponse, JSONResponse
import httpx
import logging
from typing import Optional
import bleach
from bs4 import BeautifulSoup
import os
import re

logger = logging.getLogger(__name__)
router = APIRouter()


# Development mode for testing
DEV_MODE = os.getenv("ENVIRONMENT", "development") == "development"

# Allowed domains for security - comprehensive academic sources
ALLOWED_DOMAINS = [
    # Preprints & AI
    "arxiv.org",
    "semanticscholar.org",
    "aclanthology.org",
    "openreview.net",
    "proceedings.neurips.cc",
    
    # Life Sciences
    "ncbi.nlm.nih.gov",
    "pubmed.ncbi.nlm.nih.gov",
    "pmc.ncbi.nlm.nih.gov",
    "europepmc.org",
    "biorxiv.org",
    "medrxiv.org",
    
    # Education & General
    "eric.ed.gov",
    "files.eric.ed.gov",
    "openalex.org",
    "crossref.org",
    "doaj.org",
    
    # Open Access
    "core.ac.uk",
    "unpaywall.org",
    "base-search.net",
    
    # Books & Digital Libraries
    "doabooks.org",
    "gutenberg.org",
    "archive.org",
    "openlibrary.org",
    "openstax.org",
    "oapen.org",
    "books.google.com",
    "biodiversitylibrary.org",
    "ncbi.nlm.nih.gov/books",
    
    # Open Science Publishers
    "plos.org",
    "journals.plos.org",
    "biomedcentral.com",
    "bmcmedicine.biomedcentral.com",
    "frontiersin.org",
    "mdpi.com",
    
    # Traditional Publishers
    "jmlr.org",
    "ieee.org",
    "acm.org",
    "springer.com",
    "link.springer.com",
    "sciencedirect.com",
    "nature.com",
    "science.org",
    "pnas.org",
    "wiley.com",
    "onlinelibrary.wiley.com",
    "tandfonline.com",
    "oup.com",
    "academic.oup.com",
    "cambridge.org",
    "cell.com",
    "aacrjournals.org",
    "ahajournals.org",
    "nejm.org",
    "thelancet.com",
    "bmj.com",
    "sagepub.com",
    "journals.sagepub.com",
    "jstor.org",
    "sciencemag.org",
    "annualreviews.org",
    "apa.org",
    "psycnet.apa.org",
    "royalsocietypublishing.org",
    "iop.org",
    "iopscience.iop.org",
    "rsc.org",
    "pubs.rsc.org",
    "acs.org",
    "pubs.acs.org",
    "ascopubs.org",
    "ashpublications.org",
    "physiology.org",
    "journals.physiology.org",
    "genetics.org",
    "asm.org",
    "journals.asm.org",
    "rupress.org",
    "jneurosci.org",
    "embopress.org",
    "elifesciences.org",
    "peerj.com",
    "f1000research.com",
    "wellcomeopenresearch.org",
    "gatesopenresearch.org"
]

@router.get("/proxy-pdf")
async def proxy_pdf(url: str):
    """
    Proxy PDF requests to handle CORS issues and content encoding
    """
    try:
        # Validate URL domain
        from urllib.parse import urlparse
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        
        # Check if domain is allowed (skip in dev mode for testing)
        if not DEV_MODE and not any(allowed in domain for allowed in ALLOWED_DOMAINS):
            logger.warning(f"Domain not in allowed list: {domain}")
            raise HTTPException(
                status_code=403, 
                detail=f"Domain '{domain}' not allowed for proxy. Please contact support to add this domain."
            )
        
        if DEV_MODE and not any(allowed in domain for allowed in ALLOWED_DOMAINS):
            logger.info(f"DEV MODE: Allowing unlisted domain: {domain}")
        
        # Make the actual request to get headers and content
        async with httpx.AsyncClient(follow_redirects=True, timeout=60.0) as client:
            response = await client.get(url, headers={
                "User-Agent": "Mozilla/5.0 (compatible; OpenScholar/1.0)",
                "Accept": "application/pdf, text/html, */*"
            })
            response.raise_for_status()
            
            # Get content type and encoding
            content_type = response.headers.get("content-type", "application/pdf")
            content_encoding = response.headers.get("content-encoding", "")
            
            logger.info(f"[proxy-pdf] {url} → Content-Type: {content_type}, Encoding: {content_encoding}, Status: {response.status_code}")
            
            # Validate that this is actually a PDF
            if "application/pdf" not in content_type.lower():
                logger.warning(f"URL is not a PDF: {url} (content-type: {content_type})")
                raise HTTPException(
                    status_code=415, 
                    detail=f"URL is not a PDF. Content-Type: {content_type}"
                )
            
            # Build response headers
            headers = {
                "Content-Type": content_type,
                "Cache-Control": "public, max-age=3600",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, HEAD, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type, Range",
                "Accept-Ranges": "bytes"
            }
            
            # Forward Content-Encoding if present (e.g., gzip for ERIC PDFs)
            if content_encoding:
                headers["Content-Encoding"] = content_encoding
            
            # Stream the response directly, preserving encoding
            async def stream_content():
                async with httpx.AsyncClient(follow_redirects=True, timeout=60.0) as client:
                    async with client.stream("GET", url, headers={
                        "User-Agent": "Mozilla/5.0 (compatible; OpenScholar/1.0)",
                        "Accept": "application/pdf, text/html, */*"
                    }) as stream_response:
                        stream_response.raise_for_status()
                        async for chunk in stream_response.aiter_raw():
                            yield chunk
            
            return StreamingResponse(
                stream_content(),
                media_type=content_type,
                headers=headers
            )
            
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="PDF fetch timeout")
    except httpx.RequestError as e:
        logger.error(f"Error fetching PDF: {str(e)}")
        raise HTTPException(status_code=502, detail=f"Error fetching PDF: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error in PDF proxy: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.head("/proxy-pdf")
async def proxy_pdf_head(url: str):
    """
    Check content type of a URL without downloading the full content
    """
    try:
        # Validate URL domain
        from urllib.parse import urlparse
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        
        # Check if domain is allowed (skip in dev mode for testing)
        if not DEV_MODE and not any(allowed in domain for allowed in ALLOWED_DOMAINS):
            logger.warning(f"Domain not in allowed list: {domain}")
            raise HTTPException(
                status_code=403, 
                detail=f"Domain '{domain}' not allowed for proxy."
            )
        
        # Make HEAD request to check content type
        async with httpx.AsyncClient(follow_redirects=True, timeout=30.0) as client:
            response = await client.head(url, headers={
                "User-Agent": "Mozilla/5.0 (compatible; OpenScholar/1.0)"
            })
            content_type = response.headers.get("content-type", "application/octet-stream")
            content_encoding = response.headers.get("content-encoding", "")
            
            headers = {
                "Content-Type": content_type,
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, HEAD, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type"
            }
            
            # Forward Content-Encoding if present
            if content_encoding:
                headers["Content-Encoding"] = content_encoding
                
            return Response(headers=headers)
            
    except Exception as e:
        logger.error(f"Error in HEAD request: {str(e)}")
        raise HTTPException(status_code=500, detail="Error checking content type")

@router.options("/proxy-pdf")
async def proxy_pdf_options():
    """Handle CORS preflight requests"""
    return Response(
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, HEAD, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type"
        }
    )

@router.get("/proxy-html")
async def proxy_html(url: str):
    """
    Proxy HTML content and sanitize it for safe rendering
    """
    try:
        # Validate URL domain and handle special cases
        from urllib.parse import urlparse, parse_qs, quote
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        
        # Handle Europe PMC specific URL patterns - use their API
        if 'europepmc.org' in domain:
            # Extract PMC ID from URL and use Europe PMC REST API
            pmc_match = re.search(r'PMC(\d+)', url)
            if pmc_match:
                pmc_id = f"PMC{pmc_match.group(1)}"
                # Use Europe PMC REST API for full text
                api_url = f"https://www.ebi.ac.uk/europepmc/webservices/rest/{pmc_id}/fullTextXML"
                logger.info(f"Europe PMC: Using API URL {api_url} for PMC ID {pmc_id}")
                
                # Try to get XML full text from API
                try:
                    async with httpx.AsyncClient(follow_redirects=True, timeout=30.0) as api_client:
                        api_response = await api_client.get(api_url, headers={
                            "User-Agent": "Mozilla/5.0 (compatible; OpenScholar/1.0)",
                            "Accept": "application/xml"
                        })
                        if api_response.status_code == 200:
                            # Convert XML to HTML
                            from xml.etree import ElementTree as ET
                            try:
                                root = ET.fromstring(api_response.content)
                                
                                def get_text_content(elem):
                                    """Recursively extract text content from XML element"""
                                    if elem is None:
                                        return ""
                                    
                                    text = elem.text or ""
                                    for child in elem:
                                        text += get_text_content(child)
                                        if child.tail:
                                            text += child.tail
                                    return text
                                
                                def clean_mathematical_notation(text):
                                    """Clean up LaTeX and mathematical notation artifacts"""
                                    
                                    # Remove LaTeX document class declarations
                                    text = re.sub(r'\\documentclass\[.*?\]\{minimal\}.*?\\begin\{document\}', '', text, flags=re.DOTALL)
                                    text = re.sub(r'\\end\{document\}', '', text)
                                    text = re.sub(r'\\usepackage\{.*?\}', '', text)
                                    text = re.sub(r'\\setlength\{.*?\}\{.*?\}', '', text)
                                    
                                    # Clean up common LaTeX commands
                                    text = re.sub(r'\\beta\s*', 'β', text)
                                    text = re.sub(r'\\alpha\s*', 'α', text)
                                    text = re.sub(r'\\gamma\s*', 'γ', text)
                                    text = re.sub(r'\\eta\s*', 'η', text)
                                    text = re.sub(r'\\times\s*', '×', text)
                                    text = re.sub(r'\\pm\s*', '±', text)
                                    text = re.sub(r'\\sigma\s*', 'σ', text)
                                    text = re.sub(r'\\mu\s*', 'μ', text)
                                    text = re.sub(r'\\lambda\s*', 'λ', text)
                                    text = re.sub(r'\\theta\s*', 'θ', text)
                                    text = re.sub(r'\\phi\s*', 'φ', text)
                                    text = re.sub(r'\\delta\s*', 'δ', text)
                                    text = re.sub(r'\\epsilon\s*', 'ε', text)
                                    text = re.sub(r'\\zeta\s*', 'ζ', text)
                                    text = re.sub(r'\\kappa\s*', 'κ', text)
                                    text = re.sub(r'\\rho\s*', 'ρ', text)
                                    text = re.sub(r'\\tau\s*', 'τ', text)
                                    text = re.sub(r'\\omega\s*', 'ω', text)
                                    text = re.sub(r'\\Omega\s*', 'Ω', text)
                                    text = re.sub(r'\\Pi\s*', 'Π', text)
                                    text = re.sub(r'\\Sigma\s*', 'Σ', text)
                                    
                                    # Clean up mathematical expressions
                                    text = re.sub(r'\$([^$]+)\$', r'\1', text)  # Remove single $ delimiters
                                    text = re.sub(r'\\begin\{document\}.*?\\end\{document\}', '', text, flags=re.DOTALL)
                                    
                                    # Clean up superscripts and subscripts
                                    text = re.sub(r'\^\{([^}]+)\}', r'^\1', text)
                                    text = re.sub(r'_\{([^}]+)\}', r'_\1', text)
                                    
                                    # Remove excessive whitespace
                                    text = re.sub(r'\s+', ' ', text)
                                    text = text.strip()
                                    
                                    return text
                                
                                # Create HTML structure from XML with enhanced styling
                                html_content = "<html><head><style>"
                                html_content += """
                                /* Reset and base styles */
                                * { box-sizing: border-box; }
                                body { 
                                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
                                    line-height: 1.6;
                                    color: #333;
                                    margin: 0;
                                    padding: 0;
                                }
                                
                                /* Typography */
                                h1, h2, h3, h4, h5, h6 { margin-top: 1.5em; margin-bottom: 0.5em; }
                                p { margin: 1em 0; line-height: 1.6; }
                                
                                /* Links */
                                a { color: #0066cc; text-decoration: none; }
                                a:hover { text-decoration: underline; }
                                
                                /* Images */
                                img { 
                                    max-width: 100%; 
                                    height: auto; 
                                    display: block; 
                                    margin: 1.5em auto;
                                    border-radius: 4px;
                                    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                                }
                                figure { 
                                    margin: 2em 0; 
                                    text-align: center;
                                    background: #f9f9f9;
                                    padding: 1em;
                                    border-radius: 4px;
                                }
                                figcaption { 
                                    font-size: 0.9em; 
                                    color: #666; 
                                    margin-top: 0.75em;
                                    font-style: italic;
                                    line-height: 1.4;
                                }
                                
                                /* Tables */
                                table { border-collapse: collapse; width: 100%; margin: 1em 0; }
                                th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
                                th { background-color: #f5f5f5; font-weight: bold; }
                                tr:nth-child(even) { background-color: #f9f9f9; }
                                
                                /* Lists */
                                ul, ol { margin: 1em 0; padding-left: 2em; }
                                li { margin: 0.5em 0; }
                                
                                /* Blockquotes */
                                blockquote { 
                                    border-left: 4px solid #ddd; 
                                    margin: 1em 0; 
                                    padding-left: 1em; 
                                    color: #666;
                                    font-style: italic;
                                }
                                
                                /* Code */
                                code { 
                                    background: #f5f5f5; 
                                    padding: 2px 4px; 
                                    border-radius: 3px; 
                                    font-family: 'Courier New', monospace;
                                }
                                pre { 
                                    background: #f5f5f5; 
                                    padding: 1em; 
                                    border-radius: 4px; 
                                    overflow-x: auto;
                                }
                                
                                /* Academic paper specific */
                                .pmc-article-content { max-width: 900px; margin: 0 auto; }
                                .tsec, .sec, section { margin: 2em 0; }
                                .title { font-size: 1.2em; font-weight: 600; margin: 1em 0 0.5em 0; }
                                .fm-author, .contrib-group { 
                                    margin: 1em 0; 
                                    color: #555;
                                    font-size: 0.95em;
                                }
                                .abstract, .abstractSection { 
                                    background: #f8f9fa;
                                    padding: 1.5em;
                                    border-radius: 8px;
                                    margin: 2em 0;
                                    border-left: 4px solid #0066cc;
                                }
                                .xref { 
                                    color: #0066cc; 
                                    text-decoration: none;
                                    font-size: 0.85em;
                                }
                                sup { 
                                    font-size: 0.75em; 
                                    vertical-align: super;
                                }
                                
                                /* Clean up extra spacing */
                                p:empty { display: none; }
                                br + br { display: none; }
                                """
                                html_content += "</style></head><body>"
                                
                                # Extract title
                                title_elem = root.find('.//article-title')
                                if title_elem is not None:
                                    title_text = get_text_content(title_elem).strip()
                                    title_text = clean_mathematical_notation(title_text)
                                    html_content += f"<h1>{title_text}</h1>"
                                
                                # Extract abstract
                                abstract_elem = root.find('.//abstract')
                                if abstract_elem is not None:
                                    html_content += '<div class="abstract"><h2>Abstract</h2>'
                                    for p in abstract_elem.findall('.//p'):
                                        p_text = get_text_content(p).strip()
                                        if p_text:
                                            p_text = clean_mathematical_notation(p_text)
                                            html_content += f"<p>{p_text}</p>"
                                    html_content += "</div>"
                                
                                # Extract body sections
                                body_elem = root.find('.//body')
                                if body_elem is not None:
                                    for sec in body_elem.findall('.//sec'):
                                        sec_title = sec.find('./title')
                                        if sec_title is not None:
                                            title_text = get_text_content(sec_title).strip()
                                            title_text = clean_mathematical_notation(title_text)
                                            html_content += f"<h2>{title_text}</h2>"
                                        
                                        for p in sec.findall('.//p'):
                                            p_text = get_text_content(p).strip()
                                            if p_text and len(p_text) > 10:  # Filter out very short fragments
                                                p_text = clean_mathematical_notation(p_text)
                                                html_content += f"<p>{p_text}</p>"
                                        
                                        # Process tables
                                        for table in sec.findall('.//table-wrap'):
                                            table_caption = table.find('.//caption')
                                            if table_caption is not None:
                                                caption_text = get_text_content(table_caption).strip()
                                                caption_text = clean_mathematical_notation(caption_text)
                                                html_content += f'<div style="font-weight: 600; margin: 1em 0;">{caption_text}</div>'
                                            
                                            table_elem = table.find('.//table')
                                            if table_elem is not None:
                                                html_content += '<table>'
                                                thead = table_elem.find('.//thead')
                                                if thead is not None:
                                                    html_content += '<thead>'
                                                    for tr in thead.findall('.//tr'):
                                                        html_content += '<tr>'
                                                        for th in tr.findall('.//th'):
                                                            cell_text = get_text_content(th).strip()
                                                            cell_text = clean_mathematical_notation(cell_text)
                                                            html_content += f'<th>{cell_text}</th>'
                                                        html_content += '</tr>'
                                                    html_content += '</thead>'
                                                
                                                tbody = table_elem.find('.//tbody')
                                                if tbody is not None:
                                                    html_content += '<tbody>'
                                                    for tr in tbody.findall('.//tr'):
                                                        html_content += '<tr>'
                                                        for td in tr.findall('.//td'):
                                                            cell_text = get_text_content(td).strip()
                                                            cell_text = clean_mathematical_notation(cell_text)
                                                            html_content += f'<td>{cell_text}</td>'
                                                        html_content += '</tr>'
                                                    html_content += '</tbody>'
                                                html_content += '</table>'
                                        
                                        # Process figures
                                        for fig in sec.findall('.//fig'):
                                            html_content += '<figure>'
                                            graphic = fig.find('.//graphic')
                                            if graphic is not None:
                                                href = graphic.get('{http://www.w3.org/1999/xlink}href')
                                                if href:
                                                    # Fix Europe PMC image URLs
                                                    if not href.startswith('http'):
                                                        # Remove _HTML suffix and add proper image extension
                                                        if href.endswith('_HTML'):
                                                            href = href.replace('_HTML', '')
                                                        # Europe PMC serves images as JPG
                                                        if not href.endswith(('.jpg', '.jpeg', '.png', '.gif')):
                                                            href = href + '.jpg'
                                                        # Construct full URL - Europe PMC uses specific image paths
                                                        href = f"https://europepmc.org/articles/{pmc_id}/bin/{href}"
                                                    # URL encode for proxy
                                                    encoded_url = quote(href, safe='')
                                                    html_content += f'<img src="/api/proxy-image?url={encoded_url}" alt="Figure" loading="lazy">'
                                            
                                            caption = fig.find('.//caption')
                                            if caption is not None:
                                                caption_text = get_text_content(caption).strip()
                                                caption_text = clean_mathematical_notation(caption_text)
                                                html_content += f'<figcaption>{caption_text}</figcaption>'
                                            html_content += '</figure>'
                                
                                html_content += "</body></html>"
                                
                                # Check if we got substantial content
                                content_length = len([p for p in html_content.split('<p>') if len(p.strip()) > 50])
                                if content_length > 3:  # If we have substantial content
                                    # Return the converted content
                                    return JSONResponse({
                                        "success": True,
                                        "url": url,
                                        "title": title_text if title_elem is not None else "Europe PMC Article",
                                        "content": html_content,
                                        "contentType": "html"
                                    }, headers={
                                        "Access-Control-Allow-Origin": "*",
                                        "Access-Control-Allow-Methods": "GET, OPTIONS",
                                        "Access-Control-Allow-Headers": "Content-Type"
                                    })
                                else:
                                    logger.info(f"Europe PMC API returned minimal content for {pmc_id}, falling back to HTML scraping")
                                
                            except ET.ParseError:
                                logger.warning(f"Failed to parse Europe PMC XML for {pmc_id}")
                        
                except Exception as e:
                    logger.warning(f"Failed to fetch from Europe PMC API: {e}")
                    # Fall back to regular HTML scraping
            
            # If API fails or no PMC ID found, try HTML parameters
            if '/articles/' in url and 'fullTextType=' not in url:
                url += '&fullTextType=HTML' if '?' in url else '?fullTextType=HTML'
            logger.info(f"Europe PMC URL adjusted to: {url}")
        
        # Check if domain is allowed (skip in dev mode for testing)
        if not DEV_MODE and not any(allowed in domain for allowed in ALLOWED_DOMAINS):
            logger.warning(f"Domain not in allowed list: {domain}")
            raise HTTPException(
                status_code=403, 
                detail=f"Domain '{domain}' not allowed for proxy. Please contact support to add this domain."
            )
        
        if DEV_MODE and not any(allowed in domain for allowed in ALLOWED_DOMAINS):
            logger.info(f"DEV MODE: Allowing unlisted domain: {domain}")
        
        # Fetch the HTML content with browser-like headers
        browser_headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Cache-Control": "max-age=0"
        }
        
        # Add referer for certain sites that check it
        if 'europepmc.org' in domain:
            browser_headers["Referer"] = "https://europepmc.org/"
        elif 'pubmed' in domain:
            browser_headers["Referer"] = "https://pubmed.ncbi.nlm.nih.gov/"
        
        async with httpx.AsyncClient(follow_redirects=True, timeout=30.0) as client:
            response = await client.get(url, headers=browser_headers)
            response.raise_for_status()
            
            # Parse and sanitize HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Remove script, style, and other unnecessary tags first
            for tag in soup.find_all(['script', 'style', 'noscript', 'header', 'footer', 'nav']):
                tag.decompose()
            
            # Remove PMC-specific navigation and sidebar elements
            for elem in soup.select('.ncbi-alerts, .search-input, .pmc-sidebar, .usa-banner, .jig-ncbiheader, .jig-ncbifooter, .epmc-header, .epmc-footer, .epmc-nav'):
                elem.decompose()
            
            # Remove Europe PMC specific navigation elements
            for elem in soup.select('[class*="nav"], [class*="menu"], [class*="header"], [class*="footer"], [id*="header"], [id*="footer"], [id*="nav"]'):
                # Be careful not to remove article headers
                if not any(word in elem.get_text().lower() for word in ['abstract', 'introduction', 'method', 'result', 'conclusion', 'reference', 'author', 'title']):
                    elem.decompose()
            
            # Extract metadata
            title = soup.title.string if soup.title else "Document"
            
            # Try PMC-specific selectors first (for academic papers)
            pmc_selectors = [
                '.jig-ncbiinpagenav',  # PMC article body
                '#mc',  # PMC main content  
                '.article-box',  # PMC article container
                'div.tsec',  # PMC sections
                '.article-full-text',  # Full text section
                'div[id^="sec-"]',  # Section divs
                '.body',  # Article body
                # Europe PMC specific
                '#free-full-text',  # Europe PMC main article
                '.article-browse',  # Europe PMC article container
                '#abstract-1',  # Europe PMC abstract
                '#maincontent',  # Europe PMC main content
                '.TextLayer',  # Europe PMC text layer
            ]
            
            # Then try general article selectors
            general_selectors = [
                'article', 
                'main', 
                '[role="main"]',
                '.content', 
                '#content', 
                '.article-content', 
                '.post-content', 
                '.entry-content',
                '.main-content',
                '#main-content',
                '.body-content',
                '.page-content'
            ]
            
            main_content = None
            
            # Try PMC selectors first
            for selector in pmc_selectors:
                elements = soup.select(selector)
                if elements:
                    # Combine all matching elements for PMC
                    combined_div = soup.new_tag('div')
                    combined_div['class'] = ['pmc-article-content']
                    
                    # Add title if found
                    title_elem = soup.select_one('h1.content-title, .article-title, h1')
                    if title_elem and title_elem not in elements:
                        combined_div.append(title_elem)
                    
                    # Add authors if found (Europe PMC uses different selectors)
                    authors = soup.select('.contrib-group, .fm-author, .authors, .authorlist, .author-list')
                    for author in authors:
                        if author not in elements:
                            combined_div.append(author)
                    
                    # Add abstract if found (Europe PMC specific)
                    abstract = soup.select_one('.abstract, .abstractSection, #abstract, .abs')
                    if abstract and abstract not in elements:
                        combined_div.append(abstract)
                    
                    # Add keywords if found
                    keywords = soup.select_one('.keywords, .kwd-group, .keyword-group')
                    if keywords and keywords not in elements:
                        combined_div.append(keywords)
                    
                    # Add all content elements
                    for elem in elements:
                        combined_div.append(elem)
                    
                    main_content = combined_div
                    break
            
            # If no PMC content, try general selectors
            if not main_content:
                for selector in general_selectors:
                    main_content = soup.select_one(selector)
                    if main_content:
                        break
            
            # If still no main content, try to be smarter
            if not main_content:
                # Look for the largest text-containing div
                all_divs = soup.find_all('div')
                best_div = None
                max_text_length = 0
                
                for div in all_divs:
                    # Skip navigation, header, footer, sidebar
                    if div.get('id') and any(skip in div.get('id', '').lower() for skip in ['nav', 'header', 'footer', 'sidebar', 'menu']):
                        continue
                    if div.get('class') and any(skip in ' '.join(div.get('class', [])).lower() for skip in ['nav', 'header', 'footer', 'sidebar', 'menu']):
                        continue
                    
                    text_length = len(div.get_text(strip=True))
                    if text_length > max_text_length:
                        max_text_length = text_length
                        best_div = div
                
                # If the best div is still too small, just use body content
                if not best_div or max_text_length < 500:
                    # For Europe PMC and other sites that might have minimal content
                    # Try to extract all meaningful paragraphs
                    meaningful_content = soup.new_tag('div')
                    meaningful_content['class'] = ['extracted-content']
                    
                    # Add title
                    title_elem = soup.select_one('h1, .title, [class*="title"]')
                    if title_elem:
                        meaningful_content.append(title_elem)
                    
                    # Add all paragraphs with substantial text
                    for p in soup.find_all(['p', 'div', 'section']):
                        text = p.get_text(strip=True)
                        if len(text) > 50 and not any(skip in text.lower() for skip in ['cookie', 'javascript', 'browser', 'enable']):
                            meaningful_content.append(p)
                    
                    main_content = meaningful_content if len(meaningful_content.get_text(strip=True)) > 200 else (best_div or soup.body or soup)
                else:
                    main_content = best_div
            
            # Just convert relative URLs to absolute - client will handle proxying
            if main_content:
                from urllib.parse import urljoin
                
                for img in main_content.find_all('img'):
                    src = img.get('src')
                    if src and not src.startswith(('http://', 'https://', '//', 'data:')):
                        # Convert relative URLs to absolute
                        img['src'] = urljoin(url, src)
                
                # Process links to use absolute URLs
                for link in main_content.find_all('a'):
                    href = link.get('href')
                    if href and not href.startswith(('http://', 'https://', '#', 'mailto:', 'javascript:')):
                        from urllib.parse import urljoin
                        link['href'] = urljoin(url, href)
            
            # Clean up PMC-specific artifacts in the content
            if main_content:
                # Remove "Search in PMC", "Add to search" etc.
                for elem in main_content.find_all(text=re.compile(r'(Search in PMC|Search in PubMed|View in NLM Catalog|Add to search|Find articles by)')):
                    parent = elem.parent
                    if parent and parent.name in ['a', 'button', 'span', 'div']:
                        parent.decompose()
                
                # Remove empty links and buttons
                for elem in main_content.find_all(['a', 'button']):
                    if not elem.get_text(strip=True):
                        elem.decompose()
                
                # Clean up author affiliations that are just numbers
                for elem in main_content.find_all(text=re.compile(r'^\d+,?\s*$')):
                    if elem.parent and elem.parent.name in ['sup', 'span']:
                        elem.parent.decompose()
            
            # Enhanced HTML sanitization
            allowed_tags = [
                'p', 'br', 'span', 'div', 'section', 'article',
                'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
                'ul', 'ol', 'li', 'dl', 'dt', 'dd',
                'a', 'strong', 'b', 'em', 'i', 'u', 'code', 'pre', 
                'blockquote', 'cite', 'q',
                'table', 'thead', 'tbody', 'tfoot', 'tr', 'td', 'th', 'caption',
                'img', 'figure', 'figcaption',
                'sup', 'sub', 'small', 'mark', 'del', 'ins',
                'hr', 'abbr', 'time'
            ]
            allowed_attributes = {
                'a': ['href', 'title', 'target', 'rel'],
                'img': ['src', 'alt', 'title', 'width', 'height'],
                'td': ['colspan', 'rowspan'],
                'th': ['colspan', 'rowspan'],
                'time': ['datetime'],
                'abbr': ['title'],
                '*': ['class', 'id', 'style']
            }
            
            # Clean but preserve more styling
            clean_html = bleach.clean(
                str(main_content),
                tags=allowed_tags,
                attributes=allowed_attributes,
                strip=True,
                protocols=['http', 'https', 'mailto', 'data']
            )
            
            # Add custom CSS for better rendering
            custom_css = """
            <style>
                /* Reset and base styles */
                * { box-sizing: border-box; }
                body { 
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    margin: 0;
                    padding: 0;
                }
                
                /* Typography */
                h1, h2, h3, h4, h5, h6 { margin-top: 1.5em; margin-bottom: 0.5em; }
                p { margin: 1em 0; line-height: 1.6; }
                
                /* Links */
                a { color: #0066cc; text-decoration: none; }
                a:hover { text-decoration: underline; }
                
                /* Images */
                img { 
                    max-width: 100%; 
                    height: auto; 
                    display: block; 
                    margin: 1.5em auto;
                    border-radius: 4px;
                    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                }
                figure { 
                    margin: 2em 0; 
                    text-align: center;
                    background: #f9f9f9;
                    padding: 1em;
                    border-radius: 4px;
                }
                figcaption { 
                    font-size: 0.9em; 
                    color: #666; 
                    margin-top: 0.75em;
                    font-style: italic;
                    line-height: 1.4;
                }
                
                /* Tables */
                table { border-collapse: collapse; width: 100%; margin: 1em 0; }
                th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
                th { background-color: #f5f5f5; font-weight: bold; }
                tr:nth-child(even) { background-color: #f9f9f9; }
                
                /* Lists */
                ul, ol { margin: 1em 0; padding-left: 2em; }
                li { margin: 0.5em 0; }
                
                /* Blockquotes */
                blockquote { 
                    border-left: 4px solid #ddd; 
                    margin: 1em 0; 
                    padding-left: 1em; 
                    color: #666;
                    font-style: italic;
                }
                
                /* Code */
                code { 
                    background: #f5f5f5; 
                    padding: 2px 4px; 
                    border-radius: 3px; 
                    font-family: 'Courier New', monospace;
                }
                pre { 
                    background: #f5f5f5; 
                    padding: 1em; 
                    border-radius: 4px; 
                    overflow-x: auto;
                }
                
                /* Academic paper specific */
                .pmc-article-content { max-width: 900px; margin: 0 auto; }
                .tsec, .sec, section { margin: 2em 0; }
                .title { font-size: 1.2em; font-weight: 600; margin: 1em 0 0.5em 0; }
                .fm-author, .contrib-group { 
                    margin: 1em 0; 
                    color: #555;
                    font-size: 0.95em;
                }
                .abstract, .abstractSection { 
                    background: #f8f9fa;
                    padding: 1.5em;
                    border-radius: 8px;
                    margin: 2em 0;
                    border-left: 4px solid #0066cc;
                }
                .xref { 
                    color: #0066cc; 
                    text-decoration: none;
                    font-size: 0.85em;
                }
                sup { 
                    font-size: 0.75em; 
                    vertical-align: super;
                }
                
                /* Clean up extra spacing */
                p:empty { display: none; }
                br + br { display: none; }
                
                /* Author styling */
                .contrib-group a { 
                    color: #555; 
                    text-decoration: none;
                    font-weight: 500;
                }
                
                /* Keywords and metadata */
                .kwd-group { 
                    margin: 1em 0;
                    padding: 1em;
                    background: #f0f4f8;
                    border-radius: 4px;
                }
                .kwd { 
                    display: inline-block;
                    margin: 0.2em 0.5em 0.2em 0;
                    padding: 0.3em 0.8em;
                    background: #e1e8ed;
                    border-radius: 3px;
                    font-size: 0.9em;
                }
                
                /* Reference formatting */
                .ref-list { 
                    font-size: 0.9em;
                    line-height: 1.5;
                }
                .ref-list li { 
                    margin-bottom: 0.8em;
                }
                
                /* Figure and image specific for academic papers */
                .fig { 
                    margin: 2em 0;
                    padding: 1em;
                    background: #f9fafb;
                    border: 1px solid #e5e7eb;
                    border-radius: 8px;
                }
                .fig img {
                    box-shadow: none;
                    margin: 1em auto;
                }
                .fig-caption, .caption {
                    text-align: left;
                    font-size: 0.9em;
                    line-height: 1.5;
                    color: #4b5563;
                    margin-top: 1em;
                }
                
                /* Equation and formula styling */
                .disp-formula, .inline-formula {
                    margin: 1.5em 0;
                    text-align: center;
                    font-family: 'Times New Roman', serif;
                }
                
                /* Inline graphics (often equations) */
                .inline-graphic {
                    display: inline-block;
                    vertical-align: middle;
                    margin: 0 0.2em;
                }
                
                /* Supplementary material links */
                .supplementary-material {
                    background: #eff6ff;
                    padding: 0.5em 1em;
                    border-radius: 4px;
                    margin: 1em 0;
                    border-left: 3px solid #2563eb;
                }
                
                /* Hide unnecessary elements */
                .pmc-sidebar, .usa-banner, .ncbi-alerts, .search-input,
                .jig-ncbiheader, .jig-ncbifooter, .copyright, 
                [id*="author-notes"], .author-notes,
                .object-id, .related-links, .article-meta .permissions,
                .pmc-logo, .ncbi-logo { 
                    display: none !important; 
                }
            </style>
            """
            
            # Wrap the content with styling
            clean_html = custom_css + clean_html
            
            # Return sanitized HTML with metadata
            return JSONResponse({
                "success": True,
                "url": url,
                "title": soup.title.string if soup.title else "Document",
                "content": clean_html,
                "contentType": "html"
            }, headers={
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type"
            })
            
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="HTML fetch timeout")
    except httpx.RequestError as e:
        logger.error(f"Error fetching HTML: {str(e)}")
        raise HTTPException(status_code=502, detail=f"Error fetching HTML: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error in HTML proxy: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.options("/proxy-html")
async def proxy_html_options():
    """Handle CORS preflight requests"""
    return Response(
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type"
        }
    )

@router.get("/proxy-image")
async def proxy_image(url: str):
    """
    Proxy image requests to handle CORS and blocked content
    """
    try:
        # Validate URL domain
        from urllib.parse import urlparse
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        
        # For images, be more lenient with domain checking
        # Just log if not in allowed list but continue anyway
        if not any(allowed in domain for allowed in ALLOWED_DOMAINS):
            logger.info(f"Image domain not in allowed list but proceeding: {domain}")
        
        # Fetch the image
        async with httpx.AsyncClient(follow_redirects=True, timeout=30.0) as client:
            response = await client.get(url, headers={
                "User-Agent": "Mozilla/5.0 (compatible; OpenScholar/1.0)",
                "Accept": "image/*"
            })
            response.raise_for_status()
            
            # Determine content type
            content_type = response.headers.get("Content-Type", "image/jpeg")
            
            # Return the image with proper headers
            return Response(
                content=response.content,
                media_type=content_type,
                headers={
                    "Cache-Control": "public, max-age=86400",  # Cache for 1 day
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Methods": "GET, OPTIONS",
                    "Access-Control-Allow-Headers": "Content-Type"
                }
            )
            
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Image fetch timeout")
    except httpx.RequestError as e:
        logger.error(f"Error fetching image: {str(e)}")
        raise HTTPException(status_code=502, detail=f"Error fetching image: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error in image proxy: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.options("/proxy-image")
async def proxy_image_options():
    """Handle CORS preflight requests for images"""
    return Response(
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type"
        }
    )