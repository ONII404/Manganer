# Dockerfile - Manganer Backend + Static Frontend
FROM python:3.13-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    APP_HOME=/app \
    DEBIAN_FRONTEND=noninteractive

WORKDIR $APP_HOME

# =============================================================================
# 1. Dependencias del sistema (libvips + unrar)
# =============================================================================
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    libvips \
    libvips-tools \
    libvips-dev \
    unrar \
    build-essential \
    pkg-config \
    && rm -rf /var/lib/apt/lists/* \
    && ldconfig

# =============================================================================
# 2. Dependencias Python
# =============================================================================
COPY pyproject.toml ./
RUN pip install --no-cache-dir --upgrade pip setuptools wheel
RUN pip install --no-cache-dir -e ".[dev]"
RUN pip install --no-cache-dir pyvips>=2.2.0

# =============================================================================
# 3. Código de la aplicación (COPY linter-compliant)
# =============================================================================
# ✅ Copiar app/ como directorio (destino termina en /)
COPY app/ ./app/

# ✅ Copiar archivos individuales de alembic (evita warning de "multiple sources")
COPY alembic.ini ./alembic.ini
COPY alembic/env.py ./alembic/env.py
COPY alembic/script.py.mako ./alembic/script.py.mako
COPY alembic/versions/ ./alembic/versions/

# ✅ Crear __init__.py si no existe (para que Python reconozca el paquete)
RUN touch /app/alembic/__init__.py 2>/dev/null || true

# =============================================================================
# 4. Frontend estático (se copia desde host vía volumen)
# =============================================================================
RUN mkdir -p /app/static && chmod 755 /app/static

# =============================================================================
# 5. Directorios de datos
# =============================================================================
RUN mkdir -p /app/data /app/library && chmod 777 /app/data /app/library

# =============================================================================
# 6. Healthcheck y puerto
# =============================================================================
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=20s --retries=5 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/v1/health')" || exit 1

# =============================================================================
# 7. Comando de inicio
# =============================================================================
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers ${WORKERS:-4}"]