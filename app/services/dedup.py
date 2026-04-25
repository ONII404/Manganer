from sqlalchemy.orm import Session
from app.models.file import MangaFile

def find_similar_versions(db: Session, title: str, author: str, phash: str, threshold: int = 5) -> list[dict]:
    """Busca versiones duplicadas por Hamming Distance ≤ 5."""
    if not phash:
        return []
    candidates = db.query(MangaFile).filter(
        MangaFile.title == title,
        MangaFile.author == author,
        MangaFile.phash != ""
    ).all()
    
    target_int = int(phash, 16)
    similar = []
    for c in candidates:
        c_int = int(c.phash, 16)
        hamming = bin(target_int ^ c_int).count("1")
        if hamming <= threshold:
            similar.append({"id": c.id, "path": c.file_path, "distance": hamming})
    return similar