#\!/usr/bin/env python3
"""Debug OTL format page"""

import httpx
import asyncio
from bs4 import BeautifulSoup

async def debug_format_page():
    async with httpx.AsyncClient() as client:
        # First get the book page
        book_url = "https://open.umn.edu/opentextbooks/textbooks/calculus"
        response = await client.get(book_url)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find the format link
        format_section = soup.find('section', id='Formats')
        if format_section:
            pdf_link = format_section.find('a', string='PDF')
            if pdf_link:
                format_url = pdf_link['href']
                if not format_url.startswith('http'):
                    format_url = f"https://open.umn.edu{format_url}"
                
                print(f"Format URL: {format_url}")
                
                # Follow the format link
                format_response = await client.get(format_url, follow_redirects=True)
                print(f"Format page status: {format_response.status_code}")
                print(f"Final URL: {format_response.url}")
                print(f"Content-Type: {format_response.headers.get('content-type', 'unknown')}")
                
                # Check if it's a PDF
                if 'application/pdf' in format_response.headers.get('content-type', ''):
                    print("\nThis IS a direct PDF link\!")
                else:
                    print("\nNot a direct PDF, checking page content...")
                    format_soup = BeautifulSoup(format_response.text, 'html.parser')
                    
                    # Look for download links
                    download_links = format_soup.find_all('a', href=True)
                    for link in download_links:
                        href = link['href']
                        text = link.get_text(strip=True)
                        if 'download' in text.lower() or 'pdf' in href.lower():
                            print(f"   Found: {text} -> {href}")

if __name__ == "__main__":
    asyncio.run(debug_format_page())
