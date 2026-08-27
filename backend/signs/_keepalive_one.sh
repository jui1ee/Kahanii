#!/bin/bash
# Keepalive ping for one background INCLUDE download.
# Touch /tmp/keepalive_include.stop to stop.
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
STOP_FILE="/tmp/keepalive_include.stop"
LOG="$SCRIPT_DIR/../.cache/include/_keepalive_one.log"
INTERVAL=240

echo "$(date -Iseconds) keepalive-one started (pid $$)" >> "$LOG"
i=0
while [ ! -f "$STOP_FILE" ]; do
  i=$((i+1))
  size=$(stat -c %s "/home/juilee/projects/Kahani/Bidirectional-Indian-Sign-Language-Translator/backend/.cache/include/$1" 2>/dev/null || echo 0)
  echo "$(date -Iseconds) tick=$i size=${size}B (~$(echo "scale=1; $size/1048576" | bc)MB)" >> "$LOG"
  sleep "$INTERVAL"
done
echo "$(date -Iseconds) keepalive-one stopped" >> "$LOG"