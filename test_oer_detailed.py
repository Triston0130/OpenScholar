#!/usr/bin/env python3
"""
Detailed test of OER sources to diagnose why they return 0 results
"""

import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.api_clients import LibreTextsClient, MERLOTClient, OERCommonsClient

async def test_libretexts():
    """Test LibreTexts search with detailed logging"""
    print("\n=== Testing LibreTexts ===")
    client = LibreTextsClient()
    
    # Test with a common query
    queries = ["calculus", "biology", "chemistry"]
    
    for query in queries:
        print(f"\nSearching for: {query}")
        try:
            results = await client.search(query, max_results=5)
            print(f"Found {len(results)} results")
            
            for i, paper in enumerate(results[:2]):  # Show first 2 results
                print(f"\nResult {i+1}:")
                print(f"  Title: {paper.title}")
                print(f"  Source: {paper.source}")
                print(f"  Year: {paper.year}")
                print(f"  URL: {paper.full_text_url}")
                
        except Exception as e:
            print(f"Error searching for '{query}': {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()

async def test_merlot():
    """Test MERLOT search with detailed logging"""
    print("\n=== Testing MERLOT ===")
    client = MERLOTClient()
    
    queries = ["calculus", "biology", "chemistry"]
    
    for query in queries:
        print(f"\nSearching for: {query}")
        try:
            results = await client.search(query, max_results=5)
            print(f"Found {len(results)} results")
            
            for i, paper in enumerate(results[:2]):  # Show first 2 results
                print(f"\nResult {i+1}:")
                print(f"  Title: {paper.title}")
                print(f"  Source: {paper.source}")
                print(f"  Year: {paper.year}")
                print(f"  URL: {paper.full_text_url}")
                
        except Exception as e:
            print(f"Error searching for '{query}': {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()

async def test_oer_commons():
    """Test OER Commons search with detailed logging"""
    print("\n=== Testing OER Commons ===")
    client = OERCommonsClient()
    
    queries = ["calculus", "biology", "chemistry"]
    
    for query in queries:
        print(f"\nSearching for: {query}")
        try:
            results = await client.search(query, max_results=5)
            print(f"Found {len(results)} results")
            
            for i, paper in enumerate(results[:2]):  # Show first 2 results
                print(f"\nResult {i+1}:")
                print(f"  Title: {paper.title}")
                print(f"  Source: {paper.source}")
                print(f"  Year: {paper.year}")
                print(f"  URL: {paper.full_text_url}")
                
        except Exception as e:
            print(f"Error searching for '{query}': {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()

async def main():
    """Run all tests"""
    await test_libretexts()
    await test_merlot()
    await test_oer_commons()

if __name__ == "__main__":
    asyncio.run(main())