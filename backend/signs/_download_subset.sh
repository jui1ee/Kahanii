#!/usr/bin/env bash
# Parallel download of the INCLUDE priority subset.
# Each file is launched in the background; we wait for all to finish.
set -e
CACHE="$(dirname "$0")/../.cache/include"
mkdir -p "$CACHE"

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

rm -f "$CACHE/.dl-*.log"

for f in "${FILES[@]}"; do
  (
    if [[ -s "$CACHE/$f" ]] && [[ $(stat -c%s "$CACHE/$f") -gt 1048576 ]]; then
      echo "  ✓ cached: $f"
      exit 0
    fi
    echo "  ↓ starting $f"
    curl -sSL "https://zenodo.org/records/4010759/files/$f" -o "$CACHE/$f" \
      > "$CACHE/.dl-${f}.log" 2>&1 \
      && echo "  ✓ done: $f" \
      || echo "  ✗ failed: $f (see $CACHE/.dl-${f}.log)"
  ) &
done

echo "All downloads started in the background. Waiting for completion..."
wait
echo "All downloads complete."
ls -la "$CACHE"/*.zip 2>/dev/null | awk '{print $5, $9}' | sort -n
