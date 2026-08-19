#!/usr/bin/env bash
# Resume any partial downloads that died with curl error 18.
# Uses curl -C - to continue from where the file left off.
set -e
CACHE="$(dirname "$0")/../.cache/include"
mkdir -p "$CACHE"

# Pull expected sizes from the Zenodo record so we can tell "complete" from "partial".
echo "Refreshing expected sizes from Zenodo..."
SIZES=$(curl -sL "https://zenodo.org/api/records/4010759" | python3 -c "
import json, sys
d = json.load(sys.stdin)
for f in d['files']:
    print(f['key'], f['size'])
")

declare -A EXPECTED
while read -r name size; do
  EXPECTED[$name]=$size
done <<< "$SIZES"

FILES=(
  "Greetings_1of2.zip"
  "Greetings_2of2.zip"
  "Animals_1of2.zip"
  "Animals_2of2.zip"
  "Colours_1of2.zip"
  "Colours_2of2.zip"
  "Pronouns_1of2.zip"
  "Pronouns_2of2.zip"
  "Seasons_1of1.zip"
  "Days_and_Time_1of3.zip"
  "Days_and_Time_2of3.zip"
  "Days_and_Time_3of3.zip"
)

for f in "${FILES[@]}"; do
  expected=${EXPECTED[$f]:-0}
  actual=$(stat -c%s "$CACHE/$f" 2>/dev/null || echo 0)
  if [[ "$actual" -eq "$expected" ]] && [[ "$expected" -gt 0 ]]; then
    echo "  ✓ done: $f ($actual bytes)"
    continue
  fi
  echo "  ↓ resuming $f (have $actual, need $expected)"
  curl -sSL -C - "https://zenodo.org/records/4010759/files/$f" -o "$CACHE/$f" \
    && echo "  ✓ done: $f" \
    || echo "  ✗ failed: $f"
done

echo "All downloads complete."
