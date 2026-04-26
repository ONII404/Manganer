# app/main.py
from contextlib import asynccontextmanager
from pathlib import Path
import logging
import os
import threading
import time

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

# App config & database
from app.config import settings
from app.database import Base, engine

# API routers (Importación con alias para evitar conflictos)
from app.api import health as health_router
from app.api import tasks as tasks_router
from app.api import files as files_router
from app.api import opds as opds_router

# Services & tasks
from app.services.watchdog_handler import MangaWatchdogHandler
from app.tasks.scan_tasks import process_new_file_task
from app.services.metadata_fetcher import MetadataFetcher
from app.services.translation_cache import DeepLTranslator

logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
)
logger = logging.getLogger(__name__)


class SimpleLibraryPoller:
    """Poller nativo para Docker+Windows."""
    def __init__(self, library_path: str, handler, interval: float = 2.0):
        self.library_path = Path(library_path)
        self.handler = handler
        self.interval = interval
        self.running = True
        self.known_files: set[str] = set()
        if self.library_path.exists():
            for root, _, files in os.walk(self.library_path):
                for file in files:
                    self.known_files.add(os.path.join(root, file))
        self.thread = threading.Thread(target=self._poll, daemon=True)

    def start(self) -> None:
        logger.info(f"👁️ Poller activo en {self.library_path}")
        self.thread.start()

    def stop(self) -> None:
        self.running = False
        self.thread.join()

    def _poll(self) -> None:
        while self.running:
            try:
                if not self.library_path.exists():
                    time.sleep(self.interval)
                    continue
                current_files: set[str] = set()
                for root, _, files in os.walk(self.library_path):
                    for file in files:
                        current_files.add(os.path.join(root, file))
                new_files = current_files - self.known_files
                for file_path in new_files:
                    if file_path.lower().endswith(('.cbz', '.cbr')):
                        logger.debug(f"🔍 Nuevo: {file_path}")
                        if hasattr(self.handler, '_on_event'):
                            self.handler._on_event(file_path)
                self.known_files = current_files
            except Exception as e:
                logger.error(f"❌ Error Poller: {e}")
            time.sleep(self.interval)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 Inicializando Manganer...")
    Base.metadata.create_all(bind=engine)
    logger.info("✅ DB inicializada")
    
    try:
        Path(settings.LIBRARY_DIR).mkdir(parents=True, exist_ok=True)
        handler = MangaWatchdogHandler(cooldown=2.0, task_func=process_new_file_task)
        poller = SimpleLibraryPoller(settings.LIBRARY_DIR, handler, interval=2.0)
        poller.start()
        app.state.watcher = poller
        logger.info(f"✅ Poller en {settings.LIBRARY_DIR}")
    except Exception as e:
        logger.error(f"❌ Watchdog: {e}")
    
    app.state.metadata_fetcher = MetadataFetcher(
        api_keys={"anilist": settings.ANILIST_CLIENT_ID, "mal": settings.MAL_CLIENT_ID}
    )
    app.state.translator = DeepLTranslator(
        api_key=settings.DEEPL_API_KEY, target_lang=settings.DEFAULT_LANG.upper()
    )
    logger.info("🌐 Servicios listos")
    yield
    if hasattr(app.state, "watcher"): app.state.watcher.stop()
    if hasattr(app.state, "translator"): app.state.translator.close()
    engine.dispose()


# =============================================================================
# 🚀 App FastAPI
# =============================================================================
app = FastAPI(
    title=settings.APP_NAME,
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.DEBUG else ["http://localhost:3000", "http://localhost:8000"],
    allow_credentials=True, allow_methods=["*"], allow_headers=["*"],
)

# =============================================================================
# 📡 INCLUSIÓN DE ROUTERS (Prefijos alineados)
# =============================================================================
# NOTA: files.py, tasks.py y opds.py ya tienen su propio prefix ("/files", "/tasks", "/opds")
# Por eso aquí solo usamos el prefijo base "/api/v1"
app.include_router(health_router.router, prefix="/api/v1")
app.include_router(tasks_router.router, prefix="/api/v1")
app.include_router(files_router.router, prefix="/api/v1")
app.include_router(opds_router.router, prefix="/api/v1")


# =============================================================================
# 🎨 Frontend SPA
# =============================================================================
STATIC_DIR = Path(__file__).parent.parent / "static"

if STATIC_DIR.exists() and (STATIC_DIR / "index.html").exists():
    logger.info(f"🎨 Frontend en {STATIC_DIR}")
    assets_dir = STATIC_DIR / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")
    
    @app.get("/", response_class=HTMLResponse, include_in_schema=False)
    async def serve_spa_root():
        return FileResponse(str(STATIC_DIR / "index.html"))
    
    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_spa_catchall(request: Request):
        path = request.url.path
        if path in ["/docs", "/redoc", "/openapi.json"]:
            raise HTTPException(status_code=404)
        if path.startswith("/api/") or path.startswith("/assets/"):
            raise HTTPException(status_code=404)
        index_file = STATIC_DIR / "index.html"
        if index_file.exists():
            return FileResponse(str(index_file))
        raise HTTPException(status_code=404)
else:
    @app.get("/", include_in_schema=False)
    async def root():
        return {"message": "Manganer API", "docs": "/docs", "health": "/api/v1/health"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, workers=settings.WORKERS, reload=settings.DEBUG, reload_dirs=["app"] if settings.DEBUG else None)