#!/usr/bin/env python3
"""Debug NLM full response"""

import httpx
import asyncio
from xml.etree import ElementTree as ET

async def debug_nlm_full():
    # Get one book's full details
    fetch_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
    params = {
        "db": "books",
        "id": "5794846",  # An HIV book
        "retmode": "xml"
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.get(fetch_url, params=params)
        
        # Pretty print the XML
        root = ET.fromstring(response.text)
        
        print("Full XML structure for book ID 5794846:")
        print("="*60)
        
        def print_element(elem, indent=0):
            prefix = "  " * indent
            if elem.text and elem.text.strip():
                print(f"{prefix}{elem.tag}: {elem.text.strip()[:100]}")
            else:
                print(f"{prefix}{elem.tag}")
            
            for attr, value in elem.attrib.items():
                print(f"{prefix}  @{attr}: {value}")
            
            for child in elem:
                print_element(child, indent + 1)
        
        print_element(root)

if __name__ == "__main__":
    asyncio.run(debug_nlm_full())