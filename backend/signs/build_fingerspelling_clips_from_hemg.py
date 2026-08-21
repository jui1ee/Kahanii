#!/usr/bin/env python3
"""
build_fingerspelling_clips_from_hemg.py

Builds 26 letter clips (A-Z) and 9 digit clips (1-9) for the
fingerspelling fallback, using real Indian Sign Language images
from the Hemg/Indian_sign_language_dataset on Hugging Face.

The dataset is a single ~292 MB parquet shard at:
  data/train-00000-of-00001-a1731e778755d263.parquet

Schema (per the dataset card):
  image: { bytes, path }
  label: ClassLabel with 35 names:
    0..8  -> '1'..'9'    (digits)
    9..34 -> 'A'..'Z'    (letters)

This script:
  * Reads the parquet shard with pyarrow (already in requirements).
  * Picks ONE representative image per class (first encountered — same
    "first-encounter wins" heuristic the INCLUDE sign dictionary uses).
  * Encodes each image as a looped single-frame MP4 at 320x320 to match
    the dimensions / codec of the existing placeholder clips so the
    frontend code does not change.
  * Writes:
      static/signs/_letters/a.mp4 ... z.mp4  (overwrites placeholders)
      static/signs/_digits/1.mp4  ... 9.mp4   (new folder)

Inputs:
  --parquet  path to the downloaded shard
             (default: ../.cache/hemg_alphabet.parquet)

Outputs:
  static/signs/_letters/<a-z>.mp4
  static/signs/_digits/<1-9>.mp4
"""
from __future__ import annotations

import argparse
import io
import sys
from pathlib import Path

import pyarrow.parquet as pq
from PIL import Image

HERE = Path(__file__).resolve().parent
BACKEND = HERE.parent
DEFAULT_PARQUET = BACKEND / ".cache" / "hemg_alphabet.parquet"

LETTERS_DIR = BACKEND / "static" / "signs" / "_letters"
DIGITS_DIR = BACKEND / "static" / "signs" / "_digits"

# Same dimensions/duration as build_fingerspelling_clips.py so the
# frontend's <video> tag doesn't have to behave differently.
SIZE = 320
DURATION_MS = 600
FPS = 20


def _class_name(label_idx: int) -> str:
    """
    Map the dataset's ClassLabel index to a human-readable name.

    Schema confirmed from
    https://huggingface.co/datasets/Hemg/Indian_sign_language_dataset/raw/main/README.md
        0..8   -> '1'..'9'
        9..34  -> 'A'..'Z'
    """
    if 0 <= label_idx <= 8:
        return str(label_idx + 1)        # 0 -> '1', ..., 8 -> '9'
    if 9 <= label_idx <= 34:
        return chr(ord("A") + label_idx - 9)  # 9 -> 'A', ..., 34 -> 'Z'
    raise ValueError(f"Unexpected class label {label_idx!r}")


def _clip_target(name: str) -> tuple[Path, str]:
    """
    Decide where to write the clip and what its base folder is.
    Returns (dest_path, subfolder).
    """
    if name.isalpha():
        sub = "letters"
        dest = LETTERS_DIR / f"{name.lower()}.mp4"
    elif name.isdigit():
        sub = "digits"
        dest = DIGITS_DIR / f"{name}.mp4"
    else:
        raise ValueError(f"Unexpected class name {name!r}")
    return dest, sub


def _square_pad(img: Image.Image, size: int) -> Image.Image:
    """
    Letterbox the image into a square of (size, size) with a soft
    pastel background, so we never crop hand gestures.
    """
    if img.mode != "RGB":
        img = img.convert("RGB")
    # pastel off-white
    bg = (252, 248, 240)
    canvas = Image.new("RGB", (size, size), bg)
    # fit image into (size - 32) box, preserve aspect
    box = size - 32
    w, h = img.size
    scale = min(box / w, box / h)
    new_w = max(1, int(round(w * scale)))
    new_h = max(1, int(round(h * scale)))
    img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
    x = (size - new_w) // 2
    y = (size - new_h) // 2
    canvas.paste(img, (x, y))
    return canvas


def _encode_mp4(frame: Image.Image, dest: Path) -> None:
    """
    Encode a single-frame looped MP4. Uses the same imageio-ffmpeg
    backend as build_fingerspelling_clips.py.
    """
    n_frames = max(1, DURATION_MS * FPS // 1000)
    try:
        import imageio.v2 as imageio
    except ImportError as exc:
        raise SystemExit(
            "imageio is required. pip install imageio[ffmpeg]"
        ) from exc

    dest.parent.mkdir(parents=True, exist_ok=True)
    # imageio.append_data needs ndarray, not PIL.Image (newer imageio).
    import numpy as np
    arr = np.asarray(frame)
    writer = imageio.get_writer(dest, fps=FPS, codec="libx264", quality=6)
    try:
        for _ in range(n_frames):
            writer.append_data(arr)
    finally:
        writer.close()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--parquet",
        default=str(DEFAULT_PARQUET),
        help=f"Path to the Hemg parquet shard (default: {DEFAULT_PARQUET})",
    )
    args = ap.parse_args()

    parquet_path = Path(args.parquet)
    if not parquet_path.exists():
        print(f"✗ Parquet not found at {parquet_path}", file=sys.stderr)
        print("  Download with backend/.cache/_download_alphabet.sh", file=sys.stderr)
        return 1

    print(f"Reading {parquet_path} ...")
    table = pq.read_table(parquet_path)
    cols = table.column_names
    if "image" not in cols or "label" not in cols:
        print(f"✗ Unexpected schema. Columns: {cols}", file=sys.stderr)
        return 1

    images_col = table.column("image")
    labels_col = table.column("label")

    # One representative per class.
    seen: dict[str, Image.Image] = {}
    n_rows = table.num_rows
    print(f"Scanning {n_rows} rows for one image per class ...")

    for i in range(n_rows):
        lbl_idx = labels_col[i].as_py()
        if lbl_idx is None:
            continue
        try:
            name = _class_name(int(lbl_idx))
        except ValueError:
            continue
        if name in seen:
            continue

        img_struct = images_col[i].as_py()
        # HF image feature: {"bytes": ..., "path": ...}
        img_bytes = img_struct.get("bytes") if isinstance(img_struct, dict) else None
        if not img_bytes:
            continue
        try:
            img = Image.open(io.BytesIO(img_bytes))
        except Exception as exc:  # noqa: BLE001
            print(f"  ! skip row {i} ({name}): {exc}", file=sys.stderr)
            continue

        seen[name] = img
        if len(seen) == 35:    # 9 digits + 26 letters
            break

    all_classes = set("123456789") | set("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
    missing = sorted(all_classes - set(seen.keys()))
    if missing:
        print(f"✗ Missing classes: {missing}", file=sys.stderr)
        return 1

    print(f"Got one image per class. Encoding MP4s at {SIZE}x{SIZE} ...")

    # Letters first (alphabetical), then digits (numerical).
    for name in sorted(seen.keys(), key=lambda n: (n.isdigit(), n)):
        dest, sub = _clip_target(name)
        frame = _square_pad(seen[name], SIZE)
        _encode_mp4(frame, dest)
        ok = "✓" if dest.exists() else "✗"
        size_kb = dest.stat().st_size // 1024 if dest.exists() else 0
        print(f"  {ok} {sub}/{dest.name} ({size_kb} KB)")

    print("Done.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
