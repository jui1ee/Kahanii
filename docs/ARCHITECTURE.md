# Kahani — Architecture Reference

> **Audience:** Developers, contributors, and anyone deploying or extending Kahani.
> Cross-referenced against actual code. Where old docs disagreed with the codebase, the code wins.

---

## Tech Stack

| Layer | Technology | Version | Why |
|---|---|---|---|
| Backend runtime | Python | 3.10+ (tested 3.12) | Language of choice; async support via FastAPI |
| Backend framework | FastAPI | 0.115.6 | Async-friendly, OpenAPI auto-docs, built-in validation |
| ASGI server | uvicorn[standard] | 0.32.1 | Production-grade async server; used in both dev and prod |
| Data validation | Pydantic | 2.10.3 | v2 models for request/response; strict typing |
| NLP | spaCy | 3.8.3 | Tokenize + lemmatize only (parser/NER/tagger disabled) |
| spaCy model | `en_core_web_sm` | 3.8.0 | Small English model; downloaded separately (not in `requirements.txt`) |
| PDF parsing | pypdf | 5.1.0 | Pure-Python PDF text extraction; no system deps |
| DOCX parsing | python-docx | 1.1.2 | Standard DOCX reader; paragraph extraction |
| Multipart upload | python-multipart | 0.0.20 | Required by FastAPI's `UploadFile`; not bundled with FastAPI |
| Frontend framework | React | 19.2.8 | Component model; hooks-based state |
| Frontend build | Vite | 8.2.0 | Fast HMR in dev; static-bundle output for prod |
| React plugin | @vitejs/plugin-react | 6.0.4 | JSX transform + fast-refresh |
| Frontend linter | oxlint | 1.75.0 | Fast Rust-based linter; **not** ESLint |
| Parquet reader (build-time) | pyarrow | (latest at build time) | Reads Hemg HuggingFace parquet shard |
| Image manipulation (build-time) | Pillow | (latest at build time) | Letterbox-pads Hemg images to 320×320 |
| Video encoding (build-time) | imageio[ffmpeg] + ffmpeg | (system ffmpeg) | Encodes 0.6 s h264 looped MP4s for fingerspelling clips |
| Typography (CDN) | Fredoka + Quicksand | Google Fonts | Rounded friendly sans-serif for kids |
| ISL word clips (data) | INCLUDE dataset | Zenodo 4010759 | CC-BY-4.0 real ISL video clips |
| ISL letter/digit clips (data) | Hemg/Indian_sign_language_dataset | HuggingFace | 42,745 still images, 35-class ISL alphabet/digits |

---

## Folder Structure

