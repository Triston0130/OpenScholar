#\!/usr/bin/env python3
"""Test comprehensive textbook search"""

import asyncio
from app.api_clients.open_textbook_library_scraper import OpenTextbookLibraryScraper
from app.api_clients.libretexts_enhanced import LibreTextsEnhanced

async def test_comprehensive():
    print("Comprehensive Textbook Search Test")
    print("="*60)
    
    # Initialize clients
    otl_client = OpenTextbookLibraryScraper()
    libre_client = LibreTextsEnhanced()
    
    # Test with broader search terms to get more results
    test_queries = [
        ("", 200),  # Empty query should return all/many books
        ("textbook", 100),
        ("introduction", 100),
        ("college", 100)
    ]
    
    total_unique_books = set()
    
    for query, limit in test_queries:
        print(f"\nSearching for: '{query}' (limit: {limit})")
        
        # Search both sources
        otl_results = await otl_client.search(query, max_results=limit)
        libre_results = await libre_client.search(query, max_results=limit)
        
        print(f"  Open Textbook Library: {len(otl_results)} books")
        print(f"  LibreTexts: {len(libre_results)} books")
        print(f"  Combined: {len(otl_results) + len(libre_results)} books")
        
        # Track unique titles
        for paper in otl_results + libre_results:
            total_unique_books.add(paper.title)
    
    print(f"\n{'='*60}")
    print(f"TOTAL UNIQUE TEXTBOOKS FOUND: {len(total_unique_books)}")
    print(f"{'='*60}")
    
    # Show subject diversity
    print("\nSubject Coverage Test:")
    subjects = ["mathematics", "physics", "chemistry", "biology", "history", 
                "psychology", "economics", "computer science", "engineering"]
    
    subject_totals = {}
    for subject in subjects:
        otl_results = await otl_client.search(subject, max_results=50)
        libre_results = await libre_client.search(subject, max_results=50)
        total = len(otl_results) + len(libre_results)
        subject_totals[subject] = total
        print(f"  {subject}: {total} books")
    
    print(f"\nTotal books across subjects: {sum(subject_totals.values())}")

if __name__ == "__main__":
    asyncio.run(test_comprehensive())
