#!/usr/bin/env python3
"""
Test Google Custom Search API directly with your credentials
"""

import requests
import json

def test_google_search_api():
    """Test Google Custom Search API directly"""
    
    # Your credentials from the logs
    api_key = "AIzaSyALm0Lwy5Q_c8hPwnH61twDMgFYRP_8iPo"
    search_engine_id = "455715d38730941eb"
    
    print("🔍 Testing Google Custom Search API Directly")
    print("=" * 50)
    print(f"API Key: {api_key[:20]}...")
    print(f"Search Engine ID: {search_engine_id}")
    
    # Test 1: Basic search without filetype filter
    print("\n1. Testing basic search (no PDF filter)...")
    
    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "key": api_key,
        "cx": search_engine_id,
        "q": "machine learning",
        "num": 3
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            items = data.get("items", [])
            print(f"   ✅ Found {len(items)} results")
            
            for i, item in enumerate(items[:2], 1):
                print(f"      {i}. {item.get('title', 'No title')[:60]}...")
                
        else:
            print(f"   ❌ Error: {response.status_code}")
            print(f"   Response: {response.text[:200]}...")
            return False
            
    except Exception as e:
        print(f"   ❌ Request failed: {e}")
        return False
    
    # Test 2: PDF-only search (what OpenScholar uses)
    print("\n2. Testing PDF-only search...")
    
    params_pdf = {
        "key": api_key,
        "cx": search_engine_id,
        "q": "machine learning filetype:pdf",
        "num": 3,
        "fileType": "pdf"
    }
    
    try:
        response = requests.get(url, params=params_pdf, timeout=10)
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            items = data.get("items", [])
            print(f"   Found {len(items)} PDF results")
            
            if len(items) == 0:
                print("   ⚠️  No PDF results found - this might be the issue!")
                print("   Possible causes:")
                print("      • Search engine not configured for entire web")
                print("      • PDF filtering too restrictive")
                print("      • API quota exceeded")
            else:
                print("   ✅ PDF search working!")
                for i, item in enumerate(items[:2], 1):
                    print(f"      {i}. {item.get('title', 'No title')[:60]}...")
                    print(f"         URL: {item.get('link', 'No link')}")
                    
        else:
            print(f"   ❌ Error: {response.status_code}")
            error_data = response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text
            print(f"   Response: {error_data}")
            
    except Exception as e:
        print(f"   ❌ Request failed: {e}")
    
    # Test 3: Check quota usage
    print("\n3. Checking API usage...")
    try:
        # Simple query to check if API is working at all
        simple_params = {
            "key": api_key,
            "cx": search_engine_id,
            "q": "test",
            "num": 1
        }
        
        response = requests.get(url, params=simple_params, timeout=5)
        if response.status_code == 200:
            data = response.json()
            search_info = data.get("searchInformation", {})
            total_results = search_info.get("totalResults", "unknown")
            search_time = search_info.get("searchTime", "unknown")
            
            print(f"   ✅ API is responsive")
            print(f"   Total results available: {total_results}")
            print(f"   Search time: {search_time}s")
            
        elif response.status_code == 429:
            print("   ❌ Quota exceeded - you've hit the daily limit")
        elif response.status_code == 403:
            print("   ❌ API key issue - check permissions")
        else:
            print(f"   ❌ Unexpected error: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Health check failed: {e}")
    
    print("\n" + "=" * 50)
    print("💡 Troubleshooting Tips:")
    print("1. If no basic results: Check search engine setup at cse.google.com")
    print("2. If no PDF results: Try different search terms")
    print("3. If quota exceeded: Wait until tomorrow or enable billing")
    print("4. Make sure 'Search entire web' is enabled in your CSE")

if __name__ == "__main__":
    test_google_search_api()