```
Bidirectional-Indian-Sign-Language-Translator/
│
├── backend/                         FastAPI service (port 3002)
│   ├── main.py                      All HTTP endpoints + NLP pipeline
│   ├── payload.py                   Pydantic models (StoryToken)
│   ├── requirements.txt             Python dependencies (pinned)
│   ├── .venv/                       Python virtual env (gitignored)
│   ├── .cache/                      Download cache (gitignored)
│   │   └── include/                 INCLUDE zip downloads go here
│   │
│   ├── signs/                       Dictionary + build scripts
│   │   ├── dictionary.json          22-entry lemma→filename map (generated)
│   │   ├── ATTRIBUTION.md           Dataset credits + license info
│   │   ├── build_sign_dictionary.py         Main INCLUDE build script
│   │   ├── build_sign_dictionary_extend.py  Incremental extend helper
│   │   ├── build_fingerspelling_clips.py    Legacy placeholder clip generator
│   │   ├── build_fingerspelling_clips_from_hemg.py  Real ISL alphabet clips
│   │   ├── _auto_build_dict.py      Automation helper
│   │   ├── _download_one.sh         Download a single INCLUDE zip
│   │   ├── _download_small.sh       Download small subset of INCLUDE
│   │   ├── _download_subset.py      Python-based download helper
│   │   ├── _download_subset.sh      Shell-based download helper
│   │   ├── _keepalive.sh            Pings backend every 4 min to prevent sleep
│   │   ├── _keepalive_one.sh        Single-request keepalive
│   │   ├── _resume_downloads.sh     Resume interrupted downloads
│   │   └── _resume_parallel.sh     Parallel resumable download helper
│   │
│   └── static/                      Served at /static/* by FastAPI
│       └── signs/
│           ├── *.mp4                22 INCLUDE whole-word ISL clips
│           ├── _letters/            26 Hemg ISL alphabet clips (a-z)
│           │   └── {a-z}.mp4
│           └── _digits/             9 Hemg ISL digit clips (1-9)
│               └── {1-9}.mp4
│
├── frontend/                        React + Vite UI (port 5173)
│   ├── index.html                   SPA root; loads Google Fonts
│   ├── vite.config.js               Dev proxy: /api → :3002, /static → :3002
│   ├── package.json                 npm deps; scripts: dev/build/lint/preview
│   │
│   ├── src/
│   │   ├── main.jsx                 React entry point (StrictMode + createRoot)
│   │   ├── App.jsx                  All three screens + Mascot + sync engine
│   │   ├── App.css                  Pastel styling, letter-chip colors, layout
│   │   ├── index.css                Global reset + Fredoka/Quicksand imports
│   │   └── scenes/
│   │       ├── illustrations.json   lemma → /scenes/<name>.svg map (22 entries)
│   │       └── moods.json           keyword → {gradient, accentColor} map (24 entries)
│   │
│   └── public/
│       ├── favicon.svg              Browser tab icon
│       └── scenes/                  22 stub SVG illustrations served at /scenes/
│           └── *.svg                Pastel emoji cards (horse.svg, morning.svg, etc.)
│
├── docs/                            Consolidated project docs (this folder)
│   ├── PRODUCT.md                   Feature inventory
│   ├── ARCHITECTURE.md              This file
│   └── AI.md                        AI-assisted development log
│
├── Images/
│   └── usecase_diagram.png          Use-case diagram from the original SIH submission
│
├── SolutionPPT/
│   └── _Byte Busters_ SIH 1715.pdf  Original SIH submission PDF (provenance only)
│
├── Videos/
│   └── Text_to_Indian_Sign_Language_Example.mp4  Demo video from original submission
│
├── README.md                        Project overview, datasets, run instructions
├── RUN.md                           Detailed run/deploy/troubleshoot guide
├── PRESENTATION.md                  Slide deck content (12-slide deck draft)
├── product.md                       Product spec (pre-docs consolidation)
├── context.md                       Build session log (chronological dev history)
├── storyscenes-plan.md              Sub-task plan for the scene layer feature
└── AGENTS.md                        AI agent coding rules for this project
```

---

## External API Calls

All HTTP calls originate from the **frontend** (`App.jsx`). The backend makes no outbound calls during request handling; network calls only happen in the one-time build scripts.

### Frontend → Backend (runtime)

| Caller | Method | Endpoint | Purpose | Auth |
|---|---|---|---|---|
| [`UploadScreen.submitFile()`](../frontend/src/App.jsx:82) | `POST` | `/api/upload` | Multipart story file → token list | None |
| [`UploadScreen.submitText()`](../frontend/src/App.jsx:101) | `POST` | `/api/tokenize` | Raw pasted text → token list | None |
| (Vite dev proxy / browser) | `GET` | `/static/signs/*.mp4` | Fetch ISL word clip for active token | None |
| (Vite dev proxy / browser) | `GET` | `/static/signs/_letters/*.mp4` | Fetch alphabet clip for fingerspell letter | None |
| (Vite dev proxy / browser) | `GET` | `/static/signs/_digits/*.mp4` | Fetch digit clip for fingerspell digit | None |
| (browser, no proxy) | `GET` | `/scenes/*.svg` | Fetch scene illustration (from Vite public/) | None |

