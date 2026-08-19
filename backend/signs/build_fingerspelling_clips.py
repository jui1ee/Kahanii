#!/usr/bin/env python3
"""
build_fingerspelling_clips.py

Generates letter-by-letter fingerspelling videos for the 26 English
letters A–Z. These clips are used as a fallback when a story word has
no entry in signs/dictionary.json — the frontend plays one letter clip
after another instead of a single-word sign.

We don't include any real ISL fingerspelling footage in this pass.
Instead we generate simple letter-render clips programmatically using
Pillow + an audio-less MP4 writer, so the fallback is functional out
of the box. Replacing these with real ISL alphabet clips is a
follow-up TODO; the loader is plug-compatible.

Output: backend/static/signs/_letters/a.mp4 ... z.mp4
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
BACKEND = HERE.parent
LETTERS_DIR = BACKEND / "static" / "signs" / "_letters"

# Letters we render. Keep it minimal: a-z.
LETTERS = [chr(c) for c in range(ord("a"), ord("z") + 1)]


def render_letter_clip(letter: str, dest: Path, *, size: int = 320, duration_ms: int = 600, fps: int = 20) -> None:
    """
    Render a tiny silent MP4 showing a big pastel-colored letter on
    a rounded background. This is a placeholder; replace with real
    ISL fingerspelling footage when you have it.
    """
    if dest.exists():
        return

    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        print("Pillow is required for the placeholder letter clips: pip install Pillow", file=sys.stderr)
        return

    LETTER_DIR.mkdir(parents=True, exist_ok=True) if False else None
    dest.parent.mkdir(parents=True, exist_ok=True)

    frames = []
    n_frames = max(1, duration_ms * fps // 1000)
    # Pastel background — rotate hue per letter so kids can tell them apart.
    pastel_palette = [
        (255, 224, 224),  # pink
        (224, 240, 255),  # sky
        (224, 255, 224),  # mint
        (255, 248, 224),  # yellow
        (240, 224, 255),  # lavender
        (255, 232, 224),  # peach
    ]
    bg = pastel_palette[(ord(letter) - ord("a")) % len(pastel_palette)]
    fg = (60, 60, 80)

    for i in range(n_frames):
        img = Image.new("RGB", (size, size), bg)
        draw = ImageDraw.Draw(img)
        # Rounded rectangle frame
        draw.rounded_rectangle([(8, 8), (size - 8, size - 8)], radius=24, outline=(120, 120, 140), width=4)
        # Big letter
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", size // 2)
        except OSError:
            font = ImageFont.load_default()
        bbox = draw.textbbox((0, 0), letter.upper(), font=font)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        draw.text(((size - tw) // 2 - bbox[0], (size - th) // 2 - bbox[1]), letter.upper(), fill=fg, font=font)
        frames.append(img)

    # Try imageio-ffmpeg first (no system ffmpeg required).
    try:
        import imageio.v2 as imageio

        writer = imageio.get_writer(dest, fps=fps, codec="libx264", quality=6)
        for f in frames:
            writer.append_data(f)
        writer.close()
        return
    except Exception as exc:  # noqa: BLE001
        print(f"  (imageio failed: {exc}; trying ffmpeg fallback)")

    # Fallback: invoke ffmpeg via a pipe of raw frames.
    try:
        import subprocess
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            for i, f in enumerate(frames):
                f.save(os.path.join(tmp, f"f_{i:04d}.png"))
            cmd = [
                "ffmpeg", "-y",
                "-framerate", str(fps),
                "-i", os.path.join(tmp, "f_%04d.png"),
                "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "28",
                str(dest),
            ]
            subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception as exc:  # noqa: BLE001
        print(f"  ✗ failed to render {dest}: {exc}")
        print("    Install imageio[ffmpeg] or system ffmpeg, then re-run this script.")


def main() -> int:
    LETTERS_DIR.mkdir(parents=True, exist_ok=True)

    if not _has_imageio() and not _has_ffmpeg():
        print("Need either imageio[ffmpeg] or system ffmpeg. pip install imageio[ffmpeg]")
        return 1

    for letter in LETTERS:
        dest = LETTERS_DIR / f"{letter}.mp4"
        render_letter_clip(letter, dest)
        print(f"  ✓ {letter}.mp4" if dest.exists() else f"  ✗ {letter}.mp4 (see above)")
    return 0


def _has_imageio() -> bool:
    try:
        import imageio  # noqa: F401
        return True
    except ImportError:
        return False


def _has_ffmpeg() -> bool:
    from shutil import which
    return which("ffmpeg") is not None


if __name__ == "__main__":
    sys.exit(main())