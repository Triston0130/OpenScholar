#!/usr/bin/env python3
"""
Debug BHL in live search context
"""
import asyncio
import sys
import logging
sys.path.append('.')

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)

from app.api_clients.biodiversity import BiodiversityClient

async def main():
    # Test exactly how search service calls it
    client = BiodiversityClient()
    
    # Simulate search service call
    print("Simulating search service call to BHL...")
    print("API key:", client.api_key[:8] if client.api_key else "None")
    
    # Update API key like search service does
    client.api_key = "test-key-123"  # Simulate API key from frontend
    print("After update:", client.api_key[:8] if client.api_key else "None")
    
    results = await client.search(
        query="Darwin",
        year_start=2000,
        year_end=2024,
        discipline=None,
        education_level=None,
        limit=30
    )
    
    print(f"\nResults: {len(results)}")
    
if __name__ == "__main__":
    asyncio.run(main())