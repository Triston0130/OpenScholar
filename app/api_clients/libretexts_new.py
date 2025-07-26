# app/api_clients/libretexts.py
from typing import List
from app.models import Paper
from .http import fetch_json
import logging

logger = logging.getLogger(__name__)

class LibreTextsClient:
    _URL = "https://api.libretexts.org/search"

    async def search(self, query: str, max_results: int = 20) -> List[Paper]:
        try:
            params = {"q": query, "limit": max_results}
            data = await fetch_json(self._URL, params=params)
            
            papers = []
            # The API returns an array of results
            results = data if isinstance(data, list) else data.get("results", [])
            
            for item in results[:max_results]:
                # Extract authors - LibreTexts often lists them in various fields
                authors = []
                if "authors" in item:
                    if isinstance(item["authors"], list):
                        authors = item["authors"]
                    else:
                        authors = [item["authors"]]
                elif "author" in item:
                    authors = [item["author"]]
                
                if not authors:
                    authors = ["LibreTexts Contributors"]
                
                # Build the paper object
                paper = Paper(
                    title=item.get("title", "Untitled"),
                    authors=authors,
                    year=str(item.get("year", "")) if item.get("year") else None,
                    abstract=item.get("description", item.get("summary", "")),
                    full_text_url=item.get("url", item.get("link", "")),
                    source="LibreTexts",
                    journal="LibreTexts",
                    content_type="book",
                    subjects=item.get("subjects", item.get("tags", [])),
                    license=item.get("license", "CC BY-NC-SA")
                )
                papers.append(paper)
                
            logger.info(f"LibreTexts: Found {len(papers)} results for '{query}'")
            return papers
            
        except Exception as e:
            logger.error(f"LibreTexts search failed: {e}")
            return []