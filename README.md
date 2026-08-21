# Kahani — Story Time with Signs

A kid-friendly web app that turns a children's story into a synchronized
read-along experience for hearing-impaired children:

1. The story text scrolls by with the **current word highlighted**.
2. An **Indian Sign Language (ISL) sign video** plays for that word.
3. **Audio narration** (browser TTS) reads the story out loud.

When the dictionary has no video for a word, the UI falls back to
**letter-by-letter fingerspelling** so the word is still shown — the
fallback is load-bearing, not decorative. Fingerspelling covers both
**letters (A–Z)** and **digits (1–9)**.

---

## Features

* **Three-screen flow**: upload → preview → playback.
* **File upload** (`.txt`, `.pdf`, `.docx`) and **paste-text** input
  paths both end at the same tokenized preview.
* **Per-word video clip** for dictionary hits (real ISL hand signs from
  the INCLUDE dataset).
* **Per-letter fingerspelling** for anything not in the dictionary,
  with each letter or digit rendered as a real ISL alphabet / digit
  sign from the Hemg dataset.
* **Audio-led playback**: each spoken unit (a single letter for
  fingerspell words, a whole word for sign-video words) gets a fixed
  1.35 s of stage time, with audio driving the cadence and the video
  element updating to match.
* **Post-roll hold** (700 ms): after the last unit of a story, the
  final word/letter stays visible briefly before the playback screen
  resets, so short stories don't cut off mid-gesture.
* **Pause / Restart** controls and a **Slow (0.8×) / Normal (1.0×)**
  speed toggle for the TTS engine.
* **Kid-friendly UI**: pastel palette, rounded shapes, bunny mascot,
  large tap targets (≥56 px), Fredoka + Quicksand typography.
* **No auth, no cloud**: local-only prototype. Uploads are in-memory.

---

