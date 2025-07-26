#!/usr/bin/env python3
"""Check total books in Open Textbook Library"""

import httpx
import asyncio
import json

async def check_otl_total():
    url = "https://open.umn.edu/opentextbooks/textbooks.json"
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        data = response.json()
        
        books = data.get("data", [])
        print(f"Total books in Open Textbook Library: {len(books)}")
        
        # Count by subject
        subjects = {}
        for book in books:
            for subj in book.get("subjects", []):
                subj_name = subj.get("name", "Unknown")
                subjects[subj_name] = subjects.get(subj_name, 0) + 1
        
        print("\nTop subjects:")
        for subj, count in sorted(subjects.items(), key=lambda x: x[1], reverse=True)[:10]:
            print(f"  {subj}: {count} books")

if __name__ == "__main__":
    asyncio.run(check_otl_total())