#!/usr/bin/env bash
set -euo pipefail

APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

stop_port() {
  local label="$1"
  local port="$2"
  local pids

  pids="$(lsof -tiTCP:"$port" -sTCP:LISTEN 2>/dev/null || true)"
  for pid in $pids; do
    local command
    command="$(ps -p "$pid" -o command= 2>/dev/null || true)"
    if [[ "$command" == *"deepagent_src/frontend_teach"* || "$command" == *"$APP_DIR"* ]]; then
      local pgid
      pgid="$(ps -p "$pid" -o pgid= 2>/dev/null | tr -d ' ')"
      kill -- "-$pgid" 2>/dev/null || true
      kill "$pid" 2>/dev/null || true
      echo "$label port $port stopped: $pid"
    else
      echo "$label port $port occupied by unrelated process: $pid"
    fi
  done
}

stop_pid_file() {
  local label="$1"
  local file="$2"

  if [[ ! -f "$file" ]]; then
    echo "$label not running"
    return
  fi

  local pid
  pid="$(cat "$file")"
  if kill -0 "$pid" 2>/dev/null; then
    kill -- "-$pid" 2>/dev/null || true
    kill "$pid" 2>/dev/null || true
    echo "$label stopped: $pid"
  else
    echo "$label stale pid: $pid"
  fi
  rm -f "$file"
}

stop_pid_file "frontend" "$APP_DIR/.frontend.pid"
stop_pid_file "backend" "$APP_DIR/.backend.pid"
stop_port "frontend" "5173"
stop_port "backend" "2024"
