# Plan Mode Architecture Notes

## Non-Obvious Architectural Constraints

- **No ISL grammar reordering by design** — tokens are returned in source-text order so text highlight and sign video always refer to the same word. Any ISL grammar (SOV reordering) would break this 1:1 mapping.
- **`lru_cache` singletons require process restart to refresh** — `get_nlp()` and `get_sign_dict()` are permanently cached after first call. Dictionary updates require backend restart; cannot be done live.
- **Playback timing is entirely timer-driven**, not event-driven — intentional to avoid Safari/Chrome `onboundary` and `video.onended` unreliability. Two independent durations: `signDurationMs` (default 3500ms, covers p90 of real INCLUDE clips at 3.68s) and `fsDurationMs` (default 900ms per letter). There is no longer a single `UNIT_DURATION_MS` constant. Any sync-to-audio feature must replace the whole timing model.
- **Single `<video>` element is reused** across all tokens/letters by changing `.src` in-place. A naive multi-source approach (multiple `<video>` elements or `<source>` swaps) was found unreliable — keep the explicit `.load()` + `.play()` pattern.
- **`StoryToken` is the sole API contract** between backend and frontend. Fields: `display_word`, `lemma`, `sign_video`, `is_fingerspelling`, `scene_idx`. Changes to [`payload.py`](../../backend/payload.py) require coordinated frontend updates in `App.jsx`.
- **Scene layer is purely frontend-derived** — `activeSceneIdx` is an inline expression off `activeIdx`, not a state variable. `sceneL` (lemma set for active scene) drives both illustration and mood lookups via `useMemo`. Neither requires a backend endpoint or a new `useEffect`.
- **`segment_sentences()` is a two-pass regex** — first splits on `[.?!]+(?=\s+[A-Z])|[.?!]+$`, then re-joins fragments whose tail is a title-case abbreviation (`Mr`, `Dr`, `St`). Adding new abbreviation types requires updating `_ABBREV_TAIL_RE` in [`main.py`](../../backend/main.py).
- **No multilingual support**: spaCy `en_core_web_sm` handles English only. Multilingual tokenization (Hindi, etc.) is a documented TODO in `main.py` header.
- **Backend has no auth or rate limiting** — CORS is `allow_origins=["*"]`. This is explicitly noted as local-dev-only; production hardening is a known gap.
