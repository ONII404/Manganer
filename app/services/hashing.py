# app/services/hashing.py
import hashlib
import imagehash
import pyvips
from PIL import Image
import io
from pathlib import Path
import zipfile
import rarfile
import logging

logger = logging.getLogger(__name__)

# ✅ Límite estricto de caché pyvips (50MB para hashing)
try:
    pyvips.vips_cache_set_max(50_000_000)
except Exception:
    pass  # Ignorar si ya está configurado o no disponible


def compute_sha256(file_path: Path) -> str:
    """Calcula SHA-256 de un archivo en chunks para eficiencia de memoria."""
    sha = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            sha.update(chunk)
    return sha.hexdigest()


def _extract_first_image(file_path: Path, f_type: str) -> bytes | None:
    """
    Extrae la primera imagen de un archivo comprimido sin descomprimir todo.
    Prioriza portadas/cubiertas típicas de manga.
    """
    try:
        if f_type == "cbz":
            with zipfile.ZipFile(file_path, 'r') as z:
                names = [n for n in z.namelist() 
                        if n.lower().endswith(('.jpg', '.jpeg', '.png', '.webp'))]
                if not names:
                    return None
                # Priorizar nombres que parezcan portada
                for priority in ['cover', '00', '01', '1.', 'folder']:
                    candidate = next((n for n in names if priority in n.lower()), None)
                    if candidate:
                        return z.read(candidate)
                return z.read(names[0])
                
        elif f_type == "cbr":
            with rarfile.RarFile(str(file_path)) as r:
                names = [n for n in r.namelist() 
                        if n.lower().endswith(('.jpg', '.jpeg', '.png'))]
                if not names:
                    return None
                for priority in ['cover', '00', '01', '1.', 'folder']:
                    candidate = next((n for n in names if priority in n.lower()), None)
                    if candidate:
                        return r.read(candidate)
                return r.read(names[0])
                
    except Exception as e:
        logger.warning(f"No se pudo extraer imagen de {file_path.name}: {e}")
    return None


def compute_phash(img_data: bytes) -> str:  # ✅ CORREGIDO: parámetro completo con tipo
    """
    Calcula perceptual hash (pHash) vía pyvips en modo streaming.
    Retorna string hex de 16 caracteres (64-bit hash).
    """
    if not img_data:  # ✅ CORREGIDO: usar img_data, no img_
        return ""
    
    try:
        # Cargar imagen desde buffer (sin archivo temporal)
        img = pyvips.Image.new_from_buffer(img_data, "")
        
        # Redimensionar a 32x32 para pHash estándar
        scale = 32.0 / max(img.width, img.height, 1)
        img = img.resize(scale, vscale=scale)
        
        # Convertir a escala de grises
        img = img.colourspace("b-w")
        
        # Exportar a JPEG de baja calidad para reducir ruido
        buf = img.jpegsave_buffer(Q=75, strip=True)
        
        # Calcular pHash con imagehash (8x8 = 64 bits)
        with Image.open(io.BytesIO(buf)) as pil_img:
            ph = imagehash.phash(pil_img, hash_size=8)
        
        return str(ph)
        
    except Exception as e:
        logger.error(f"Error calculando pHash: {e}")
        return ""


def compute_file_hashes(file_path: Path) -> dict:
    """
    Calcula todos los hashes necesarios para un archivo de manga.
    Retorna dict con: sha256, phash, size, type.
    """
    suffix = file_path.suffix.lower()
    f_type = "cbz" if suffix == ".cbz" else "cbr"
    
    # SHA-256 para detección de duplicados exactos
    sha = compute_sha256(file_path)
    
    # Metadatos básicos
    size = file_path.stat().st_size
    
    # pHash para detección de versiones similares
    img_buf = _extract_first_image(file_path, f_type)
    ph = compute_phash(img_buf) if img_buf else ""
    
    return {
        "sha256": sha,
        "phash": ph,
        "size": size,
        "type": f_type,
    }