#!/usr/bin/env python3
"""Check if OTL has a direct PDF pattern"""

import httpx
import asyncio
from bs4 import BeautifulSoup

async def check_otl_pdf_pattern():
    # Check the landing page for Book of Proof
    url = "https://open.umn.edu/opentextbooks/textbooks/7"
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        print(f"Checking landing page: {url}")
        print("="*60)
        
        # Look for download links
        print("\nLooking for download/PDF links:")
        
        # Check all links
        for link in soup.find_all('a', href=True):
            href = link.get('href', '')
            text = link.get_text(strip=True)
            
            # Look for PDF-related links
            if 'pdf' in href.lower() or 'download' in text.lower() or 'pdf' in text.lower():
                print(f"Text: {text}")
                print(f"URL: {href}")
                print()
        
        # Check for specific download patterns
        download_link = soup.find('a', {'class': 'btn-download'})
        if download_link:
            print(f"\nDownload button found: {download_link.get('href')}")
        
        # Check for external links
        external_links = soup.find_all('a', {'class': 'external-link'})
        for link in external_links:
            print(f"\nExternal link: {link.get_text(strip=True)}")
            print(f"URL: {link.get('href')}")

if __name__ == "__main__":
    asyncio.run(check_otl_pdf_pattern())