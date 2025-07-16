#!/usr/bin/env python3
"""
Debug script to test citation count functionality in OpenScholar API
"""
import asyncio
import json
import httpx
from app.api_clients.semantic_scholar import SemanticScholarClient
from app.api_clients.europe_pmc import EuropePMCClient

async def test_semantic_scholar_citation_data():
    """Test Semantic Scholar API response and citation data"""
    print("🔬 Testing Semantic Scholar API citation data")
    print("=" * 60)
    
    client = SemanticScholarClient()
    
    # Test with a well-known paper that should have citations
    test_queries = [
        "attention is all you need",
        "BERT pre-training",
        "deep learning",
        "machine learning education"
    ]
    
    for query in test_queries:
        print(f"\n🔍 Testing query: '{query}'")
        try:
            # Make direct API call to see raw response
            params = {
                "query": query,
                "limit": 5,
                "fields": "title,authors,abstract,year,venue,publicationTypes,doi,url,citationCount"
            }
            
            response = await client.client.get(f"{client.base_url}paper/search", params=params)
            data = response.json()
            
            print(f"📊 API Response status: {response.status_code}")
            print(f"📊 Total results in response: {len(data.get('data', []))}")
            
            # Check raw citation data
            for i, item in enumerate(data.get("data", [])[:3]):
                print(f"\n  Paper {i+1}:")
                print(f"    Title: {item.get('title', 'N/A')[:80]}...")
                print(f"    Year: {item.get('year', 'N/A')}")
                print(f"    Citation Count (raw): {item.get('citationCount', 'N/A')}")
                print(f"    DOI: {item.get('doi', 'N/A')}")
                print(f"    Publication Types: {item.get('publicationTypes', [])}")
            
            # Test normalized papers
            papers = await client.search(query)
            print(f"\n📋 Normalized papers: {len(papers)}")
            
            for i, paper in enumerate(papers[:3]):
                print(f"  Paper {i+1} citation_count: {paper.citation_count}")
                
        except Exception as e:
            print(f"❌ Error testing '{query}': {e}")
    
    await client.client.aclose()

async def test_europe_pmc_citation_data():
    """Test Europe PMC API response and citation data"""
    print("\n🔬 Testing Europe PMC API citation data")
    print("=" * 60)
    
    client = EuropePMCClient()
    
    test_queries = [
        "COVID-19",
        "machine learning",
        "education research",
        "child development"
    ]
    
    for query in test_queries:
        print(f"\n🔍 Testing query: '{query}'")
        try:
            # Build search query
            search_query = f"{query} AND OPEN_ACCESS:y"
            
            params = {
                "query": search_query,
                "format": "json",
                "pageSize": 5,
                "resultType": "core"
            }
            
            response = await client.client.get(f"{client.base_url}/search", params=params)
            data = response.json()
            
            print(f"📊 API Response status: {response.status_code}")
            
            if "resultList" in data and "result" in data["resultList"]:
                results = data["resultList"]["result"]
                print(f"📊 Total results in response: {len(results)}")
                
                # Check raw citation data
                for i, item in enumerate(results[:3]):
                    print(f"\n  Paper {i+1}:")
                    print(f"    Title: {item.get('title', 'N/A')[:80]}...")
                    print(f"    Year: {item.get('pubYear', 'N/A')}")
                    print(f"    Citation Count (citedByCount): {item.get('citedByCount', 'N/A')}")
                    print(f"    DOI: {item.get('doi', 'N/A')}")
                    print(f"    Has Full Text URL: {'fullTextUrlList' in item}")
                
                # Test normalized papers
                papers = await client.search(query, 2020, 2024)
                print(f"\n📋 Normalized papers: {len(papers)}")
                
                for i, paper in enumerate(papers[:3]):
                    print(f"  Paper {i+1} citation_count: {paper.citation_count}")
            else:
                print("❌ No results found in response")
                
        except Exception as e:
            print(f"❌ Error testing '{query}': {e}")
    
    await client.client.aclose()

async def test_api_documentation():
    """Test API endpoints directly to understand field names"""
    print("\n📚 Testing API documentation and field names")
    print("=" * 60)
    
    # Test Semantic Scholar with a known high-citation paper
    print("\n🔬 Testing Semantic Scholar with known high-citation paper...")
    try:
        async with httpx.AsyncClient() as client:
            # Search for "Attention is All You Need" - a famous transformer paper
            response = await client.get(
                "https://api.semanticscholar.org/graph/v1/paper/search",
                params={
                    "query": "Attention is All You Need transformer",
                    "limit": 1,
                    "fields": "title,authors,year,citationCount,url,doi"
                }
            )
            data = response.json()
            
            if data.get("data"):
                paper = data["data"][0]
                print(f"  Title: {paper.get('title')}")
                print(f"  Citation Count: {paper.get('citationCount')}")
                print(f"  Year: {paper.get('year')}")
                print(f"  Available fields: {list(paper.keys())}")
            
    except Exception as e:
        print(f"❌ Error testing Semantic Scholar: {e}")
    
    # Test Europe PMC with a known paper
    print("\n🔬 Testing Europe PMC with known paper...")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://www.ebi.ac.uk/europepmc/webservices/rest/search",
                params={
                    "query": "COVID-19 AND OPEN_ACCESS:y",
                    "format": "json",
                    "pageSize": 1,
                    "resultType": "core"
                }
            )
            data = response.json()
            
            if data.get("resultList", {}).get("result"):
                paper = data["resultList"]["result"][0]
                print(f"  Title: {paper.get('title')}")
                print(f"  Citation Count (citedByCount): {paper.get('citedByCount')}")
                print(f"  Year: {paper.get('pubYear')}")
                print(f"  Available fields: {list(paper.keys())[:10]}...")  # Show first 10 fields
                
                # Check if citedByCount exists and is populated
                cited_by = paper.get('citedByCount')
                if cited_by is not None:
                    print(f"  ✅ citedByCount field found with value: {cited_by}")
                else:
                    print(f"  ❌ citedByCount field is None or missing")
                    
    except Exception as e:
        print(f"❌ Error testing Europe PMC: {e}")

async def main():
    """Run all citation debugging tests"""
    print("🐛 OpenScholar Citation Count Debugging")
    print("=" * 80)
    
    await test_semantic_scholar_citation_data()
    await test_europe_pmc_citation_data()
    await test_api_documentation()
    
    print("\n✅ Citation debugging tests completed!")

if __name__ == "__main__":
    asyncio.run(main())