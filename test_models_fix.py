#!/usr/bin/env python3
"""
Test script to verify the SQLAlchemy models work correctly after fixing the metadata column issue
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_models_import():
    """Test that models can be imported without SQLAlchemy errors"""
    print("🧪 Testing model imports...")
    
    try:
        from app.database.models import User, Collection, Paper, Tag, SearchHistory, APIUsage, UserSession
        print("✅ All models imported successfully")
        
        # Test that we can create instances
        user = User(
            email="test@example.com",
            name="Test User",
            role="researcher"
        )
        print("✅ User model instance created")
        
        collection = Collection(
            name="Test Collection",
            description="A test collection",
            user_id=user.id,
            extra_metadata={"test": "data"}  # Test the renamed column
        )
        print("✅ Collection model instance created with extra_metadata")
        
        paper = Paper(
            title="Test Paper",
            authors=["Test Author"],
            source="test",
            extra_metadata={"doi": "10.1234/test"}  # Test the renamed column
        )
        print("✅ Paper model instance created with extra_metadata")
        
        return True
        
    except Exception as e:
        print(f"❌ Model import test failed: {e}")
        return False

def test_database_initialization():
    """Test that database can be initialized with the new models"""
    print("\n🗄️ Testing database initialization...")
    
    try:
        from app.database import initialize_database, create_tables, check_database_health
        
        # Initialize database (SQLite by default)
        initialize_database()
        print("✅ Database initialized")
        
        # Create tables
        create_tables()
        print("✅ Database tables created successfully")
        
        # Check health
        health = check_database_health()
        print(f"✅ Database health: {health['status']}")
        
        return health['status'] == 'healthy'
        
    except Exception as e:
        print(f"❌ Database initialization test failed: {e}")
        return False

def test_services():
    """Test that database services work with new column names"""
    print("\n🔧 Testing database services...")
    
    try:
        from app.database.services import UserService, CollectionService, PaperService
        from app.database import get_session
        
        with get_session() as session:
            # Test user creation
            user = UserService.create_user(
                session, 
                email="test@example.com",
                name="Test User",
                role="researcher"
            )
            print(f"✅ User created: {user.email}")
            
            # Test collection creation with extra_metadata
            collection = CollectionService.create_collection(
                session,
                user_id=str(user.id),
                name="Test Collection",
                description="Test collection with metadata"
            )
            print(f"✅ Collection created: {collection.name}")
            
            # Test paper creation with extra_metadata
            paper_data = {
                "title": "Test Paper",
                "authors": ["Test Author"],
                "source": "test",
                "extra_metadata": {"test": "metadata"}
            }
            paper = PaperService.create_or_update_paper(session, paper_data)
            print(f"✅ Paper created: {paper.title}")
            
        return True
        
    except Exception as e:
        print(f"❌ Database services test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🔧 OpenScholar SQLAlchemy Models Test (After metadata column fix)")
    print("=" * 70)
    
    tests = [
        test_models_import,
        test_database_initialization,
        test_services
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
    
    print("\n" + "=" * 70)
    print(f"📊 Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All tests passed! SQLAlchemy models are working correctly.")
        print("\n✅ The metadata column issue has been fixed successfully!")
        print("✅ Database models now use 'extra_metadata' instead of 'metadata'")
        print("✅ Ready to run the application with: python run.py")
        return True
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
