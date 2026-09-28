#!/usr/bin/env bash
set -e

echo "Applying pending migrations..."
alembic upgrade head

echo "Starting Uvicorn production server..."
exec uvicorn app.main:app --host 0.0.0.0 --port $PORT