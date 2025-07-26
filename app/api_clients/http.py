import httpx
import asyncio
import logging

logger = logging.getLogger(__name__)

async def fetch_json(url: str, params: dict | None = None, *, ua: str="OpenScholar/1.0", timeout: float = 20):
    headers = {"User-Agent": ua, "Accept": "application/json"}
    async with httpx.AsyncClient(timeout=timeout, follow_redirects=True, headers=headers) as cli:
        r = await cli.get(url, params=params)
        r.raise_for_status()
        return r.json()