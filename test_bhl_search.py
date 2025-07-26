#!/usr/bin/env python3
"""
Test BHL in actual search scenarios
"""
import asyncio
import sys
sys.path.append('.')

from app.api_clients.biodiversity import BiodiversityClient
from app.api_clients.open_textbook_library import OpenTextbookLibraryClient
from app.api_clients.libretexts import LibreTextsClient
from app.api_clients.mit_ocw import MITOpenCourseWareClient

async def test_individual_sources():
    """Test each source individually"""
    print("Testing Individual Sources")
    print("="*60)
    
    # Test BHL
    print("\n1. BHL (Biodiversity Heritage Library):")
    bhl_client = BiodiversityClient(api_key="00000000-0000-0000-0000-000000000000")
    bhl_results = await bhl_client.search("biology", 1800, 2024, limit=10)
    print(f"   Results: {len(bhl_results)}")
    if bhl_results:
        print(f"   Sample: {bhl_results[0].title[:60]}...")
    
    # Test Open Textbook Library
    print("\n2. Open Textbook Library:")
    otl_client = OpenTextbookLibraryClient()
    otl_results = await otl_client.search("biology", max_results=10)
    print(f"   Results: {len(otl_results)}")
    if otl_results:
        print(f"   Sample: {otl_results[0].title[:60]}...")
    
    # Test LibreTexts
    print("\n3. LibreTexts:")
    lt_client = LibreTextsClient()
    lt_results = await lt_client.search("biology", max_results=10)
    print(f"   Results: {len(lt_results)}")
    if lt_results:
        print(f"   Sample: {lt_results[0].title[:60]}...")
    
    # Test MIT OCW
    print("\n4. MIT OpenCourseWare:")
    mit_client = MITOpenCourseWareClient()
    mit_results = await mit_client.search("biology", max_results=10)
    print(f"   Results: {len(mit_results)}")
    if mit_results:
        print(f"   Sample: {mit_results[0].title[:60]}...")

async def test_combined_search():
    """Test searching multiple sources together"""
    print("\n\nTesting Combined Search (Biology)")
    print("="*60)
    
    query = "biology"
    total_results = 0
    
    # Search all sources
    sources = [
        ("BHL", BiodiversityClient(api_key="00000000-0000-0000-0000-000000000000"), 
         lambda c: c.search(query, 1800, 2024, limit=10)),
        ("Open Textbook Library", OpenTextbookLibraryClient(), 
         lambda c: c.search(query, max_results=10)),
        ("LibreTexts", LibreTextsClient(), 
         lambda c: c.search(query, max_results=10)),
        ("MIT OCW", MITOpenCourseWareClient(), 
         lambda c: c.search(query, max_results=10))
    ]
    
    for name, client, search_func in sources:
        try:
            results = await search_func(client)
            print(f"\n{name}: {len(results)} results")
            total_results += len(results)
            
            # Show first result
            if results:
                paper = results[0]
                print(f"  Title: {paper.title[:70]}...")
                print(f"  Year: {paper.year}")
                print(f"  Source: {paper.source}")
                
        except Exception as e:
            print(f"\n{name}: ERROR - {str(e)}")
    
    print(f"\nTotal results across all sources: {total_results}")

async def test_search_terms():
    """Test BHL with various search terms"""
    print("\n\nTesting BHL with Different Search Terms")
    print("="*60)
    
    client = BiodiversityClient(api_key="00000000-0000-0000-0000-000000000000")
    
    terms = ["Darwin", "evolution", "species", "biology", "botany", "zoology"]
    
    for term in terms:
        results = await client.search(term, 1800, 2024, limit=5)
        print(f"\n'{term}': {len(results)} results")
        if results:
            print(f"  First: {results[0].title[:60]}...")

async def main():
    """Run all tests"""
    await test_individual_sources()
    await test_combined_search()
    await test_search_terms()
    
    print("\n\nSUMMARY")
    print("="*60)
    print("If BHL returns 0 results for 'biology' but works for 'Darwin',")
    print("it means BHL's content is more focused on historical/taxonomic works")
    print("rather than modern textbook-style content.")

if __name__ == "__main__":
    asyncio.run(main())