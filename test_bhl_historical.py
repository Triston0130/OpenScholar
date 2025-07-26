#!/usr/bin/env python3
"""Test BHL search with historical dates"""

import asyncio
from app.api_clients.biodiversity import BiodiversityClient

async def test_bhl_historical():
    print("Testing BHL with historical dates (1800-1900)")
    print("=" * 60)
    
    client = BiodiversityClient()
    
    # Test with historical date range
    results = await client.search(
        query="Darwin species",
        year_start=1800,
        year_end=1900,
        limit=10
    )
    
    print(f"\n✅ Found {len(results)} results for 'Darwin species' (1800-1900):\n")
    
    for i, paper in enumerate(results, 1):
        print(f"{i}. {paper.title}")
        print(f"   Year: {paper.year}")
        if paper.authors:
            print(f"   Authors: {', '.join(paper.authors[:3])}")
        print()
    
    # Test with specific historical year
    print("\n" + "=" * 60)
    print("Testing specific year 1859 (Origin of Species publication year)")
    print("=" * 60)
    
    results = await client.search(
        query="species origin",
        year_start=1859,
        year_end=1859,
        limit=5
    )
    
    print(f"\n✅ Found {len(results)} results for 'species origin' in 1859:\n")
    
    for i, paper in enumerate(results, 1):
        print(f"{i}. {paper.title}")
        print(f"   Year: {paper.year}")
        print()

if __name__ == "__main__":
    asyncio.run(test_bhl_historical())