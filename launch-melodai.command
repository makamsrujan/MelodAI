#!/bin/bash

# MelodAI Launcher — starts backend and opens browser automatically
# Usage: Double-click this file or run: bash launch-melodai.command

set -e

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENGINE_DIR="$REPO_ROOT/acestep-engine"
VENV_DIR="$ENGINE_DIR/venv"
PORT=8000
URL="http://localhost:$PORT"

# Check if venv exists
if [ ! -f "$VENV_DIR/bin/activate" ]; then
    echo "❌ Virtual environment not found at $VENV_DIR"
    echo "Please run setup first:"
    echo ""
    echo "  git clone https://github.com/ace-step/ACE-Step.git /tmp/ace-step"
    echo "  cp -R /tmp/ace-step/. $ENGINE_DIR"
    echo "  cd $ENGINE_DIR"
    echo "  python3.11 -m venv venv"
    echo "  source venv/bin/activate"
    echo "  pip install -e ."
    echo "  pip install -r requirements-server.txt"
    echo ""
    exit 1
fi

echo "🚀 Starting MelodAI backend..."
cd "$ENGINE_DIR"

# Check if server is already running
if curl -s "$URL/health" > /dev/null 2>&1; then
    echo "✅ Backend already running at $URL"
else
    # Start the server in the background
    source "$VENV_DIR/bin/activate"
    nohup uvicorn server:app --port $PORT > /tmp/melodai-server.log 2>&1 &
    SERVER_PID=$!
    echo "📡 Backend starting (PID: $SERVER_PID)..."
    
    # Wait for server to be ready
    echo "⏳ Waiting for backend to respond..."
    for i in {1..30}; do
        if curl -s "$URL/health" > /dev/null 2>&1; then
            echo "✅ Backend is ready!"
            break
        fi
        sleep 1
    done
fi

# Open browser
echo "🌐 Opening MelodAI in your browser..."
open "$URL"
echo "Done! Server logs: tail -f /tmp/melodai-server.log"
