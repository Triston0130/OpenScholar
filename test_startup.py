#!/usr/bin/env python3
"""Test startup sequence"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("1. Testing startup sequence...")

try:
    print("2. Importing FastAPI...")
    from fastapi import FastAPI
    
    print("3. Creating app instance...")
    app = FastAPI()
    
    print("4. Importing main module...")
    # This is where it might hang
    from app.main import lifespan
    
    print("5. Testing cache import...")
    from app.cache import initialize_cache
    
    print("6. Running cache initialization...")
    import asyncio
    asyncio.run(initialize_cache())
    
    print("7. SUCCESS!")
    
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()