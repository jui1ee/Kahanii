# Kahani — AI-Assisted Development Log

> **Purpose:** A factual record of how AI tools — specifically **bobshell** — were used throughout the design and implementation of Kahani.

---

## Overview

Kahani was built in a pair-programming model with **bobshell** as the primary coding assistant. The project began as an ISL translator and was rebuilt from scratch into a clean, working product across a series of focused sessions. AI assistance touched every stage of the work — from the initial audit and scope negotiation, through implementation, data pipeline construction, debugging, and documentation.

---

## 1. Refining Code After Building an Initial Rough Version

### Per-unit utterance scheduler — replacing onboundary

The initial playback implementation used `SpeechSynthesisUtterance.onboundary` with a binary-search mapping from `charIndex` back to a token index. This created two failure modes:

1. **Same-clip repeated units** (e.g. "the" fingerspelled twice in a row) — `onboundary` wouldn't always fire again if the surface string was identical.
2. **Short-utterance `onend` failure** — browsers, especially Safari, didn't reliably fire `onend` for single-letter utterances, causing the scheduler to get stuck.

bobshell rewrote the scheduler in [`frontend/src/App.jsx`](../frontend/src/App.jsx) to eliminate both failure modes:
- Built `spokenUnits[]` — one entry per spoken unit (letter/digit for fingerspell, whole word for sign-video).
- Each unit gets its own `SpeechSynthesisUtterance(unit.surface)` via `speakUnit(idx)`.
- Advance is exclusively timer-driven: `setTimeout(signDurationMs | fsDurationMs)`.
- `onstart` is used only to set `(activeIdx, activeLetter)` — it never gates advance.
- `onend`, `video.onEnded`, `onboundary` are all removed from the advance path.

This change is recorded in commit `4f2512b` 

### Timing refinement — post-roll and duration constants

After the scheduler was working, a user-reported issue ("short stories cut off mid-gesture") led to bobshell adding `POST_ROLL_MS = 700` — a deferred reset after the final unit so the last word/letter stays visible briefly before the screen resets. Commit `daa8ebb`.

Later, the single `UNIT_DURATION_MS = 1350` constant was replaced with two independent sliders (`signDurationMs` and `fsDurationMs`) so that sign-video tokens (which need ~3.5 s for a real INCLUDE clip to be meaningful) and fingerspell letter tokens (which only need ~0.9 s) could be tuned independently. Commit `aee46ef`.

### Fingerspelling placeholder → real ISL clips

The initial fingerspelling fallback used procedurally-generated pastel-card placeholder clips (`build_fingerspelling_clips.py`). bobshell:
1. Identified the Hemg/Indian_sign_language_dataset as a suitable replacement (35-class ISL still-image dataset on HuggingFace).
2. Wrote [`build_fingerspelling_clips_from_hemg.py`](../backend/signs/build_fingerspelling_clips_from_hemg.py): downloads a single ~292 MB Parquet shard, reads with `pyarrow`, letterbox-pads with Pillow, encodes with `imageio[ffmpeg]` into 320×320 0.6 s h264 looped MP4s.
3. Extended the frontend to route digits to `_digits/` and letters to `_letters/`, adding pastel cyan chip styling for digits.

---

## 2. Deciding Feature Feasibility — What Was Evaluated, Cut, and Kept

### Cut: ISL → text (webcam gesture recognition)
The user suggested a sign language recognition pipeline using MediaPipe + TFLite classifier for recognising signs from a webcam feed. bobshell evaluated this against the new product brief (a read-along app for children, not a signing tool) and recommended **out of scope for current version**. Reason: the feature required webcam access, was error-prone with children in frame, and was entirely orthogonal to the story-playback use case.

### Cut: ISL grammar reordering
The original `isl_nlp.py` and `code.py` implemented ISL grammar reordering (reordering English words into ISL sentence order before sign lookup). bobshell flagged this as actively harmful: reordering means the word being signed is no longer the same word currently highlighted in the story text, breaking the three-channel sync. **Deleted**. Word order is preserved exactly as it appears in the source. 



### Kept: Fingerspelling as a first-class feature
An early design question was whether the fingerspelling fallback should be a silent degradation or a visible, designed feature. bobshell advised making it **load-bearing** — the fallback covers every word not in the dictionary (which is most words in a real story), so it needed to be high-quality, clearly labelled, and well-timed. This informed the decision to source real ISL alphabet clips from Hemg and add the letter-chip row with distinct digit/letter coloring.

### Kept: Timer-driven sync (over event-driven)
Several approaches were evaluated for synchronising text highlight, video, and audio:
- **`onboundary` events**: rejected — too unreliable on Safari.
- **`video.onEnded` events**: rejected — doesn't fire for same-clip repeated units.
- **`SpeechSynthesisUtterance.onend`**: rejected — unreliable for short utterances.
- **`setTimeout` only**: chosen — deterministic, browser-agnostic, never gets stuck.

### Deferred: More INCLUDE dictionary words
The dictionary currently covers 22 words from a partial INCLUDE download (~6.1 GB). Expanding it requires running `build_sign_dictionary.py` after adding more INCLUDE category zips. bobshell designed the build pipeline to be resumable and the dictionary to be hot-swappable (minus the `lru_cache` restart requirement), so expansion is a one-command operation for a maintainer.

