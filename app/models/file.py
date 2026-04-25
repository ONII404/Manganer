from sqlalchemy import Column, Integer, String, BigInteger, Float, DateTime, Index, func
from app.database import Base 

class MangaFile(Base):
    __tablename__ = "manga_files"
    id = Column(Integer, primary_key=True)
    file_path = Column(String, unique=True, index=True, nullable=False)
    file_hash = Column(String(64), index=True, nullable=False)  # SHA-256
    file_size = Column(BigInteger, nullable=False)
    file_type = Column(String(10), nullable=False)              # cbz, cbr
    title = Column(String, index=True)
    author = Column(String, index=True)
    chapter_num = Column(Float, index=True)
    phash = Column(String(16), index=True)                      # pHash 64-bit hex
    created_at = Column(DateTime, server_default=func.now())
    
    __table_args__ = (
        Index("idx_title_author", title, author),
        Index("idx_file_hash", file_hash),
        Index("idx_phash", phash),
    )