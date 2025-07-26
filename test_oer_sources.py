#!/usr/bin/env python3
"""
Test script for OER sources
Run this to verify OER sources are working without BeautifulSoup dependency
"""

import asyncio
import sys
sys.path.append('.')

from app.api_clients import (
    OpenTextbookLibraryClient,
    PressbooksClient,
    LibreTextsClient,
    MERLOTClient,
    OERCommonsClient,
    MITOpenCourseWareClient
)

async def test_source(client_class, name, query="mathematics"):
    """Test a single OER source"""
    print(f"\n{'='*50}")
    print(f"Testing {name}...")
    print(f"{'='*50}")
    
    try:
        client = client_class()
        results = await client.search(query, max_results=3)
        
        if results:
            print(f"✅ SUCCESS: Found {len(results)} results")
            for i, paper in enumerate(results, 1):
                print(f"\n{i}. {paper.title}")
                print(f"   Authors: {', '.join(paper.authors[:3])}")
                print(f"   Source: {paper.source}")
                print(f"   URL: {paper.full_text_url}")
        else:
            print(f"⚠️  No results found for query '{query}'")
            
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()

async def main():
    """Test all OER sources"""
    print("Testing OER Sources Integration")
    print("Query: 'mathematics'")
    
    sources = [
        (OpenTextbookLibraryClient, "Open Textbook Library"),
        (PressbooksClient, "Pressbooks Networks"),
        (LibreTextsClient, "LibreTexts"),
        (MERLOTClient, "MERLOT"),
        (OERCommonsClient, "OER Commons"),
        (MITOpenCourseWareClient, "MIT OpenCourseWare"),
    ]
    
    for client_class, name in sources:
        await test_source(client_class, name)
    
    print(f"\n{'='*50}")
    print("Test complete!")

if __name__ == "__main__":
    asyncio.run(main())