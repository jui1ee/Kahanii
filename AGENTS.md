# AGENTS.md

This file provides guidance to agents when working with code in this repository.

## Stack

- **Backend**: Python 3.10+ / FastAPI on port **3002**, venv at `backend/.venv/`
- **Frontend**: React 19 / Vite on port **5173**, linter is **oxlint** (not ESLint)
- No test suite exists — validation is done via smoke `curl` calls

## Commands

```bash
# Backend (run from backend/)
.venv/bin/python main.py                        # dev server :3002
.venv/bin/uvicorn main:app --workers 4          # production

# Frontend (run from frontend/)
npm run dev                                     # dev server :5173
npm run lint                                    # oxlint (not eslint)
npm run build                                   # outputs to dist/

# One-time backend setup
.venv/bin/pip install -r requirements.txt
.venv/bin/python -m spacy download en_core_web_sm   # required — app crashes without it

# Smoke test
curl -X POST -H 'Content-Type: application/json' \
  -d '{"text":"The horse ran."}' http://127.0.0.1:3002/api/tokenize
```

## Critical Gotchas

- **spaCy model required**: `en_core_web_sm` must be downloaded before the backend starts; it is not in `requirements.txt`.
- **`get_sign_dict()` is `lru_cache`d**: after rebuilding `signs/dictionary.json`, you **must restart** the backend process — the new dictionary won't be picked up automatically.
- **Sign dictionary is sparse** (~22 entries); most words fall back to fingerspelling. Expand by dropping INCLUDE zips into `backend/.cache/include/` and running `backend/signs/build_sign_dictionary.py`.
- **Vite proxies `/api` and `/static` to `:3002`** in dev (see [`vite.config.js`](frontend/vite.config.js)). The frontend uses `http://localhost:3002` as `API_BASE` by default; override with `VITE_API_BASE` at build time for production.
- **Letter clips live at `/static/signs/_letters/<char>.mp4`**, digit clips at `/static/signs/_digits/<char>.mp4`. Generate with `backend/signs/build_fingerspelling_clips.py`.
- **Safari TTS caveat**: `SpeechSynthesisUtterance.onboundary` fires only at sentence boundaries on Safari — the playback timer is intentionally timer-driven (not event-driven) to work around this.

## Code Style

### Python (`backend/`)
- `from __future__ import annotations` at the top of every module
- Type hints everywhere; Pydantic v2 models in [`payload.py`](backend/payload.py)
- Pure functions over stateful objects — `tokenize()` has no side effects
- Lazy imports inside functions for optional heavy deps (pypdf, python-docx)
- `@lru_cache(maxsize=1)` for singleton loaders (`get_nlp`, `get_sign_dict`)

### JavaScript (`frontend/src/`)
- React 19, JSX (`.jsx` extension), no TypeScript
- All API calls use `API_BASE` constant at top of [`App.jsx`](frontend/src/App.jsx:4) — never hardcode backend URLs
- Playback advance is **timer-driven** (`UNIT_DURATION_MS = 1350 ms`) — do not change to `onended`/`onboundary` events; they are intentionally avoided due to browser bugs
- Inline styles for one-offs; CSS classes in `App.css` for reusable components

## Architecture

```
Upload/Paste → POST /api/upload or /api/tokenize
             → spaCy lemmatize → attach_sign_video() → List[StoryToken]
             → PreviewScreen (word inventory)
             → PlaybackScreen (SpeechSynthesis + video <element> loop)
                  ├── sign_video token  → /static/signs/<lemma>.mp4
                  └── fingerspell token → /static/signs/_letters/<char>.mp4
```

`StoryToken` (defined in [`payload.py`](backend/payload.py)) is the single data contract between backend and frontend.
