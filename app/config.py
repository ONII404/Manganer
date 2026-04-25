# app/tasks/config.py
from pydantic_settings import BaseSettings
from pathlib import Path

class Settings(BaseSettings):
    APP_NAME: str = "Manganer"
    DEBUG: bool = False
    WORKERS: int = 4
    DB_URL: str = "sqlite:///./data/manganer.db"
    DATA_DIR: Path = Path("/app/data")
    LIBRARY_DIR: str = "/app/library"
    REDIS_URL: str = "redis://redis:6379/0"
    MAX_MEMORY_MB: int = 1200
    
    # 🔐 API Keys para servicios externos
    DEEPL_API_KEY: str = ""
    ANILIST_CLIENT_ID: str = ""
    MAL_CLIENT_ID: str = ""
    MAL_CLIENT_SECRET: str = ""
    
    # ⚙️ OPDS
    OPDS_PUBLIC: bool = True
    OPDS_RATE_LIMIT_PER_IP: int = 60
    DEFAULT_LANG: str = "es"
    
    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}

settings = Settings()