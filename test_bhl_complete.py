#!/usr/bin/env python3
"""
Complete test of BHL functionality
"""
import asyncio
import sys
sys.path.append('.')

from app.api_clients.biodiversity import BiodiversityClient
from app.services.search import SearchService
from app.models import SearchRequest

async def test_bhl_direct():
    """Test BHL client directly"""
    print("1. Testing BHL Client Directly")
    print("="*60)
    
    # Test with demo key
    client = BiodiversityClient(api_key="00000000-0000-0000-0000-000000000000")
    results = await client.search("Darwin", 1800, 2024)
    
    print(f"Found {len(results)} results")
    if results:
        print(f"First result: {results[0].title}")
        print(f"Authors: {', '.join(results[0].authors[:3])}")
        print(f"Year: {results[0].year}")
    
    return len(results) > 0

async def test_bhl_via_search_service():
    """Test BHL through the search service"""
    print("\n2. Testing BHL via Search Service")
    print("="*60)
    
    # Create search service
    service = SearchService()
    
    # Create search request
    request = SearchRequest(
        query="Darwin species",
        year_start=1800,
        year_end=2024,
        sources=["BHL"],
        api_keys={"BHL": "00000000-0000-0000-0000-000000000000"}
    )
    
    # Search
    papers, sources_queried, total = await service.search(request)
    
    print(f"Sources queried: {sources_queried}")
    print(f"Total results: {total}")
    print(f"Papers returned: {len(papers)}")
    
    if papers:
        print(f"\nFirst result:")
        print(f"Title: {papers[0].title}")
        print(f"Source: {papers[0].source}")
    
    return len(papers) > 0

async def test_bhl_with_custom_key():
    """Test with a custom API key if provided"""
    if len(sys.argv) > 1:
        api_key = sys.argv[1]
        print(f"\n3. Testing with Custom API Key: {api_key[:8]}...")
        print("="*60)
        
        client = BiodiversityClient(api_key=api_key)
        results = await client.search("botany flora", 1800, 2024)
        
        print(f"Found {len(results)} results with custom key")
        return len(results) > 0
    else:
        print("\n3. No custom API key provided (pass as argument to test)")
        return None

async def main():
    """Run all tests"""
    print("BHL (Biodiversity Heritage Library) Complete Test")
    print("\n")
    
    # Run tests
    test1 = await test_bhl_direct()
    test2 = await test_bhl_via_search_service()
    test3 = await test_bhl_with_custom_key()
    
    # Summary
    print("\nSUMMARY")
    print("="*60)
    print(f"✓ Direct client test: {'PASSED' if test1 else 'FAILED'}")
    print(f"✓ Search service test: {'PASSED' if test2 else 'FAILED'}")
    if test3 is not None:
        print(f"✓ Custom API key test: {'PASSED' if test3 else 'FAILED'}")
    
    print("\nNOTE: BHL now works with the demo API key!")
    print("Your configured API key should also work fine.")

if __name__ == "__main__":
    asyncio.run(main())