# app/api_clients/open_textbook_library.py
from typing import List, Optional
from app.models import Paper
from .http import fetch_json
import logging
import httpx
from bs4 import BeautifulSoup
import asyncio

logger = logging.getLogger(__name__)

class OpenTextbookLibraryClient:
    _URL = "https://open.umn.edu/opentextbooks/textbooks.json"
    
    async def _fetch_pdf_url(self, landing_page_url: str) -> Optional[str]:
        """Fetch the direct PDF URL from a book's landing page"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(landing_page_url)
                response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Look for PDF download link
            # OTL uses links like /opentextbooks/formats/XXX for PDFs
            pdf_links = soup.find_all('a', href=True)
            for link in pdf_links:
                href = link.get('href', '')
                text = link.get_text(strip=True).lower()
                
                # Check if this is a PDF download link
                if 'pdf' in text and '/opentextbooks/formats/' in href:
                    # Convert relative URL to absolute
                    if href.startswith('/'):
                        return f"https://open.umn.edu{href}"
                    return href
            
            # Fallback: look for any link with .pdf extension
            for link in pdf_links:
                href = link.get('href', '')
                if href.endswith('.pdf'):
                    if href.startswith('/'):
                        return f"https://open.umn.edu{href}"
                    elif not href.startswith('http'):
                        return f"https://open.umn.edu/{href}"
                    return href
            
            return None
            
        except Exception as e:
            logger.warning(f"Failed to fetch PDF URL from {landing_page_url}: {e}")
            return None

    async def search(self, query: str, max_results: int = 20) -> List[Paper]:
        try:
            data = await fetch_json(self._URL)
            
            # Search in title, description, and subjects
            query_lower = query.lower()
            hits = []
            
            for book in data.get("data", []):
                # Check title
                title = book.get("title", "").lower()
                description = book.get("description", "").lower()
                
                # Check subjects
                subjects_match = False
                for subject in book.get("subjects", []):
                    if query_lower in subject.get("name", "").lower():
                        subjects_match = True
                        break
                
                if query_lower in title or query_lower in description or subjects_match:
                    hits.append(book)
                    
                if len(hits) >= max_results:
                    break

            papers = []
            for b in hits:
                # Extract authors from contributors
                authors = []
                for contrib in b.get("contributors", []):
                    if contrib.get("contribution") in ["Author", "Editor"]:
                        # Build full name from parts
                        first = contrib.get("first_name", "")
                        middle = contrib.get("middle_name", "")
                        last = contrib.get("last_name", "")
                        
                        name_parts = [first, middle, last]
                        full_name = " ".join(part for part in name_parts if part)
                        
                        if full_name:
                            authors.append(full_name)
                
                if not authors:
                    authors = ["Open Textbook Library"]
                
                # Extract subjects
                subjects = [s.get("name", "") for s in b.get("subjects", [])]
                
                # Get landing page URL
                landing_page_url = f"https://open.umn.edu/opentextbooks/textbooks/{b.get('id', '')}"
                
                # Fetch direct PDF URL from landing page
                pdf_url = await self._fetch_pdf_url(landing_page_url)
                
                # Use PDF URL if found, otherwise fallback to landing page
                full_text_url = pdf_url if pdf_url else landing_page_url
                
                paper = Paper(
                    title=b.get("title", "Untitled"),
                    authors=authors,
                    year=str(b.get("copyright_year", "")) if b.get("copyright_year") else None,
                    abstract=b.get("description", ""),
                    full_text_url=full_text_url,
                    source="Open Textbook Library",
                    journal="Open Textbook Library",
                    content_type="book",
                    subjects=subjects,
                    license=b.get("license", "CC BY"),
                    download_formats=["PDF", "EPUB", "Online"]
                )
                papers.append(paper)
                
            logger.info(f"Open Textbook Library: Found {len(papers)} results for '{query}'")
            return papers
            
        except Exception as e:
            logger.error(f"Open Textbook Library search failed: {e}")
            return []