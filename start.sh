#!/usr/bin/env bash
set -e

# Python deps
if [ ! -d ".venv" ]; then
  python3 -m venv .venv
fi
source .venv/bin/activate
pip install --upgrade pip wheel >/dev/null 2>&1
pip install -r requirements.txt >/dev/null 2>&1

# Frontend deps/build
if [ ! -d "web/node_modules" ]; then
  echo "Installing frontend deps..."
  (cd web && npm install >/dev/null 2>&1)
fi
if [ ! -d "web/dist" ]; then
  echo "Building frontend..."
  (cd web && npm run build)
fi

exec uvicorn main:app --host 0.0.0.0 --port 8000
