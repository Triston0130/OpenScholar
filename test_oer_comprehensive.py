#!/usr/bin/env python3
"""
Comprehensive test of OER sources with various queries
"""
import asyncio
import sys
sys.path.append('.')

from app.api_clients.open_textbook_library import OpenTextbookLibraryClient
from app.api_clients.libretexts import LibreTextsClient
from app.api_clients.mit_ocw import MITOpenCourseWareClient

async def test_query(query: str):
    """Test all working OER sources with a specific query"""
    print(f"\n{'='*60}")
    print(f"Testing query: '{query}'")
    print('='*60)
    
    clients = [
        ("Open Textbook Library", OpenTextbookLibraryClient()),
        ("LibreTexts", LibreTextsClient()),
        ("MIT OpenCourseWare", MITOpenCourseWareClient())
    ]
    
    total_results = 0
    
    for name, client in clients:
        try:
            papers = await client.search(query, max_results=20)
            print(f"\n{name}: {len(papers)} results")
            
            # Show first 3 results
            for i, paper in enumerate(papers[:3]):
                print(f"  {i+1}. {paper.title}")
                if paper.authors and paper.authors[0] != name:
                    print(f"     By: {', '.join(paper.authors[:2])}")
                    
            total_results += len(papers)
            
        except Exception as e:
            print(f"\n{name}: ERROR - {str(e)}")
    
    print(f"\nTotal results across all sources: {total_results}")
    return total_results

async def main():
    queries = [
        "mathematics",
        "calculus",
        "physics", 
        "biology",
        "chemistry",
        "computer science",
        "economics"
    ]
    
    print("COMPREHENSIVE OER SOURCE TEST")
    print("Testing multiple queries across all working sources...")
    
    all_results = 0
    for query in queries:
        results = await test_query(query)
        all_results += results
    
    print(f"\n{'='*60}")
    print(f"SUMMARY: {all_results} total results across {len(queries)} queries")
    print('='*60)

if __name__ == "__main__":
    asyncio.run(main())