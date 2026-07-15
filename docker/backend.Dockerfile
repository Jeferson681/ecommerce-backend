# Stage 1: Build dependencies
FROM python:3.13-slim AS builder

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Build-time validation: verify critical packages are importable
RUN python -c "import psycopg; print('psycopg version:', psycopg.__version__)" && \
    python -c "import sqlalchemy; print('sqlalchemy version:', sqlalchemy.__version__)" && \
    python -c "import alembic; print('alembic available')" && \
    python -c "import fastapi; print('fastapi version:', fastapi.__version__)"

# Stage 2: Production
FROM python:3.13-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

RUN useradd -m -u 1000 appuser

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /usr/local/lib/python3.13/site-packages /usr/local/lib/python3.13/site-packages

# Runtime validation: verify packages were copied correctly
RUN python -c "import psycopg; print('psycopg version:', psycopg.__version__)" && \
    python -c "import sqlalchemy; print('sqlalchemy version:', sqlalchemy.__version__)" && \
    python -c "import alembic; print('alembic available')" && \
    python -c "import fastapi; print('fastapi version:', fastapi.__version__)" && \
    python -m alembic --help >/dev/null && \
    python -m uvicorn --help >/dev/null && \
    python - <<'PY'
from sqlalchemy import create_engine
engine = create_engine("postgresql+psycopg://user:pass@localhost/db")
print("SQLAlchemy driver:", engine.dialect.driver)
assert engine.dialect.driver == "psycopg", f"Wrong driver: {engine.dialect.driver}"
PY

COPY backend/ ./backend/
COPY alembic.ini .
COPY alembic/ ./alembic/
COPY docker/backend-entrypoint.sh /app/entrypoint.sh

RUN chmod +x /app/entrypoint.sh && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=5 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/healthz')" || exit 1

ARG VERSION=unknown
ARG COMMIT=unknown
ARG BUILD_DATE=unknown

LABEL org.opencontainers.image.title="ecommerce-backend"
LABEL org.opencontainers.image.description="FastAPI backend"
LABEL org.opencontainers.image.version=$VERSION
LABEL org.opencontainers.image.revision=$COMMIT
LABEL org.opencontainers.image.created=$BUILD_DATE

CMD ["/app/entrypoint.sh"]
