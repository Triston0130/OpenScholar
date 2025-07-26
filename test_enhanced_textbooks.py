#!/usr/bin/env python3
"""Test enhanced textbook implementations"""

import asyncio
from app.api_clients.open_textbook_library_scraper import OpenTextbookLibraryScraper
from app.api_clients.libretexts_enhanced import LibreTextsEnhanced

async def test_enhanced_clients():
    print("Testing Enhanced Textbook Clients")
    print("="*60)
    
    # Test Open Textbook Library Scraper
    print("\n1. Testing Open Textbook Library Scraper:")
    otl_client = OpenTextbookLibraryScraper()
    otl_results = await otl_client.search("calculus", max_results=20)
    print(f"   Found {len(otl_results)} results for 'calculus'")
    if otl_results:
        print("   Sample titles:")
        for i, paper in enumerate(otl_results[:3]):
            print(f"   {i+1}. {paper.title}")
    
    # Test LibreTexts Enhanced
    print("\n2. Testing LibreTexts Enhanced:")
    libre_client = LibreTextsEnhanced()
    libre_results = await libre_client.search("calculus", max_results=20)
    print(f"   Found {len(libre_results)} results for 'calculus'")
    if libre_results:
        print("   Sample titles:")
        for i, paper in enumerate(libre_results[:3]):
            print(f"   {i+1}. {paper.title}")
    
    # Test with different queries
    queries = ["introduction", "physics", "biology", "chemistry"]
    
    print("\n3. Testing various subjects:")
    for query in queries:
        print(f"\n   Query: '{query}'")
        
        otl_results = await otl_client.search(query, max_results=50)
        libre_results = await libre_client.search(query, max_results=50)
        
        print(f"   - Open Textbook Library: {len(otl_results)} books")
        print(f"   - LibreTexts: {len(libre_results)} books")
        print(f"   - Total: {len(otl_results) + len(libre_results)} books")

if __name__ == "__main__":
    asyncio.run(test_enhanced_clients())