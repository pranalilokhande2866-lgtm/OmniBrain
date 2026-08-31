#!/usr/bin/env bash
# One-time project setup: virtualenv, dependencies, .env, seed the
# synthetic stock DB. Run from the project root:
#   bash scripts/setup.sh
set -euo pipefail

cd "$(dirname "$0")/.."

if [ ! -d "venv" ]; then
  echo "Creating virtual environment..."
  python3 -m venv venv
fi

source venv/bin/activate

echo "Installing dependencies (this pulls torch + sentence-transformers, may take a few minutes)..."
pip install --upgrade pip -q
pip install -r requirements.txt -q

if [ ! -f ".env" ]; then
  echo "Creating .env from .env.example - add your OPENAI_API_KEY before running the app."
  cp .env.example .env
fi

echo "Seeding synthetic stock database..."
cd backend
python -m app.db.init_db
cd ..

echo ""
echo "Setup complete. Next steps:"
echo "  1. Edit .env and add your OPENAI_API_KEY"
echo "  2. bash scripts/run_dev.sh"
