# app/api_clients/oer_commons.py
from typing import List
from app.models import Paper
from .http import fetch_json
import logging

logger = logging.getLogger(__name__)

class OERCommonsClient:
    _URL = "https://www.oercommons.org/lorapi/items"

    async def search(self, query: str, max_results: int = 20) -> List[Paper]:
        try:
            params = {"search": query, "limit": max_results}
            # OER Commons requires specific headers
            data = await fetch_json(self._URL, params=params, ua="OpenScholar/1.0 (Educational Research)")
            
            papers = []
            # Handle the response structure
            items = data if isinstance(data, list) else data.get("items", data.get("results", []))
            
            for item in items[:max_results]:
                # Extract authors
                authors = []
                if "authors" in item:
                    authors = item["authors"] if isinstance(item["authors"], list) else [item["authors"]]
                elif "creator" in item:
                    authors = [item["creator"]]
                elif "contributors" in item:
                    authors = item["contributors"]
                    
                if not authors:
                    authors = ["OER Commons Contributor"]
                
                # Build paper object
                paper = Paper(
                    title=item.get("title", item.get("name", "Untitled")),
                    authors=authors,
                    year=str(item.get("year", "")) if item.get("year") else None,
                    abstract=item.get("description", item.get("abstract", "")),
                    full_text_url=item.get("url", item.get("link", "")),
                    source="OER Commons",
                    journal="OER Commons",
                    content_type="book",
                    subjects=item.get("subjects", item.get("keywords", [])),
                    license=item.get("license", "CC BY")
                )
                papers.append(paper)
                
            logger.info(f"OER Commons: Found {len(papers)} results for '{query}'")
            return papers
            
        except Exception as e:
            logger.error(f"OER Commons search failed: {e}")
            return []