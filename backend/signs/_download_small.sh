#!/usr/bin/env bash
# SMALL subset of INCLUDE — one zip per category, picked by size.
# Total expected: ~5-7 GB.
# Categories: Greetings, Animals, Colours, Pronouns, Days_and_Time,
# Seasons, Clothes, Home (more storybook overlap than the prior attempt).
set -e
CACHE="$(dirname "$0")/../.cache/include"
mkdir -p "$CACHE"

# Get sizes from the Zenodo record and pick the smallest zip per category.
python3 - <<EOF > "$CACHE/.smalls.txt"
import json, urllib.request, re
from collections import defaultdict
d = json.loads(urllib.request.urlopen("https://zenodo.org/api/records/4010759").read())
by_cat = defaultdict(list)
for f in d["files"]:
    name = f["key"]
    if not name.endswith(".zip"):
        continue
    # Strip trailing "_XofY.zip" to get category base
    m = re.match(r"^(.+?)_\d+of\d+\.zip$", name)
    if m:
        cat = m.group(1)
    else:
        cat = name.replace(".zip", "")
    by_cat[cat].append((f["size"], name))

# Pick the smallest zip per category, but EXCLUDE categories we don't want.
EXCLUDE = {"Adjectives", "Places", "Society", "Jobs", "Means_of_Transportation",
           "Electronics", "People", "Clothes", "Home"}
for cat, files in sorted(by_cat.items()):
    if cat in EXCLUDE:
        continue
    files.sort()
    chosen_size, chosen_name = files[0]
    print(f"{chosen_name} {chosen_size}")
EOF

echo "Files to download (smallest per category):"
cat "$CACHE/.smalls.txt"
echo ""

rm -f "$CACHE/.dl-*.log"

# Launch each download in parallel, with retry.
while read -r fname expected; do
  (
    attempts=0
    while (( attempts < 4 )); do
      attempts=$((attempts + 1))
      if [[ -s "$CACHE/$fname" ]] && [[ $(stat -c%s "$CACHE/$fname" 2>/dev/null || echo 0) -ge "$expected" ]]; then
        echo "  ✓ cached: $fname"
        exit 0
      fi
      echo "  ↓ attempt $attempts: $fname"
      if curl -sSL -C - --max-time 1800 "https://zenodo.org/records/4010759/files/$fname" \
            -o "$CACHE/$fname" > "$CACHE/.dl-${fname}.log" 2>&1; then
        actual=$(stat -c%s "$CACHE/$fname" 2>/dev/null || echo 0)
        if [[ "$actual" -ge "$expected" ]]; then
          echo "  ✓ done: $fname"
          exit 0
        fi
      fi
      echo "  ↻ retry $fname"
      sleep 5
    done
    echo "  ✗ gave up: $fname"
  ) &
done < "$CACHE/.smalls.txt"

echo "All downloads started in parallel. Waiting for completion..."
wait
echo "All downloads complete."

# Verify and report.
echo "Final status:"
printf "  %-8s  %s\n" SIZE NAME
while read -r fname expected; do
  actual=$(stat -c%s "$CACHE/$fname" 2>/dev/null || echo 0)
  if [[ "$actual" -ge "$expected" ]]; then
    printf "  ✓ %6.1f MB  %s\n" "$(echo "scale=1; $actual/1024/1024" | bc)" "$fname"
  else
    printf "  ✗ %6.1f MB  %s (expected %s)\n" \
      "$(echo "scale=1; $actual/1024/1024" | bc)" "$fname" "$expected"
  fi
done < "$CACHE/.smalls.txt"
