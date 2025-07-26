#!/usr/bin/env python3
"""Debug NLM Bookshelf search"""

import httpx
import asyncio
from xml.etree import ElementTree as ET

async def debug_nlm_search(query):
    print(f"\n{'='*60}")
    print(f"Testing NLM Bookshelf search for: '{query}'")
    print('='*60)
    
    search_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
    
    # Simple search
    params = {
        "db": "books",
        "term": query,
        "retmax": "20",
        "retmode": "xml"
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.get(search_url, params=params)
        print(f"\nSearch URL: {response.url}")
        
        root = ET.fromstring(response.text)
        
        # Get count
        count = root.find("Count")
        if count is not None:
            print(f"Total matching books: {count.text}")
        
        # Get IDs
        id_list = root.find("IdList")
        if id_list is not None:
            ids = [id_elem.text for id_elem in id_list.findall("Id")]
            print(f"Retrieved {len(ids)} book IDs")
            
            if ids:
                # Get details for first few books
                print("\nFetching details for first 3 books...")
                fetch_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
                fetch_params = {
                    "db": "books",
                    "id": ",".join(ids[:3]),
                    "retmode": "xml"
                }
                
                fetch_resp = await client.get(fetch_url, params=fetch_params)
                fetch_root = ET.fromstring(fetch_resp.text)
                
                for i, doc_sum in enumerate(fetch_root.findall(".//DocSum")):
                    print(f"\nBook {i+1}:")
                    book_id = doc_sum.find("Id")
                    if book_id is not None:
                        print(f"  ID: {book_id.text}")
                    
                    for item in doc_sum.findall("Item"):
                        name = item.get("Name")
                        if name in ["Title", "PubDate", "AuthorList"]:
                            print(f"  {name}: {item.text or 'N/A'}")

async def main():
    queries = ["HIV", "cancer", "diabetes", "nutrition", "anatomy"]
    for query in queries:
        await debug_nlm_search(query)
        await asyncio.sleep(0.5)  # Rate limiting

if __name__ == "__main__":
    asyncio.run(main())