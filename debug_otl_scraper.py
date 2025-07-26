#!/usr/bin/env python3
"""Debug OTL scraper"""

import httpx
import asyncio
from bs4 import BeautifulSoup

async def debug_otl():
    async with httpx.AsyncClient() as client:
        # Try search with proper headers
        search_url = "https://open.umn.edu/opentextbooks/textbooks"
        params = {
            'term': 'calculus',
            'commit': 'Search'
        }
        headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }
        
        print(f"Requesting: {search_url}")
        print(f"Params: {params}")
        
        response = await client.get(search_url, params=params, headers=headers, follow_redirects=True)
        print(f"Status: {response.status_code}")
        print(f"Final URL: {response.url}")
        print(f"Content-Type: {response.headers.get('content-type', 'Not set')}")
        
        # Save response for inspection
        with open("otl_response.html", "w") as f:
            f.write(response.text)
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Try different selectors
        selectors = [
            ('div', {'class': 'cover-book-info'}),
            ('article', {'class': 'book'}),
            ('div', {'class': 'book-item'}),
            ('div', {'class': 'textbook'}),
            ('div', {'class': 'result'}),
            ('li', {'class': 'book'}),
            ('div', {'class': 'book-listing'}),
            ('div', {'class': 'col-md-3'}),  # Grid layout
            ('div', {'class': 'book-cover'}),
            ('div', {'class': 'row'}),  # Row containers
            ('article', {}),  # Any article tag
            ('div', {'class': 'col-lg-4'}),  # Bootstrap grid
            ('div', {'class': 'card'}),  # Card layout
        ]
        
        for tag, attrs in selectors:
            items = soup.find_all(tag, attrs)
            if items:
                print(f"\nFound {len(items)} items with selector: {tag} {attrs}")
                # Show first item
                if items:
                    print(f"Sample HTML: {str(items[0])[:200]}...")
                break
        else:
            print("\nNo book items found with any selector")
            
            # Check page title
            title = soup.find('title')
            if title:
                print(f"\nPage title: {title.text}")
            
            # Check for error messages
            error = soup.find(['div', 'p'], class_=['error', 'alert', 'message'])
            if error:
                print(f"\nError message: {error.text}")
            
            # Show some content
            body_text = soup.get_text()[:500]
            print(f"\nPage content preview: {body_text}")

if __name__ == "__main__":
    asyncio.run(debug_otl())