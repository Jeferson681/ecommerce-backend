#!/bin/sh
set -e

# Run pending database migrations
alembic upgrade head

# Start the application
exec uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
