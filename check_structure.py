#!/usr/bin/env python3
"""
Quick project structure verification
"""

import os
import sys

def check_project_structure():
    """Check if all expected files and directories exist"""
    print("📁 Checking OpenScholar project structure...")
    
    # Expected files and directories
    expected_items = [
        # Main files
        "requirements.txt",
        "database_setup.py", 
        "run_tests.sh",
        "app/main.py",
        
        # Security module
        "app/security/validation.py",
        
        # Cache module
        "app/cache/redis_cache.py",
        
        # Database module
        "app/database/models.py",
        "app/database/services.py",
        
        # Logging module
        "app/logging/structured_logger.py",
        
        # Test files
        "tests/test_security_validation.py",
        "tests/test_cache_system.py",
        "tests/test_api_endpoints.py",
        "tests/test_logging_system.py",
        "tests/test_frontend_components.py",
        
        # Frontend
        "frontend/",
        
        # Virtual environment
        "venv/",
    ]
    
    missing_items = []
    present_items = []
    
    for item in expected_items:
        if os.path.exists(item):
            present_items.append(item)
            print(f"✅ {item}")
        else:
            missing_items.append(item)
            print(f"❌ {item} - MISSING")
    
    print(f"\n📊 Structure check: {len(present_items)} present, {len(missing_items)} missing")
    
    if missing_items:
        print("\n⚠️  Missing items:")
        for item in missing_items:
            print(f"  - {item}")
        return False
    else:
        print("\n✅ All expected files and directories are present!")
        return True

def check_file_sizes():
    """Check file sizes to ensure they're not empty"""
    print("\n📏 Checking file sizes...")
    
    key_files = [
        "app/security/validation.py",
        "app/cache/redis_cache.py", 
        "app/database/models.py",
        "tests/test_security_validation.py",
        "requirements.txt"
    ]
    
    for file_path in key_files:
        if os.path.exists(file_path):
            size = os.path.getsize(file_path)
            if size > 0:
                print(f"✅ {file_path}: {size:,} bytes")
            else:
                print(f"❌ {file_path}: Empty file!")
        else:
            print(f"❌ {file_path}: Does not exist")

def check_python_version():
    """Check Python version compatibility"""
    print(f"\n🐍 Python version: {sys.version}")
    
    version_info = sys.version_info
    if version_info.major == 3 and version_info.minor >= 8:
        print("✅ Python version is compatible")
        return True
    else:
        print("❌ Python version may not be compatible (requires 3.8+)")
        return False

def main():
    """Run all checks"""
    print("🔍 OpenScholar Project Structure Check")
    print("=" * 50)
    
    # Change to project directory
    os.chdir("/Users/tristonmiller/Desktop/SwiftBarPlugins1/OpenScholar")
    
    checks = [
        check_python_version,
        check_project_structure,
        check_file_sizes
    ]
    
    all_passed = True
    
    for check in checks:
        try:
            if not check():
                all_passed = False
        except Exception as e:
            print(f"❌ Check {check.__name__} failed: {e}")
            all_passed = False
    
    print("\n" + "=" * 50)
    
    if all_passed:
        print("🎉 Project structure looks good!")
        print("\n🚀 Next steps:")
        print("1. Install requirements: pip install -r requirements.txt")
        print("2. Setup database: python database_setup.py setup")
        print("3. Run tests: ./run_tests.sh")
        print("4. Start server: python run.py")
    else:
        print("⚠️  Some checks failed. See output above for details.")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
