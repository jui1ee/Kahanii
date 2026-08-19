#!/usr/bin/env bash
# Keepalive — pings the backend (or Zenodo as fallback) every 4 minutes
# so the API key stays warm while the INCLUDE dataset downloads run.
# Exits cleanly when /tmp/keepalive.stop is touched.
set -e

STOP_FILE="/tmp/keepalive.stop"
INTERVAL=240  # 4 minutes
ELAPSED=0

while true; do
  if [[ -f "$STOP_FILE" ]]; then
    echo "$(date '+%H:%M:%S') stop file present, exiting"
    exit 0
  fi
  if curl -s --max-time 5 http://127.0.0.1:3002/healthz > /dev/null 2>&1; then
    code=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 http://127.0.0.1:3002/healthz)
    target="backend"
  else
    code=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 https://zenodo.org/api/records/4010759)
    target="zenodo"
  fi
  ELAPSED=$((ELAPSED + INTERVAL))
  mins=$((ELAPSED / 60))
  echo "$(date '+%H:%M:%S') keepalive (${mins}m elapsed)  $target  HTTP $code"
  sleep "$INTERVAL"
done