# Plan Mode Architecture Notes

## Non-Obvious Architectural Constraints

- **No ISL grammar reordering by design** — tokens are returned in source-text order so text highlight and sign video always refer to the same word. Any ISL grammar (SOV reordering) would break this 1:1 mapping.
- **`lru_cache` singletons require process restart to refresh** — `get_nlp()` and `get_sign_dict()` are permanently cached after first call. Dictionary updates require backend restart; cannot be done live.
- **Playback timing is entirely timer-driven** (`UNIT_DURATION_MS = 1350 ms`), not event-driven. This is intentional to avoid Safari/Chrome `onboundary` and `video.onended` unreliability for short clips. Any sync-to-audio feature must replace the whole timing model.
- **Single `<video>` element is reused** across all tokens/letters by changing `.src` in-place. A naive multi-source approach (multiple `<video>` elements or `<source>` swaps) was found unreliable — keep the explicit `.load()` + `.play()` pattern.
- **`StoryToken` is the sole API contract** between backend and frontend. Changes to [`payload.py`](../../backend/payload.py) require coordinated frontend updates in `App.jsx`.
- **No multilingual support**: spaCy `en_core_web_sm` handles English only. Multilingual tokenization (Hindi, etc.) is a documented TODO in `main.py` header.
- **Backend has no auth or rate limiting** — CORS is `allow_origins=["*"]`. This is explicitly noted as local-dev-only; production hardening is a known gap.
