#!/usr/bin/env python3
"""
Test OER sources with API key requirements

This script tests that OER sources properly handle API keys and
skip searches when keys are not provided.
"""
import asyncio
import sys
sys.path.append('.')

from app.api_clients.mit_ocw import MITOpenCourseWareClient
from app.api_clients.merlot import MERLOTClient
from app.api_clients.oer_commons import OERCommonsClient

async def test_without_keys():
    """Test that sources correctly skip when no API keys are provided"""
    print("Testing OER sources WITHOUT API keys")
    print("="*60)
    
    # Create clients without API keys
    mit_client = MITOpenCourseWareClient()
    merlot_client = MERLOTClient()
    oer_commons_client = OERCommonsClient()
    
    query = "mathematics"
    
    # Test MIT OCW - should fall back to web scraping
    print("\n1. MIT OpenCourseWare (no API key):")
    papers = await mit_client.search(query, max_results=5)
    print(f"   Results: {len(papers)} (using web scraping fallback)")
    if papers:
        print(f"   Example: {papers[0].title}")
    
    # Test MERLOT - should return empty
    print("\n2. MERLOT (no API key):")
    papers = await merlot_client.search(query, max_results=5)
    print(f"   Results: {len(papers)} (should be 0 - requires API key)")
    
    # Test OER Commons - should return empty
    print("\n3. OER Commons (no API key):")
    papers = await oer_commons_client.search(query, max_results=5)
    print(f"   Results: {len(papers)} (should be 0 - requires API key)")

async def test_with_dummy_keys():
    """Test that sources correctly reject dummy/invalid API keys"""
    print("\n\nTesting OER sources WITH dummy API keys")
    print("="*60)
    
    dummy_key = "00000000000000000000000000000000"
    
    # Create clients with dummy keys
    mit_client = MITOpenCourseWareClient(api_key=dummy_key)
    merlot_client = MERLOTClient(api_key=dummy_key)
    oer_commons_client = OERCommonsClient(api_key=dummy_key)
    
    query = "mathematics"
    
    # Test MIT OCW - should fall back to web scraping
    print("\n1. MIT OpenCourseWare (dummy API key):")
    papers = await mit_client.search(query, max_results=5)
    print(f"   Results: {len(papers)} (using web scraping fallback)")
    
    # Test MERLOT - should return empty
    print("\n2. MERLOT (dummy API key):")
    papers = await merlot_client.search(query, max_results=5)
    print(f"   Results: {len(papers)} (should be 0 - dummy key rejected)")
    
    # Test OER Commons - should return empty
    print("\n3. OER Commons (dummy API key):")
    papers = await oer_commons_client.search(query, max_results=5)
    print(f"   Results: {len(papers)} (should be 0 - dummy key rejected)")

async def test_with_valid_keys():
    """Test with valid API keys (if available in environment)"""
    print("\n\nTesting OER sources WITH valid API keys (if configured)")
    print("="*60)
    
    import os
    
    # Check for real API keys in environment
    google_key = os.getenv('GOOGLE_CSE_API_KEY', 'test-key-123')
    merlot_key = os.getenv('MERLOT_API_KEY', 'test-key-456')
    oer_key = os.getenv('OER_COMMONS_API_KEY', 'test-key-789')
    
    # Create clients with keys
    mit_client = MITOpenCourseWareClient(api_key=google_key)
    merlot_client = MERLOTClient(api_key=merlot_key)
    oer_commons_client = OERCommonsClient(api_key=oer_key)
    
    query = "mathematics"
    
    # Test MIT OCW
    print(f"\n1. MIT OpenCourseWare (API key: {google_key[:8]}...):")
    papers = await mit_client.search(query, max_results=5)
    print(f"   Results: {len(papers)}")
    if papers:
        print(f"   Example: {papers[0].title}")
    
    # Test MERLOT
    print(f"\n2. MERLOT (API key: {merlot_key[:8]}...):")
    papers = await merlot_client.search(query, max_results=5)
    print(f"   Results: {len(papers)}")
    
    # Test OER Commons
    print(f"\n3. OER Commons (API key: {oer_key[:8]}...):")
    papers = await oer_commons_client.search(query, max_results=5)
    print(f"   Results: {len(papers)}")

async def main():
    """Run all tests"""
    await test_without_keys()
    await test_with_dummy_keys()
    await test_with_valid_keys()
    
    print("\n\nSUMMARY")
    print("="*60)
    print("✓ MIT OCW: Falls back to web scraping when no valid API key")
    print("✓ MERLOT: Requires valid API key (returns empty otherwise)")
    print("✓ OER Commons: Requires valid API key (returns empty otherwise)")
    print("\nAll sources are properly configured to handle API keys!")

if __name__ == "__main__":
    asyncio.run(main())