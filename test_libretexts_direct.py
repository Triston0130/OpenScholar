#!/usr/bin/env python3
"""Test LibreTexts direct PDF download"""

import asyncio
import httpx
from bs4 import BeautifulSoup

async def test_libretexts_download():
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Test the specific accounting book
        book_url = "https://biz.libretexts.org/Bookshelves/Accounting/Accounting_in_the_Finance_World"
        
        # Also test from a chapter to see if we get different results
        chapter_url = "https://biz.libretexts.org/Bookshelves/Accounting/Accounting_in_the_Finance_World/01%3A_Why_Is_Financial_Accounting_Important"
        
        print(f"Testing: {book_url}")
        response = await client.get(book_url)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Look for download links
        print("\nLooking for download links...")
        for link in soup.find_all('a'):
            href = link.get('href', '')
            text = link.get_text(strip=True)
            
            if any(word in text.lower() for word in ['download', 'pdf', 'full', 'complete']):
                print(f"Found: '{text}' -> {href}")
        
        # Try the downloadfull URL from this specific book
        full_url = f"{book_url}?downloadfull"
        print(f"\nTesting: {full_url}")
        try:
            dl_response = await client.get(full_url, follow_redirects=True)
            content_type = dl_response.headers.get('content-type', 'unknown')
            print(f"Response: {content_type} {dl_response.status_code}")
            print(f"Final URL: {dl_response.url}")
            
            if 'pdf' in content_type:
                print("✓ Found PDF!")
            else:
                print("✗ Not a PDF")
                
                # Look for PDF links in the download page
                dl_soup = BeautifulSoup(dl_response.text, 'html.parser')
                for link in dl_soup.find_all('a', href=True):
                    href = link.get('href', '')
                    if '@api/deki' in href and 'pdf' in href:
                        print(f"Found API PDF link: {href}")
                        
                        # Test this API link
                        if not href.startswith('http'):
                            href = f"https://biz.libretexts.org{href}"
                        api_response = await client.get(href)
                        api_content_type = api_response.headers.get('content-type', 'unknown')
                        print(f"API response: {api_content_type} ({len(api_response.content)} bytes)")
                
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_libretexts_download())