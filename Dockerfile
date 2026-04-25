# Dockerfile - Manganer Backend + Static Frontend
FROM python:3.13-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    APP_HOME=/app \
    DEBIAN_FRONTEND=noninteractive

WORKDIR $APP_HOME

# =============================================================================
# 1. Dependencias del sistema (libvips + unrar con repo non-free)
# =============================================================================
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl ca-certificates gnupg \
    && echo "deb http://deb.debian.org/debian bookworm main contrib non-free" > /etc/apt/sources.list \
    && echo "deb http://deb.debian.org/debian-security bookworm-security main contrib non-free" >> /etc/apt/sources.list \
    && apt-get update \
    && apt-get install -y --no-install-recommends \
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
# 3. Código de la aplicación
# =============================================================================
COPY app/ ./app/

# Copiar Alembic SOLO si los archivos existen (sin fallar si no)
RUN bash -c '[[ -f alembic.ini ]] && cp alembic.ini ./ || true'
RUN bash -c '[[ -f alembic/env.py ]] && mkdir -p ./alembic && cp alembic/env.py ./alembic/ || true'
RUN bash -c '[[ -f alembic/script.py.mako ]] && cp alembic/script.py.mako ./alembic/ || true'
RUN bash -c '[[ -d alembic/versions ]] && cp -r alembic/versions ./alembic/ || true'

# Crear estructura mínima de alembic si no existe
RUN mkdir -p /app/alembic/versions && \
    touch /app/alembic/__init__.py && \
    echo "# Minimal env.py for Manganer" > /app/alembic/env.py && \
    echo '"""${message}"""\nfrom alembic import op\nimport sqlalchemy as sa\ndef upgrade(): pass\ndef downgrade(): pass' > /app/alembic/script.py.mako

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