#!/usr/bin/env python3
"""
Test Google Search API client for PDF-only results
"""

import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.api_clients.google_search import GoogleSearchClient
from app.models import SearchRequest

async def test_google_search():
    """Test Google Search PDF client"""
    print("=== Testing Google Search PDF Client ===")
    
    # Initialize client
    client = GoogleSearchClient()
    
    # Check if API credentials are configured
    if not client.api_key:
        print("❌ GOOGLE_SEARCH_API_KEY not set in environment")
        return False
    
    if not client.search_engine_id:
        print("❌ GOOGLE_SEARCH_ENGINE_ID not set in environment")
        return False
    
    print(f"✅ API Key configured: {client.api_key[:10]}...")
    print(f"✅ Search Engine ID configured: {client.search_engine_id}")
    
    # Test queries
    test_queries = [
        "machine learning",
        "climate change research",
        "neural networks",
    ]
    
    total_results = 0
    
    for query in test_queries:
        print(f"\n🔍 Testing query: '{query}'")
        
        try:
            # Search for PDFs
            papers = await client.search(
                query=query,
                year_start=2020,
                year_end=2024,
                limit=5
            )
            
            print(f"✅ Found {len(papers)} PDF results")
            total_results += len(papers)
            
            # Display first few results
            for i, paper in enumerate(papers[:3], 1):
                print(f"  {i}. {paper.title[:80]}...")
                print(f"     Authors: {', '.join(paper.authors[:3])}")
                print(f"     Year: {paper.year}")
                print(f"     Source: {paper.source}")
                print(f"     PDF URL: {paper.full_text_url}")
                
                # Verify it's actually a PDF URL
                if paper.full_text_url and paper.full_text_url.lower().endswith('.pdf'):
                    print(f"     ✅ Valid PDF URL")
                else:
                    print(f"     ❌ Invalid PDF URL")
                
                print()
            
        except Exception as e:
            print(f"❌ Error searching for '{query}': {e}")
            return False
    
    print(f"\n=== Test Summary ===")
    print(f"Total PDF results found: {total_results}")
    
    if total_results > 0:
        print("✅ Google Search PDF integration working!")
        return True
    else:
        print("❌ No PDF results found - check API configuration")
        return False

async def test_search_service_integration():
    """Test Google Search integration with SearchService"""
    print("\n=== Testing SearchService Integration ===")
    
    from app.services.search import SearchService
    
    # Initialize search service
    service = SearchService()
    
    # Create a search request with only Google Search
    request = SearchRequest(
        query="artificial intelligence",
        sources=["Google Search"],
        year_start=2022,
        year_end=2024,
        per_page=5
    )
    
    try:
        # Perform search
        print(f"🔍 Searching with SearchService: '{request.query}'")
        results = await service.search(request)
        
        papers, sources_queried, total_results, source_counts = results[:4]
        
        print(f"✅ SearchService integration successful")
        print(f"   Sources queried: {sources_queried}")
        print(f"   Total results: {total_results}")
        print(f"   Results this page: {len(papers)}")
        print(f"   Source counts: {source_counts}")
        
        # Display results
        for i, paper in enumerate(papers, 1):
            print(f"  {i}. {paper.title[:60]}...")
            print(f"     PDF URL: {paper.full_text_url}")
            
        await service.close()
        return len(papers) > 0
        
    except Exception as e:
        print(f"❌ SearchService integration error: {e}")
        await service.close()
        return False

async def main():
    """Run all tests"""
    print("OpenScholar Google Search PDF Integration Test")
    print("=" * 50)
    
    # Test 1: Direct API client
    success1 = await test_google_search()
    
    if success1:
        # Test 2: SearchService integration
        success2 = await test_search_service_integration()
    else:
        success2 = False
    
    print("\n" + "=" * 50)
    if success1 and success2:
        print("🎉 All tests PASSED! Google Search PDF integration is working.")
        print("\nNext steps:")
        print("1. Configure Google Search API credentials in .env")
        print("2. Test in the frontend with various queries")
        print("3. Verify PDF reader functionality")
    else:
        print("❌ Some tests FAILED. Check the configuration and API credentials.")
        
        if not success1:
            print("\n📝 To set up Google Search API:")
            print("1. Go to Google Cloud Console")
            print("2. Enable Custom Search API")
            print("3. Create a Custom Search Engine at https://cse.google.com")
            print("4. Configure it to search the entire web")
            print("5. Add filetype:pdf in the advanced settings")
            print("6. Set GOOGLE_SEARCH_API_KEY and GOOGLE_SEARCH_ENGINE_ID in .env")

if __name__ == "__main__":
    asyncio.run(main())