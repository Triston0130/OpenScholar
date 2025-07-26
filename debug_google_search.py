#!/usr/bin/env python3
"""
Debug Google Search API integration
"""

import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def debug_google_search():
    """Debug the Google Search integration step by step"""
    print("🔍 Debugging Google Search Integration")
    print("=" * 50)
    
    try:
        # Test 1: Import the client
        print("1. Testing imports...")
        from app.api_clients.google_search import GoogleSearchClient
        from app.models import SearchRequest
        print("   ✅ Imports successful")
        
        # Test 2: Check environment variables
        print("\n2. Checking environment variables...")
        api_key = os.getenv("GOOGLE_SEARCH_API_KEY")
        engine_id = os.getenv("GOOGLE_SEARCH_ENGINE_ID")
        
        if api_key:
            print(f"   ✅ GOOGLE_SEARCH_API_KEY found: {api_key[:10]}...")
        else:
            print("   ❌ GOOGLE_SEARCH_API_KEY not found in environment")
            
        if engine_id:
            print(f"   ✅ GOOGLE_SEARCH_ENGINE_ID found: {engine_id}")
        else:
            print("   ❌ GOOGLE_SEARCH_ENGINE_ID not found in environment")
        
        # Test 3: Initialize client
        print("\n3. Testing client initialization...")
        client = GoogleSearchClient()
        print(f"   Client API key: {client.api_key[:10] if client.api_key else 'None'}...")
        print(f"   Client engine ID: {client.search_engine_id or 'None'}")
        
        if not client.api_key or not client.search_engine_id:
            print("   ⚠️  Client not properly configured with credentials")
            return False
        
        # Test 4: Test search service integration
        print("\n4. Testing SearchService integration...")
        from app.services.search import SearchService
        service = SearchService()
        print("   ✅ SearchService initialized")
        
        # Test 5: Test API keys update mechanism
        print("\n5. Testing API key update mechanism...")
        test_api_keys = {
            'Google Search': 'test_api_key',
            'Google Search_ENGINE_ID': 'test_engine_id'
        }
        service.update_api_keys(test_api_keys)
        print(f"   Updated API key: {service.google_search_client.api_key}")
        print(f"   Updated engine ID: {service.google_search_client.search_engine_id}")
        
        # Test 6: Try a mock search (without actual API call)
        print("\n6. Testing search request structure...")
        search_request = SearchRequest(
            query="test query",
            sources=["Google Search"],
            year_start=2020,
            year_end=2024
        )
        print(f"   ✅ SearchRequest created: {search_request.query}")
        print(f"   ✅ Sources: {search_request.sources}")
        
        print("\n✅ All tests passed - backend should be working")
        return True
        
    except Exception as e:
        print(f"\n❌ Error during debugging: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_actual_search():
    """Test an actual search if credentials are available"""
    print("\n" + "=" * 50)
    print("🔍 Testing Actual Google Search API Call")
    print("=" * 50)
    
    try:
        from app.api_clients.google_search import GoogleSearchClient
        
        client = GoogleSearchClient()
        
        if not client.api_key or not client.search_engine_id:
            print("❌ Cannot test actual search - credentials not configured")
            return False
        
        print("🔍 Making actual API call to Google...")
        print(f"   Using API key: {client.api_key[:10]}...")
        print(f"   Using engine ID: {client.search_engine_id}")
        
        papers = await client.search(
            query="machine learning",
            year_start=2020,
            year_end=2024,
            limit=3
        )
        
        print(f"✅ API call successful! Found {len(papers)} results")
        
        for i, paper in enumerate(papers, 1):
            print(f"\n   Result {i}:")
            print(f"     Title: {paper.title[:60]}...")
            print(f"     Authors: {', '.join(paper.authors[:2])}")
            print(f"     Year: {paper.year}")
            print(f"     PDF URL: {paper.full_text_url}")
        
        return True
        
    except Exception as e:
        print(f"❌ API call failed: {e}")
        
        # Check if it's an authentication error
        if "401" in str(e) or "403" in str(e):
            print("\n🔑 This looks like an authentication error.")
            print("   Please check:")
            print("   1. Your Google Search API key is correct")
            print("   2. Your Custom Search Engine ID is correct") 
            print("   3. Custom Search API is enabled in Google Cloud Console")
            print("   4. You're not using SerPAPI - you need Google Custom Search API")
        
        return False

async def main():
    """Run all debug tests"""
    print("Google Search Debug Tool")
    print("=" * 50)
    
    # Run basic debugging
    basic_success = await debug_google_search()
    
    if basic_success:
        # Try actual API call
        await test_actual_search()
    
    print("\n" + "=" * 50)
    print("🔧 If you're still getting 500 errors:")
    print("1. Make sure you're using Google Custom Search API (not SerpAPI)")
    print("2. Check that the API key and engine ID are saved in the frontend")
    print("3. Restart your backend server")
    print("4. Check the backend console for detailed error messages")

if __name__ == "__main__":
    asyncio.run(main())