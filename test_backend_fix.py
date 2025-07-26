#!/usr/bin/env python3
"""Test if the backend is working properly after fixes"""
import asyncio
import aiohttp
import time

async def test_backend():
    """Test the backend endpoints"""
    
    base_url = "http://localhost:8765"
    
    print("Testing backend health...")
    
    async with aiohttp.ClientSession() as session:
        # Test health endpoint
        try:
            async with session.get(f"{base_url}/health") as resp:
                print(f"Health check: {resp.status}")
                if resp.status == 200:
                    data = await resp.json()
                    print(f"Response: {data}")
        except Exception as e:
            print(f"Health check failed: {e}")
        
        # Test if server is responsive
        print("\nTesting responsiveness...")
        start = time.time()
        try:
            async with session.get(f"{base_url}/api/search?query=test", timeout=aiohttp.ClientTimeout(total=5)) as resp:
                elapsed = time.time() - start
                print(f"Search endpoint responded in {elapsed:.2f}s - Status: {resp.status}")
        except asyncio.TimeoutError:
            print("Search endpoint timed out!")
        except Exception as e:
            print(f"Search endpoint error: {e}")

if __name__ == "__main__":
    asyncio.run(test_backend())