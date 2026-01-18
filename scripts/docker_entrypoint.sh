#!/usr/bin/env bash
set -euo pipefail

export PYTHONPATH=/app

alembic -c /app/alembic.ini upgrade head
python /app/scripts/seed_dev.py

exec uvicorn src.app.main:app --host 0.0.0.0 --port 8000