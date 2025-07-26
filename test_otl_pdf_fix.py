#!/usr/bin/env python3
"""Test Open Textbook Library PDF extraction with MIT OCW redirects"""

import asyncio
import sys
sys.path.append('.')

from app.api_clients.pdf_extractor import PDFExtractor

async def test_otl_pdf_extraction():
    extractor = PDFExtractor()
    
    # Test URLs from Open Textbook Library that redirect to different sites
    test_urls = [
        "https://open.umn.edu/opentextbooks/textbooks/10",  # Calculus textbook (MIT OCW)
        "https://open.umn.edu/opentextbooks/textbooks/communication-for-business-success",  # LibreTexts example
    ]
    
    for url in test_urls:
        print(f"\nTesting: {url}")
        pdf_url = await extractor.extract_pdf_url(url)
        if pdf_url:
            print(f"✓ Extracted PDF URL: {pdf_url}")
        else:
            print(f"✗ Failed to extract PDF URL")

if __name__ == "__main__":
    asyncio.run(test_otl_pdf_extraction())