#!/usr/bin/env python3
"""
Test script for OpenScholar API
"""
import asyncio
import json
from app.models import SearchRequest
from app.services import SearchService

async def test_child_nutrition():
    """Test the API with child nutrition query"""
    print("🧪 Testing OpenScholar API Integration")
    print("=" * 50)
    
    service = SearchService()
    
    try:
        # Test query
        request = SearchRequest(
            query="child nutrition",
            year_start=2017,
            year_end=2024
        )
        
        print(f"🔍 Searching for: '{request.query}' ({request.year_start}-{request.year_end})")
        print("📚 Querying APIs: ERIC, CORE, DOAJ, Europe PMC, PubMed Central")
        print()
        
        # Perform search
        papers, sources = await service.search(request)
        
        print(f"✅ Search completed successfully!")
        print(f"📊 Total papers found: {len(papers)}")
        print(f"🔗 Sources queried: {', '.join(sources)}")
        print()
        
        # Show breakdown by source
        source_counts = {}
        for paper in papers:
            source_counts[paper.source] = source_counts.get(paper.source, 0) + 1
        
        print("📋 Results by source:")
        for source in sources:
            count = source_counts.get(source, 0)
            status = "✅" if count > 0 else "❌"
            print(f"  {status} {source}: {count} papers")
        print()
        
        # Show sample papers
        if papers:
            print("📄 Sample papers:")
            for i, paper in enumerate(papers[:3]):  # Show first 3
                print(f"  {i+1}. {paper.title[:70]}...")
                print(f"     Authors: {', '.join(paper.authors[:2])}{'...' if len(paper.authors) > 2 else ''}")
                print(f"     Year: {paper.year} | Source: {paper.source}")
                if paper.full_text_url:
                    print(f"     🔗 Full text: {paper.full_text_url[:50]}...")
                print()
        
        print("🎉 Test completed successfully!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        await service.close()

if __name__ == "__main__":
    asyncio.run(test_child_nutrition())