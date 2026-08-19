#!/usr/bin/env python3
"""
Watch the .cache/include/ directory and build the sign dictionary every
time a new INCLUDE zip finishes downloading. Triggers as soon as the
first zip is complete, then again each time another finishes.

This way the app starts using real sign videos the moment the smallest
zip lands — no need to wait for all six.

Run in the background while downloads are running:
    python3 signs/_auto_build_dict.py
    # Ctrl-C to stop
"""
import os
import sys
import time
import zipfile
import shutil
import json
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
BACKEND = HERE.parent
CACHE = BACKEND / ".cache" / "include"
RAW = BACKEND / ".cache" / "raw"
SIGNS_DIR = BACKEND / "signs"
STATIC_SIGNS = BACKEND / "static" / "signs"
DICT_PATH = SIGNS_DIR / "dictionary.json"

# Build script does the real work.
BUILD_SCRIPT = BACKEND / "signs" / "build_sign_dictionary.py"


def expected_sizes():
    """Pull expected sizes from Zenodo so we know when each zip is complete."""
    import urllib.request
    d = json.loads(urllib.request.urlopen("https://zenodo.org/api/records/4010759").read())
    return {f["key"]: f["size"] for f in d["files"]}


def is_complete(path: Path, expected_size: int) -> bool:
    return path.exists() and path.stat().st_size >= expected_size


def main():
    if not BUILD_SCRIPT.exists():
        print(f"missing build script: {BUILD_SCRIPT}")
        sys.exit(1)

    print("Watching for complete INCLUDE zips...")
    seen_complete: set[str] = set()
    last_check_log = 0
    while True:
        try:
            sizes = expected_sizes()
        except Exception:
            sizes = {}

        completed_now = []
        for fname, expected in sizes.items():
            p = CACHE / fname
            if is_complete(p, expected) and fname not in seen_complete:
                # Sanity check: must be a valid zip
                try:
                    with zipfile.ZipFile(p) as zf:
                        bad = zf.testzip()
                        if bad is None:
                            completed_now.append(fname)
                            seen_complete.add(fname)
                except (zipfile.BadZipFile, Exception):
                    pass

        for fname in completed_now:
            print(f"\n[{time.strftime('%H:%M:%S')}] ✓ {fname} complete — invoking build_sign_dictionary.py")
            try:
                # The build script handles extract + clip-pick + dict write
                # idempotently across whatever is in CACHE.
                subprocess.run([sys.executable, str(BUILD_SCRIPT)], check=True)
                print(f"  ↳ dictionary built. {len(json.loads(DICT_PATH.read_text()))} entries.")
            except subprocess.CalledProcessError as e:
                print(f"  ↳ build failed: {e}")

        # Heartbeat every 30s so we know we're alive.
        now = time.time()
        if now - last_check_log >= 30:
            cached_gb = sum(p.stat().st_size for p in CACHE.glob("*.zip") if p.exists()) / 1024**3
            n_done = len(seen_complete)
            print(f"[{time.strftime('%H:%M:%S')}] watching... {n_done} complete, {cached_gb:.2f} GB cached")
            last_check_log = now

        time.sleep(10)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("stopped")