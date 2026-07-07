#!/usr/bin/env bash
# Double-click this file to launch MelodAI:
#   1. Starts the backend if it isn't already running
#   2. Waits until the model server is healthy
#   3. Opens the app in your default browser
# (Right-click > Open the first time if macOS Gatekeeper warns about it.)

cd "$(dirname "$0")"
ENGINE="$(pwd)/acestep-engine"

echo "MelodAI launcher"
echo "================"

# 1. Is a HEALTHY backend already up? (and only one instance)
RUNNING=$(pgrep -f "uvicorn server:app" | wc -l | tr -d ' ')
if [ "$RUNNING" = "1" ] && curl -s --max-time 3 http://localhost:8000/health >/dev/null 2>&1; then
  echo "Backend already running (1 instance)."
else
  # Clean slate: force-kill any stale/duplicate instances first so multiple
  # copies of the model can't pile up and thrash memory.
  if [ "$RUNNING" != "0" ]; then
    echo "Clearing $RUNNING stale backend process(es)..."
    pkill -9 -f "uvicorn server:app" 2>/dev/null
    sleep 3
  fi
  echo "Starting backend..."
  cd "$ENGINE"
  source venv/bin/activate
  # start detached so closing this window doesn't kill it
  nohup uvicorn server:app --port 8000 >/tmp/melodai_acestep.log 2>&1 &
  cd ..

  # 2. Wait for it to answer (up to ~30s)
  printf "Waiting for backend"
  for i in $(seq 1 30); do
    if curl -s --max-time 2 http://localhost:8000/health >/dev/null 2>&1; then
      echo " ready."
      break
    fi
    printf "."
    sleep 1
  done
fi

# 3. Open the app
echo "Opening MelodAI at http://localhost:8000 ..."
open "http://localhost:8000"

echo ""
echo "Done. Leave the backend running in the background."
echo "The first song also downloads/loads the model, so it takes a bit longer."
