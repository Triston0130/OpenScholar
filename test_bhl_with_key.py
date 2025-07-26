#!/usr/bin/env python3
"""
Test BHL API with a real API key
"""
import asyncio
import httpx
import json

async def test_bhl_api(api_key: str):
    """Test BHL API directly"""
    
    print(f"Testing BHL API with key: {api_key[:8]}...")
    print("="*60)
    
    # Test different API operations
    operations = [
        {
            "name": "GetLanguages (simple test)",
            "params": {
                "op": "GetLanguages",
                "apikey": api_key,
                "format": "json"
            }
        },
        {
            "name": "PublicationSearch (basic)",
            "params": {
                "op": "PublicationSearch",
                "searchterm": "darwin",
                "apikey": api_key,
                "format": "json"
            }
        },
        {
            "name": "PublicationSearchAdvanced",
            "params": {
                "op": "PublicationSearchAdvanced",
                "searchterm": "darwin",
                "searchtype": "F",
                "apikey": api_key,
                "format": "json",
                "limit": 5
            }
        }
    ]
    
    async with httpx.AsyncClient() as client:
        for op in operations:
            print(f"\nTesting: {op['name']}")
            print("-" * 40)
            
            url = "https://www.biodiversitylibrary.org/api3"
            
            try:
                response = await client.get(url, params=op['params'], timeout=30)
                print(f"Status Code: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Check API response status
                    if "Status" in data:
                        print(f"API Status: {data['Status']}")
                    
                    if "ErrorMessage" in data:
                        print(f"Error Message: {data['ErrorMessage']}")
                    
                    if "Result" in data:
                        results = data["Result"]
                        if isinstance(results, list):
                            print(f"Results: {len(results)} items")
                            if results and op['name'] == "PublicationSearchAdvanced":
                                # Show first result
                                first = results[0]
                                print(f"First result: {first.get('Title', 'No title')}")
                        else:
                            print(f"Result type: {type(results)}")
                    
                else:
                    print(f"Error: HTTP {response.status_code}")
                    print(f"Response: {response.text[:200]}")
                    
            except Exception as e:
                print(f"Exception: {type(e).__name__}: {str(e)}")

async def main():
    print("BHL API Key Test")
    print("\nTo test your API key, run:")
    print("python3 test_bhl_with_key.py YOUR_API_KEY")
    print("\nIf you don't have an API key, register at:")
    print("https://www.biodiversitylibrary.org/api3/docs/docs.html")
    
    # Check if API key was provided as argument
    import sys
    if len(sys.argv) > 1:
        api_key = sys.argv[1]
        await test_bhl_api(api_key)
    else:
        print("\nNo API key provided. Testing with demo key...")
        await test_bhl_api("00000000-0000-0000-0000-000000000000")

if __name__ == "__main__":
    asyncio.run(main())