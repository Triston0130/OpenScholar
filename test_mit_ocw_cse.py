#!/usr/bin/env python3
"""
Test MIT OpenCourseWare with Google Custom Search Engine

This script tests both the CSE and fallback implementations.
To use CSE, set these environment variables:
- GOOGLE_CSE_API_KEY: Your Google API key
- GOOGLE_CSE_ID or MIT_OCW_CSE_ID: Your Custom Search Engine ID
"""
import asyncio
import sys
import os
sys.path.append('.')

from app.api_clients.mit_ocw import MITOpenCourseWareClient
from app.api_clients.mit_ocw_cse import MITOpenCourseWareCSEClient

async def test_mit_ocw():
    """Test MIT OCW search with and without CSE"""
    queries = ["calculus", "machine learning", "quantum physics"]
    
    print("MIT OpenCourseWare Search Test")
    print("="*60)
    
    # Check if CSE is configured
    has_cse = bool(os.getenv('GOOGLE_CSE_API_KEY') and 
                   (os.getenv('GOOGLE_CSE_ID') or os.getenv('MIT_OCW_CSE_ID')))
    
    if has_cse:
        print("✓ Google CSE is configured")
    else:
        print("✗ Google CSE not configured (set GOOGLE_CSE_API_KEY and GOOGLE_CSE_ID)")
        print("  Will use web scraping fallback")
    
    print()
    
    # Test regular client (will use CSE if available)
    client = MITOpenCourseWareClient()
    
    for query in queries:
        print(f"\nSearching for: '{query}'")
        print("-"*40)
        
        try:
            papers = await client.search(query, max_results=10)
            print(f"Found {len(papers)} results")
            
            for i, paper in enumerate(papers[:5], 1):
                print(f"\n{i}. {paper.title}")
                print(f"   URL: {paper.full_text_url}")
                if hasattr(paper, 'doi') and paper.doi:
                    print(f"   Course: {paper.doi}")
                print(f"   Year: {paper.year}")
                print(f"   Abstract: {paper.abstract[:150]}...")
                
        except Exception as e:
            print(f"Error: {str(e)}")
    
    # Test CSE client directly if configured
    if has_cse:
        print("\n" + "="*60)
        print("Testing Google CSE Client Directly")
        print("="*60)
        
        cse_client = MITOpenCourseWareCSEClient()
        
        try:
            papers = await cse_client.search("artificial intelligence", max_results=5)
            print(f"\nDirect CSE search found {len(papers)} results for 'artificial intelligence'")
            
            for i, paper in enumerate(papers, 1):
                print(f"\n{i}. {paper.title}")
                if hasattr(paper, 'doi') and paper.doi:
                    print(f"   Course Number: {paper.doi.replace('MIT-', '')}")
                    
        except Exception as e:
            print(f"CSE Error: {str(e)}")

async def main():
    """Run the test"""
    print("\nTo enable Google CSE, set these environment variables:")
    print("export GOOGLE_CSE_API_KEY='your-api-key'")
    print("export GOOGLE_CSE_ID='your-cse-id'")
    print("\nTo create a CSE for MIT OCW:")
    print("1. Go to https://programmablesearchengine.google.com/")
    print("2. Create a new search engine")
    print("3. Add 'ocw.mit.edu' as a site to search")
    print("4. Get your CSE ID and API key\n")
    
    await test_mit_ocw()

if __name__ == "__main__":
    asyncio.run(main())