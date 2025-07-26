#\!/usr/bin/env python3
"""Test the API directly"""

import requests

# Test the extract-pdf-url endpoint
url = "http://localhost:8000/extract-pdf-url"
test_cases = [
    "https://human.libretexts.org/Bookshelves/History",
    "https://bio.libretexts.org/Bookshelves/Biotechnology",
    "https://math.libretexts.org/Bookshelves/Calculus"
]

for test_url in test_cases:
    response = requests.post(url, json={"url": test_url})
    result = response.json()
    print(f"\nInput:  {test_url}")
    print(f"Full response: {result}")
    print(f"Output: {result.get('pdf_url', 'N/A')}")
    print(f"Extracted: {result.get('extracted', False)}")
    changed = result.get('pdf_url') != result.get('original_url')
    print(f"Changed: {changed}")
