#!/bin/sh
set -e

# Runtime validation: verify critical packages are importable
python -c "import psycopg; print('psycopg version:', psycopg.__version__)" || { echo 'ERROR: psycopg not available'; exit 1; }
python -c "import sqlalchemy; print('sqlalchemy version:', sqlalchemy.__version__)" || { echo 'ERROR: sqlalchemy not available'; exit 1; }
python -c "import alembic; print('alembic available')" || { echo 'ERROR: alembic not available'; exit 1; }
python -c "import fastapi; print('fastapi version:', fastapi.__version__)" || { echo 'ERROR: fastapi not available'; exit 1; }

# Validate DATABASE_URL driver
python -c "from urllib.parse import urlparse; import os; url = os.environ.get('DATABASE_URL', ''); parsed = urlparse(url); assert 'psycopg' in parsed.scheme, f'ERROR: DATABASE_URL uses wrong driver: {parsed.scheme}'; print('DATABASE_URL driver:', parsed.scheme)" || { echo 'ERROR: DATABASE_URL validation failed'; exit 1; }

# Run pending database migrations
python -m alembic upgrade head

# Start the application
exec python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
