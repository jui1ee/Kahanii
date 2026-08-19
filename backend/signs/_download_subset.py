#!/usr/bin/env python3
"""Kick off INCLUDE subset downloads in the background."""
import os
import urllib.request
import sys
from pathlib import Path

CACHE = Path("/home/juilee/projects/Kahani/Bidirectional-Indian-Sign-Language-Translator/backend/.cache/include")
CACHE.mkdir(parents=True, exist_ok=True)

# Priority subset: ~9.8 GB. Storybook-relevant.
FILES = [
    "Greetings_1of2.zip",
    "Greetings_2of2.zip",
    "Animals_1of2.zip",
    "Animals_2of2.zip",
    "Colours_1of2.zip",
    "Colours_2of2.zip",
    "Pronouns_1of2.zip",
    "Pronouns_2of2.zip",
    "Seasons_1of1.zip",
    "Days_and_Time_1of3.zip",
    "Days_and_Time_2of3.zip",
    "Days_and_Time_3of3.zip",
]

def report(block_num, block_size, total_size):
    if total_size > 0:
        pct = min(100, block_num * block_size * 100 / total_size)
        mb = block_num * block_size / 1024 / 1024
        sys.stdout.write(f"\r    {pct:5.1f}%  {mb:7.1f} MB")
        sys.stdout.flush()

for f in FILES:
    dest = CACHE / f
    if dest.exists() and dest.stat().st_size > 1024 * 1024:
        print(f"  ✓ {f} cached ({dest.stat().st_size/1024/1024:.1f} MB)")
        continue
    url = f"https://zenodo.org/records/4010759/files/{f}"
    print(f"\n  ↓ {f}")
    try:
        urllib.request.urlretrieve(url, dest, reporthook=report)
        print(f"\r    ✓ {f} ({dest.stat().st_size/1024/1024:.1f} MB)")
    except Exception as e:
        print(f"\n    ✗ {f}: {e}")
        if dest.exists():
            dest.unlink()

print("\nDone.")