## Repo layout

    backend/         FastAPI service — upload, parse, tokenize, sign lookup
      main.py        HTTP endpoints
      payload.py     Pydantic request/response models
      signs/
        build_sign_dictionary.py          INCLUDE -> lemma -> clip
        build_fingerspelling_clips_from_hemg.py   Hemg -> alphabet/digit clips
        build_fingerspelling_clips.py     legacy pastel placeholder generator
        dictionary.json                   generated, 22 INCLUDE entries
        ATTRIBUTION.md                    license + dataset credits
      static/signs/  Served at /static/signs/
        *.mp4          INCLUDE clips (whole-word signs)
        _letters/*.mp4 Hemg alphabet clips (a-z)
        _digits/*.mp4  Hemg digit clips (1-9)
      .cache/        Downloads cache (gitignored)

    frontend/        React (Vite) UI
      src/App.jsx    Three screens + per-unit utterance scheduler
      src/App.css    Pastel kid-friendly styling, letter/digit chip colors
      vite.config.js Dev-server proxies /api and /static to backend

    docs-legacy/     Archived screenshots/PDFs from the original SIH
                     submission — kept for provenance, not used.

---

## Run it locally

Two terminals.

### 1. Backend (port 3002)

    cd backend
    python3 -m venv .venv
    .venv/bin/pip install -r requirements.txt
    .venv/bin/python -m spacy download en_core_web_sm
    .venv/bin/python signs/build_fingerspelling_clips_from_hemg.py
    # optional: .venv/bin/python signs/build_sign_dictionary.py
    .venv/bin/python main.py

`build_fingerspelling_clips_from_hemg.py` downloads a single ~292 MB
parquet shard of the Hemg/Indian_sign_language_dataset from
HuggingFace, picks one image per class, and writes 26 letter clips
plus 9 digit clips as 320×320 / 0.6 s h264 looped MP4s at
`static/signs/_letters/` and `static/signs/_digits/`.

`build_sign_dictionary.py` is optional. It downloads a smart subset
of the INCLUDE dataset (~6.1 GB across 6 zips) and writes a
`signs/dictionary.json` of `lemma → filename` plus the staged clip at
`static/signs/<lemma>.mp4`. Without this step, every word falls back
to fingerspelling.

### 2. Frontend (port 5173)

    cd frontend
    npm install
    npm run dev

Open <http://localhost:5173/>. The Vite dev server proxies `/api` and
`/static` to the backend, so no CORS or absolute-URL gymnastics needed.

For a production-style build:

    cd frontend && npm run build
    # static assets in frontend/dist — serve via any HTTP server,
    # pointing the app at the backend via VITE_API_BASE at build time.

---

## Datasets

### INCLUDE — whole-word sign videos

* **Name**: *INCLUDE: A Large Scale Dataset for Indian Sign Language
  Recognition*
* **Authors**: Advaith Sridhar, Rohith Gandhi Ganesan, Pratyush Kumar,
  Mitesh M. Khapra (IIT Madras / AI4Bharat)
* **Paper**: DOI [10.1145/3394171.3413528](https://doi.org/10.1145/3394171.3413528)
  (ACM Multimedia 2020)
* **Distribution**: [Zenodo record 4010759](https://zenodo.org/records/4010759)
* **License**: [CC-BY-4.0](https://creativecommons.org/licenses/by/4.0/)
* **Format**: short MP4 / MOV clips of isolated signs, organized by
  category (Greetings, Animals, Colours, Pronouns, Days and Time,
  Seasons, Home, …).
* **In Kahani**: used for **whole-word sign clips** that play when
  the dictionary has a lemma match. The current dictionary covers
  ~22 entries from a partial download of the priority subset; many
  children's-story words will still fall back to fingerspelling.
* **Credit**: surfaced in the app footer on every screen.

### Hemg/Indian_sign_language_dataset — alphabet + digit signs

* **Name**: *Indian_sign_language_dataset* (HuggingFace mirror)
* **Distribution**: [huggingface.co/datasets/Hemg/Indian_sign_language_dataset](https://huggingface.co/datasets/Hemg/Indian_sign_language_dataset)
* **Format**: a single ~292 MB Parquet shard (`train-00000-of-00001-*.parquet`)
  containing 42,745 still images. **Schema**: `image` (struct with
  `bytes` and `path`) and `label` (35-way `ClassLabel`).
* **Classes (35)**:
  * `0..8`  → digits `1`–`9` (9 classes)
  * `9..34` → letters `A`–`Z` (26 classes)
* **In Kahani**: used for the **fingerspelling fallback**. Each
  class contributes one representative image, encoded as a 320×320
  0.6 s h264 looped MP4. There is **no class for digit 0** in this
  dataset — if a story contains `0`, the corresponding clip 404s.
* **Build script**: `backend/signs/build_fingerspelling_clips_from_hemg.py`
  (uses `pyarrow` to read the parquet and `imageio[ffmpeg]` to encode
  the MP4).
* **Credit**: shown in the app footer alongside the INCLUDE credit.

---

## What's deliberately out of scope

* **ISL → text** (gesture recognition from webcam). The previous
  prototype had this; it was deleted in this rebuild because the
  product is a story-playback experience for hearing-impaired
  children, not a signing tool.
* **Multilingual input**. The previous googletrans dependency is
  dropped. A `# TODO: reintroduce translation later if needed` marker
  is left in `backend/main.py`.
* **User accounts, cloud storage, deployment config**.

---

## Status

Prototype. End-to-end playable with `paste-text` input. Real-world
upload of `.pdf` / `.docx` / `.txt` works on the backend; the React
upload form supports all three.

Known limitations of this pass:

* **Dictionary size**: the curated INCLUDE subset covers ~22 words
  after a partial download (Zenodo transfers frequently drop mid-stream,
  see the build script for the resumable download + keepalive pattern).
  Children's stories will mostly hit the fingerspelling fallback —
  that's by design, see the Features section above.
* **Hemg has no digit 0**: stories containing `0` will 404 on that
  clip. The fallback path keeps the word visible but the digit-0
  hand sign is missing.
* **Sync mechanism**: per-unit utterances with a fixed `setTimeout`
  drive the cadence. Works in Chrome / Edge / Firefox. Safari's TTS
  engine has weaker `onstart` / `onend` guarantees; on Safari the
  letter-by-letter fingerspelling may collapse to the whole word
  being spoken at once.
* **First-frame latency on big clips**: long INCLUDE clips
  (~11 MB, 1920×1080) take ~100–500 ms to decode the first frame,
  so the user may see only the first ~700–1100 ms of a 2.16 s clip.
  Acceptable for kid-friendly read-along; polish if needed later.
