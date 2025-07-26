#!/usr/bin/env python3
"""
Basic test script to verify OpenScholar components are working
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test that all main modules can be imported"""
    print("🧪 Testing imports...")
    
    try:
        from app.security.validation import SearchQueryValidator, APIKeyValidator
        print("✅ Security validation module imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import security validation: {e}")
        return False
    
    try:
        from app.cache.redis_cache import CacheManager
        print("✅ Cache module imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import cache module: {e}")
        return False
    
    try:
        from app.database.models import User, Collection, Paper
        print("✅ Database models imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import database models: {e}")
        return False
    
    try:
        from app.logging.structured_logger import setup_logging
        print("✅ Logging module imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import logging module: {e}")
        return False
    
    return True

def test_search_validation():
    """Test search query validation"""
    print("\n🔍 Testing search validation...")
    
    try:
        from app.security.validation import SearchQueryValidator
        
        # Test valid query
        valid_query = SearchQueryValidator(
            query="machine learning education",
            limit=50,
            year_start=2020,
            year_end=2024
        )
        print(f"✅ Valid query processed: {valid_query.query}")
        
        # Test invalid query (should raise ValidationError)
        try:
            SearchQueryValidator(query="<script>alert('xss')</script>")
            print("❌ XSS validation failed - should have rejected malicious query")
            return False
        except Exception:
            print("✅ XSS validation working - malicious query rejected")
        
        return True
        
    except Exception as e:
        print(f"❌ Search validation test failed: {e}")
        return False

def test_database_connection():
    """Test database connection and models"""
    print("\n🗄️ Testing database connection...")
    
    try:
        from app.database import initialize_database, check_database_health
        
        # Initialize database (SQLite by default)
        initialize_database()
        
        # Check health
        health = check_database_health()
        print(f"✅ Database health: {health['status']}")
        
        if health['status'] == 'healthy':
            print(f"✅ Database engine: {health.get('engine', 'unknown')}")
            return True
        else:
            print(f"❌ Database unhealthy: {health.get('error', 'unknown')}")
            return False
            
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False

def test_cache_system():
    """Test cache system initialization"""
    print("\n💾 Testing cache system...")
    
    try:
        from app.cache.redis_cache import CacheManager
        
        # Test cache manager creation
        cache_manager = CacheManager()
        print("✅ Cache manager created successfully")
        
        # Test key builder
        from app.cache.redis_cache import CacheKeyBuilder
        key_builder = CacheKeyBuilder()
        cache_key = key_builder.search_results_key("test query", limit=50)
        print(f"✅ Cache key generated: {cache_key}")
        
        return True
        
    except Exception as e:
        print(f"❌ Cache test failed: {e}")
        return False

def test_logging_system():
    """Test logging system"""
    print("\n📝 Testing logging system...")
    
    try:
        from app.logging.structured_logger import setup_logging, get_logger
        
        # Setup logging
        setup_logging("test_app", "INFO")
        logger = get_logger("test_module")
        
        # Test logging
        logger.info("Test log message", event_type="test_event")
        print("✅ Logging system working")
        
        return True
        
    except Exception as e:
        print(f"❌ Logging test failed: {e}")
        return False

def main():
    """Run all basic tests"""
    print("🚀 OpenScholar Basic Component Tests")
    print("=" * 50)
    
    tests = [
        test_imports,
        test_search_validation,
        test_database_connection,
        test_cache_system,
        test_logging_system
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} crashed: {e}")
            failed += 1
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All basic tests passed! OpenScholar components are working.")
        return True
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
