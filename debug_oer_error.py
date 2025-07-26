#!/usr/bin/env python3
"""
Debug script to find exact OER source errors
"""

import sys
import traceback

# Test imports
print("Testing imports...")

try:
    from app.api_clients import OpenTextbookLibraryClient
    print("✓ OpenTextbookLibraryClient imported")
except Exception as e:
    print(f"✗ OpenTextbookLibraryClient import failed: {e}")
    traceback.print_exc()

try:
    from app.api_clients import PressbooksClient
    print("✓ PressbooksClient imported")
except Exception as e:
    print(f"✗ PressbooksClient import failed: {e}")
    traceback.print_exc()

try:
    from app.api_clients import LibreTextsClient
    print("✓ LibreTextsClient imported")
except Exception as e:
    print(f"✗ LibreTextsClient import failed: {e}")
    traceback.print_exc()

try:
    from app.api_clients import MERLOTClient
    print("✓ MERLOTClient imported")
except Exception as e:
    print(f"✗ MERLOTClient import failed: {e}")
    traceback.print_exc()

try:
    from app.api_clients import OERCommonsClient
    print("✓ OERCommonsClient imported")
except Exception as e:
    print(f"✗ OERCommonsClient import failed: {e}")
    traceback.print_exc()

try:
    from app.api_clients import MITOpenCourseWareClient
    print("✓ MITOpenCourseWareClient imported")
except Exception as e:
    print(f"✗ MITOpenCourseWareClient import failed: {e}")
    traceback.print_exc()

print("\nChecking for BeautifulSoup...")
try:
    import bs4
    print(f"✓ BeautifulSoup4 version {bs4.__version__} is installed")
except ImportError:
    print("✗ BeautifulSoup4 is NOT installed - this is required for DOAB and LibreTexts")
    print("  Install with: pip install beautifulsoup4")

print("\nChecking search service integration...")
try:
    from app.services.search import SearchService
    service = SearchService()
    
    # Check if OER clients are initialized
    attrs_to_check = [
        'open_textbook_library_client',
        'pressbooks_client', 
        'libretexts_client',
        'merlot_client',
        'oer_commons_client',
        'mit_ocw_client'
    ]
    
    for attr in attrs_to_check:
        if hasattr(service, attr):
            print(f"✓ SearchService has {attr}")
        else:
            print(f"✗ SearchService missing {attr}")
            
except Exception as e:
    print(f"✗ SearchService check failed: {e}")
    traceback.print_exc()

print("\nDone!")