from celery import shared_task
from app.tasks.base import BaseTask
from app.core.redis_client import update_task_progress
from app.services.hashing import compute_file_hashes
from app.services.router import resolve_dynamic_path, validate_space, atomic_move
from app.services.dedup import find_similar_versions
from app.models.file import MangaFile
from app.database import SessionLocal
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

@shared_task(bind=True, base=BaseTask, name="manga.scan_file")
def process_new_file_task(self, file_path: str):
    path = Path(file_path)
    if not path.exists():
        return {"status": "skipped", "reason": "not_found"}

    update_task_progress(self.request.id, {"status": "hashing", "progress": 10, "file": path.name})
    hashes = compute_file_hashes(path)
    update_task_progress(self.request.id, {"status": "routing", "progress": 40})

    # Metadatos básicos (fallback: nombre de archivo)
    meta = {"author": "Unknown", "title": path.stem, "version": 1, "ext": path.suffix}
    
    db = SessionLocal()
    try:
        # Duplicado exacto
        existing = db.query(MangaFile).filter_by(file_hash=hashes["sha256"]).first()
        if existing:
            return {"status": "duplicate_sha", "id": existing.id}

        # Version stacking
        similar = find_similar_versions(db, meta["title"], meta["author"], hashes["phash"])
        if similar:
            meta["version"] = max(s["distance"] for s in similar) + 1

        # Routing dinámico
        template = "{author}/{title}/v{version}/{title}{ext}"
        target = resolve_dynamic_path(template, meta)

        if not validate_space(target, hashes["size"]):
            raise RuntimeError("Espacio insuficiente")

        final_path = atomic_move(path, target)
        
        entry = MangaFile(
            file_path=str(final_path),
            file_hash=hashes["sha256"],
            file_size=hashes["size"],
            file_type=hashes["type"],
            title=meta["title"],
            author=meta["author"],
            chapter_num=meta.get("chapter", 0),
            phash=hashes["phash"]
        )
        db.add(entry)
        db.commit()
        update_task_progress(self.request.id, {"status": "completed", "progress": 100})
        return {"status": "indexed", "id": entry.id, "versions": similar}
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Fallo escaneando {path.name}: {e}")
        raise
    finally:
        db.close()