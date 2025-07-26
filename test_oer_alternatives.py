#!/usr/bin/env python3
"""
Test alternative approaches for OER sources
"""

import httpx
import asyncio
import json

async def test_merlot_web_search():
    """Test MERLOT web search interface"""
    print("\n=== Testing MERLOT Web Search ===")
    # Try the regular web search endpoint
    url = "https://www.merlot.org/merlot/searchMaterials.htm"
    params = {
        'keywords': 'biology textbook',
        'allKeyWords': 'true',
        'licenseKey': ''  # Try without license key
    }
    
    async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
        try:
            print(f"Making request to: {url}")
            response = await client.get(url, params=params)
            print(f"Status code: {response.status_code}")
            print(f"Response length: {len(response.text)} characters")
            print(f"Content type: {response.headers.get('content-type', 'unknown')}")
            
            if 'results' in response.text.lower():
                print("Found 'results' in response")
            else:
                print("No 'results' found in response")
                
        except Exception as e:
            print(f"Error: {type(e).__name__}: {e}")

async def test_oer_commons_follow_redirect():
    """Test OER Commons with redirect following"""
    print("\n=== Testing OER Commons with Redirect ===")
    url = "https://www.oercommons.org/api/v1/materials/"
    params = {
        'keywords': 'biology',
        'limit': 5
    }
    
    async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
        try:
            print(f"Making request to: {url}")
            response = await client.get(url, params=params)
            print(f"Final status code: {response.status_code}")
            print(f"Final URL: {response.url}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    print(f"Response is JSON: {list(data.keys())}")
                except:
                    print(f"Response is not JSON. Content type: {response.headers.get('content-type', 'unknown')}")
                    print(f"Response preview: {response.text[:200]}")
            
        except Exception as e:
            print(f"Error: {type(e).__name__}: {e}")

async def test_libretexts_search():
    """Test LibreTexts search API"""
    print("\n=== Testing LibreTexts Search ===")
    # Try the search endpoint directly
    base_url = "https://bio.libretexts.org"
    search_url = f"{base_url}/@search"
    
    params = {
        'q': 'cell biology',
        'limit': 5
    }
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            print(f"Making request to: {search_url}")
            response = await client.get(search_url, params=params)
            print(f"Status code: {response.status_code}")
            
            if response.status_code == 200:
                print(f"Response length: {len(response.text)} characters")
                if 'results' in response.text.lower() or 'search' in response.text.lower():
                    print("Found search-related content in response")
                    # Check if there's a specific search API
                    if '@api' in response.text:
                        print("Found API references in response")
            
        except Exception as e:
            print(f"Error: {type(e).__name__}: {e}")

if __name__ == "__main__":
    asyncio.run(test_merlot_web_search())
    asyncio.run(test_oer_commons_follow_redirect())
    asyncio.run(test_libretexts_search())