---

## 3. Maintaining Persistent Context and Continuity Across Sessions

### `context.md` as a living session log
bobshell authored and maintained [`context.md`](../context.md) as a chronological build log across multiple sessions. It records:
- The starting-point audit (what the repo contained, what was broken).
- The user brief and every explicit decision that followed from it.
- Each phase of work: deletions, restructuring, backend implementation, frontend, sign dictionary builder, fingerspelling fallback, Hemg upgrade, per-unit scheduler, cosmetic changes.
- A "Currently Functional" snapshot and "Documented Gaps" section that are updated after each working pass.

This file gave bobshell a reliable foundation for each new session without having to re-read all source files from scratch.

### `product.md` as a living product spec
[`product.md`](../product.md) was kept updated with each feature pass — not just as a spec but as the authoritative description of what the app currently does (as opposed to what was originally planned). bobshell updated it in sync with code changes (commit `8c27827` updates both at once).

### Feature branches
The storyscenes feature (scene illustrations + mood backdrop) was developed on `feat/storyscenes` and kept separate from `main` during planning and implementation. bobshell authored [`storyscenes-plan.md`](../storyscenes-plan.md) as a sub-task breakdown before writing any code, ensuring the implementation was scoped precisely and didn't break existing behaviour.

---

## 4. Maintaining Git Commit History and Version Control

bobshell committed changes in logical, atomic units with descriptive messages. Examples from the project's git log:

| Commit | What it captured |
|---|---|
| `c69fff4` Initial Kahani implementation | First working end-to-end version |
| `4f2512b` Replace placeholder fingerspelling with real ISL signs | Backend build script + frontend routing rework in one commit |
| `daa8ebb` Bump unit duration and add 700ms post-roll | Single-purpose timing fix |
| `8c27827` Update README, product.md, context.md for Hemg + per-unit scheduler | Docs always committed with the code that made them stale |
| `8dda5e3` added the presentation doc | Presentation content added as its own commit |
| `8cc7cb2` Add storybook scene layer: illustrations + mood backdrop | Complete feature in one commit |
| `aee46ef` Fix hardcoded unit timing: independent sliders, fixed TTS rate | Bug fix + UX improvement |

The commit message for `8c27827` is notably detailed — listing exactly which sections of which files changed and why — because it covered a docs-only update that needed to clearly explain what code changes had preceded it.

---

## 5. Running Automated Smoke Tests

No automated test suite exists in this project (documented in `AGENTS.md`). The validated testing path is a set of `curl` smoke tests against the live backend, established and documented by bobshell in [`RUN.md`](../RUN.md):

```bash
# Liveness
curl http://127.0.0.1:3002/healthz

# Tokenize a multi-word phrase with known dictionary hits
curl -X POST -H 'Content-Type: application/json' \
  -d '{"text":"The horse ran in the morning."}' \
  http://127.0.0.1:3002/api/tokenize

# Single sign lookup
curl http://127.0.0.1:3002/api/signs/summer

# Verify a clip actually serves
curl -o /dev/null -w "%{http_code}\n" http://127.0.0.1:3002/static/signs/summer.mp4
```

The canonical test input `"The horse ran in 2024 morning."` was chosen by bobshell specifically because it exercises:
- A known dictionary hit (`horse`, `morning`)
- Fingerspelled letters (`ran`, `in`)
- Digits requiring `_digits/` routing (`2`, `0`, `2`, `4`)
- The `POST_ROLL_MS` hold at the end of a short story

---

## 6. Branching and Merging Features Cleanly

### `feat/storyscenes` branch
The scene illustrations + mood backdrop feature was developed on a dedicated `feat/storyscenes` branch (visible in `git branch -a` output). bobshell authored [`storyscenes-plan.md`](../storyscenes-plan.md) which:
- Explicitly listed **unchanged invariants** (timer loop, video reuse, Safari workaround, `lru_cache` loaders, existing API response shape) to define what the feature must not touch.
- Broke the work into three numbered sub-tasks (backend `scene_idx`, static data, frontend wiring) with explicit todo lists per sub-task.
- Listed every file that would change, and every file that would not.

This plan made the merge trivially clean: no conflicts with `main` because the plan had anticipated all touch-points.

---

## 7. Generating and Maintaining Project Documentation

bobshell generated and kept the following docs in sync with the codebase throughout development:

| File | Role | How bobshell managed it |
|---|---|---|
| `README.md` | User-facing overview | Updated alongside code in commit `8c27827`; refreshed datasets section, repo layout, known limitations |
| `RUN.md` | Operational guide | Written by bobshell; covers setup, smoke tests, troubleshooting, production deployment |
| `product.md` | Living product spec | Updated each pass to reflect what is currently implemented, not just planned |
| `context.md` | Session continuity log | Extended each pass with a new section; never overwrites history |
| `storyscenes-plan.md` | Feature planning doc | Written before implementation to scope the work; sub-task status updated inline |
| `PRESENTATION.md` | Academic presentation | Written by bobshell for a course/conference submission (commit `8dda5e3`) |
| `backend/signs/ATTRIBUTION.md` | License credits | Written at project init; lists dataset credits required by CC-BY-4.0 |
| `docs/` (this folder) | Consolidated docs | Generated by bobshell in this session, cross-referencing all prior docs against the actual codebase |

