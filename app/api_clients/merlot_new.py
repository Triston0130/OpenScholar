# app/api_clients/merlot.py
from typing import List
from app.models import Paper
from .http import fetch_json
import logging
import asyncio

logger = logging.getLogger(__name__)

class MERLOTClient:
    _URL = "https://www.merlot.org/merlot/materials.json"

    async def search(self, query: str, max_results: int = 20) -> List[Paper]:
        try:
            # MERLOT requires throttling - 2 req/s
            await asyncio.sleep(0.5)  # Ensure we don't exceed rate limit
            
            params = {"simpleQuery": query, "page": 1, "size": max_results}
            data = await fetch_json(self._URL, params=params)
            
            papers = []
            # Parse MERLOT's response structure
            materials = data if isinstance(data, list) else data.get("materials", data.get("results", []))
            
            for material in materials[:max_results]:
                # Extract authors
                authors = []
                if "authors" in material:
                    authors = material["authors"] if isinstance(material["authors"], list) else [material["authors"]]
                elif "author" in material:
                    authors = [material["author"]]
                elif "contributors" in material:
                    authors = material["contributors"]
                    
                if not authors:
                    authors = ["MERLOT Contributor"]
                
                # Build paper object
                paper = Paper(
                    title=material.get("title", material.get("name", "Untitled")),
                    authors=authors,
                    year=str(material.get("year", "")) if material.get("year") else None,
                    abstract=material.get("description", material.get("abstract", "")),
                    full_text_url=material.get("url", material.get("link", "")),
                    source="MERLOT",
                    journal="MERLOT",
                    content_type="book",
                    subjects=material.get("subjects", material.get("categories", [])),
                    license=material.get("license", "CC BY")
                )
                papers.append(paper)
                
            logger.info(f"MERLOT: Found {len(papers)} results for '{query}'")
            return papers
            
        except Exception as e:
            logger.error(f"MERLOT search failed: {e}")
            return []