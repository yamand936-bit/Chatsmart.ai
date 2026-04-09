#!/bin/bash
set -e

# Wait for DB to be up
echo "Waiting for PostgreSQL to be ready..."
sleep 5

# Run migrations
echo "Running Alembic migrations..."
alembic upgrade head

# Start application
echo "Starting FastAPI server..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
