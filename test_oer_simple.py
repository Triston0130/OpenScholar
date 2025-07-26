#!/usr/bin/env python3
"""
Simple test to check if OER APIs are accessible
"""

import httpx
import asyncio
import json

async def test_merlot_api():
    """Test MERLOT API directly"""
    print("\n=== Testing MERLOT API ===")
    url = "https://www.merlot.org/merlot/materials.json"
    params = {
        'keywords': 'biology',
        'materialType': 'Open Textbook',
        'licenseType': 'cc',
        'sort': 'relevance',
        'page': 1,
        'pageSize': 5
    }
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            print(f"Making request to: {url}")
            print(f"Parameters: {params}")
            response = await client.get(url, params=params)
            print(f"Status code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"Response keys: {list(data.keys())}")
                materials = data.get('materials', [])
                print(f"Found {len(materials)} materials")
                
                if materials:
                    print("\nFirst material:")
                    print(json.dumps(materials[0], indent=2)[:500] + "...")
            else:
                print(f"Response text: {response.text[:500]}")
                
        except Exception as e:
            print(f"Error: {type(e).__name__}: {e}")

async def test_libretexts_api():
    """Test LibreTexts API directly"""
    print("\n=== Testing LibreTexts API ===")
    base_url = "https://bio.libretexts.org"
    books_url = f"{base_url}/Bookshelves"
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            print(f"Making request to: {books_url}")
            response = await client.get(books_url)
            print(f"Status code: {response.status_code}")
            
            if response.status_code == 200:
                print("Successfully fetched LibreTexts bookshelf page")
                print(f"Response length: {len(response.text)} characters")
                
                # Check if we can find any book links
                if '/Bookshelves/' in response.text:
                    print("Found book links in response")
                else:
                    print("No book links found in response")
            else:
                print(f"Failed to fetch page")
                
        except Exception as e:
            print(f"Error: {type(e).__name__}: {e}")

async def test_oer_commons_api():
    """Test OER Commons API directly"""
    print("\n=== Testing OER Commons API ===")
    url = "https://www.oercommons.org/api/v1/materials/"
    params = {
        'keywords': 'biology',
        'limit': 5
    }
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            print(f"Making request to: {url}")
            print(f"Parameters: {params}")
            response = await client.get(url, params=params)
            print(f"Status code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"Response keys: {list(data.keys())}")
                results = data.get('results', [])
                print(f"Found {len(results)} results")
                
                if results:
                    print("\nFirst result:")
                    print(json.dumps(results[0], indent=2)[:500] + "...")
            else:
                print(f"Response text: {response.text[:500]}")
                
        except Exception as e:
            print(f"Error: {type(e).__name__}: {e}")

async def main():
    """Run all tests"""
    await test_merlot_api()
    await test_libretexts_api()
    await test_oer_commons_api()

if __name__ == "__main__":
    asyncio.run(main())