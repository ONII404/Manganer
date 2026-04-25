import xml.etree.ElementTree as ET
from pathlib import Path
import zipfile
from pydantic import BaseModel, Field
from typing import Optional
import defusedxml.ElementTree as DET
import logging

class ComicInfoV2(BaseModel):
    """Schema tipo-safe para ComicInfo.xml v2.0"""
    title: Optional[str] = None
    series: Optional[str] = None
    number: Optional[str] = None
    writer: Optional[str] = None
    penciller: Optional[str] = None
    genre: Optional[str] = None
    summary: Optional[str] = None
    year: Optional[int] = None
    publisher: Optional[str] = None
    pages: Optional[int] = None
    web: Optional[str] = None
    language_iso: str = Field(default="es", pattern=r"^[a-z]{2}(-[A-Z]{2})?$")
    
    
    def to_xml(self) -> bytes:
        root = ET.Element("ComicInfo", {
            "xmlns:xsi": "http://www.w3.org/2001/XMLSchema-instance",
            "xmlns:xsd": "http://www.w3.org/2001/XMLSchema"
        })
        for field, value in self.model_dump(exclude_none=True).items():
            if value is not None:
                child = ET.SubElement(root, field.title().replace("_", ""))
                child.text = str(value)
        return ET.tostring(root, encoding="utf-8", xml_declaration=True)
    
    @classmethod
    def from_xml(cls, xml_bytes: bytes) -> "ComicInfoV2":
        root = DET.fromstring(xml_bytes)
        data = {}
        for child in root:
            tag = child.tag.lower()
            if tag in cls.model_fields:
                value = child.text or ""
                if tag == "year" and value.isdigit():
                    value = int(value)
                data[tag] = value
        return cls(**data)

logger = logging.getLogger(__name__)

def extract_comic_info(cbz_path: Path) -> ComicInfoV2 | None:
    """Extrae ComicInfo.xml desde archivo .cbz sin descomprimir completo."""
    try:
        with zipfile.ZipFile(cbz_path, 'r') as zf:
            if "ComicInfo.xml" in zf.namelist():
                xml_data = zf.read("ComicInfo.xml")
                return ComicInfoV2.from_xml(xml_data)
    except Exception as e:
        logger.warning(f"⚠️ No se pudo leer ComicInfo.xml de {cbz_path.name}: {e}")
    return None

def inject_comic_info(cbz_path: Path, comic_info: ComicInfoV2) -> bool:
    """Inyecta/actualiza ComicInfo.xml en .cbz atómicamente."""
    import tempfile, shutil, os
    temp_fd, temp_path = tempfile.mkstemp(dir=cbz_path.parent, suffix=".cbz.tmp")
    os.close(temp_fd)
    try:
        with zipfile.ZipFile(cbz_path, 'r') as src, zipfile.ZipFile(temp_path, 'w') as dst:
            # Copiar todo excepto ComicInfo.xml viejo
            for item in src.infolist():
                if item.filename != "ComicInfo.xml":
                    dst.writestr(item, src.read(item.filename))
            # Añadir nuevo ComicInfo.xml al inicio (estándar)
            dst.writestr("ComicInfo.xml", comic_info.to_xml())
        shutil.move(temp_path, cbz_path)
        return True
    except Exception as e:
        if os.path.exists(temp_path):
            os.unlink(temp_path)
        logger.error(f"❌ Fallo inyectando ComicInfo.xml: {e}")
        return False