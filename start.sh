#!/usr/bin/env bash
# Start the MelodAI backend (local ACE-Step). Open MelodAI.html in a browser after.
set -e

REPO_ROOT="$(cd "$(dirname "$0")" && pwd)"
ENGINE_DIR="$REPO_ROOT/acestep-engine"

cd "$ENGINE_DIR"

if [ ! -d venv ]; then
  echo "First-time setup: creating venv and installing ACE-Step..."
  python3.11 -m venv venv
  source venv/bin/activate
  pip install --upgrade pip
  pip install -e .
  pip install torchcodec
else
  source venv/bin/activate
fi

echo ""
echo "Starting MelodAI backend on http://localhost:8000"
echo "Open http://localhost:8000 in your browser (API docs at /docs)."
echo ""
exec uvicorn server:app --host 0.0.0.0 --port 8000