`API_BASE` is set from `import.meta.env.VITE_API_BASE` with fallback `http://localhost:3002`. In dev, the Vite proxy intercepts `/api` and `/static` paths transparently.

### Build Scripts → External (one-time setup only)

| Script | External endpoint | Purpose |
|---|---|---|
| [`build_sign_dictionary.py`](../backend/signs/build_sign_dictionary.py) | `https://zenodo.org/records/4010759` | Downloads INCLUDE dataset zips |
| [`build_fingerspelling_clips_from_hemg.py`](../backend/signs/build_fingerspelling_clips_from_hemg.py) | HuggingFace datasets CDN | Downloads Hemg parquet shard (~292 MB) |

---

## Libraries — Why Each Is Used

### Backend (`requirements.txt`)

| Package | Why |
|---|---|
| `fastapi==0.115.6` | HTTP framework with async support, automatic OpenAPI docs, dependency injection |
| `uvicorn[standard]==0.32.1` | ASGI server that runs FastAPI; `[standard]` includes `watchfiles` and `websockets` |
| `pydantic==2.10.3` | Defines `StoryToken` request/response model; validates types at the boundary |
| `spacy==3.8.3` | Tokenization and lemmatization pipeline; parser/NER/tagger disabled for speed |
| `pypdf==5.1.0` | PDF text extraction for `.pdf` uploads; pure Python, no LibreOffice/system deps |
| `python-docx==1.1.2` | DOCX paragraph extraction for `.docx` uploads |
| `python-multipart==0.0.20` | Required by FastAPI's `UploadFile` for `multipart/form-data` parsing; not auto-installed by FastAPI |

### Frontend (`package.json`)

| Package | Why |
|---|---|
| `react@^19.2.8` | UI component model; hooks for state/effects |
| `react-dom@^19.2.8` | DOM renderer for React |
| `vite@^8.2.0` | Build tool + dev server; fast HMR; dev proxy |
| `@vitejs/plugin-react@^6.0.4` | JSX transform and fast-refresh for Vite |
| `oxlint@^1.75.0` | Linter (Rust-based); **not** ESLint — run via `npm run lint` |
| `@types/react` / `@types/react-dom` | TypeScript type definitions (used for IDE support; project is pure JSX, no TypeScript) |

### Build-time only (not in requirements.txt)

| Package | Why |
|---|---|
| `pyarrow` | Reads the Hemg Parquet shard to extract images per class |
| `Pillow` | Letterbox-pads each Hemg image into 320×320 square on pastel background |
| `imageio[ffmpeg]` | Encodes the padded image as a 0.6 s h264 single-frame looped MP4 |

---

## Data Models

### `StoryToken` ([`backend/payload.py`](../backend/payload.py))

The single data contract between backend and frontend. Every API response is `List[StoryToken]`.

| Field | Type | Description |
|---|---|---|
| `display_word` | `str` | Original surface form as it appears in the story (e.g. "ran", "2024") |
| `lemma` | `str` | Lowercased lemma used for dictionary lookup (e.g. "run", "2024") |
| `sign_video` | `Optional[str]` | Path like `/static/signs/horse.mp4`, or `null` for fingerspelling |
| `is_fingerspelling` | `bool` | `true` when the word falls back to letter-by-letter display |
| `scene_idx` | `int` | 0-based sentence/scene index; all tokens in the same sentence share the same value |

### `signs/dictionary.json`

A flat JSON object: `{ "<lemma>": "<filename>.mp4" }`. Keys are lowercase/stripped lemmas. Values are bare filenames (not full paths). 22 entries currently.

Loading: `get_sign_dict()` in `main.py` is `@lru_cache(maxsize=1)` — loaded once at first request, cached for the lifetime of the process. **Must restart the backend after rebuilding the dictionary.**

### `scenes/illustrations.json` + `scenes/moods.json`

Bundled into the frontend JS bundle at build time via Vite's JSON import. Not served as API endpoints.

---

## Data Flow — End to End

### Path A: File Upload

