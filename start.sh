#!/bin/bash
set -e

# Start Python backend on port 8001
cd /app/backend
python3 -m uvicorn main:app --host 0.0.0.0 --port 8001 &
API_PID=$!
echo "Python backend started on port 8001 (PID: $API_PID)"

# Wait for backend to be ready
for i in $(seq 1 10); do
  if curl -s http://localhost:8001/api/health > /dev/null 2>&1; then
    echo "Backend is ready"
    break
  fi
  echo "Waiting for backend... ($i)"
  sleep 1
done

# Start Node SSR server on Railway's PORT
cd /app
echo "Starting Node SSR server on port $PORT"
node server.mjs

# If Node exits, kill the backend too
kill $API_PID 2>/dev/null
# trigger redeploy
