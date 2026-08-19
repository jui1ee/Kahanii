# Kahani — Story Time with Signs

A kid-friendly web app that turns a children's story into a synchronized
read-along experience for hearing-impaired children:

1. The story text scrolls by with the **current word highlighted**.
2. An **Indian Sign Language (ISL) sign video** plays for that word.
3. **Audio narration** (browser TTS) reads the story out loud.

When the dictionary has no video for a word, the UI falls back to
**letter-by-letter fingerspelling** so the word is still shown — the
fallback is load-bearing, not decorative.

---

## Repo layout

    backend/         FastAPI service — upload, parse, tokenize, sign lookup
      main.py        HTTP endpoints
      payload.py     Pydantic request/response models
      signs/         Dictionary builder + attribution
      static/signs/  Served at /static/signs/ — curated clips + letters
      .cache/        Downloads cache (gitignored)

    frontend/        React (Vite) UI
      src/App.jsx    Three screens: upload → preview → playback
      src/App.css    Pastel kid-friendly styling
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
    .venv/bin/python signs/build_fingerspelling_clips.py     # one-time
    .venv/bin/python signs/build_sign_dictionary.py          # one-time, ~9.8 GB
    .venv/bin/python main.py

`build_sign_dictionary.py` downloads the INCLUDE priority subset
(Greetings, Animals, Colours, Pronouns, Seasons, Days and Time) from
Zenodo (CC-BY-4.0). Subsequent runs are cached in `.cache/include/`.

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

## What's deliberately out of scope

* ISL → text (gesture recognition from webcam). The previous prototype
  had this; it was deleted in this rebuild because the product is a
  story-playback experience for hearing-impaired children, not a
  signing tool.
* Multilingual input. The previous googletrans dependency is dropped.
  A `# TODO: reintroduce translation later if needed` marker is left
  in `backend/main.py`.
* User accounts, cloud storage, deployment config.

---

## Data attribution

Sign clips are courtesy of the INCLUDE dataset
(Sridhar et al., ACM Multimedia 2020, DOI
[10.1145/3394171.3413528](https://doi.org/10.1145/3394171.3413528),
licensed [CC-BY-4.0](https://creativecommons.org/licenses/by/4.0/),
[Zenodo record 4010759](https://zenodo.org/records/4010759)).
Credit is surfaced in the app footer on every screen.

See `backend/signs/ATTRIBUTION.md` for full details.

---

## Status

Prototype. Tested end-to-end with `pasted-text` input. Real-world
upload of .pdf / .docx / .txt works on the backend; the React upload
form supports all three.

Known limitations of this pass:

* **Dictionary size**: the curated subset covers roughly 200+ INCLUDE
  words (after extraction & dedup). Children's stories will mostly
  hit the fingerspelling fallback — that's by design, see above.
* **Letter clips**: the placeholder fingerspelling videos are
  procedurally rendered letters on pastel cards, not real ISL
  alphabet footage. Replacing these is the highest-value follow-up.
* **Sync mechanism**: uses `SpeechSynthesisUtterance.onboundary` for
  word-by-word timing. Tested in Chrome/Edge; Safari fires
  `onboundary` only at sentence boundaries, so on Safari the
  highlight advances only between sentences (every word still gets
  its sign video — the swap just loses word-level granularity). A
  pre-computed timestamp approach is the fallback for Safari, see
  `App.jsx` comments.
