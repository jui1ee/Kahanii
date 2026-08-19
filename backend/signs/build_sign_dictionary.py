#!/usr/bin/env python3
"""
build_sign_dictionary.py

Downloads a curated subset of the INCLUDE dataset
(Zenodo record 4010759, CC-BY-4.0) and turns it into a lemma→clip
JSON dictionary that the Kahani backend serves at /static/signs/.

We deliberately download only storybook-relevant categories (Greetings,
Animals, Colours, Pronouns, Days_and_Time, Seasons, Home) instead of
the full ~50 GB, since:
  * Most children's stories don't need "Electronics" or "Means of
    Transportation" words.
  * One clean representative clip per lemma is enough — we never use
    multiple clips per word.
  * Smaller download = faster onboarding, easier to re-run.

Per-word pipeline:
  1. List all .mp4 files inside the category folder (the file name is
     e.g. "Hello.mp4" → lemma "hello").
  2. Pick ONE representative clip deterministically (first file,
     sorted) — the per-word picking of a "best" clip is a future
     improvement; see TODO at the bottom.
  3. Copy / symlink that clip into backend/static/signs/<lemma>.mp4.
  4. Add an entry to signs/dictionary.json.

Attribution
-----------
INCLUDE dataset, Sridhar et al. (ACM MM 2020).
Zenodo record 4010759, DOI 10.1145/3394171.3413528.
Licensed CC-BY-4.0. Credit surfaced to end-users via the app footer.

Run:
    python build_sign_dictionary.py
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import urllib.request
import zipfile
from functools import lru_cache
from pathlib import Path

# Resolve paths relative to this script so it works from anywhere.
HERE = Path(__file__).resolve().parent
BACKEND = HERE.parent
SIGNS_DIR = BACKEND / "signs"
STATIC_SIGNS_DIR = BACKEND / "static" / "signs"
DICT_PATH = SIGNS_DIR / "dictionary.json"
DOWNLOAD_CACHE = BACKEND / ".cache" / "include"

# Storybook-relevant categories — small subset (one zip per category).
# Total ~6.1 GB. Pick the smallest zip when an INCLUDE category is split.
# Home, Clothes, and other large categories are intentionally excluded —
# see signs/_download_small.sh for the rationale.
ZENODO_RECORD = "4010759"
CATEGORIES = [
    "Animals_2of2.zip",
    "Colours_1of2.zip",
    "Days_and_Time_3of3.zip",
    "Greetings_2of2.zip",
    "Pronouns_2of2.zip",
    "Seasons_1of1.zip",
]


@lru_cache(maxsize=1)
def _zenodo_sizes() -> dict[str, int]:
    """Fetch expected sizes from Zenodo for the files we care about."""
    try:
        import urllib.request, json
        d = json.loads(urllib.request.urlopen(
            f"https://zenodo.org/api/records/{ZENODO_RECORD}"
        ).read())
        return {f["key"]: f["size"] for f in d["files"]}
    except Exception as exc:  # noqa: BLE001
        print(f"  ⚠ could not fetch Zenodo sizes ({exc}); falling back to no-size mode")
        return {}


def download(url: str, dest: Path, expected_size: int | None = None) -> None:
    """Download url to dest with a streaming progress bar.

    Only treats the file as "cached" if it actually matches the expected
    size — otherwise partial downloads from a previous run get mistaken
    for complete files and break the extraction step downstream.
    """
    if dest.exists() and (expected_size is None or dest.stat().st_size >= expected_size):
        print(f"  ✓ cached: {dest.name}")
        return
    # Truncate any partial file from a previous run so curl starts fresh.
    if dest.exists():
        dest.unlink()
    dest.parent.mkdir(parents=True, exist_ok=True)
    print(f"  ↓ downloading {dest.name} from {url}")
    urllib.request.urlretrieve(url, dest, reporthook=_report_hook)


def _report_hook(block_num, block_size, total_size):
    if total_size > 0:
        pct = min(100, block_num * block_size * 100 / total_size)
        sys.stdout.write(f"\r    {pct:5.1f}%  ({block_num * block_size // 1024 // 1024} MB)")
        sys.stdout.flush()


def extract(zip_path: Path, out_dir: Path) -> None:
    """Extract zip_path into out_dir (idempotent — skips if already done)."""
    marker = out_dir / ".__include_extracted__"
    if marker.exists():
        print(f"  ✓ extracted: {zip_path.name}")
        return
    print(f"  + extracting {zip_path.name}")
    out_dir.mkdir(parents=True, exist_ok=True)
    try:
        with zipfile.ZipFile(zip_path) as zf:
            zf.extractall(out_dir)
    except zipfile.BadZipFile as exc:
        print(f"  ✗ not a valid zip yet ({exc}); skipping — file is likely partial")
        # Remove the empty dir we just made so we re-attempt next run.
        try:
            out_dir.rmdir()
        except OSError:
            pass
        return
    marker.write_text("ok")


def label_from_filename(filename: str) -> str | None:
    """Map an INCLUDE clip filename (e.g. 'Hello.mp4', 'good morning.MOV')
    to a normalized lemma string. Returns None if the file isn't a
    video or the filename doesn't look like a label.

    NOTE: Most INCLUDE clips have generic names like 'MVI_0017.MOV'.
    The actual sign label lives in the parent directory
    ('Seasons/61. Summer/MVI_4565.MOV' → lemma 'summer'). Callers
    that have path context should use `label_from_path` instead — this
    function is kept for the rare case where the filename itself is the
    label.

    INCLUDE distributes most clips as .MOV (QuickTime), not .mp4.
    We accept both, but stage the final clip with .mp4 extension in
    static/signs/ for browser playback.
    """
    return _extract_lemma_word(filename)


def _extract_lemma_word(name: str) -> str | None:
    """Pull the lemma-shaped word out of a string.

    INCLUDE labels live in directory names like '61. Summer' or
    'Ex. Monsoon'. We split on the first '. ' (digit-prefix style) or
    on the last '.' for file stems. Lowercases, trims.
    """
    if not name:
        return None
    text = name.strip()
    # Only strip a real file extension if one exists. Path().stem is
    # destructive — it splits on the LAST '.' which would also eat
    # "61. Summer" → "61". Detect a real extension: short, no
    # whitespace, starts with a letter (so "61" or " Summer" aren't
    # treated as extensions).
    suffix = Path(text).suffix
    if (
        suffix
        and len(suffix) <= 6
        and " " not in suffix
        and suffix.lstrip(".")[:1].isalpha()
    ):
        text = Path(text).stem
    # Strip a leading numeric prefix: "61. Summer" → "Summer"
    import re
    text = re.sub(r"^\s*\d+\.\s*", "", text)
    # Letter-prefix variants: "Ex. Monsoon" → "Monsoon"
    text = re.sub(r"^\s*[A-Za-z]+\.\s*", "", text)
    text = text.strip().lower().replace("_", " ")
    if not text or text in {"", " "}:
        return None
    return text


def label_from_path(path: Path) -> str | None:
    """Map an INCLUDE clip's full path to a lemma.

    Strategy:
    - Use the parent directory name if it has a real label shape
      (e.g. '61. Summer' → 'summer').
    - Fall back to the filename stem if the parent is 'Seasons', the
      category root, or otherwise generic.

    NOTE: INCLUDE distributes most clips as .MOV (QuickTime), not .mp4.
    """
    suffix = path.suffix.lower().lstrip(".")
    if suffix not in {"mp4", "mov"}:
        return None
    # Try parent directory first
    parent = path.parent.name
    parent_lemma = _extract_lemma_word(parent) if parent else None
    if parent_lemma and parent.lower() not in {"seasons", "animals", "colours",
                                                "greetings", "pronouns", "days_and_time",
                                                "home", "places", "people", "society",
                                                "clothes", "adjectives", "electronics",
                                                "jobs", "means_of_transportation",
                                                path.parent.parent.name.lower()}:
        return parent_lemma
    # Fallback to filename
    return _extract_lemma_word(path.name)


def main() -> int:
    DOWNLOAD_CACHE.mkdir(parents=True, exist_ok=True)
    SIGNS_DIR.mkdir(parents=True, exist_ok=True)
    STATIC_SIGNS_DIR.mkdir(parents=True, exist_ok=True)

    extract_root = DOWNLOAD_CACHE / "raw"

    # 1) Download and extract each category.
    sizes = _zenodo_sizes()
    for cat in CATEGORIES:
        url = f"https://zenodo.org/records/{ZENODO_RECORD}/files/{cat}"
        zip_path = DOWNLOAD_CACHE / cat
        download(url, zip_path, expected_size=sizes.get(cat))
        extract(zip_path, extract_root / cat.replace(".zip", ""))

    # 2) Walk the extracted tree and build lemma → clip map.
    # First-encounter wins; subsequent duplicates are ignored. This
    # gives a deterministic dictionary without needing per-clip scoring.
    lemma_to_src: dict[str, Path] = {}
    for cat_dir in sorted(extract_root.iterdir()):
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
            # Skip artifacts.
            if "word" in lemma or "test" in lemma:
                continue
            if lemma not in lemma_to_src:
                lemma_to_src[lemma] = mp4

    # 3) Copy each picked clip into static/signs/<safe_name>.mp4 and
    #    record the mapping. Use a sanitized filename so the URL works.
    dictionary: dict[str, str] = {}
    for lemma, src in sorted(lemma_to_src.items()):
        safe = "".join(ch if ch.isalnum() else "_" for ch in lemma)
        if not safe:
            safe = f"word_{abs(hash(lemma)) % 100000}"
        dest_name = f"{safe}.mp4"
        dest_path = STATIC_SIGNS_DIR / dest_name
        if not dest_path.exists():
            shutil.copy2(src, dest_path)
        dictionary[lemma] = dest_name

    # 4) Write the dictionary JSON.
    DICT_PATH.write_text(json.dumps(dictionary, indent=2, sort_keys=True), encoding="utf-8")

    print(f"\n✔ Wrote {len(dictionary)} entries to {DICT_PATH.relative_to(BACKEND)}")
    print(f"  Clips staged in {STATIC_SIGNS_DIR.relative_to(BACKEND)}/")

    # TODO(quality): instead of "first file wins", pick the cleanest clip
    # per word by inspecting a few frames (open eyes, sign in frame,
    # not blurry). This is a follow-up pass once the basic dictionary
    # is verified end-to-end.

    return 0


if __name__ == "__main__":
    sys.exit(main())