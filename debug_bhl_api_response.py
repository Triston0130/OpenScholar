#!/usr/bin/env python3
"""Debug BHL API response to see what's happening with year field"""

import asyncio
from app.api_clients.biodiversity import BiodiversityClient
import json

async def debug_bhl():
    client = BiodiversityClient()
    
    # Use httpx directly to make the API call
    import httpx
    async with httpx.AsyncClient() as http_client:
        response = await http_client.get(
            "https://www.biodiversitylibrary.org/api3/",
            params={
                "op": "PublicationSearch",
                "searchterm": "Darwin evolution",
                "searchtype": "F",  # Full text search
                "apikey": "00000000-0000-0000-0000-000000000000",
                "format": "json",
                "startDate": "1800",
                "endDate": "1900"
            }
        )
        response = response.json()
    
    if response and "Result" in response:
        print(f"Total results: {len(response['Result'])}")
        print("\nFirst few results:")
        for i, book in enumerate(response["Result"][:3]):
            print(f"\n{i+1}. Title: {book.get('Title', 'N/A')}")
            print(f"   Year: {book.get('Year', 'N/A')} (type: {type(book.get('Year'))})")
            print(f"   PublicationDate: {book.get('PublicationDate', 'N/A')}")
            print(f"   Date: {book.get('Date', 'N/A')}")
            print(f"   Authors: {book.get('Authors', 'N/A')}")

if __name__ == "__main__":
    asyncio.run(debug_bhl())