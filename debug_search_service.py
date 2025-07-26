#!/usr/bin/env python3
"""
Debug SearchService Google Search integration
"""

import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.search import SearchService
from app.models import SearchRequest

async def debug_search_service():
    """Debug SearchService integration"""
    print("=== Debugging SearchService Google Search Integration ===")
    
    # Set environment variables
    os.environ['GOOGLE_SEARCH_API_KEY'] = 'AIzaSyCvk9CM1oQVs1d6T_VE-nIkAO0Gky0op7M'
    os.environ['GOOGLE_SEARCH_ENGINE_ID'] = 'f7e881b00f097472b'
    
    # Test direct Google Search client first
    from app.api_clients.google_search import GoogleSearchClient
    
    print("=== Testing Direct Google Search Client ===")
    client = GoogleSearchClient()
    print(f"API Key: {client.api_key[:10]}..." if client.api_key else "❌ No API key")
    print(f"Search Engine ID: {client.search_engine_id}")
    
    # Test direct search
    direct_papers = await client.search(query="aces", year_start=2000, year_end=2025, limit=5)
    print(f"Direct Google Search returned: {len(direct_papers)} papers")
    
    for i, paper in enumerate(direct_papers[:3], 1):
        print(f"  {i}. {paper.title[:60]}...")
        print(f"     PDF URL: {paper.full_text_url}")
    
    print("\n=== Testing SearchService Integration ===")
    
    # Initialize search service
    service = SearchService()
    
    # Check if Google Search client is configured
    print(f"Google Search API Key: {service.google_search_client.api_key[:10]}..." if service.google_search_client.api_key else "❌ No API key")
    print(f"Search Engine ID: {service.google_search_client.search_engine_id}")
    
    # Create a search request with only Google Search
    request = SearchRequest(
        query="aces",
        sources=["Google Search"],
        year_start=2000,
        year_end=2025,
        per_page=10  # Fixed validation error
    )
    
    print(f"\n🔍 Testing SearchService with query: '{request.query}'")
    print(f"Sources requested: {request.sources}")
    
    try:
        # Perform search
        results = await service.search(request)
        
        papers, sources_queried, total_results, source_counts = results[:4]
        
        print(f"\n✅ SearchService results:")
        print(f"   Sources queried: {sources_queried}")
        print(f"   Total results: {total_results}")
        print(f"   Papers returned: {len(papers)}")
        print(f"   Source counts: {source_counts}")
        
        # Display results
        if papers:
            print(f"\nFirst few papers:")
            for i, paper in enumerate(papers[:3], 1):
                print(f"  {i}. {paper.title[:80]}...")
                print(f"     Authors: {', '.join(paper.authors[:3])}")
                print(f"     Year: {paper.year}")
                print(f"     PDF URL: {paper.full_text_url}")
                print()
        else:
            print("\n❌ No papers returned!")
            
    except Exception as e:
        print(f"❌ SearchService error: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        await service.close()

if __name__ == "__main__":
    asyncio.run(debug_search_service())