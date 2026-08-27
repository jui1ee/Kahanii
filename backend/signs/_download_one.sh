#!/bin/bash
# Background curl-resumable download for one INCLUDE category.
# Usage: _download_one.sh <zip-filename>
#   e.g. _download_one.sh Pronouns_1of2.zip
# Logs to _download_<basename>.log.
set -u
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
CACHE="$SCRIPT_DIR/../.cache/include"
ZIP="${1:?usage: $0 <zip-filename>}"
LOG="$CACHE/.dl-$ZIP.log"

cd "$CACHE"

# Get expected size from Zenodo (best-effort; we fall back to no-size
# mode if the API is unreachable).
EXPECTED=$(curl -sSL "https://zenodo.org/api/records/4010759" 2>/dev/null \
  | python3 -c "
import json, sys
try:
    d = json.load(sys.stdin)
    for f in d.get('files', []):
        if f['key'] == '$ZIP':
            print(f['size']); break
except Exception:
    pass
" 2>/dev/null || echo 0)

echo "$(date -Iseconds) start: $ZIP expected=${EXPECTED}B" >> "$LOG"
echo "$(date -Iseconds) start: $ZIP expected=${EXPECTED}B" >&2

# Resumable download with curl -C - and 10 retries.
curl -sSL -C - --retry 10 --retry-delay 5 --retry-all-errors \
  --connect-timeout 30 --max-time 7200 \
  -o "$CACHE/$ZIP" \
  "https://zenodo.org/records/4010759/files/$ZIP" >> "$LOG" 2>&1
RC=$?
ACTUAL=$(stat -c%s "$CACHE/$ZIP" 2>/dev/null || echo 0)
echo "$(date -Iseconds) finished: $ZIP rc=$RC actual=${ACTUAL}B" >> "$LOG"
echo "$(date -Iseconds) finished: $ZIP rc=$RC actual=${ACTUAL}B expected=${EXPECTED}B" >&2
exit $RC