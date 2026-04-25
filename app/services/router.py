import os
import shutil
import tempfile
from pathlib import Path
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

def resolve_dynamic_path(template: str, meta: Dict[str, Any]) -> Path:
    """Resuelve plantillas: {author}/{title}/v{version}/{title}.{ext}"""
    return Path(template.format(**meta)).resolve()

def validate_space(target: Path, required_bytes: int, margin: float = 0.05) -> bool:
    """Valida espacio libre con margen de seguridad."""
    if not target.parent.exists():
        return True
    usage = shutil.disk_usage(target.parent)
    return usage.free >= (required_bytes * (1 + margin))

def atomic_move(src: Path, dest: Path) -> Path:
    """Movimiento atómico garantizado en mismo filesystem."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    temp_fd, temp_path = tempfile.mkstemp(dir=dest.parent, suffix=".tmp")
    os.close(temp_fd)
    try:
        shutil.copy2(src, temp_path)
        os.replace(temp_path, dest)  # Atómico en POSIX/NTFS mismo FS
        return dest
    except Exception as e:
        if os.path.exists(temp_path):
            os.unlink(temp_path)
        raise RuntimeError(f"Fallo atómico: {e}") from e