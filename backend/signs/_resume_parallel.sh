#!/usr/bin/env bash
# Resume partial INCLUDE downloads IN PARALLEL.
# Picks up where _download_small.sh left off using curl -C -.
# Exits when all files match expected sizes OR after MAX_ATTEMPTS.
set -e
CACHE="$(dirname "$0")/../.cache/include"
SUBSET_FILE="$CACHE/.smalls.txt"

if [[ ! -f "$SUBSET_FILE" ]]; then
  echo "Missing $SUBSET_FILE — run _download_small.sh first to set it up."
  exit 1
fi

MAX_ATTEMPTS=10
echo "Resuming downloads in parallel (up to $MAX_ATTEMPTS attempts each)..."
rm -f "$CACHE/.dl-*.log"

while read -r fname expected; do
  (
    attempts=0
    while (( attempts < MAX_ATTEMPTS )); do
      attempts=$((attempts + 1))
      actual=$(stat -c%s "$CACHE/$fname" 2>/dev/null || echo 0)
      if [[ "$actual" -ge "$expected" ]]; then
        echo "  ✓ done: $fname"
        exit 0
      fi
      echo "  ↓ attempt $attempts: $fname (have $((actual/1024/1024))MB, need $((expected/1024/1024))MB)"
      if curl -sSL -C - --max-time 1800 \
            "https://zenodo.org/records/4010759/files/$fname" \
            -o "$CACHE/$fname" > "$CACHE/.dl-${fname}.log" 2>&1; then
        actual=$(stat -c%s "$CACHE/$fname" 2>/dev/null || echo 0)
        if [[ "$actual" -ge "$expected" ]]; then
          echo "  ✓ done: $fname"
          exit 0
        fi
      fi
      sleep 3
    done
    echo "  ✗ gave up: $fname"
  ) &
done < "$SUBSET_FILE"

echo "All parallel resumes launched."
wait
echo "All resumes complete."

echo ""
echo "Final status:"
while read -r fname expected; do
  actual=$(stat -c%s "$CACHE/$fname" 2>/dev/null || echo 0)
  if [[ "$actual" -ge "$expected" ]]; then
    printf "  ✓ %6.1f MB  %s\n" "$(echo "scale=1; $actual/1024/1024" | bc)" "$fname"
  else
    printf "  ✗ %6.1f MB  %s (need %d more bytes)\n" \
      "$(echo "scale=1; $actual/1024/1024" | bc)" "$fname" "$((expected - actual))"
  fi
done < "$SUBSET_FILE"