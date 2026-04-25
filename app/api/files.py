# app/api/files.py
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from app.database import get_db
from app.models.file import MangaFile
from pydantic import BaseModel

router = APIRouter(prefix="/files", tags=["Files"])

class FileListResponse(BaseModel):
    files: list[dict]
    total: int

@router.get("", response_model=FileListResponse)
def list_files(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Listar archivos de manga con paginación y búsqueda."""
    query = db.query(MangaFile)
    
    # Búsqueda por título o autor
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            (MangaFile.title.ilike(search_term)) | 
            (MangaFile.author.ilike(search_term))
        )
    
    # Contar total para paginación
    total = query.count()
    
    # Aplicar paginación y ordenar por fecha descendente
    files = query.order_by(MangaFile.created_at.desc()).offset(offset).limit(limit).all()
    
    # Serializar a dict (en producción usar Pydantic models)
    return FileListResponse(
        files=[{
            "id": f.id,
            "file_path": f.file_path,
            "file_hash": f.file_hash,
            "file_size": f.file_size,
            "file_type": f.file_type,
            "title": f.title,
            "author": f.author,
            "chapter_num": f.chapter_num,
            "phash": f.phash,
            "created_at": f.created_at.isoformat() if f.created_at else None,
        } for f in files],
        total=total,
    )