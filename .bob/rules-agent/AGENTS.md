# Agent Coding Rules

## Non-Obvious Patterns

- **Never use `JSON.stringify` directly for `dictionary.json`** — always use the same `json.dump` round-trip pattern in `build_sign_dictionary.py` (keys are normalized to lowercase/stripped on load, so mismatches silently miss).
- **`tokenize()` in [`main.py`](../../backend/main.py) deliberately disables `parser`, `ner`, `tagger`, `attribute_ruler`** when the lemmatizer pipe isn't present. Don't re-enable them — it's ~5× slower and was previously a source of ISL reordering bugs.
- **Sentence segmentation uses `segment_sentences()` in [`main.py`](../../backend/main.py)**, a pure-Python regex splitter — spaCy's `parser` is still disabled. Each `StoryToken` carries a `scene_idx` (0-based) set here; the frontend derives `activeSceneIdx` inline from `tokens[activeIdx].scene_idx`.
- **`scenes/illustrations.json` and `scenes/moods.json` keys must be lemmas** (matching `StoryToken.lemma`, lowercased). Key order is priority order — first matching lemma in the scene wins. Add `"default"` to `moods.json` as the fallback; it is required.
- **The `spokenUnits` memo in [`App.jsx`](../../frontend/src/App.jsx) flattens fingerspelling words into one entry per letter.** The `letterIdx` field on each unit is the index into the active token's letter sequence — keep this contract if you change the playback loop.
- **`signDurationMs` / `fsDurationMs` are the two timer values fed into `speakUnit`'s `setTimeout`.** There is no longer a single `UNIT_DURATION_MS` constant. Sign-video units use `signDurationMs` (default 3500ms); fingerspell letter units use `fsDurationMs` (default 900ms). `u.rate` is fixed at `0.9`, not derived from either.
- **No test runner is set up** — the only validation path is `curl` smoke tests (see [`RUN.md`](../../RUN.md)) and manual browser testing.
- **`cancelledRef`** in `PlaybackScreen` is the stop signal for all async timers. Any new async operation in that component must check `cancelledRef.current` before acting.
- **Frontend has no router** — screen state (`'upload' | 'preview' | 'play'`) lives in `App` component state only.
- **`python-multipart` is required by FastAPI's `UploadFile`** but isn't listed as a FastAPI dependency — it is explicitly pinned in `requirements.txt`. Don't remove it.
