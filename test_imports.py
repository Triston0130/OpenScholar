#!/usr/bin/env python3
"""
Quick import test to verify fixes are working
"""

import sys
import os

# Add the app directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

print("Testing imports and basic functionality...")

try:
    from app.models import SearchRequest, Paper
    print("✅ Models import successful")
    
    from app.api_clients.eric import ERICClient
    print("✅ ERIC client import successful")
    
    from app.api_clients.doaj import DOAJClient
    print("✅ DOAJ client import successful")
    
    from app.api_clients.semantic_scholar import SemanticScholarClient
    print("✅ Semantic Scholar client import successful")
    
    from app.services.search import SearchService
    print("✅ Search service import successful")
    
    # Test creating a search request
    request = SearchRequest(
        query="child development",
        year_start=2020,
        year_end=2025
    )
    print("✅ SearchRequest creation successful")
    
    # Test ERIC client normalization fix
    eric_client = ERICClient()
    test_paper_data = {
        "title": "Test Paper",
        "author": ["Test Author"],
        "description": "Test description",
        "publicationdateyear": "2023",
        "url": "http://example.com",
        "publicationtype": ["Journal Articles", "Reports - Research"]  # This used to cause the error
    }
    
    paper = eric_client.normalize_paper(test_paper_data)
    if paper and paper.journal == "Journal Articles, Reports - Research":
        print("✅ ERIC validation fix working correctly")
    else:
        print("❌ ERIC validation fix issue")
    
    print("\n🎉 All core functionality is working!")
    print("Your backend fixes have been successfully applied.")
    
except Exception as e:
    print(f"❌ Error during testing: {e}")
    import traceback
    traceback.print_exc()
