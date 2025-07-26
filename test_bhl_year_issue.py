#!/usr/bin/env python3
"""Test to identify year field issues with BHL"""

import asyncio
from app.api_clients.biodiversity import BiodiversityClient

async def test_bhl_year():
    client = BiodiversityClient()
    
    # Search with historical dates
    results = await client.search(
        query="Darwin evolution",
        year_start=1800,
        year_end=1900,
        limit=30
    )
    
    print(f"Total results: {len(results)}")
    print("\nChecking year fields:")
    
    none_years = []
    for i, paper in enumerate(results):
        if paper.year is None or paper.year == "":
            none_years.append((i, paper.title))
        print(f"{i+1}. Year: {repr(paper.year)} - {paper.title[:60]}...")
    
    if none_years:
        print(f"\n⚠️  Found {len(none_years)} papers with None/empty year:")
        for idx, title in none_years:
            print(f"   - Index {idx}: {title[:80]}...")

if __name__ == "__main__":
    asyncio.run(test_bhl_year())