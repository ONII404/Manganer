from sqlalchemy import Column, Integer, String, Text, DateTime, Index, func, Boolean
from sqlalchemy.orm import relationship
from app.database import Base 

class MetadataSource(Base):
    __tablename__ = "metadata_sources"
    id = Column(Integer, primary_key=True)
    manga_file_id = Column(Integer, nullable=False, index=True)
    source = Column(String(20), nullable=False)  # anilist, mal, mangaupdates
    external_id = Column(String(64), nullable=False)
    last_fetched = Column(DateTime, server_default=func.now())
    __table_args__ = (Index("idx_source_external", "source", "external_id"),)

class TranslationCache(Base):
    """Caché de traducciones indexada por SHA-256 del texto original."""
    __tablename__ = "translations_cache"
    text_hash = Column(String(64), primary_key=True)  # SHA-256
    original = Column(Text, nullable=False)
    translated = Column(Text, nullable=False)
    source_lang = Column(String(5), default="ja")
    target_lang = Column(String(5), default="es")
    provider = Column(String(20), default="deepl")
    created_at = Column(DateTime, server_default=func.now())
    usage_count = Column(Integer, default=0)
    
    __table_args__ = (Index("idx_usage", "usage_count", "created_at"),)

class ComicInfo(Base):
    """Metadatos estándar ComicInfo.xml v2.0"""
    __tablename__ = "comic_info"
    id = Column(Integer, primary_key=True)
    manga_file_id = Column(Integer, unique=True, nullable=False, index=True)
    title = Column(String(255), index=True)
    series = Column(String(255))
    number = Column(String(20))
    writer = Column(String(255))
    penciller = Column(String(255))
    genre = Column(String(255))
    summary = Column(Text)
    year = Column(Integer)
    publisher = Column(String(255))
    pages = Column(Integer)
    web = Column(String(512))
    language_iso = Column(String(10), default="es")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())