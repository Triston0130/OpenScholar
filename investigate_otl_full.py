#!/usr/bin/env python3
"""Investigate Open Textbook Library full catalog access"""

import httpx
import asyncio
from bs4 import BeautifulSoup
import json

async def investigate_otl():
    async with httpx.AsyncClient() as client:
        # Try different potential API endpoints
        endpoints = [
            "https://open.umn.edu/opentextbooks/textbooks.json",
            "https://open.umn.edu/opentextbooks/api/textbooks",
            "https://open.umn.edu/opentextbooks/textbooks.json?limit=1000",
            "https://open.umn.edu/opentextbooks/textbooks.json?page=1&per_page=100",
            "https://open.umn.edu/opentextbooks/books.json",
            "https://open.umn.edu/api/v1/textbooks"
        ]
        
        print("Testing potential API endpoints:")
        for endpoint in endpoints:
            try:
                response = await client.get(endpoint, timeout=5.0)
                if response.status_code == 200:
                    try:
                        data = response.json()
                        if isinstance(data, dict) and "data" in data:
                            count = len(data["data"])
                        elif isinstance(data, list):
                            count = len(data)
                        else:
                            count = "Unknown structure"
                        print(f"✓ {endpoint}: Status {response.status_code}, Books: {count}")
                    except:
                        print(f"✓ {endpoint}: Status {response.status_code}, Not JSON")
                else:
                    print(f"✗ {endpoint}: Status {response.status_code}")
            except Exception as e:
                print(f"✗ {endpoint}: Error - {type(e).__name__}")
        
        # Check the main catalog page
        print("\nChecking main catalog page for total count:")
        catalog_url = "https://open.umn.edu/opentextbooks/textbooks"
        response = await client.get(catalog_url)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Look for total count
            text = soup.get_text()
            import re
            total_match = re.search(r'(\d+,?\d*)\s+(?:open\s+)?textbooks?', text, re.IGNORECASE)
            if total_match:
                print(f"Found total count on page: {total_match.group(1)} textbooks")
            
            # Check if there's pagination
            pagination = soup.find_all(['nav', 'div'], class_=['pagination', 'pager'])
            if pagination:
                print("Found pagination elements - might need to scrape multiple pages")
            
            # Look for subject browse links
            subject_links = soup.find_all('a', href=re.compile(r'/textbooks\?.*subject'))
            if subject_links:
                print(f"Found {len(subject_links)} subject category links")

if __name__ == "__main__":
    asyncio.run(investigate_otl())