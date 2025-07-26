from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Tuple
import httpx
import asyncio
from app.models import Paper
from app.utils.open_access_validator import open_access_validator
import logging

logger = logging.getLogger(__name__)

class BaseAPIClient(ABC):
    """Base class for all API clients"""
    
    def __init__(self, base_url: str, timeout: int = 30):
        self.base_url = base_url
        self.timeout = timeout
        self.client = httpx.AsyncClient(timeout=timeout)
    
    @abstractmethod
    async def search(self, query: str, year_start: int, year_end: int, 
                    discipline: Optional[str] = None, 
                    education_level: Optional[str] = None,
                    limit: int = 20) -> List[Paper]:
        """Search for papers and return normalized results"""
        pass
    
    def normalize_paper(self, raw_paper: Dict[str, Any]) -> Optional[Paper]:
        """Normalize raw API response to Paper model - can be overridden as async"""
        # Default implementation - subclasses should override
        raise NotImplementedError("Subclasses must implement normalize_paper")
    
    async def validate_open_access(self, paper: Paper) -> Tuple[bool, str]:
        """
        Validate that a paper is truly open access.
        Returns (is_open_access, reason)
        
        This method should be called by all API clients before returning papers.
        """
        # First check DOI - strongest signal
        if paper.doi:
            # Check if it's a known paywall DOI
            if not open_access_validator.is_doi_likely_open_access(paper.doi):
                return False, f"DOI from paywall publisher: {paper.doi}"
        
        # Then validate full metadata
        is_oa, reason = await open_access_validator.validate_paper(
            title=paper.title,
            journal=paper.journal,
            doi=paper.doi,
            license_info=None,  # Could be extracted from paper if available
            abstract=paper.abstract,
            full_text_url=paper.full_text_url,
            check_url_accessibility=False  # Don't check URL accessibility to avoid slowdowns
        )
        
        if not is_oa:
            logger.debug(f"{self.__class__.__name__} paper rejected - {reason}: {paper.title[:50]}...")
        
        return is_oa, reason
    
    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()