This very `docs/` folder is an example: bobshell read all 9 project `.md` files, cross-referenced them against the code, identified discrepancies, and produced three consolidated, accurate, source-of-truth documents.

---

## 8. Adding New Features Into the Existing Codebase Seamlessly

### Scene layer feature (feat/storyscenes)
When the storybook scene layer was requested, bobshell:

1. **Read the existing code** before planning — specifically `App.jsx` line references, `App.css` existing class names, `payload.py` model fields, and the backend `tokenize()` function.
2. **Designed for non-breaking extension**: `scene_idx` field added to `StoryToken` with a `default=0` so single-sentence stories and existing callers get a safe fallback; the `/api/tokenize` response shape is additive, not changed.
3. **Wrapped rather than rewriting**: the `tokenize()` function was refactored to call `segment_sentences()` and iterate segments, but the inner per-token loop body was left completely unchanged.
4. **Preserved the video element**: the plan explicitly called out that `.video-panel` internals and the `<video>` element were not to be modified, to avoid breaking the carefully debugged clip-swap behaviour.
5. **Derived state, not new state**: `activeSceneIdx` is derived inline from `activeIdx` — no new `useState`, no new `useEffect`. The scene layer adds no new async paths to `PlaybackScreen`.

### Independent sign/FS duration sliders (commit `aee46ef`)
The single `UNIT_DURATION_MS` constant was split into two independently-controllable React state values (`signDurationMs`, `fsDurationMs`) without changing the scheduler logic: `speakUnit()` reads `isSignVideo ? signDurationMs : fsDurationMs` from its closure. The change was additive to the existing control row.

---

## 9. Setting Up Data Pipelines and Build Scaffolding

### INCLUDE build pipeline (`build_sign_dictionary.py`)
bobshell wrote the full INCLUDE dataset build pipeline:
- Resumable Zenodo download with expected-size verification (Zenodo transfers drop mid-stream; the script checks byte count before treating a zip as complete).
- Custom extension detection for INCLUDE filenames like `"61. Summer"` where `Path.stem` would incorrectly strip the number.
- Category folder traversal to pick one representative clip per lemma.
- Atomic copy to `static/signs/<safe_lemma>.mp4`.
- `dictionary.json` written with normalized lowercase keys.

A collection of helper shell scripts (`_download_one.sh`, `_download_subset.sh`, `_resume_downloads.sh`, `_resume_parallel.sh`, `_keepalive.sh`) were also created to manage the slow, interruptible Zenodo download process over a session.

### Hemg fingerspelling pipeline (`build_fingerspelling_clips_from_hemg.py`)
The Hemg pipeline was designed to be a one-shot, idempotent build:
- Downloads a single Parquet file from HuggingFace.
- Reads 42,745 rows with `pyarrow`, picking the first representative row per class.
- Letterbox-pads each image to 320×320 with Pillow (pastel background).
- Encodes each as a 0.6 s h264 MP4 with `imageio[ffmpeg]`.
- Writes 26 letter clips and 9 digit clips.
- Idempotent: re-running overwrites existing clips without error.

---

## 10. Other Concrete AI-Assisted Development Instances

### Initial codebase audit
bobshell's first action was a full audit of the repo, identifying:
- Broken `/translate` endpoint referencing `isl_nlp.py` functions that had been removed.
- `words.txt` generated by scanning `static/signfiles/` — a folder that no longer existed.


This audit directly shaped the rebuild spec.

### Kid-friendly UX design
bobshell implemented the accessibility-first UX decisions throughout `App.jsx` and `App.css`:
- `u.rate = 0.9` — fixed TTS rate chosen for ages 4–10 (per `AGENTS.md` and code comment); not user-controllable.
- `u.pitch = 1.05` — slightly warmer voice.
- ≥56 px tap targets on all interactive elements.
- Pastel palette (no dark backgrounds, no harsh saturation) defined as CSS custom properties.
- Inline SVG mascot (happy / thinking moods) with no external asset dependency.
- `preload="auto"` on the `<video>` element — reduces first-frame latency on INCLUDE clips.


### Scene stub SVG generation
Rather than leaving the scene panel empty until real illustrations could be commissioned, bobshell generated 22 stub SVG files (`frontend/public/scenes/*.svg`) — pastel rounded-rect cards with an emoji and keyword label matching the app's chip style — so the feature was fully end-to-end testable immediately.

---

## Notes

- **All AI assistance described here used bobshell** as the primary tool.
- No LLM-generated code was committed without review; commit messages describe what changed and why at a technical level.
- The `AGENTS.md` file (project rules for the agent coding mode) was maintained throughout to capture non-obvious project patterns — preventing the AI from re-introducing known-bad patterns (e.g. re-enabling spaCy's parser, using `JSON.stringify` on `dictionary.json`, relying on `onboundary` for advance).
