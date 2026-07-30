#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
APP_DIR="$ROOT/deepagent_src/frontend_teach"
WEB_DIR="$APP_DIR/web"
LOG_DIR="$APP_DIR/.logs"
BACKEND_PID="$APP_DIR/.backend.pid"
FRONTEND_PID="$APP_DIR/.frontend.pid"

mkdir -p "$LOG_DIR"

if [[ -f "$BACKEND_PID" ]] && kill -0 "$(cat "$BACKEND_PID")" 2>/dev/null; then
  echo "backend already running: $(cat "$BACKEND_PID")"
else
  python3 - "$ROOT" "$LOG_DIR/backend.log" "$BACKEND_PID" <<'PY'
import subprocess
import sys

cwd, log_path, pid_path = sys.argv[1:]
log = open(log_path, "ab", buffering=0)
process = subprocess.Popen(
    ["uv", "run", "langgraph", "dev", "--config", "deepagent_src/frontend_teach/langgraph.json", "--no-browser", "--no-reload", "--port", "2024"],
    cwd=cwd,
    stdout=log,
    stderr=subprocess.STDOUT,
    start_new_session=True,
)
with open(pid_path, "w", encoding="utf-8") as file:
    file.write(str(process.pid))
PY
  echo "backend started: $(cat "$BACKEND_PID")"
fi

if [[ -f "$FRONTEND_PID" ]] && kill -0 "$(cat "$FRONTEND_PID")" 2>/dev/null; then
  echo "frontend already running: $(cat "$FRONTEND_PID")"
else
  python3 - "$WEB_DIR" "$LOG_DIR/frontend.log" "$FRONTEND_PID" <<'PY'
import subprocess
import sys

cwd, log_path, pid_path = sys.argv[1:]
log = open(log_path, "ab", buffering=0)
process = subprocess.Popen(
    ["npm", "run", "dev", "--", "--host", "127.0.0.1", "--port", "5173"],
    cwd=cwd,
    stdout=log,
    stderr=subprocess.STDOUT,
    start_new_session=True,
)
with open(pid_path, "w", encoding="utf-8") as file:
    file.write(str(process.pid))
PY
  echo "frontend started: $(cat "$FRONTEND_PID")"
fi

echo "backend:  http://127.0.0.1:2024"
echo "frontend: http://127.0.0.1:5173"
echo "logs:     $LOG_DIR"
