# app/services/hashing.py
"""
Servicios de hashing para archivos de manga (.cbz, .cbr).
Calcula hashes SHA-256, tamaño, tipo y perceptual hash (phash) para deduplicación.
Compatible con Python 3.13+ (imghdr fue eliminado).
"""

import hashlib
import zipfile
from pathlib import Path
from typing import Union

try:
    import imagehash
    from PIL import Image
    HAS_IMAGEHASH = True
except ImportError:
    HAS_IMAGEHASH = False


def compute_file_hashes(file_path: Union[str, Path]) -> dict:
    """
    Calcular hashes y metadatos para un archivo .cbz/.cbr.
    
    Args:
        file_path: Ruta del archivo (acepta str o pathlib.Path)
    
    Returns:
        dict con:
            - sha256: Hash SHA-256 del contenido completo
            - size: Tamaño en bytes
            - type: Extensión sin punto ('cbz', 'cbr')
            - phash: Perceptual hash de la primera imagen (si está disponible)
    
    Raises:
        FileNotFoundError: Si el archivo no existe
        ValueError: Si la extensión no es .cbz o .cbr
    """
    # ✅ FIX CRÍTICO: Convertir a Path si es string
    fp = Path(file_path) if isinstance(file_path, str) else file_path
    
    # Validaciones básicas
    if not fp.exists():
        raise FileNotFoundError(f"Archivo no encontrado: {fp}")
    
    suffix = fp.suffix.lower()
    if suffix not in ('.cbz', '.cbr'):
        raise ValueError(f"Extensión no soportada: {suffix}. Esperado: .cbz o .cbr")
    
    file_type = suffix.lstrip('.')
    
    # Calcular SHA-256 del archivo completo
    sha256_hash = hashlib.sha256()
    with open(fp, "rb") as f:
        # Leer en chunks para manejar archivos grandes sin consumir memoria
        for chunk in iter(lambda: f.read(8192), b""):
            sha256_hash.update(chunk)
    
    # Obtener tamaño
    file_size = fp.stat().st_size
    
    # Calcular perceptual hash de la primera imagen (para deduplicación visual)
    phash = None
    if HAS_IMAGEHASH:
        try:
            phash = _compute_phash_from_archive(fp)
        except Exception:
            # Si falla el phash, no bloqueamos el procesamiento
            pass
    
    return {
        "sha256": sha256_hash.hexdigest(),
        "size": file_size,
        "type": file_type,
        "phash": str(phash) if phash else None,
    }


def _compute_phash_from_archive(archive_path: Path) -> str | None:
    """
    Extraer la primera imagen válida de un .cbz/.cbr y calcular su perceptual hash.
    
    Args:
        archive_path: Ruta al archivo .cbz o .cbr (ya validado como Path)
    
    Returns:
        str con el phash, o None si no se pudo calcular
    """
    try:
        with zipfile.ZipFile(archive_path, 'r') as zf:
            # Lista de extensiones de imagen válidas
            image_extensions = ('.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp')
            
            # Ordenar archivos para procesar en orden consistente
            names = sorted(n for n in zf.namelist() if not n.endswith('/'))
            
            for name in names:
                # Ignorar archivos de metadatos o carpetas
                if any(skip in name.lower() for skip in ['__macosx', '.ds_store', 'comicinfo.xml']):
                    continue
                
                # Verificar si es una imagen por extensión
                if not name.lower().endswith(image_extensions):
                    continue
                
                try:
                    # Extraer y abrir la imagen
                    with zf.open(name) as img_file:
                        # imagehash necesita un archivo real o BytesIO
                        import io
                        img = Image.open(io.BytesIO(img_file.read()))
                        
                        # Convertir a RGB si es necesario (para manejar PNG con alpha, etc.)
                        if img.mode not in ('RGB', 'L'):
                            img = img.convert('RGB')
                        
                        # Calcular perceptual hash (8x8 = 64 bits, buen balance precisión/velocidad)
                        phash = imagehash.phash(img, hash_size=8)
                        return str(phash)
                        
                except Exception:
                    # Si falla esta imagen, intentar con la siguiente
                    continue
                    
    except zipfile.BadZipFile:
        # Archivo corrupto o no es un ZIP válido
        pass
    except Exception:
        # Cualquier otro error (PIL, imagehash, etc.)
        pass
    
    return None


def verify_file_integrity(file_path: Union[str, Path], expected_hash: str) -> bool:
    """
    Verificar que un archivo coincide con un hash SHA-256 esperado.
    
    Args:
        file_path: Ruta del archivo a verificar
        expected_hash: Hash SHA-256 esperado (hex string)
    
    Returns:
        True si los hashes coinciden, False en caso contrario
    """
    try:
        fp = Path(file_path) if isinstance(file_path, str) else file_path
        if not fp.exists():
            return False
        
        sha256_hash = hashlib.sha256()
        with open(fp, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256_hash.update(chunk)
        
        return sha256_hash.hexdigest() == expected_hash.lower()
    except Exception:
        return False


def get_file_type(file_path: Union[str, Path]) -> str | None:
    """
    Obtener el tipo de archivo basado en la extensión.
    
    Args:
        file_path: Ruta del archivo
    
    Returns:
        'cbz', 'cbr', o None si no es reconocido
    """
    fp = Path(file_path) if isinstance(file_path, str) else file_path
    suffix = fp.suffix.lower()
    
    if suffix in ('.cbz', '.cbr'):
        return suffix.lstrip('.')
    return None