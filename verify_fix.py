#!/usr/bin/env python3
"""
Quick verification script to test if main.py can be imported without the metadata column error
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_main_import():
    """Test that main.py can be imported without SQLAlchemy errors"""
    print("🧪 Testing main.py import...")
    
    try:
        # This should not raise a SQLAlchemy error about metadata being reserved
        from app.main import app
        print("✅ main.py imported successfully")
        print("✅ FastAPI app created without SQLAlchemy errors")
        
        # Test that we can access the app
        print(f"✅ App title: {app.title}")
        print(f"✅ App version: {app.version}")
        
        return True
        
    except Exception as e:
        print(f"❌ main.py import failed: {e}")
        return False

def test_database_models():
    """Test that database models can be used"""
    print("\n🗄️ Testing database models...")
    
    try:
        from app.database.models import Collection, Paper
        
        # Test that we can create instances with the new column names
        collection = Collection(
            name="Test",
            user_id="test-user-id",
            extra_metadata={"test": "data"}
        )
        print("✅ Collection model works with extra_metadata")
        
        paper = Paper(
            title="Test Paper",
            authors=["Test Author"],
            source="test",
            extra_metadata={"doi": "10.1234/test"}
        )
        print("✅ Paper model works with extra_metadata")
        
        return True
        
    except Exception as e:
        print(f"❌ Database models test failed: {e}")
        return False

def main():
    """Run verification tests"""
    print("🔧 OpenScholar SQLAlchemy Fix Verification")
    print("=" * 50)
    
    tests = [
        test_main_import,
        test_database_models
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
    print(f"📊 Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 SQLAlchemy metadata column issue FIXED!")
        print("✅ The application should now start without errors.")
        print("✅ Ready to run: python run.py")
        return True
    else:
        print("⚠️  Some verification tests failed.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
