# Kahani — Product

A kid-friendly web app that turns any children's story into a synchronized read-along experience for hearing-impaired children.

## The promise

A parent or teacher uploads a story (`.txt` / `.pdf` / `.docx`) — or pastes text. The child watches a friendly bunny mascot play the story back with three things happening in lockstep:

1. **The story text scrolls word by word**, with the current word highlighted in a pastel gradient.
2. **An Indian Sign Language (ISL) video** plays for that word — a real human signing.
3. **Audio narration** reads the story aloud via browser text-to-speech.

When a word has no sign video, the UI falls back to **letter-by-letter fingerspelling** (also with a real ISL hand sign for each letter or digit). The fallback is the load-bearing feature, not a nice-to-have.

## Who it's for

* **Primary**: hearing-impaired children (ages 4–10) learning to read with sign support.
* **Secondary**: parents / teachers preparing a story session.
* **Tertiary**: deaf schools that need a quick way to convert any printed story into signed narration.

## Core features

### Upload & parse
* Drag-and-drop or click-to-pick file upload
* Paste text as an alternative input
* Supports `.txt`, `.pdf`, `.docx`
* 5 MB upload limit (plenty for any children's story)
* Server-side text extraction with `pypdf` (PDF) and `python-docx` (DOCX)
* All parsing happens in-memory, nothing is persisted

### Read-along playback
* Three screens: upload → preview → play
* **Word-by-word text highlight** — past words fade to 55% opacity, active word is gradient-scaled with a drop shadow
* **Per-unit audio** — each spoken unit (a single letter / digit for fingerspell words, the whole word for sign-video words) gets its own `SpeechSynthesisUtterance`, scheduled back-to-back with a fixed `setTimeout` between them
* **Audio-led cadence** — every unit gets exactly `UNIT_DURATION_MS` (1.35 s) of stage time. Audio and video events do **not** gate the advance; only the timer does. This avoids stuck-state bugs from unreliable `onend` / `onended` events.
* **Post-roll hold** (700 ms) — after the last unit of a story, the final word / letter stays visible briefly before the playback screen resets. Short stories don't cut off mid-gesture.
* **Pause / Restart** controls, plus a **Slow (0.8×) / Normal (1.0×)** speed toggle for the TTS engine.

### Sign video dictionary
* 22 real **INCLUDE** sign video clips serving right now (animal, mouse, horse, we, they, you, good evening, good night, thank you, pleased, morning, afternoon, evening, night, time, second, summer, spring, winter, fall, monsoon, season)
* CC-BY-4.0 licensed, credited in the app footer
* Designed to grow — dropping more INCLUDE data into `static/signs/` and rebuilding `signs/dictionary.json` instantly adds words

### Fingerspelling fallback
* Letter-by-letter playback for any word not in the dictionary
* Active letter / digit highlighted as a chip below the video
* **Real ISL hand signs** for every letter (`a`–`z`) and digit (`1`–`9`), sourced from the **Hemg/Indian_sign_language_dataset** on HuggingFace (35 classes total — 9 digits + 26 letters). Each is a 320×320 / 0.6 s h264 single-frame looped MP4.
* **Letter chips**: pastel yellow. **Digit chips**: pastel cyan (visually distinct so kids can tell the two apart at a glance).
* Caveat: the Hemg dataset has **no class for digit 0**. Stories containing `0` will 404 on that clip; the rest of the word still works.

### Kid-friendly UX
* **Pastel palette** — pink, sky, mint, yellow, lavender. Never harsh or saturated.
* **Rounded everything** — 12–32 px border radius, no sharp corners.
* **Bunny mascot** — happy on upload, thinking in empty states.
* **Big tap targets** — ≥56 px, works on tablets.
* **One clear action per screen** — upload → preview → play.
* **Large readable story text** — 28 px, generous line spacing.
* **No dark theme**.
* **Disabled state** on action buttons until input is present.
* **Friendly error messages** with visual cues.

### Accessibility
* Speech synthesis uses slightly higher pitch (1.05) so narration feels less robotic.
* All controls reachable via keyboard.
* ARIA labels on icon-only buttons.
* `<noscript>` fallback would be trivial to add (full SPA blocks without JS).

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│  Browser (React + Vite)                                         │
│  ├─ UploadScreen → PreviewScreen → PlaybackScreen               │
│  └─ PlaybackScreen:                                              │
│     Per-unit utterance scheduler                                 │
│     spokenUnits = [{tokenIdx, letterIdx, surface}, ...]          │
│       ├─ for sign-video: surface = whole word                   │
│       └─ for fingerspell: surface = "T" / "H" / "E" / ...        │
│                                                                 │
│     speakUnit(idx):                                             │
│       ├─ speak(unit.surface)                                    │
│       ├─ onstart -> setActiveIdx + setActiveLetter               │
│       └─ setTimeout(UNIT_DURATION_MS) -> speakUnit(idx+1)        │
│                                                                 │
│     [currentVideoSrc] effect: videoRef.current.src = ...        │
│                                .load() + .play()                │
│                                                                 │
│     [letterSequence, activeLetter] effect: per-letter clip       │
└─────────────────────────────────────────────────────────────────┘
                            │ HTTP
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│  FastAPI (Python 3.12)                            port :3002    │
│  ├─ POST /api/upload   (multipart file → token JSON)           │
│  ├─ POST /api/tokenize  (raw text → token JSON)                │
│  ├─ GET  /api/signs/{lemma}                                     │
│  ├─ GET  /static/signs/...                                      │
│  └─ spaCy en_core_web_sm: tokenize + lemmatize ONLY             │
│       (parser, tagger, NER disabled — pure function)           │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│  Data                                                            │
│  ├─ signs/dictionary.json (22 lemma → video-filename entries)   │
│  ├─ static/signs/*.mp4 (curated INCLUDE clips)                  │
│  ├─ static/signs/_letters/*.mp4 (Hemg alphabet clips)           │
│  └─ static/signs/_digits/*.mp4 (Hemg digit clips)               │
└─────────────────────────────────────────────────────────────────┘
```

## Tech stack

| Layer | Tech | Why |
|---|---|---|
| Backend | Python 3.12, FastAPI 0.115, uvicorn | Async-friendly, fast, OpenAPI built-in |
| NLP | spaCy 3.8 + en_core_web_sm | Tokenize + lemmatize only — no parser, no reordering |
| File parsing | pypdf 5.1, python-docx 1.1 | Industry-standard, no system deps |
| Validation | pydantic 2.10 | Type-safe request/response |
| Frontend | React 19, Vite 8 | Fast HMR, no build step needed in dev |
| Sync | Web Speech API (`SpeechSynthesisUtterance`) + `setTimeout` | Per-unit utterances with a fixed timer; no reliance on `onboundary` for cadence |
| Typography | Fredoka + Quicksand (Google Fonts) | Rounded friendly sans |
| Mascot | Inline SVG | No asset deps, scales with the UI |
| Data — words | INCLUDE (Zenodo 4010759, CC-BY-4.0) | Real ISL video, openly licensed |
| Data — letters/digits | Hemg/Indian_sign_language_dataset (HuggingFace) | Still images of ISL alphabet + digits |
| Build tools | pyarrow (parquet reader), imageio + ffmpeg (MP4 writer), Pillow (image padding) | One-shot build script for Hemg clips |

## What makes the sync work

The classic three-channel sync problem (text + audio + video) drifts when each channel has its own timer. Kahani solves it by using **one source of truth**:

1. Build a `spokenUnits` array — one entry per spoken unit. For sign-video words the surface is the whole word; for fingerspell words the surface is a single upper-case letter or digit (`"T"`, `"H"`, `"E"`, …).
2. `speakUnit(idx)` creates a `SpeechSynthesisUtterance(unit.surface)`, speaks it, and schedules a `setTimeout(UNIT_DURATION_MS = 1350)` to call `speakUnit(idx + 1)`.
3. The `onstart` callback atomically sets `(activeIdx, activeLetter)` so the chip row, the text highlight, and the `<video>` element all update in lockstep with the spoken unit.
4. A separate `[currentVideoSrc]` effect calls `videoRef.current.src = currentVideoSrc; .load(); .play()` whenever the active unit's video path changes — handles both letter / digit clips and full-word INCLUDE clips.
5. After the last unit, a `POST_ROLL_MS = 700` `setTimeout` holds the final state before resetting to the upload screen.

There is no separate per-letter timer. Audio and video events are **not** used to gate the advance — only the `setTimeout` is. This sidesteps every browser-specific timing bug we hit with `onboundary` and `<video>.onEnded>`.

## Datasets

### INCLUDE — whole-word sign videos

* **Name**: *INCLUDE: A Large Scale Dataset for Indian Sign Language Recognition*
* **Authors**: Advaith Sridhar, Rohith Gandhi Ganesan, Pratyush Kumar, Mitesh M. Khapra (IIT Madras / AI4Bharat)
* **Paper**: DOI [10.1145/3394171.3413528](https://doi.org/10.1145/3394171.3413528) (ACM Multimedia 2020)
* **Distribution**: [Zenodo record 4010759](https://zenodo.org/records/4010759)
* **License**: [CC-BY-4.0](https://creativecommons.org/licenses/by/4.0/)
* **Format**: short MP4 / MOV clips of isolated signs, organized by category (Greetings, Animals, Colours, Pronouns, Days and Time, Seasons, Home, …).
* **In Kahani**: used for **whole-word sign clips** that play when the dictionary has a lemma match. The current dictionary covers ~22 entries from a partial download of the priority subset; many children's-story words still fall back to fingerspelling.
* **Build script**: `backend/signs/build_sign_dictionary.py` — resumable Zenodo download + per-category folder traversal that picks a clean representative clip per lemma.
* **Credit**: shown in the app footer on every screen.

### Hemg/Indian_sign_language_dataset — alphabet + digit signs

* **Distribution**: [huggingface.co/datasets/Hemg/Indian_sign_language_dataset](https://huggingface.co/datasets/Hemg/Indian_sign_language_dataset)
* **Format**: a single ~292 MB Parquet shard (`train-00000-of-00001-*.parquet`) containing 42,745 still images. Schema: `image` (struct with `bytes` and `path`) and `label` (35-way `ClassLabel`).
* **Classes (35)**:
  * `0..8`  → digits `1`–`9` (9 classes)
  * `9..34` → letters `A`–`Z` (26 classes)
* **License**: not explicitly stated on the dataset card; treated as research-use. If a stricter license appears, re-evaluate.
* **In Kahani**: used for the **fingerspelling fallback**. Each class contributes one representative image, encoded as a 320×320 / 0.6 s h264 single-frame looped MP4. There is **no class for digit 0** — stories containing `0` will 404 on that clip.
* **Build script**: `backend/signs/build_fingerspelling_clips_from_hemg.py` — uses `pyarrow` to read the parquet, `Pillow` to letterbox each image into a 320×320 square, and `imageio[ffmpeg]` to encode the MP4.
* **Credit**: shown in the app footer alongside the INCLUDE credit.

## Upgrade paths

### Easy (next sprint)
* Add the remaining INCLUDE halves (Animals_1of2, Greetings_1of2, Colours_1of2, Pronouns_1of2, Days_and_Time_1of3 + 2of3) — 5–7 GB more downloads, ~100 more dictionary entries.
* Hot-reload dictionary: file-watch on `signs/dictionary.json` to invalidate the lru_cache without backend restart.

### Medium
* Smart clip selection: instead of "first file wins", inspect frames for open eyes + sign in frame + no blur.
* Per-content-word dictionary expansion: scrape, with permission, additional ISL resources (Indian government ISL data, AI4Bharat extensions).
* Story library for parents / teachers: pre-loaded stories so the upload step is optional.
* Speed toggle: intermediate levels (0.6, 0.7, 0.9, 1.0, 1.1, 1.2).

### Hard
* Real-time AI-generated sign avatar for any word (out of scope, but architecturally possible: generate per-word video on demand, cache).
* Two-handed ISL signs (current dict is single-hand).
* Continuous fingerspelling (auto-advance per real letter, not per fixed-duration).
* Multi-language support: Hindi input → English translation → ISL (deferred per spec).

## Non-features (decided)

* **No accounts, no auth** — local-only prototype.
* **No cloud storage** — uploads are in-memory, never persisted.
* **No analytics** — no telemetry, no tracking.
* **No mobile app** — web only, but works on tablets.
* **No ISL→text gesture recognition** — explicitly out of scope.
* **No multilingual input** — English only in this pass.
* **No ISL grammar reordering** — word order preserved so the video references the right word.
* **No SiGML/avatar rendering** — replaced with real video clips.

## License

* **Code**: see LICENSE (project default).
* **INCLUDE sign clips**: CC-BY-4.0 (Sridhar et al., ACM MM 2020).
* **Hemg alphabet / digit clips**: from `Hemg/Indian_sign_language_dataset` on HuggingFace; license per the dataset card.
* **spaCy model**: MIT.
* **App**: prototype, no production deployment yet.
