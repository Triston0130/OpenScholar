#!/usr/bin/env python3
"""Test what's blocking the import"""
import sys
print("1. Starting import test...")

try:
    print("2. Importing os and sys...")
    import os
    
    print("3. Setting up path...")
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    
    print("4. Trying to import app...")
    import app
    print("5. App module imported")
    
    print("6. Trying to import app.main...")
    from app import main
    print("7. Main module imported")
    
    print("8. Trying to import the FastAPI app...")
    from app.main import app
    print("9. SUCCESS: FastAPI app imported!")
    
except Exception as e:
    print(f"ERROR at step: {e}")
    import traceback
    traceback.print_exc()

print("Test complete")