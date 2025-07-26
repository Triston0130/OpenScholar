#!/usr/bin/env python3
"""
OpenScholar API Test Script
Test individual APIs to debug issues
"""

import asyncio
import sys
import os
from dotenv import load_dotenv

# Add the app directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.api_clients import ERICClient, COREClient, DOAJClient, SemanticScholarClient

# Load environment variables
load_dotenv()

async def test_eric():
    """Test ERIC API"""
    print("Testing ERIC API...")
    try:
        client = ERICClient()
        results = await client.search("education", 2020, 2025, limit=5)
        print(f"✅ ERIC: {len(results)} results")
        if results:
            print(f"   Sample title: {results[0].title[:50]}...")
        await client.close()
        return True
    except Exception as e:
        print(f"❌ ERIC Error: {e}")
        return False

async def test_core():
    """Test CORE API"""
    print("Testing CORE API...")
    try:
        api_key = os.getenv("CORE_API_KEY")
        if not api_key or api_key == "your_core_api_key_here":
            print("❌ CORE: No API key configured")
            return False
            
        client = COREClient(api_key=api_key)
        results = await client.search("education", 2020, 2025, limit=5)
        print(f"✅ CORE: {len(results)} results")
        if results:
            print(f"   Sample title: {results[0].title[:50]}...")
        await client.close()
        return True
    except Exception as e:
        print(f"❌ CORE Error: {e}")
        return False

async def test_doaj():
    """Test DOAJ API"""
    print("Testing DOAJ API...")
    try:
        client = DOAJClient()
        results = await client.search("education", 2020, 2025, limit=5)
        print(f"✅ DOAJ: {len(results)} results")
        if results:
            print(f"   Sample title: {results[0].title[:50]}...")
        await client.close()
        return True
    except Exception as e:
        print(f"❌ DOAJ Error: {e}")
        return False

async def test_semantic_scholar():
    """Test Semantic Scholar API"""
    print("Testing Semantic Scholar API...")
    try:
        client = SemanticScholarClient()
        results = await client.search("education", 2020, 2025)
        print(f"✅ Semantic Scholar: {len(results)} results")
        if results:
            print(f"   Sample title: {results[0].title[:50]}...")
        await client.close()
        return True
    except Exception as e:
        print(f"❌ Semantic Scholar Error: {e}")
        return False

async def main():
    """Run all API tests"""
    print("OpenScholar API Tests")
    print("=" * 50)
    
    tests = [
        ("ERIC", test_eric),
        ("CORE", test_core),
        ("DOAJ", test_doaj),
        ("Semantic Scholar", test_semantic_scholar),
    ]
    
    results = {}
    for name, test_func in tests:
        results[name] = await test_func()
        print()
    
    print("Summary:")
    print("-" * 30)
    for name, success in results.items():
        status = "✅ Working" if success else "❌ Failed"
        print(f"{name}: {status}")
    
    working_apis = sum(results.values())
    total_apis = len(results)
    print(f"\n{working_apis}/{total_apis} APIs working")
    
    if working_apis == 0:
        print("\n⚠️  No APIs are working. Check your configuration.")
    elif working_apis < total_apis:
        print("\n⚠️  Some APIs need attention. See errors above.")
    else:
        print("\n🎉 All APIs working correctly!")

if __name__ == "__main__":
    asyncio.run(main())
