# Agent Coding Rules

## Non-Obvious Patterns

- **Never use `JSON.stringify` directly for `dictionary.json`** — always use the same `json.dump` round-trip pattern in `build_sign_dictionary.py` (keys are normalized to lowercase/stripped on load, so mismatches silently miss).
- **`tokenize()` in [`main.py`](../../backend/main.py:134) deliberately disables `parser`, `ner`, `tagger`, `attribute_ruler`** when the lemmatizer pipe isn't present. Don't re-enable them — it's ~5× slower and was previously a source of ISL reordering bugs.
- **The `spokenUnits` memo in [`App.jsx`](../../frontend/src/App.jsx:336) flattens fingerspelling words into one entry per letter.** The `letterIdx` field on each unit is the index into the active token's letter sequence — keep this contract if you change the playback loop.
- **No test runner is set up** — the only validation path is `curl` smoke tests (see [`RUN.md`](../../RUN.md)) and manual browser testing.
- **`cancelledRef`** in `PlaybackScreen` is the stop signal for all async timers. Any new async operation in that component must check `cancelledRef.current` before acting.
- **Frontend has no router** — screen state (`'upload' | 'preview' | 'play'`) lives in `App` component state only.
- **`python-multipart` is required by FastAPI's `UploadFile`** but isn't listed as a FastAPI dependency — it is explicitly pinned in `requirements.txt`. Don't remove it.
