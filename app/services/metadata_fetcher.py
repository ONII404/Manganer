import asyncio
import httpx
import hashlib
import logging
from typing import Optional, Literal
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from app.config import settings
from app.database import SessionLocal
from app.models.metadata import TranslationCache, MetadataSource

logger = logging.getLogger(__name__)

SourceName = Literal["anilist", "mal", "mangaupdates"]

class MetadataFetcher:
    """Cliente unificado con fallback automático y rate limiting."""
    
    SOURCES = {
        "anilist": {"url": "https://graphql.anilist.co", "priority": 1},
        "mal": {"url": "https://api.myanimelist.net/v2", "priority": 2},
        "mangaupdates": {"url": "https://api.mangaupdates.com/v1", "priority": 3},
    }
    
    def __init__(self, api_keys: dict[str, str] | None = None):
        self.api_keys = api_keys or {}
        self._client: httpx.AsyncClient | None = None
    
    async def __aenter__(self):
        self._client = httpx.AsyncClient(
            timeout=15.0,
            http2=True,
            limits=httpx.Limits(max_keepalive_connections=10, max_connections=20)
        )
        return self
    
    async def __aexit__(self, *exc):
        if self._client:
            await self._client.aclose()
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((httpx.NetworkError, httpx.TimeoutException))
    )
    async def _fetch_anilist(self, title: str) -> dict | None:
        query = """
        query($title: String) {
          Page(perPage: 1) {
            media(search: $title, type: MANGA) {
              id, title { romaji, english, native }, description, 
              genres, startDate { year }, coverImage { large }
            }
          }
        }
        """
        try:
            resp = await self._client.post(
                self.SOURCES["anilist"]["url"],
                json={"query": query, "variables": {"title": title}},
                headers={"Content-Type": "application/json"}
            )
            resp.raise_for_status()
            data = resp.json()["data"]["Page"]["media"]
            return data[0] if data else None
        except Exception as e:
            logger.warning(f"⚠️ AniList fallback: {e}")
            return None
    
    async def _fetch_mal(self, title: str) -> dict | None:
        # Requiere OAuth2 token en api_keys["mal"]
        token = self.api_keys.get("mal")
        if not token:
            return None
        try:
            resp = await self._client.get(
                f"{self.SOURCES['mal']['url']}/manga",
                params={"q": title, "limit": 1},
                headers={"Authorization": f"Bearer {token}"}
            )
            resp.raise_for_status()
            data = resp.json()["data"]
            return data[0]["node"] if data else None
        except Exception as e:
            logger.warning(f"⚠️ MAL fallback: {e}")
            return None
    
    async def fetch(self, title: str, author: str = "") -> dict | None:
        """Fetch con fallback en cascada por prioridad."""
        for source in sorted(self.SOURCES.keys(), key=lambda s: self.SOURCES[s]["priority"]):
            logger.info(f"🔍 Buscando '{title}' en {source}...")
            result = None
            if source == "anilist":
                result = await self._fetch_anilist(title)
            elif source == "mal":
                result = await self._fetch_mal(title)
            # mangaupdates requiere scraping complejo → omitido en MVP
            
            if result:
                logger.info(f"✅ Metadatos obtenidos desde {source}")
                return {"source": source, "data": result}
        
        logger.warning(f"❌ Sin metadatos para '{title}' tras intentar todas las fuentes")
        return None