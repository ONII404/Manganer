import os
from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import QueuePool
from app.config import settings

# Crear directorio de datos si no existe
os.makedirs(settings.DATA_DIR, exist_ok=True)

# ✅ Base declarativa definida y exportada desde aquí
Base = declarative_base()

engine = create_engine(
    settings.DB_URL,
    connect_args={"check_same_thread": False},
    poolclass=QueuePool,
    pool_size=4,
    max_overflow=8,
    pool_pre_ping=True,
    echo=settings.DEBUG,
)

@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    """Configura PRAGMAs de SQLite para rendimiento y concurrencia."""
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA cache_size=-200000")  # ~200MB page cache
    cursor.execute("PRAGMA synchronous=NORMAL")  # Balance speed/safety
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.execute("PRAGMA busy_timeout=5000")   # Evita SQLITE_BUSY
    cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """Dependency para FastAPI: yield de sesión DB."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()