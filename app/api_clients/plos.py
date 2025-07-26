from typing import List, Dict, Any, Optional
import httpx
from app.api_clients.base import BaseAPIClient
from app.models import Paper
import logging
import asyncio
import time
import re
from urllib.parse import quote

logger = logging.getLogger(__name__)

class PLOSClient(BaseAPIClient):
    """PLOS (Public Library of Science) API client for open access scientific articles"""
    
    def __init__(self):
        super().__init__(base_url="https://api.plos.org")
        self.last_request_time = 0
        self.min_request_interval = 0.5
        
        self.client.headers.update({
            "User-Agent": "OpenScholar Research Tool/1.0 (mailto:research@openscholar.app)",
            "Accept": "application/json"
        })
    
    async def _wait_for_rate_limit(self):
        """Rate limiting"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.min_request_interval:
            wait_time = self.min_request_interval - time_since_last
            await asyncio.sleep(wait_time)
        
        self.last_request_time = time.time()
    
    async def search(self, query: str, year_start: int, year_end: int,
                    discipline: Optional[str] = None,
                    education_level: Optional[str] = None,
                    limit: int = 20) -> List[Paper]:
        """Search PLOS for open access articles"""
        
        await self._wait_for_rate_limit()
        
        try:
            search_url = f"{self.base_url}/search"
            
            # Build query - search for any of the terms, not exact phrase
            # Split query into terms and join with OR
            query_terms = query.split()
            search_terms = " OR ".join([f'everything:"{term}"' for term in query_terms])
            search_query = f'({search_terms})'
            
            # Add year filter
            if year_start and year_end:
                search_query += f' AND publication_date:[{year_start}-01-01T00:00:00Z TO {year_end}-12-31T23:59:59Z]'
            elif year_start:
                search_query += f' AND publication_date:[{year_start}-01-01T00:00:00Z TO *]'
            elif year_end:
                search_query += f' AND publication_date:[* TO {year_end}-12-31T23:59:59Z]'
            
            # Add discipline filter
            if discipline:
                discipline_map = {
                    "biology": "Biology",
                    "medicine": "Medicine",
                    "genetics": "Genetics",
                    "computational biology": "Computational Biology",
                    "ecology": "Ecology",
                    "pathogens": "Pathogens",
                    "neglected tropical diseases": "Neglected Tropical Diseases"
                }
                if discipline.lower() in discipline_map:
                    search_query += f' AND subject:"{discipline_map[discipline.lower()]}"'
            
            params = {
                "q": search_query,
                "fl": "id,doi,title,author,publication_date,journal,abstract,subject,article_type,volume,issue,page_count",
                "rows": min(limit, 100),
                "start": 0,
                "wt": "json"
            }
            
            logger.info(f"Searching PLOS for: {query}")
            
            response = await self.client.get(search_url, params=params, timeout=30.0)
            response.raise_for_status()
            
            data = response.json()
            papers = []
            
            # Parse response
            docs = data.get("response", {}).get("docs", [])
            
            for doc in docs:
                paper = await self._article_to_paper(doc)
                if paper:
                    papers.append(paper)
                    if len(papers) >= limit:
                        break
            
            logger.info(f"PLOS returned {len(papers)} articles for query: {query}")
            return papers
            
        except Exception as e:
            logger.error(f"Error searching PLOS: {e}")
            return []
    
    async def _article_to_paper(self, article: Dict[str, Any]) -> Optional[Paper]:
        """Convert PLOS article to Paper object"""
        try:
            # Get title
            title = article.get("title", "")
            if isinstance(title, list) and title:
                title = title[0]
            if not title:
                return None
            
            # Get authors
            authors = article.get("author", [])
            if not isinstance(authors, list):
                authors = [authors] if authors else []
            
            # Clean author names
            clean_authors = []
            for author in authors:
                if isinstance(author, str):
                    # Remove affiliations in parentheses
                    author = re.sub(r'\s*\([^)]*\)', '', author).strip()
                    if author:
                        clean_authors.append(author)
            
            if not clean_authors:
                clean_authors = ["PLOS Authors"]
            
            # Get DOI
            doi = article.get("doi", "")
            if isinstance(doi, list) and doi:
                doi = doi[0]
            
            # Get abstract
            abstract = article.get("abstract", "")
            if isinstance(abstract, list) and abstract:
                abstract = " ".join(abstract)
            if not abstract:
                abstract = "Open access article from PLOS"
            
            # Clean abstract of HTML tags
            abstract = re.sub(r'<[^>]+>', '', abstract)
            abstract = re.sub(r'\s+', ' ', abstract).strip()
            
            # Get publication date and year
            pub_date = article.get("publication_date", "")
            year = ""
            if pub_date:
                year_match = re.search(r'(\d{4})', pub_date)
                if year_match:
                    year = year_match.group(1)
            
            # Get journal
            journal = article.get("journal", "")
            if isinstance(journal, list) and journal:
                journal = journal[0]
            
            # Get subjects
            subjects = article.get("subject", [])
            if not isinstance(subjects, list):
                subjects = [subjects] if subjects else []
            
            # Filter subjects to remove very broad ones
            subjects = [s for s in subjects if s and len(s) > 3 and s != "Research Article"]
            
            # Build URL
            article_id = article.get("id", "")
            if doi:
                full_text_url = f"https://journals.plos.org/plosone/article?id={doi}"
            elif article_id:
                full_text_url = f"https://journals.plos.org/plosone/article?id={article_id}"
            else:
                return None
            
            # Article type
            article_type = article.get("article_type", "")
            if isinstance(article_type, list) and article_type:
                article_type = article_type[0]
            
            return Paper(
                title=title,
                authors=clean_authors[:10],  # PLOS can have many authors
                abstract=abstract[:1500],  # Limit abstract length
                year=year,
                source="PLOS",
                full_text_url=full_text_url,
                doi=doi,
                journal=journal,
                citation_count=None,  # PLOS doesn't provide citation counts in search
                influential_citation_count=None,
                content_type="paper",
                isbn=None,
                publisher="Public Library of Science",
                page_count=article.get("page_count"),
                language="en",
                subjects=subjects[:5] if subjects else ["Science"],
                download_formats=["PDF", "XML", "Online"]
            )
            
        except Exception as e:
            logger.error(f"Error converting PLOS article to paper: {e}")
            return None
    
    async def normalize_paper(self, raw_item: Dict[str, Any], year_start: int, year_end: int) -> Optional[Paper]:
        """Compatibility method"""
        return await self._article_to_paper(raw_item)