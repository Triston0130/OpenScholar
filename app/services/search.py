from typing import List, Set, Tuple
import asyncio
import logging
from app.models import Paper, SearchRequest
from app.api_clients import ERICClient, COREClient, DOAJClient, EuropePMCClient, PMCClient, PubMedClient, SemanticScholarClient
from app.utils import sort_papers
import hashlib
import re

logger = logging.getLogger(__name__)

class SearchService:
    """Service to handle multi-source search and deduplication"""
    
    def __init__(self, core_api_key: str = None):
        self.eric_client = ERICClient()
        self.core_client = COREClient(api_key=core_api_key)
        self.doaj_client = DOAJClient()
        self.europe_pmc_client = EuropePMCClient()
        self.pmc_client = PMCClient()
        self.pubmed_client = PubMedClient()
        self.semantic_scholar_client = SemanticScholarClient()
        
    async def search(self, request: SearchRequest) -> Tuple[List[Paper], List[str]]:
        """
        Search multiple sources and return deduplicated results
        Returns: (papers, sources_queried)
        """
        sources_queried = []
        
        # Create search tasks for all APIs
        tasks = []
        
        # ERIC search
        tasks.append(self.eric_client.search(
            query=request.query,
            year_start=request.year_start,
            year_end=request.year_end,
            discipline=request.discipline,
            education_level=request.education_level,
            limit=100
        ))
        sources_queried.append("ERIC")
        
        # CORE search
        tasks.append(self.core_client.search(
            query=request.query,
            year_start=request.year_start,
            year_end=request.year_end,
            discipline=request.discipline,
            education_level=request.education_level,
            limit=100
        ))
        sources_queried.append("CORE")
        
        # DOAJ search
        tasks.append(self.doaj_client.search(
            query=request.query,
            year_start=request.year_start,
            year_end=request.year_end,
            discipline=request.discipline,
            education_level=request.education_level,
            limit=100
        ))
        sources_queried.append("DOAJ")
        
        # Europe PMC search
        tasks.append(self.europe_pmc_client.search(
            query=request.query,
            year_start=request.year_start,
            year_end=request.year_end,
            discipline=request.discipline,
            education_level=request.education_level,
            limit=100
        ))
        sources_queried.append("Europe PMC")
        
        # PubMed Central search
        tasks.append(self.pmc_client.search(
            query=request.query,
            year_start=request.year_start,
            year_end=request.year_end,
            discipline=request.discipline,
            education_level=request.education_level,
            limit=100
        ))
        sources_queried.append("PubMed Central")
        
        # PubMed search
        tasks.append(self.pubmed_client.search(
            query=request.query,
            year_start=request.year_start,
            year_end=request.year_end,
            discipline=request.discipline,
            education_level=request.education_level
        ))
        sources_queried.append("PubMed")
        
        # Semantic Scholar search
        tasks.append(self.semantic_scholar_client.search(
            query=request.query,
            year_start=request.year_start,
            year_end=request.year_end,
            discipline=request.discipline,
            education_level=request.education_level
        ))
        sources_queried.append("Semantic Scholar")
        
        # Execute all searches concurrently with timeout
        try:
            results = await asyncio.wait_for(
                asyncio.gather(*tasks, return_exceptions=True),
                timeout=30.0  # 30 second timeout
            )
        except asyncio.TimeoutError:
            logger.error("Search timeout - some APIs may be slow")
            results = [None] * len(tasks)
        
        # Combine results
        all_papers = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Error from {sources_queried[i]}: {result}")
            elif result:
                logger.info(f"Got {len(result)} results from {sources_queried[i]}")
                all_papers.extend(result)
            else:
                logger.info(f"No results from {sources_queried[i]}")
        
        # Deduplicate papers
        deduplicated_papers = self._deduplicate_papers(all_papers)
        
        # Apply citation count filter if specified
        if request.min_citations is not None:
            deduplicated_papers = [
                paper for paper in deduplicated_papers 
                if paper.citation_count is not None and paper.citation_count >= request.min_citations
            ]
        
        # Apply sorting based on request
        sorted_papers = sort_papers(deduplicated_papers, request.query, request.sort_by)
        
        return sorted_papers, sources_queried
    
    def _deduplicate_papers(self, papers: List[Paper]) -> List[Paper]:
        """Deduplicate papers based on DOI and title similarity"""
        seen_dois: Set[str] = set()
        seen_titles: Set[str] = set()
        deduplicated = []
        
        for paper in papers:
            # Check DOI first
            if paper.doi and paper.doi in seen_dois:
                continue
            
            # Check title similarity
            normalized_title = self._normalize_title(paper.title)
            if normalized_title in seen_titles:
                continue
            
            # Add to deduplicated list
            deduplicated.append(paper)
            
            if paper.doi:
                seen_dois.add(paper.doi)
            seen_titles.add(normalized_title)
        
        return deduplicated
    
    def _normalize_title(self, title: str) -> str:
        """Normalize title for comparison"""
        # Convert to lowercase
        title = title.lower()
        # Remove punctuation and extra spaces
        title = re.sub(r'[^\w\s]', '', title)
        title = re.sub(r'\s+', ' ', title).strip()
        # Create a hash for efficient comparison
        return hashlib.md5(title.encode()).hexdigest()
    
    async def close(self):
        """Close all API clients"""
        await self.eric_client.close()
        await self.core_client.close()
        await self.doaj_client.close()
        await self.europe_pmc_client.close()
        await self.pmc_client.close()
        await self.pubmed_client.close()
        await self.semantic_scholar_client.close()