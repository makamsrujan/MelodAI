#!/usr/bin/env bash
# Start the MelodAI backend (local ACE-Step). Open MelodAI.html in a browser after.
set -e
cd "$(dirname "$0")/acestep-engine"

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
echo "Now open MelodAI.html in your browser."
echo ""
exec uvicorn server:app --port 8000
