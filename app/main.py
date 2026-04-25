# app/main.py
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from watchdog.observers import Observer
from pathlib import Path
import logging
import asyncio

# Config
from app.config import settings
from app.database import Base, engine, get_db
from app.api import health, tasks, opds, files
from app.services.watchdog_handler import MangaWatchdogHandler
from app.tasks.scan_tasks import process_new_file_task
from app.services.metadata_fetcher import MetadataFetcher
from app.services.translation_cache import DeepLTranslator

logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager para inicialización y shutdown limpio."""
    logger.info("🚀 Inicializando Manganer...")
    
    # Crear tablas de base de datos
    Base.metadata.create_all(bind=engine)
    logger.info("✅ Base de datos inicializada con WAL")
    
    # Iniciar Watchdog para escaneo de archivos
    handler = MangaWatchdogHandler(cooldown=2.0, task_func=process_new_file_task)
    observer = Observer()
    observer.schedule(handler, str(settings.DATA_DIR), recursive=True)
    observer.start()
    app.state.watcher = observer
    logger.info(f"👁️ Watchdog activo en {settings.DATA_DIR}")
    
    # Inicializar servicios globales
    app.state.metadata_fetcher = MetadataFetcher(
        api_keys={
            "anilist": settings.ANILIST_CLIENT_ID,
            "mal": settings.MAL_CLIENT_ID,
        }
    )
    app.state.translator = DeepLTranslator(
        api_key=settings.DEEPL_API_KEY,
        target_lang=settings.DEFAULT_LANG.upper()
    )
    logger.info("🌐 Servicios de metadatos y traducción inicializados")
    
    yield
    
    # Shutdown limpio
    logger.info("🛑 Cerrando servicios...")
    if hasattr(app.state, "watcher"):
        app.state.watcher.stop()
        app.state.watcher.join()
    if hasattr(app.state, "translator"):
        app.state.translator.close()
    engine.dispose()
    logger.info("✅ Shutdown completado")


# Crear aplicación FastAPI
app = FastAPI(
    title=settings.APP_NAME,
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/api/docs" if settings.DEBUG else None,
    redoc_url="/api/redoc" if settings.DEBUG else None,
    openapi_url="/api/openapi.json" if settings.DEBUG else None,
)

# CORS middleware (ajustar para producción)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.DEBUG else ["http://localhost:3000", "http://localhost:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir routers de API
app.include_router(health.router, prefix="/api/v1", tags=["System"])
app.include_router(tasks.router, prefix="/api/v1", tags=["Tasks"])
app.include_router(opds.router, prefix="/api/v1", tags=["OPDS"])
app.include_router(files.router, prefix="/api/v1", tags=["Files"])


# =============================================================================
# 🎨 SERVICIO DE FRONTEND (SPA) - Producción
# =============================================================================

STATIC_DIR = Path(__file__).parent.parent / "static"

if STATIC_DIR.exists() and (STATIC_DIR / "index.html").exists():
    logger.info(f"🎨 Frontend estático detectado en {STATIC_DIR}")
    
    # Montar assets estáticos (JS, CSS, imágenes)
    assets_dir = STATIC_DIR / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")
    
    # Fallback para SPA: servir index.html para rutas no-API
    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_spa(request: Request, full_path: str):
        """Sirve el frontend React para rutas no-API (SPA routing)."""
        # Excluir explícitamente rutas de API
        if full_path.startswith("api/"):
            return JSONResponse(status_code=404, content={"detail": "API endpoint not found"})
        
        # Excluir rutas de documentación (solo en debug)
        if settings.DEBUG and full_path in ("docs", "redoc", "openapi.json"):
            return JSONResponse(status_code=404, content={"detail": "Not found"})
        
        # Servir index.html para cualquier otra ruta (habilita client-side routing)
        index_file = STATIC_DIR / "index.html"
        if index_file.exists():
            return FileResponse(str(index_file))
        
        return JSONResponse(status_code=404, content={"detail": "Frontend not built"})
else:
    # Modo desarrollo sin frontend buildado
    @app.get("/")
    async def root():
        return {
            "message": "Manganer API",
            "docs": "/api/docs" if settings.DEBUG else None,
            "health": "/api/v1/health",
            "note": "Build frontend with: cd frontend && npm run build, then copy to app/static/"
        }


# =============================================================================
# 🏁 Punto de entrada
# =============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        workers=settings.WORKERS,
        reload=settings.DEBUG,
        reload_dirs=["app"] if settings.DEBUG else None,
    )