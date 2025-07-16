#!/usr/bin/env python3
"""
Test the citation count fixes in OpenScholar
"""
import asyncio
import json
from app.models import SearchRequest
from app.services import SearchService

async def test_citation_fixes():
    """Test the citation fixes with various queries"""
    print("🔧 Testing Citation Count Fixes in OpenScholar")
    print("=" * 60)
    
    service = SearchService()
    
    # Test cases with different temporal ranges to get diverse citation data
    test_cases = [
        {
            "query": "machine learning",
            "year_start": 2015,
            "year_end": 2020,
            "description": "Machine learning (2015-2020) - Should have higher citations"
        },
        {
            "query": "deep learning",
            "year_start": 2012,
            "year_end": 2018,
            "description": "Deep learning (2012-2018) - Should have high citations"
        },
        {
            "query": "child development",
            "year_start": 2010,
            "year_end": 2020,
            "description": "Child development (2010-2020) - Broader range for citations"
        },
        {
            "query": "artificial intelligence",
            "year_start": 2016,
            "year_end": 2019,
            "description": "AI (2016-2019) - Peak citation period"
        }
    ]
    
    try:
        for case in test_cases:
            print(f"\n🔍 Testing: {case['description']}")
            print("=" * 50)
            
            request = SearchRequest(
                query=case["query"],
                year_start=case["year_start"],
                year_end=case["year_end"],
                sort_by="citations"  # Sort by citations to see highest cited papers first
            )
            
            # Perform search
            papers, sources = await service.search(request)
            
            print(f"📊 Results: {len(papers)} papers from {len(sources)} sources")
            print(f"🔗 Sources: {', '.join(sources)}")
            
            # Analyze citation data
            citation_stats = {
                "papers_with_citations": 0,
                "papers_with_influential": 0,
                "max_citations": 0,
                "max_influential": 0,
                "total_citations": 0,
                "total_influential": 0,
                "by_source": {}
            }
            
            for paper in papers:
                # Track by source
                if paper.source not in citation_stats["by_source"]:
                    citation_stats["by_source"][paper.source] = {
                        "count": 0,
                        "with_citations": 0,
                        "max_citations": 0
                    }
                
                citation_stats["by_source"][paper.source]["count"] += 1
                
                # Regular citations
                if paper.citation_count is not None and paper.citation_count > 0:
                    citation_stats["papers_with_citations"] += 1
                    citation_stats["total_citations"] += paper.citation_count
                    citation_stats["max_citations"] = max(citation_stats["max_citations"], paper.citation_count)
                    citation_stats["by_source"][paper.source]["with_citations"] += 1
                    citation_stats["by_source"][paper.source]["max_citations"] = max(
                        citation_stats["by_source"][paper.source]["max_citations"], 
                        paper.citation_count
                    )
                
                # Influential citations
                if paper.influential_citation_count is not None and paper.influential_citation_count > 0:
                    citation_stats["papers_with_influential"] += 1
                    citation_stats["total_influential"] += paper.influential_citation_count
                    citation_stats["max_influential"] = max(citation_stats["max_influential"], paper.influential_citation_count)
            
            # Print statistics
            print(f"\n📈 Citation Statistics:")
            print(f"  Papers with citations: {citation_stats['papers_with_citations']}/{len(papers)} ({citation_stats['papers_with_citations']/len(papers)*100:.1f}%)")
            print(f"  Papers with influential citations: {citation_stats['papers_with_influential']}/{len(papers)} ({citation_stats['papers_with_influential']/len(papers)*100:.1f}%)")
            print(f"  Max citations: {citation_stats['max_citations']}")
            print(f"  Max influential citations: {citation_stats['max_influential']}")
            
            if citation_stats["papers_with_citations"] > 0:
                avg_citations = citation_stats["total_citations"] / citation_stats["papers_with_citations"]
                print(f"  Average citations (cited papers only): {avg_citations:.1f}")
            
            # Show top cited papers
            cited_papers = [p for p in papers if p.citation_count and p.citation_count > 0]
            if cited_papers:
                print(f"\n🏆 Top 3 cited papers:")
                for i, paper in enumerate(cited_papers[:3]):
                    print(f"  {i+1}. [{paper.citation_count} citations] {paper.title[:80]}...")
                    if paper.influential_citation_count:
                        print(f"     [{paper.influential_citation_count} influential] {paper.year} | {paper.source}")
                    else:
                        print(f"     {paper.year} | {paper.source}")
            
            # Show citation data by source
            print(f"\n📋 Citation data by source:")
            for source, stats in citation_stats["by_source"].items():
                citation_rate = stats["with_citations"] / stats["count"] * 100 if stats["count"] > 0 else 0
                print(f"  {source}: {stats['with_citations']}/{stats['count']} papers with citations ({citation_rate:.1f}%)")
                if stats["max_citations"] > 0:
                    print(f"    Max citations: {stats['max_citations']}")
        
        print(f"\n✅ Citation fixes testing completed!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        await service.close()

if __name__ == "__main__":
    asyncio.run(test_citation_fixes())