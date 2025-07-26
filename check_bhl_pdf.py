#!/usr/bin/env python3
"""Check what BHL API actually returns for PDF links"""

import httpx
import asyncio
import json

async def check_bhl_api():
    async with httpx.AsyncClient() as client:
        # Get a book from BHL
        response = await client.get(
            "https://www.biodiversitylibrary.org/api3/",
            params={
                "op": "PublicationSearch",
                "searchterm": "Darwin",
                "searchtype": "F",
                "apikey": "00000000-0000-0000-0000-000000000000",
                "format": "json",
                "limit": 1
            }
        )
        
        data = response.json()
        if data.get("Status") == "ok" and data.get("Result"):
            book = data["Result"][0]
            print("Book data keys:", list(book.keys()))
            print("\nTitle:", book.get("Title"))
            print("TitleID:", book.get("TitleID"))
            print("ItemID:", book.get("ItemID"))
            print("TitleUrl:", book.get("TitleUrl"))
            print("ItemUrl:", book.get("ItemUrl"))
            
            # Check if there's any PDF-related field
            for key, value in book.items():
                if 'pdf' in key.lower() or 'download' in key.lower():
                    print(f"{key}: {value}")
            
            # The actual PDF URL pattern for BHL is:
            # https://www.biodiversitylibrary.org/itempdf/{ItemID}
            if book.get("ItemID"):
                print(f"\nConstructed PDF URL: https://www.biodiversitylibrary.org/itempdf/{book['ItemID']}")
            elif book.get("TitleID"):
                print(f"\nConstructed PDF URL: https://www.biodiversitylibrary.org/pdfs/{book['TitleID']}.pdf")

if __name__ == "__main__":
    asyncio.run(check_bhl_api())