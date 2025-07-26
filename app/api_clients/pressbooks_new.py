# app/api_clients/pressbooks.py
from typing import List
from app.models import Paper
from .http import fetch_json
import logging

logger = logging.getLogger(__name__)

class PressbooksClient:
    _URL = "https://directory.pressbooks.network/wp-json/pressbooks/v1/search"

    async def search(self, query: str, max_results: int = 20) -> List[Paper]:
        try:
            # Calculate how many pages we might need
            per_page = min(max_results, 50)  # API usually limits per page
            params = {"term": query, "page": 1, "per_page": per_page}
            
            data = await fetch_json(self._URL, params=params)
            
            papers = []
            # Handle both array response and object with results key
            results = data if isinstance(data, list) else data.get("results", data.get("books", []))
            
            for book in results[:max_results]:
                # Extract authors - Pressbooks often has them in metadata
                authors = []
                if "authors" in book:
                    authors = book["authors"] if isinstance(book["authors"], list) else [book["authors"]]
                elif "author" in book:
                    authors = [book["author"]]
                elif "metadata" in book and "author" in book["metadata"]:
                    authors = [book["metadata"]["author"]]
                    
                if not authors:
                    authors = ["Pressbooks Author"]
                
                # Get the URL
                url = book.get("url", book.get("link", book.get("book_url", "")))
                
                # Build paper object
                paper = Paper(
                    title=book.get("title", book.get("name", "Untitled")),
                    authors=authors,
                    year=str(book.get("year", "")) if book.get("year") else None,
                    abstract=book.get("description", book.get("summary", "")),
                    full_text_url=url,
                    source="Pressbooks",
                    journal="Pressbooks",
                    content_type="book",
                    subjects=book.get("subjects", book.get("categories", [])),
                    license=book.get("license", "CC BY")
                )
                papers.append(paper)
                
            logger.info(f"Pressbooks: Found {len(papers)} results for '{query}'")
            return papers
            
        except Exception as e:
            logger.error(f"Pressbooks search failed: {e}")
            return []