```
User drops/picks file
    │
    ▼
UploadScreen.submitFile()
    POST /api/upload  (multipart, max 5MB)
    │
    ▼
backend/main.py upload_story()
    → extract_text(filename, data)
        .txt/.md  → _extract_text_from_txt()  (utf-8 → latin-1 fallback)
        .pdf      → _extract_text_from_pdf()   (pypdf PdfReader)
        .docx     → _extract_text_from_docx()  (python-docx Document)
    → tokenize(text)
        → segment_sentences(text)          (regex splitter, no spaCy parser)
        → for each segment: nlp(segment)   (spaCy, lemmatizer only)
        → for each token: StoryToken(...)
        → attach_sign_video(tokens)        (dict lookup, marks sign_video / is_fingerspelling)
    → List[StoryToken] returned as JSON
    │
    ▼
App.onStoryLoaded({ tokens, filename })
    → setScreen('preview')
    │
    ▼
PreviewScreen
    User reviews word inventory, clicks "▶ Play story"
    → setScreen('play')
    │
    ▼
PlaybackScreen
    → builds spokenSegments + spokenUnits memos
    → playFromStart() called
        → speakUnit(0)
            ├─ SpeechSynthesisUtterance(unit.surface)
            ├─ u.onstart → setActiveIdx + setActiveLetter → UI update
            │               (text highlight + video swap + chip highlight)
            └─ setTimeout(signDurationMs | fsDurationMs) → speakUnit(idx+1)
        → [currentVideoSrc] effect → video.src + .load() + .play()
        → [activeIdx, tokens] effect → build letterSequence for fingerspell
        → [letterSequence, activeLetter] effect → update video for FS letters
        → after last unit: setTimeout(700ms) → reset to upload screen
```

### Path B: Paste Text

Same as Path A from `tokenize(text)` onward; only the HTTP endpoint differs (`/api/tokenize` with JSON body vs `/api/upload` multipart).

---

## Build, Run, and Deployment

### Development Setup (first time)

```bash
# Backend
cd backend
python3 -m venv .venv
.venv/bin/pip install --upgrade pip
.venv/bin/pip install -r requirements.txt
.venv/bin/python -m spacy download en_core_web_sm  # required; not in requirements.txt

# Generate real ISL fingerspelling clips from Hemg dataset (~292 MB download)
.venv/bin/python signs/build_fingerspelling_clips_from_hemg.py

# Optional: download INCLUDE subset and build word dictionary (~6 GB, 30-90 min)
.venv/bin/python signs/build_sign_dictionary.py

# Frontend
cd ../frontend
npm install
```

### Running Locally

```bash
# Terminal 1 — backend on :3002
cd backend && .venv/bin/python main.py

# Terminal 2 — frontend on :5173
cd frontend && npm run dev
```

Open `http://localhost:5173/`. Vite proxies `/api` and `/static` to the backend.

### Smoke Tests

```bash
curl http://127.0.0.1:3002/healthz
# {"status":"ok"}

curl -X POST -H 'Content-Type: application/json' \
  -d '{"text":"The horse ran."}' http://127.0.0.1:3002/api/tokenize

curl http://127.0.0.1:3002/api/signs/summer
# {"lemma":"summer","found":true,"fingerspell":false,"video":"/static/signs/summer.mp4"}
```

### Linting

```bash
cd frontend && npm run lint    # oxlint (not eslint)
```

### Production Build

```bash
cd frontend && npm run build
# Static assets output to frontend/dist/
# Point dist/ at any HTTP server; set VITE_API_BASE at build time.

VITE_API_BASE=https://api.kahani.example.com npm run build
```

### Production Backend

```bash
cd backend
.venv/bin/uvicorn main:app --host 0.0.0.0 --port 3002 --workers 4
# or via gunicorn:
.venv/bin/pip install gunicorn
.venv/bin/gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:3002
```

### Minimal nginx Config (prod)

