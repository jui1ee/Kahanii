#!/usr/bin/env python3
"""
build_sign_dictionary_extend.py

Extend the INCLUDE sign dictionary by downloading the *other half* of
each split category that build_sign_dictionary.py already touched:

  - Animals_2of2.zip  -> also Animals_1of2.zip   (more animals)
  - Greetings_2of2.zip -> also Greetings_1of2.zip (more greetings)
  - Pronouns_2of2.zip  -> also Pronouns_1of2.zip  (more pronouns)
  - Days_and_Time_3of3.zip -> also Days_and_Time_1of3 + 2of3.zip

Plus a retry for Colours_1of2.zip which previously failed at 67 MB /
1.2 GB after 10 retries.

This script is independent of build_sign_dictionary.py. It uses the
same label-extraction logic and dictionary format. It MERGES with the
existing dictionary.json so we don't lose the 22 entries from the
initial smart subset.

Download strategy
-----------------
Uses the system curl with -C - (resume) --retry 10 --retry-delay 5.
The previous Python urllib.urlretrieve approach failed repeatedly
because urlretrieve treats dropped transfers as fatal errors with no
retry. curl -C - is the proven survivor pattern that the previous
download saga converged on.

Resumable / idempotent
----------------------
The script is safe to re-run. If a zip is already fully downloaded
(matches Zenodo expected size), it skips. If a zip is partial, it
resumes. Extraction is also idempotent (marker file in extract dir).

Output
------
  - .cache/include/<zip>           (continued download)
  - .cache/include/raw/<extract>/  (extracted tree)
  - static/signs/<safe>.mp4        (curated clips)
  - signs/dictionary.json          (merged dictionary)

Attribution
-----------
INCLUDE dataset, Sridhar et al. (ACM MM 2020).
Zenodo record 4010759, DOI 10.1145/3394171.3413528.
Licensed CC-BY-4.0.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import urllib.request
import zipfile
from pathlib import Path

# Re-use the helpers already in build_sign_dictionary.py so the
# label-extraction logic stays in one place.
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from build_sign_dictionary import (  # noqa: E402
    BACKEND, SIGNS_DIR, STATIC_SIGNS_DIR, DICT_PATH, DOWNLOAD_CACHE,
    ZENODO_RECORD, _extract_lemma_word, label_from_path,
)

# Categories to add on top of the original 6. Each is one zip from
# the *other* half of a split category.
EXTEND_CATEGORIES = [
    "Pronouns_1of2.zip",
    "Animals_1of2.zip",
    "Greetings_1of2.zip",
    "Days_and_Time_1of3.zip",
    "Days_and_Time_2of3.zip",
    "Colours_1of2.zip",
]


def _zenodo_sizes() -> dict[str, int]:
    """Fetch expected sizes from Zenodo. Re-uses the same logic as
    build_sign_dictionary._zenodo_sizes but is duplicated here so this
    script is self-contained."""
    try:
        d = json.loads(urllib.request.urlopen(
            f"https://zenodo.org/api/records/{ZENODO_RECORD}"
        ).read())
        return {f["key"]: f["size"] for f in d["files"]}
    except Exception as exc:  # noqa: BLE001
        print(f"  ⚠ could not fetch Zenodo sizes ({exc}); size check disabled")
        return {}


def curl_download(url: str, dest: Path, expected_size: int | None) -> bool:
    """Download url to dest with curl -C - (resume) --retry 10.

    Returns True on success (file matches expected size or no expected
    size was available), False on hard failure (curl exit code != 0
    AND file still short).
    """
    if dest.exists():
        actual = dest.stat().st_size
        if expected_size is None or actual >= expected_size:
            print(f"  ✓ cached: {dest.name} ({actual // 1024 // 1024} MB)")
            return True
        else:
            print(f"  ↻ resume: {dest.name} (have {actual // 1024 // 1024} MB, "
                  f"need {expected_size // 1024 // 1024} MB)")
    else:
        print(f"  ↓ start: {dest.name} (target ~{expected_size // 1024 // 1024} MB)"
              if expected_size else f"  ↓ start: {dest.name} (size unknown)")

    dest.parent.mkdir(parents=True, exist_ok=True)
    # -sSL silent + follow redirects + show errors
    # -C - resume from current size
    # --retry 10 with --retry-delay 5
    # --connect-timeout 30 --max-time 7200 (2h per attempt)
    rc = subprocess.call([
        "curl", "-sSL",
        "-C", "-",
        "--retry", "10",
        "--retry-delay", "5",
        "--retry-all-errors",
        "--connect-timeout", "30",
        "--max-time", "7200",
        "-o", str(dest),
        url,
    ])
    actual = dest.stat().st_size if dest.exists() else 0
    if expected_size is not None and actual < expected_size:
        print(f"  ✗ curl exited {rc}; have {actual} bytes, need {expected_size}")
        return False
    print(f"  ✓ done: {dest.name} ({actual // 1024 // 1024} MB)")
    return True


def extract(zip_path: Path, out_dir: Path) -> bool:
    """Extract zip_path into out_dir. Returns True if extracted (or
    already extracted), False on bad zip / partial file."""
    marker = out_dir / ".__include_extracted__"
    if marker.exists():
        print(f"  ✓ extracted: {zip_path.name}")
        return True
    out_dir.mkdir(parents=True, exist_ok=True)
    try:
        with zipfile.ZipFile(zip_path) as zf:
            zf.extractall(out_dir)
    except zipfile.BadZipFile as exc:
        print(f"  ✗ bad zip ({exc}); skipping — file is likely partial")
        try:
            # Clean up any partial extraction
            for child in out_dir.iterdir():
                if child.name == marker.name:
                    continue
                if child.is_dir():
                    shutil.rmtree(child, ignore_errors=True)
                else:
                    child.unlink(missing_ok=True)
        except OSError:
            pass
        return False
    marker.write_text("ok")
    print(f"  + extracted {zip_path.name}")
    return True


def main(argv: list[str] | None = None) -> int:
    """Run all extend categories, or just the one passed via --zip <name>.

    Usage:
      build_sign_dictionary_extend.py                # all 6 categories
      build_sign_dictionary_extend.py --zip Pronouns_1of2.zip   # one only
    """
    import argparse
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--zip", help="Download just this one zip and stop. "
                                  "Useful for category-by-category pacing.")
    args = ap.parse_args(argv)

    DOWNLOAD_CACHE.mkdir(parents=True, exist_ok=True)
    SIGNS_DIR.mkdir(parents=True, exist_ok=True)
    STATIC_SIGNS_DIR.mkdir(parents=True, exist_ok=True)
    extract_root = DOWNLOAD_CACHE / "raw"

    categories = [args.zip] if args.zip else EXTEND_CATEGORIES
    print(f"\nExtending dictionary with {len(categories)} category(s): {categories}")

    sizes = _zenodo_sizes()

    # Phase 1: download + extract the new zips. Track which zips
    # actually completed (some may still be partial after retries).
    completed_zips: list[str] = []
    for cat in EXTEND_CATEGORIES:
        url = f"https://zenodo.org/records/{ZENODO_RECORD}/files/{cat}"
        zip_path = DOWNLOAD_CACHE / cat
        ok = curl_download(url, zip_path, expected_size=sizes.get(cat))
        if ok and extract(zip_path, extract_root / cat.replace(".zip", "")):
            completed_zips.append(cat)
        else:
            print(f"  ⚠ {cat} incomplete after retries; will skip in dict")

    if not completed_zips:
        print("\n✗ No new zips finished; dictionary unchanged.")
        return 1

    # Phase 2: walk the newly-extracted trees and collect lemma -> clip.
    # Same first-encounter-wins strategy as build_sign_dictionary.py.
    new_lemma_to_src: dict[str, Path] = {}
    for cat in completed_zips:
        cat_dir = extract_root / cat.replace(".zip", "")
        if not cat_dir.is_dir():
            continue
        for mp4 in sorted(cat_dir.rglob("*")):
            if not mp4.is_file():
                continue
            if not mp4.name.lower().endswith((".mp4", ".mov")):
                continue
            lemma = label_from_path(mp4)
            if lemma is None:
                continue
            if "word" in lemma or "test" in lemma:
                continue
            if lemma not in new_lemma_to_src:
                new_lemma_to_src[lemma] = mp4

    # Phase 3: merge with existing dictionary. Existing entries win
    # (their clip path is already established); new entries fill in
    # the gaps.
    existing: dict[str, str] = {}
    if DICT_PATH.exists():
        existing = json.loads(DICT_PATH.read_text(encoding="utf-8"))

    merged: dict[str, str] = dict(existing)
    added: list[str] = []
    for lemma, src in sorted(new_lemma_to_src.items()):
        if lemma in merged:
            continue
        safe = "".join(ch if ch.isalnum() else "_" for ch in lemma)
        if not safe:
            safe = f"word_{abs(hash(lemma)) % 100000}"
        dest_name = f"{safe}.mp4"
        dest_path = STATIC_SIGNS_DIR / dest_name
        if not dest_path.exists():
            shutil.copy2(src, dest_path)
        merged[lemma] = dest_name
        added.append(lemma)

    DICT_PATH.write_text(
        json.dumps(merged, indent=2, sort_keys=True), encoding="utf-8"
    )

    print(f"\n✔ Dictionary now has {len(merged)} entries "
          f"({len(added)} newly added from {len(completed_zips)} zips)")
    if added:
        print(f"  New lemmas: {', '.join(added[:30])}"
              + ("..." if len(added) > 30 else ""))
    print(f"  Clips staged in {STATIC_SIGNS_DIR.relative_to(BACKEND)}/")
    return 0


if __name__ == "__main__":
    sys.exit(main())