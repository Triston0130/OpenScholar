#!/usr/bin/env python3
"""Test LibreTexts URL conversion"""

import sys
sys.path.append('.')

from app.api_clients.pdf_extractor import PDFExtractor

def test_libretexts_conversion():
    extractor = PDFExtractor()
    
    test_urls = [
        "https://math.libretexts.org/Bookshelves/Arithmetic_and_Basic_Math",
        "https://geo.libretexts.org/Bookshelves/Meteorology_and_Climate_Science",
        "https://biz.libretexts.org/Bookshelves/Accounting/Accounting_in_the_Finance_World"
    ]
    
    for url in test_urls:
        pdf_url = extractor._libretexts_to_pdf(url)
        print(f"Original: {url}")
        print(f"PDF:      {pdf_url}")
        print()

if __name__ == "__main__":
    test_libretexts_conversion()