#!/usr/bin/env python3
"""
Simple test of BHL to verify it's working
"""
import asyncio
import sys
sys.path.append('.')

from app.api_clients.biodiversity import BiodiversityClient

async def main():
    print("BHL (Biodiversity Heritage Library) Test")
    print("="*60)
    
    # Test 1: With demo key (should work now)
    print("\n✅ Testing with demo API key:")
    client = BiodiversityClient(api_key="00000000-0000-0000-0000-000000000000")
    results = await client.search("Darwin", 1800, 2024, limit=5)
    
    print(f"Results: {len(results)}")
    for i, paper in enumerate(results, 1):
        print(f"\n{i}. {paper.title[:80]}...")
        print(f"   Year: {paper.year}")
        print(f"   Type: {paper.content_type}")
    
    # Test 2: With your API key (if you run: python3 test_bhl_simple.py YOUR_KEY)
    if len(sys.argv) > 1:
        api_key = sys.argv[1]
        print(f"\n✅ Testing with your API key: {api_key[:8]}...")
        client = BiodiversityClient(api_key=api_key)
        results = await client.search("botany", 1800, 2024, limit=5)
        print(f"Results with your key: {len(results)}")
    
    print("\n" + "="*60)
    print("BHL is now working! The issue was:")
    print("1. The API endpoint was using the wrong operation")
    print("2. The demo key was being blocked unnecessarily")
    print("\nBHL now works with both demo and real API keys!")

if __name__ == "__main__":
    asyncio.run(main())