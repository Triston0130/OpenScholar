#!/usr/bin/env python3
import asyncio
import sys
sys.path.append('.')

from app.api_clients.open_textbook_library import OpenTextbookLibraryClient
from app.api_clients.libretexts import LibreTextsClient

async def main():
    for name, cli in [("OTL", OpenTextbookLibraryClient()), ("LibreTexts", LibreTextsClient())]:
        try:
            papers = await cli.search("mathematics", max_results=10)
            print(f"\n{name}: {len(papers)} hits")
            for i, paper in enumerate(papers[:3]):
                print(f"  {i+1}. {paper.title}")
                print(f"     Authors: {', '.join(paper.authors[:3])}")
                print(f"     URL: {paper.full_text_url}")
        except Exception as e:
            print(f"{name}: ERROR - {e}")

asyncio.run(main())