#!/usr/bin/env python3
"""
Detailed debugging of SearchService Google Search integration
"""

import asyncio
import sys
import os
import logging
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set up logging
logging.basicConfig(level=logging.DEBUG)

from app.services.search import SearchService
from app.models import SearchRequest

async def debug_detailed():
    """Detailed debugging"""
    print("=== Detailed SearchService Google Search Debug ===")
    
    # Set environment variables
    os.environ['GOOGLE_SEARCH_API_KEY'] = 'AIzaSyCvk9CM1oQVs1d6T_VE-nIkAO0Gky0op7M'
    os.environ['GOOGLE_SEARCH_ENGINE_ID'] = 'f7e881b00f097472b'
    
    # Initialize search service
    service = SearchService()
    
    # Check Google Search client
    client = service.google_search_client
    print(f"API Key: {client.api_key}")
    print(f"Engine ID: {client.search_engine_id}")
    
    # Test direct client call
    print("\n=== Testing direct client call ===")
    try:
        direct_results = await client.search(
            query="nutrition cognition",
            year_start=2000,
            year_end=2025,
            limit=5
        )
        print(f"Direct client returned: {len(direct_results)} results")
        for i, paper in enumerate(direct_results, 1):
            print(f"  {i}. {paper.title[:50]}...")
    except Exception as e:
        print(f"Direct client error: {e}")
        import traceback
        traceback.print_exc()
    
    # Test via SearchService
    print("\n=== Testing via SearchService ===")
    request = SearchRequest(
        query="nutrition cognition",
        sources=["Google Search"],
        year_start=2000,
        year_end=2025,
        per_page=10
    )
    
    try:
        results = await service.search(request)
        papers, sources_queried, total_results, source_counts = results[:4]
        
        print(f"SearchService returned:")
        print(f"  Total results: {total_results}")
        print(f"  Sources queried: {sources_queried}")
        print(f"  Source counts: {source_counts}")
        print(f"  Papers: {len(papers)}")
        
        for i, paper in enumerate(papers, 1):
            print(f"  {i}. {paper.title[:50]}...")
            
    except Exception as e:
        print(f"SearchService error: {e}")
        import traceback
        traceback.print_exc()
    
    await service.close()

if __name__ == "__main__":
    asyncio.run(debug_detailed())