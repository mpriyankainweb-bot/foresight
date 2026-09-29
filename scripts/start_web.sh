#!/bin/sh
set -eu

# Keep the backend private to this container; Next.js proxies /health and /api/*.
/opt/foresight-venv/bin/uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 &
API_PID=$!

cleanup() {
  kill -TERM "$API_PID" 2>/dev/null || true
  wait "$API_PID" 2>/dev/null || true
}
trap cleanup INT TERM EXIT

cd /app
node server.js &
WEB_PID=$!
wait "$WEB_PID"
