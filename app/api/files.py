# app/api/files.py
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from app.database import get_db
from app.models.file import MangaFile
from pydantic import BaseModel

# ✅ Prefijo del router (se combina con el de main.py)
router = APIRouter(prefix="/files", tags=["Files"])

class FileListResponse(BaseModel):
    files: list[dict]
    total: int

# =============================================================================
# ✅ Ruta base: "" → se combina con /api/v1 + /files = /api/v1/files
# =============================================================================
@router.get("", response_model=FileListResponse)
def list_files(
    limit: int = Query(default=100, ge=1, le=10000),
    offset: int = Query(default=0, ge=0),
    search: Optional[str] = Query(default=None, max_length=200),
    db: Session = Depends(get_db)
):
    """Listar archivos con paginación y búsqueda."""
    query = db.query(MangaFile)
    
    if search and search.strip():
        search_term = f"%{search.strip()}%"
        query = query.filter(
            (MangaFile.title.ilike(search_term)) | 
            (MangaFile.author.ilike(search_term)) |
            (MangaFile.file_path.ilike(search_term))
        )
    
    total = query.count()
    files = query.order_by(MangaFile.created_at.desc()).offset(offset).limit(limit).all()
    
    return FileListResponse(
        files=[
            {
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
            }
            for f in files
        ],
        total=total,
    )

# =============================================================================
# ✅ Ruta relativa: "/scan" → /api/v1 + /files + /scan = /api/v1/files/scan
# =============================================================================
@router.post("/scan")
async def trigger_scan():
    """Trigger escaneo manual."""
    from app.tasks.scan_tasks import scan_library_task
    task = scan_library_task.delay()
    return {"status": "scanning", "task_id": task.id}

# =============================================================================
# ✅ Ruta relativa: "/{file_id}" → /api/v1 + /files + /{file_id} = /api/v1/files/{id}
# =============================================================================
@router.get("/{file_id}")
async def get_file(file_id: int, db: Session = Depends(get_db)):
    """Obtener archivo por ID."""
    file = db.query(MangaFile).filter(MangaFile.id == file_id).first()
    if not file:
        raise HTTPException(status_code=404, detail="Archivo no encontrado")
    
    return {
        "id": file.id,
        "file_path": file.file_path,
        "file_hash": file.file_hash,
        "file_size": file.file_size,
        "file_type": file.file_type,
        "title": file.title,
        "author": file.author,
        "chapter_num": file.chapter_num,
        "phash": file.phash,
        "created_at": file.created_at.isoformat() if file.created_at else None,
    }