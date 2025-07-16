#!/usr/bin/env python3
"""
Test citation counts with older papers that should have more citations
"""
import asyncio
import httpx
from app.api_clients.europe_pmc import EuropePMCClient

async def test_older_papers():
    """Test Europe PMC with older papers that should have citations"""
    print("🔬 Testing citation counts with older papers")
    print("=" * 60)
    
    client = EuropePMCClient()
    
    # Test with older papers that should have more citations
    test_cases = [
        {
            "query": "machine learning",
            "year_start": 2010,
            "year_end": 2020,
            "description": "Machine learning papers from 2010-2020"
        },
        {
            "query": "deep learning",
            "year_start": 2012,
            "year_end": 2018,
            "description": "Deep learning papers from 2012-2018"
        },
        {
            "query": "child development",
            "year_start": 2015,
            "year_end": 2020,
            "description": "Child development papers from 2015-2020"
        }
    ]
    
    for case in test_cases:
        print(f"\n🔍 Testing: {case['description']}")
        
        try:
            # Build search query with year filter
            search_query = f"{case['query']} AND OPEN_ACCESS:y AND PUB_YEAR:[{case['year_start']} TO {case['year_end']}]"
            
            params = {
                "query": search_query,
                "format": "json",
                "pageSize": 10,
                "resultType": "core"
            }
            
            response = await client.client.get(f"{client.base_url}/search", params=params)
            data = response.json()
            
            print(f"📊 API Response status: {response.status_code}")
            
            if "resultList" in data and "result" in data["resultList"]:
                results = data["resultList"]["result"]
                print(f"📊 Total results: {len(results)}")
                
                citation_counts = []
                
                # Check citation data for all papers
                for i, item in enumerate(results):
                    cited_by = item.get('citedByCount', 0)
                    if cited_by is not None:
                        citation_counts.append(cited_by)
                        
                    print(f"  Paper {i+1}:")
                    print(f"    Title: {item.get('title', 'N/A')[:80]}...")
                    print(f"    Year: {item.get('pubYear', 'N/A')}")
                    print(f"    Citations: {cited_by}")
                
                # Statistics
                if citation_counts:
                    print(f"\n📈 Citation statistics:")
                    print(f"    Total papers with citation data: {len([c for c in citation_counts if c > 0])}")
                    print(f"    Max citations: {max(citation_counts)}")
                    print(f"    Min citations: {min(citation_counts)}")
                    print(f"    Average citations: {sum(citation_counts) / len(citation_counts):.1f}")
                    
                    # Show papers with highest citations
                    papers_with_citations = [(i, c) for i, c in enumerate(citation_counts) if c > 0]
                    if papers_with_citations:
                        papers_with_citations.sort(key=lambda x: x[1], reverse=True)
                        print(f"    Papers with most citations:")
                        for idx, citations in papers_with_citations[:3]:
                            paper = results[idx]
                            print(f"      - {citations} citations: {paper.get('title', 'N/A')[:60]}...")
                
        except Exception as e:
            print(f"❌ Error testing {case['description']}: {e}")
    
    await client.client.aclose()

async def test_semantic_scholar_with_api_key():
    """Test if Semantic Scholar needs an API key or has rate limiting issues"""
    print("\n🔬 Testing Semantic Scholar API rate limits and requirements")
    print("=" * 60)
    
    try:
        async with httpx.AsyncClient() as client:
            # Try a simple request with different approaches
            approaches = [
                {
                    "url": "https://api.semanticscholar.org/graph/v1/paper/search",
                    "params": {
                        "query": "machine learning",
                        "limit": 3,
                        "fields": "title,year,citationCount"
                    },
                    "headers": {},
                    "description": "Basic request"
                },
                {
                    "url": "https://api.semanticscholar.org/graph/v1/paper/search",
                    "params": {
                        "query": "machine learning",
                        "limit": 3,
                        "fields": "title,year,citationCount"
                    },
                    "headers": {"User-Agent": "OpenScholar Research Tool"},
                    "description": "With User-Agent"
                }
            ]
            
            for approach in approaches:
                print(f"\n🧪 Testing: {approach['description']}")
                try:
                    response = await client.get(
                        approach["url"],
                        params=approach["params"],
                        headers=approach["headers"],
                        timeout=10.0
                    )
                    
                    print(f"  Status: {response.status_code}")
                    
                    if response.status_code == 200:
                        data = response.json()
                        papers = data.get("data", [])
                        print(f"  Papers returned: {len(papers)}")
                        
                        for i, paper in enumerate(papers):
                            print(f"    Paper {i+1}: {paper.get('title', 'N/A')[:50]}...")
                            print(f"      Year: {paper.get('year', 'N/A')}")
                            print(f"      Citations: {paper.get('citationCount', 'N/A')}")
                    else:
                        print(f"  Error response: {response.text[:200]}")
                        
                except Exception as e:
                    print(f"  Exception: {e}")
                    
                # Wait between requests to avoid rate limiting
                await asyncio.sleep(2)
                
    except Exception as e:
        print(f"❌ Error testing Semantic Scholar: {e}")

async def main():
    """Run citation tests with older papers"""
    await test_older_papers()
    await test_semantic_scholar_with_api_key()

if __name__ == "__main__":
    asyncio.run(main())