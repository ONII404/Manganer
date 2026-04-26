# app/api/opds.py
from fastapi import APIRouter, Depends, Query, HTTPException, Request
from fastapi.responses import Response
from sqlalchemy.orm import Session
from typing import Literal
import xml.etree.ElementTree as ET
import json
from app.database import get_db
from app.models.file import MangaFile
from app.services.comic_info import ComicInfoV2

# ✅ tags definido aquí, NO en include_router() de main.py
router = APIRouter(tags=["OPDS"])

def get_auth(request: Request) -> bool:
    """Auth básica opcional para OPDS."""
    auth = request.headers.get("Authorization")
    if not auth:
        return True  # Permitir acceso público por defecto
    # Implementar token verification aquí si es necesario
    return True

# ✅ Rutas: GET /api/v1/opds/v1.2/catalog.xml
@router.get("/v1.2/catalog.xml")
def opds_12_catalog(
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, le=100),
    _: bool = Depends(get_auth)
):
    """OPDS 1.2: Catálogo XML paginado compatible con Mihon/Panels."""
    offset = (page - 1) * per_page
    items = db.query(MangaFile).offset(offset).limit(per_page).all()
    total = db.query(MangaFile).count()
    
    # Construir XML OPDS 1.2
    ns = {
        "atom": "http://www.w3.org/2005/Atom",
        "opds": "http://opds-spec.org/2010/catalog",
        "thr": "http://purl.org/syndication/thread/1.0"
    }
    root = ET.Element("feed", ns)
    ET.SubElement(root, "id").text = "tag:manganer,2024:/opds"
    ET.SubElement(root, "title").text = "Manganer Library"
    ET.SubElement(root, "updated").text = "2024-01-01T00:00:00Z"
    
    # Paginación
    if page > 1:
        prev = ET.SubElement(root, "link", {
            "rel": "previous", "type": "application/atom+xml",
            "href": f"/opds/v1.2/catalog.xml?page={page-1}&per_page={per_page}"
        })
    if offset + per_page < total:
        next_link = ET.SubElement(root, "link", {
            "rel": "next", "type": "application/atom+xml",
            "href": f"/opds/v1.2/catalog.xml?page={page+1}&per_page={per_page}"
        })
    
    for item in items:
        entry = ET.SubElement(root, "entry")
        ET.SubElement(entry, "id").text = f"tag:manganer:file:{item.id}"
        ET.SubElement(entry, "title").text = item.title or item.file_path
        ET.SubElement(entry, "author").text = item.author or "Unknown"
        ET.SubElement(entry, "content", {"type": "text"}).text = f"{item.file_size // (1024**2)} MB"
        # Enlace de adquisición (streaming)
        ET.SubElement(entry, "link", {
            "rel": "http://opds-spec.org/acquisition",
            "type": "application/x-cbz",
            "href": f"/opds/v1.2/stream/{item.id}"
        })
        # Miniatura
        ET.SubElement(entry, "link", {
            "rel": "http://opds-spec.org/image/thumbnail",
            "type": "image/jpeg",
            "href": f"/opds/v1.2/thumbnail/{item.id}"
        })
    
    return Response(
        content=ET.tostring(root, encoding="utf-8", xml_declaration=True),
        media_type="application/atom+xml"
    )

# ✅ Rutas: GET /api/v1/opds/v2.0/catalog.json
@router.get("/v2.0/catalog.json")
def opds_20_catalog(
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, le=100),
    _: bool = Depends(get_auth)
):
    """OPDS 2.0: Catálogo JSON-LD."""
    offset = (page - 1) * per_page
    items = db.query(MangaFile).offset(offset).limit(per_page).all()
    total = db.query(MangaFile).count()
    
    catalog = {
        "@context": "https://opds.io/ns/v2.0",
        "@type": "Catalog",
        "metadata": {
            "title": "Manganer Library",
            "itemsPerPage": per_page,
            "currentPage": page,
            "totalItems": total
        },
        "navigation": [],
        "publications": []
    }
    
    if page > 1:
        catalog["navigation"].append({
            "rel": "previous",
            "href": f"/opds/v2.0/catalog.json?page={page-1}&per_page={per_page}"
        })
    if offset + per_page < total:
        catalog["navigation"].append({
            "rel": "next",
            "href": f"/opds/v2.0/catalog.json?page={page+1}&per_page={per_page}"
        })
    
    for item in items:
        pub = {
            "@type": "Publication",
            "metadata": {
                "title": item.title or item.file_path,
                "author": item.author or "Unknown",
                "numberOfPages": 1,  # Placeholder
                "fileSize": item.file_size
            },
            "links": [
                {"rel": "self", "href": f"/opds/v2.0/publication/{item.id}", "type": "application/json"},
                {"rel": "acquisition", "href": f"/opds/v2.0/stream/{item.id}", "type": "application/x-cbz"},
                {"rel": "preview", "href": f"/opds/v2.0/thumbnail/{item.id}", "type": "image/jpeg"}
            ]
        }
        catalog["publications"].append(pub)
    
    return catalog

# ✅ Rutas: GET /api/v1/opds/v1.2/stream/{file_id}
@router.get("/v1.2/stream/{file_id}")
def opds_stream(file_id: int, db: Session = Depends(get_db), _: bool = Depends(get_auth)):
    """Streaming directo del archivo .cbz/.cbr (para lectores)."""
    item = db.query(MangaFile).filter_by(id=file_id).first()
    if not item:
        raise HTTPException(404, "Archivo no encontrado")
    # En producción: usar FileResponse con X-Accel-Redirect / sendfile
    return {"stream_url": f"file://{item.file_path}", "content_type": "application/x-cbz"}

# ✅ Rutas: GET /api/v1/opds/v1.2/thumbnail/{file_id}
@router.get("/v1.2/thumbnail/{file_id}")
def opds_thumbnail(file_id: int, db: Session = Depends(get_db), _: bool = Depends(get_auth)):
    """Miniatura pre-generada (placeholder)."""
    # Integrar con pyvips para generar thumbnail on-the-fly si no existe
    raise HTTPException(501, "Thumbnail generation not implemented yet")