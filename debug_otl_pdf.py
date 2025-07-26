#!/usr/bin/env python3
"""Debug OTL PDF URL extraction"""

import httpx
import asyncio
from bs4 import BeautifulSoup
import re

async def debug_pdf_extraction():
    async with httpx.AsyncClient() as client:
        # Test with a specific book page
        book_url = "https://open.umn.edu/opentextbooks/textbooks/calculus"
        
        print(f"Fetching: {book_url}")
        response = await client.get(book_url)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Save for inspection
            with open("otl_book_page.html", "w") as f:
                f.write(response.text)
            
            print("\n1. Looking for PDF links ending with .pdf:")
            pdf_links = soup.find_all('a', href=re.compile(r'\.pdf$', re.IGNORECASE))
            print(f"   Found {len(pdf_links)} direct PDF links")
            for link in pdf_links[:3]:
                print(f"   - {link.get('href', 'No href')}")
            
            print("\n2. Looking for download section:")
            download_section = soup.find('div', class_='downloads')
            print(f"   Download section found: {download_section is not None}")
            
            print("\n3. Looking for any download links:")
            # Try different selectors
            selectors = [
                ('a', {'class': 'download'}),
                ('a', {'class': 'btn-download'}),
                ('a', {'title': re.compile(r'download', re.IGNORECASE)}),
                ('div', {'class': 'book-formats'}),
                ('section', {'class': 'downloads'}),
            ]
            
            # Also check for links with specific text
            pdf_text_links = soup.find_all('a', string=re.compile(r'PDF', re.IGNORECASE))
            if pdf_text_links:
                print(f"\n   Found {len(pdf_text_links)} links with 'PDF' text")
                for link in pdf_text_links[:3]:
                    print(f"   - Text: {link.get_text(strip=True)}")
                    print(f"     Href: {link.get('href', 'No href')}")
            
            for tag, attrs in selectors:
                elements = soup.find_all(tag, attrs)
                if elements:
                    print(f"\n   Found {len(elements)} elements with {tag} {attrs}")
                    for elem in elements[:2]:
                        if tag == 'a':
                            print(f"     - Text: {elem.get_text(strip=True)}")
                            print(f"       Href: {elem.get('href', 'No href')}")
                        else:
                            print(f"     - Content preview: {str(elem)[:200]}...")
            
            print("\n4. Looking for format/download related content:")
            # Search for any text mentioning formats
            for text in soup.find_all(string=re.compile(r'(PDF|Download|Format)', re.IGNORECASE)):
                parent = text.parent
                if parent and parent.name == 'a':
                    print(f"\n   Found link with text: {text.strip()}")
                    print(f"   Href: {parent.get('href', 'No href')}")

if __name__ == "__main__":
    asyncio.run(debug_pdf_extraction())