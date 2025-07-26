#!/usr/bin/env python3
"""
Debug BHL API issue
"""
import asyncio
import httpx

async def test_bhl_advanced_search(api_key):
    """Test the PublicationSearchAdvanced endpoint"""
    
    url = "https://www.biodiversitylibrary.org/api3"
    
    # Test with required parameters
    params = {
        "op": "PublicationSearchAdvanced",
        "title": "Darwin",  # Try with title parameter
        "searchtype": "F",
        "apikey": api_key,
        "format": "json",
        "limit": 5
    }
    
    print(f"Testing BHL API key: {api_key[:16]}...")
    print(f"URL: {url}")
    print(f"Params: {params}")
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params)
        print(f"\nStatus: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if "Result" in data:
                print(f"Results: {len(data['Result'])}")
                if data['Result']:
                    print(f"First: {data['Result'][0].get('Title', 'No title')[:60]}...")
        else:
            print(f"Error: {response.text[:200]}")

async def main():
    # Test with demo key
    print("Test 1: Demo key with PublicationSearchAdvanced")
    print("-"*60)
    await test_bhl_advanced_search("00000000-0000-0000-0000-000000000000")
    
    print("\n\nTest 2: Check what parameters PublicationSearchAdvanced needs")
    print("-"*60)
    
    # Test what the error message says
    url = "https://www.biodiversitylibrary.org/api3"
    params = {
        "op": "PublicationSearchAdvanced",
        "searchterm": "Darwin",  # This parameter might be wrong
        "apikey": "00000000-0000-0000-0000-000000000000",
        "format": "json"
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params)
        print(f"Status: {response.status_code}")
        data = response.json()
        if "ErrorMessage" in data:
            print(f"Error: {data['ErrorMessage']}")
        print(f"Full response: {data}")

if __name__ == "__main__":
    asyncio.run(main())