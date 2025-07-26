#!/usr/bin/env python3
"""Test enhanced OTL client with PDF URL fetching"""

import asyncio
from app.api_clients.open_textbook_library import OpenTextbookLibraryClient

async def test_otl_enhanced():
    client = OpenTextbookLibraryClient()
    
    print("Testing Open Textbook Library with enhanced PDF fetching...")
    print("="*60)
    
    # Search for "proof" to find Book of Proof
    results = await client.search("proof", max_results=3)
    
    print(f"\nFound {len(results)} results")
    
    for i, paper in enumerate(results, 1):
        print(f"\n{i}. {paper.title}")
        print(f"   Authors: {', '.join(paper.authors[:2])}")
        print(f"   Year: {paper.year}")
        print(f"   URL: {paper.full_text_url}")
        
        # Check if it's a PDF URL or landing page
        if paper.full_text_url.endswith('.pdf') or '/formats/' in paper.full_text_url:
            print("   ✅ Direct PDF URL!")
        else:
            print("   ⚠️  Landing page URL")

if __name__ == "__main__":
    asyncio.run(test_otl_enhanced())