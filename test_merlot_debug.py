#!/usr/bin/env python3
"""
Debug MERLOT API response
"""

import httpx
import asyncio
import json

async def test_merlot_api_debug():
    """Test MERLOT API with different parameters"""
    print("\n=== Testing MERLOT API Debug ===")
    url = "https://www.merlot.org/merlot/materials.json"
    
    # Try different parameter combinations
    test_cases = [
        {
            'name': 'Original parameters',
            'params': {
                'keywords': 'biology',
                'materialType': 'Open Textbook',
                'licenseType': 'cc',
                'sort': 'relevance',
                'page': 1,
                'pageSize': 5
            }
        },
        {
            'name': 'Simple search',
            'params': {
                'keywords': 'biology'
            }
        },
        {
            'name': 'Without material type filter',
            'params': {
                'keywords': 'biology',
                'licenseType': 'cc',
                'page': 1,
                'pageSize': 5
            }
        }
    ]
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        for test in test_cases:
            print(f"\n--- {test['name']} ---")
            try:
                print(f"Parameters: {test['params']}")
                response = await client.get(url, params=test['params'])
                print(f"Status code: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    print(f"Full response: {json.dumps(data, indent=2)}")
                else:
                    print(f"Response text: {response.text}")
                    
            except Exception as e:
                print(f"Error: {type(e).__name__}: {e}")

if __name__ == "__main__":
    asyncio.run(test_merlot_api_debug())