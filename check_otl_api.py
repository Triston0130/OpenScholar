#!/usr/bin/env python3
"""Check Open Textbook Library API for PDF URLs"""

import httpx
import asyncio
import json

async def check_otl_api():
    url = "https://open.umn.edu/opentextbooks/textbooks.json"
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        data = response.json()
        
        # Get first book that contains "proof" to match your example
        for book in data.get("data", []):
            if "proof" in book.get("title", "").lower():
                print("Book found:")
                print(f"ID: {book.get('id')}")
                print(f"Title: {book.get('title')}")
                print(f"Landing page: https://open.umn.edu/opentextbooks/textbooks/{book.get('id')}")
                
                # Check all fields for PDF-related info
                print("\nChecking for PDF-related fields:")
                for key, value in book.items():
                    if isinstance(value, str) and ('pdf' in key.lower() or 'pdf' in str(value).lower() or 'download' in key.lower()):
                        print(f"  {key}: {value}")
                
                # Check resources field
                if "resources" in book:
                    print("\nResources field:")
                    print(json.dumps(book["resources"], indent=2))
                
                # Check if there's a download field
                if "download" in book:
                    print("\nDownload field:")
                    print(json.dumps(book["download"], indent=2))
                    
                # Check if there's a pdf_url or similar
                for field in ["pdf_url", "pdf", "download_url", "file", "url"]:
                    if field in book:
                        print(f"\n{field}: {book[field]}")
                
                break

if __name__ == "__main__":
    asyncio.run(check_otl_api())