#!/usr/bin/env python3
"""Test search service directly"""
import asyncio
from app.models import SearchRequest
from app.services.search import SearchService

async def test_search():
    # Create search service
    search_service = SearchService()
    
    # Create test request
    request = SearchRequest(
        query="nutrition",
        page=1,
        per_page=10,
        require_authors=True
    )
    
    print(f"Testing search with request: {request}")
    
    try:
        # Perform search
        papers, sources = await search_service.search(request)
        
        print(f"\nResults:")
        print(f"Total papers found: {len(papers)}")
        print(f"Sources queried: {sources}")
        
        # Show first few results
        for i, paper in enumerate(papers[:3]):
            print(f"\nPaper {i+1}:")
            print(f"  Title: {paper.title}")
            print(f"  Authors: {', '.join(paper.authors) if paper.authors else 'No authors'}")
            print(f"  Year: {paper.year}")
            print(f"  Source: {paper.source}")
            
    except Exception as e:
        print(f"Error during search: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await search_service.close()

# Run the test
if __name__ == "__main__":
    asyncio.run(test_search())