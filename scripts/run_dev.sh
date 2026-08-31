#!/usr/bin/env bash
# Starts the FastAPI backend and Streamlit frontend together.
# Run from the project root: bash scripts/run_dev.sh
set -euo pipefail

cd "$(dirname "$0")/.."
source venv/bin/activate

cleanup() {
  echo ""
  echo "Shutting down..."
  kill "$BACKEND_PID" 2>/dev/null || true
}
trap cleanup EXIT

echo "Starting FastAPI backend on http://localhost:8000 ..."
(cd backend && uvicorn app.main:app --reload --port 8000) &
BACKEND_PID=$!

sleep 3

echo "Starting Streamlit frontend on http://localhost:8501 ..."
(cd frontend && streamlit run streamlit_app.py)
