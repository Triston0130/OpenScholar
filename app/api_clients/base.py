from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import httpx
import asyncio
from app.models import Paper

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
    
    @abstractmethod
    def normalize_paper(self, raw_paper: Dict[str, Any]) -> Optional[Paper]:
        """Normalize raw API response to Paper model"""
        pass
    
    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()