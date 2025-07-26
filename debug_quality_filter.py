#!/usr/bin/env python3
"""
Debug quality filtering for Google Search results
"""

import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.api_clients.google_search import GoogleSearchClient
from app.utils.search_optimizer import SearchOptimizer

async def debug_quality_filter():
    print("=== Debug Quality Filter for Google Search ===")
    
    # Set environment variables
    os.environ['GOOGLE_SEARCH_API_KEY'] = 'AIzaSyCvk9CM1oQVs1d6T_VE-nIkAO0Gky0op7M'
    os.environ['GOOGLE_SEARCH_ENGINE_ID'] = 'f7e881b00f097472b'
    
    # Get Google Search results
    client = GoogleSearchClient()
    papers = await client.search(query="nutrition cognition", limit=5)
    
    print(f"Google Search returned {len(papers)} papers:")
    for i, paper in enumerate(papers, 1):
        print(f"\n{i}. Title: {paper.title}")
        print(f"   Authors: {paper.authors}")
        print(f"   Year: {paper.year}")
        print(f"   Abstract length: {len(paper.abstract) if paper.abstract else 0}")
        print(f"   Content type: {paper.content_type}")
    
    # Test quality filter
    print(f"\n=== Testing Quality Filter ===")
    optimizer = SearchOptimizer()
    quality_papers = optimizer._filter_quality_papers(papers, "Google Search")
    
    print(f"Quality filter passed: {len(quality_papers)} papers")
    for i, paper in enumerate(quality_papers, 1):
        print(f"  {i}. {paper.title[:50]}...")
    
    # Show what was filtered out
    filtered_out = len(papers) - len(quality_papers)
    if filtered_out > 0:
        print(f"\nFiltered out {filtered_out} papers:")
        for paper in papers:
            if paper not in quality_papers:
                print(f"  ❌ {paper.title[:50]}...")
                print(f"     Authors: {paper.authors}")
                print(f"     Year: {paper.year}")
                
                # Check each filter condition
                if not paper.title or len(paper.title.strip()) < 5:
                    print(f"     ❌ Rejected: title too short")
                elif paper.content_type == "paper" and (not paper.authors or 
                    len(paper.authors) == 0 or 
                    (len(paper.authors) == 1 and paper.authors[0].lower() in ['anonymous', 'unknown', ''])):
                    print(f"     ❌ Rejected: invalid authors")
                elif not paper.year or paper.year == "Unknown":
                    print(f"     ❌ Rejected: invalid year")
                else:
                    print(f"     ❌ Rejected: unknown reason")

if __name__ == "__main__":
    asyncio.run(debug_quality_filter())