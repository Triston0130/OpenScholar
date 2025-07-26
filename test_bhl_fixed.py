#!/usr/bin/env python3
"""
Test the fixed BHL API client
"""
import asyncio
import sys
sys.path.append('.')

from app.api_clients.biodiversity import BiodiversityClient

async def test_bhl():
    """Test BHL with the fixed implementation"""
    
    print("Testing Fixed BHL Client")
    print("="*60)
    
    # Test with demo key (should now work)
    print("\nTesting with demo API key:")
    client = BiodiversityClient(api_key="00000000-0000-0000-0000-000000000000")
    
    queries = ["darwin", "evolution", "species"]
    
    for query in queries:
        print(f"\nSearching for: '{query}'")
        results = await client.search(query, 1800, 2024)
        print(f"Results: {len(results)}")
        
        if results:
            for i, paper in enumerate(results[:3], 1):
                print(f"\n{i}. {paper.title}")
                print(f"   Authors: {', '.join(paper.authors[:2])}")
                print(f"   Year: {paper.year}")
                print(f"   URL: {paper.full_text_url}")
    
    # Test with your API key if provided
    import sys
    if len(sys.argv) > 1:
        api_key = sys.argv[1]
        print(f"\n\nTesting with your API key: {api_key[:8]}...")
        client = BiodiversityClient(api_key=api_key)
        results = await client.search("botany", 1800, 2024)
        print(f"Results with your key: {len(results)}")

if __name__ == "__main__":
    asyncio.run(test_bhl())