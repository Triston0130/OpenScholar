#!/usr/bin/env python3
"""Test PDFExtractor directly"""

import asyncio
import sys
sys.path.append('.')

from app.api_clients.pdf_extractor import PDFExtractor

async def test_libretexts():
    extractor = PDFExtractor()
    
    test_url = "https://bio.libretexts.org/Bookshelves/Biotechnology"
    print(f"Testing: {test_url}")
    
    result = await extractor.extract_pdf_url(test_url)
    print(f"Result: {result}")
    
    # Test the conversion function directly
    converted = extractor._libretexts_to_pdf(test_url)
    print(f"Direct conversion: {converted}")

if __name__ == "__main__":
    asyncio.run(test_libretexts())