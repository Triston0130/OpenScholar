"""
Test endpoint for OER sources
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any
import traceback

router = APIRouter()

@router.get("/api/test-oer")
async def test_oer_sources() -> Dict[str, Any]:
    """Test all OER sources and return status"""
    results = {}
    
    # Test imports
    sources = [
        ("OpenTextbookLibraryClient", "app.api_clients", "open_textbook_library_client"),
        ("PressbooksClient", "app.api_clients", "pressbooks_client"),
        ("LibreTextsClient", "app.api_clients", "libretexts_client"),
        ("MERLOTClient", "app.api_clients", "merlot_client"),
        ("OERCommonsClient", "app.api_clients", "oer_commons_client"),
        ("MITOpenCourseWareClient", "app.api_clients", "mit_ocw_client"),
    ]
    
    for class_name, module_path, service_attr in sources:
        try:
            # Try to import
            module = __import__(module_path, fromlist=[class_name])
            client_class = getattr(module, class_name)
            
            # Try to instantiate
            client = client_class()
            
            # Try a simple search
            test_results = await client.search("test", max_results=1)
            
            results[class_name] = {
                "status": "success",
                "can_import": True,
                "can_instantiate": True,
                "can_search": True,
                "result_count": len(test_results)
            }
            
        except Exception as e:
            results[class_name] = {
                "status": "error",
                "error": str(e),
                "traceback": traceback.format_exc()
            }
    
    # Check BeautifulSoup
    try:
        import bs4
        results["beautifulsoup4"] = {
            "status": "installed",
            "version": bs4.__version__
        }
    except ImportError:
        results["beautifulsoup4"] = {
            "status": "missing",
            "error": "BeautifulSoup4 not installed"
        }
    
    return results