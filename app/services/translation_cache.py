import hashlib
from sqlalchemy.orm import Session
from app.models.metadata import TranslationCache
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import httpx
import logging

logger = logging.getLogger(__name__)

class DeepLTranslator:
    """Traductor con rate limiting explícito y caché persistente."""
    
    RATE_LIMIT = 5  # llamadas/segundo (Free tier: 5/s, Pro: 25/s)
    
    def __init__(self, api_key: str, target_lang: str = "ES"):
        self.api_key = api_key
        self.target_lang = target_lang
        self._client = httpx.Client(base_url="https://api-free.deepl.com/v2", timeout=30)
    
    def _hash_text(self, text: str) -> str:
        return hashlib.sha256(text.encode("utf-8")).hexdigest()
    
    def _get_cached(self, db: Session, text: str) -> str | None:
        h = self._hash_text(text)
        entry = db.query(TranslationCache).filter_by(text_hash=h).first()
        if entry:
            db.query(TranslationCache).filter_by(text_hash=h).update({"usage_count": TranslationCache.usage_count + 1})
            db.commit()
            return entry.translated
        return None
    
    def _set_cached(self, db: Session, original: str, translated: str, source_lang: str):
        h = self._hash_text(original)
        entry = TranslationCache(
            text_hash=h, original=original, translated=translated,
            source_lang=source_lang, target_lang=self.target_lang,
            usage_count=1
        )
        db.merge(entry)  # UPSERT
        db.commit()
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=2, min=4, max=30),
        retry=retry_if_exception_type((httpx.HTTPStatusError, httpx.NetworkError))
    )
    def _translate_api(self, text: str) -> str:
        resp = self._client.post(
            "/translate",
            data={
                "auth_key": self.api_key,
                "text": text,
                "target_lang": self.target_lang,
                "preserve_formatting": "true",
                "tag_handling": "xml"  # Preserva etiquetas HTML/XML
            }
        )
        resp.raise_for_status()
        return resp.json()["translations"][0]["text"]
    
    def translate(self, db: Session, text: str, source_lang: str = "JA") -> str:
        if not text or len(text.strip()) < 3:
            return text
        cached = self._get_cached(db, text)
        if cached:
            return cached
        try:
            result = self._translate_api(text)
            self._set_cached(db, text, result, source_lang)
            return result
        except Exception as e:
            logger.error(f"❌ DeepL error: {e}")
            return text  # Fallback: texto original
    
    def translate_batch(self, db: Session, texts: list[str], source_lang: str = "JA") -> list[str]:
        """Traducción por lotes para optimizar cuota API."""
        # Filtrar ya cacheados
        to_translate = [(i, t) for i, t in enumerate(texts) if not self._get_cached(db, t)]
        if not to_translate:
            return texts
        
        # Agrupar en batches de 50 (límite DeepL)
        results = texts.copy()
        for i in range(0, len(to_translate), 50):
            batch = to_translate[i:i+50]
            try:
                resp = self._client.post(
                    "/translate",
                    data={
                        "auth_key": self.api_key,
                        "text": [t for _, t in batch],
                        "target_lang": self.target_lang,
                        "preserve_formatting": "true"
                    }
                )
                resp.raise_for_status()
                translations = [tr["text"] for tr in resp.json()["translations"]]
                for (idx, orig), trans in zip(batch, translations):
                    results[idx] = trans
                    self._set_cached(db, orig, trans, source_lang)
            except Exception as e:
                logger.error(f"❌ Batch DeepL error: {e}")
                # Continuar con textos no traducidos
        return results
    
    def close(self):
        self._client.close()