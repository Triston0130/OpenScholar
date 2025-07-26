#!/usr/bin/env python3
"""
Test all OER sources to see which ones actually return results
"""
import asyncio
import sys
sys.path.append('.')

from app.api_clients.oer_commons import OERCommonsClient
from app.api_clients.mit_ocw import MITOpenCourseWareClient
from app.api_clients.merlot import MERLOTClient
from app.api_clients.libretexts import LibreTextsClient
from app.api_clients.pressbooks import PressbooksClient
from app.api_clients.open_textbook_library import OpenTextbookLibraryClient

async def test_all():
    """Test all OER clients"""
    clients = [
        ("OER Commons", OERCommonsClient()),
        ("MIT OpenCourseWare", MITOpenCourseWareClient()),
        ("MERLOT", MERLOTClient()),
        ("LibreTexts", LibreTextsClient()),
        ("Pressbooks", PressbooksClient()),
        ("Open Textbook Library", OpenTextbookLibraryClient())
    ]
    
    print("Testing all OER sources with query 'mathematics'...\n")
    print(f"{'Source':<25} {'Status':<15} {'Results':<10}")
    print("-" * 50)
    
    for name, client in clients:
        try:
            results = await client.search("mathematics", max_results=5)
            status = "✓ WORKING" if results else "✗ NO RESULTS"
            print(f"{name:<25} {status:<15} {len(results):<10}")
        except Exception as e:
            print(f"{name:<25} {'✗ ERROR':<15} {str(e)[:30]}...")

if __name__ == "__main__":
    asyncio.run(test_all())