#!/usr/bin/env bash
# start.sh — Launch autoresearch-council-arena
# Starts: FastAPI backend (8001) + React frontend (5173) + experiment loop

set -e

ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

# Check for .env
if [ ! -f .env ]; then
  echo "ERROR: .env not found. Copy .env.example and add your OPENROUTER_API_KEY."
  echo "  cp .env.example .env && nano .env"
  exit 1
fi

# Check for uv
if ! command -v uv &>/dev/null; then
  echo "ERROR: 'uv' not found. Install it: https://docs.astral.sh/uv/getting-started/installation/"
  exit 1
fi

# Install Python dependencies
echo "[start] Installing Python dependencies..."
uv pip install httpx python-dotenv fastapi uvicorn --quiet

# Install frontend dependencies
if [ ! -d frontend/node_modules ]; then
  echo "[start] Installing frontend dependencies..."
  cd frontend && npm install --silent && cd ..
fi

# Start FastAPI backend
echo "[start] Starting backend on http://localhost:8001 ..."
uv run python -m uvicorn backend.server:app --host 0.0.0.0 --port 8001 --reload &
BACKEND_PID=$!

# Give backend a moment to start
sleep 2

# Start React frontend
echo "[start] Starting frontend on http://localhost:5173 ..."
(cd "$ROOT/frontend" && npm run dev) &
FRONTEND_PID=$!

sleep 2
echo ""
echo "========================================"
echo "  AutoResearch Council Arena is running"
echo "  Frontend: http://localhost:5173"
echo "  Backend:  http://localhost:8001"
echo "========================================"
echo ""

# Start experiment loop (foreground — Ctrl+C to stop everything)
# All output is tee'd to run.log for post-run inspection
echo "[start] Starting experiment loop (Ctrl+C to stop)..."
echo "[start] Logging to run.log"
uv run python run.py 2>&1 | tee run.log

# Cleanup on exit
kill $BACKEND_PID $FRONTEND_PID 2>/dev/null || true
