#!/usr/bin/env python3
"""
Test BHL API client to debug why it's not working
"""
import asyncio
import sys
sys.path.append('.')

from app.api_clients.biodiversity import BiodiversityClient
import logging

# Enable debug logging
logging.basicConfig(level=logging.INFO)

async def test_bhl():
    """Test BHL with different API key scenarios"""
    
    print("Testing BHL API Client")
    print("="*60)
    
    # Test 1: Without API key (should skip)
    print("\n1. Testing without API key:")
    client = BiodiversityClient()
    results = await client.search("darwin", 1800, 2024)
    print(f"   Results: {len(results)} (should be 0)")
    
    # Test 2: With demo API key (should skip)
    print("\n2. Testing with demo API key:")
    client = BiodiversityClient(api_key="00000000-0000-0000-0000-000000000000")
    results = await client.search("darwin", 1800, 2024)
    print(f"   Results: {len(results)} (should be 0)")
    
    # Test 3: With dummy key (should skip)
    print("\n3. Testing with dummy API key:")
    client = BiodiversityClient(api_key="00000000000000000000000000000000")
    results = await client.search("darwin", 1800, 2024)
    print(f"   Results: {len(results)} (should be 0)")
    
    # Test 4: With a "valid" test key
    print("\n4. Testing with test API key:")
    client = BiodiversityClient(api_key="test-key-12345")
    results = await client.search("darwin", 1800, 2024)
    print(f"   Results: {len(results)}")
    if results:
        print(f"   First result: {results[0].title}")
    
    # Test 5: Direct API call
    print("\n5. Testing direct API call:")
    import httpx
    async with httpx.AsyncClient() as http_client:
        url = "https://www.biodiversitylibrary.org/api3"
        params = {
            "op": "PublicationSearchAdvanced",
            "searchterm": "darwin",
            "searchtype": "F",
            "apikey": "test-key-12345",
            "format": "json",
            "limit": 5
        }
        try:
            response = await http_client.get(url, params=params)
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                if "Status" in data:
                    print(f"   API Status: {data.get('Status')}")
                if "ErrorMessage" in data:
                    print(f"   Error: {data.get('ErrorMessage')}")
                if "Result" in data:
                    print(f"   Results found: {len(data.get('Result', []))}")
        except Exception as e:
            print(f"   Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_bhl())