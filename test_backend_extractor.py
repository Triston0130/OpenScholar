#!/usr/bin/env python3
"""Test PDF extractor directly"""

import asyncio
import sys
sys.path.append('.')

from app.api_clients.pdf_extractor import PDFExtractor

async def test():
    extractor = PDFExtractor()
    
    test_url = "https://human.libretexts.org/Bookshelves/History"
    print(f"Testing: {test_url}")
    
    result = await extractor.extract_pdf_url(test_url)
    print(f"Result: {result}")
    
    # Test the internal method directly
    result2 = await extractor._extract_libretexts_pdf(test_url)
    print(f"LibreTexts method result: {result2}")
    
    # Test the conversion function
    result3 = extractor._libretexts_to_pdf(test_url)
    print(f"Conversion function result: {result3}")

if __name__ == "__main__":
    asyncio.run(test())