```nginx
server {
  listen 80;
  server_name kahani.example.com;
  root /var/www/kahani/dist;
  index index.html;

  location / { try_files $uri /index.html; }            # SPA fallback
  location /api/    { proxy_pass http://127.0.0.1:3002; }
  location /static/ { proxy_pass http://127.0.0.1:3002; }
}
```

---

## Key Design Decisions

### 1. Parser/NER/tagger disabled in spaCy
```python
nlp(segment, disable=["parser", "ner", "tagger", "attribute_ruler"])
```
Only tokenizer + lemmatizer run. ~5× faster on long stories. Eliminates any risk of ISL reordering logic from the old codebase accidentally re-engaging.

### 2. Sentence segmentation via custom regex, not spaCy parser
`segment_sentences()` in `main.py` uses a regex split on `[.?!]` with an abbreviation guard (`Mr.`, `Dr.`, etc.). This lets `scene_idx` be assigned correctly without enabling the spaCy parser pipeline.

### 3. Timer-driven advance, not event-driven
`speakUnit()` uses `setTimeout(signDurationMs | fsDurationMs)` for advance. `onend` (TTS) and `video.onEnded` are **not** used for advancing — documented unreliable on Safari for short utterances and same-clip repeated units. The timer is deterministic across all browsers.

### 4. `lru_cache` on loaders
Both `get_nlp()` and `get_sign_dict()` are `@lru_cache(maxsize=1)`. Safe (read-only after first load) and means the spaCy model and dictionary are loaded exactly once per process lifetime. **Consequence:** must restart the backend after any dictionary rebuild.

### 5. All uploads are in-memory
`await file.read()` → parse → `tokenize()` → return JSON. No temp files, no filesystem writes, no database. Privacy by construction.

### 6. Two-column playback layout with scene layer
Left column: sign-video panel stacked above scene-illustration panel.
Right column: text flow + controls (unchanged from pre-scene implementation).
Scene backdrop: `position: fixed; z-index: 0` — behind all white-background panels.

---

## Important Constraints / Gotchas

| Gotcha | Detail |
|---|---|
| `en_core_web_sm` not in `requirements.txt` | Must be downloaded with `python -m spacy download en_core_web_sm` separately; app crashes on startup without it |
| `get_sign_dict()` is cached | Restart backend after rebuilding `signs/dictionary.json` |
| `python-multipart` is explicit | FastAPI does not pull it in automatically; if removed from `requirements.txt`, file upload breaks silently |
| No digit-0 clip | Hemg dataset has no class for digit 0; `/static/signs/_digits/0.mp4` 404s |
| CORS open in dev | `allow_origins=["*"]` in `main.py` — lock this down for production |
| `lru_cache` not shared across workers | In multi-worker uvicorn, each worker loads its own copy of the NLP model and dict |
| `extract_text()` also accepts `.md` files | The file-input `accept` attribute and the backend's `extract_text()` both handle `.md` as plain text (not documented in most places) |

---

## Notes / Discrepancies Found

1. **`backend/README.md` response example** omits `scene_idx` field — the field was added as part of the storyscenes implementation and the backend README was not updated. The actual response shape always includes `scene_idx`.

2. **`context.md` section 3.4** says the original sync mechanism was `SpeechSynthesisUtterance.onboundary` with binary-search `charIndex` → token index. The code was later completely replaced by the per-unit utterance scheduler (`onstart` + `setTimeout`). The binary-search approach no longer exists in `App.jsx`.

3. **`RUN.md` "Optional: sign dictionary + fingerspelling clips"** says "The app works without these — every word falls back to letter-by-letter fingerspelling using placeholder pastel cards." — This is only true if `build_fingerspelling_clips_from_hemg.py` has NOT been run. Once run, the real Hemg clips replace the placeholders. After a fresh setup following current `README.md`, the real clips are used.

4. **`Signs/ATTRIBUTION.md`** was written before the Hemg dataset was added and does not credit it. The app footer credits both INCLUDE and Hemg, but `ATTRIBUTION.md` only mentions INCLUDE and spaCy.
