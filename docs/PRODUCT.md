# Kahani — Product Feature Inventory

> **Audience:** Product owners, designers, new contributors.
> **Source of truth:** [`frontend/src/App.jsx`](../frontend/src/App.jsx), [`backend/main.py`](../backend/main.py), and [`backend/payload.py`](../backend/payload.py). Where old docs disagreed with code, code wins; discrepancies are noted at the bottom.

Kahani (Hindi for "story") is a kid-friendly browser-based read-along app that turns any children's story into a synchronized three-channel experience for hearing-impaired children:

1. **Story text** scrolls word by word with the current word highlighted.
2. **Indian Sign Language (ISL) video** plays for each word.
3. **Audio narration** (browser TTS) reads the story aloud.

---

## Module 1 — App Shell

### 1.1 Persistent Header
| Element | What it does |
|---|---|
| 🐰 brand mark (emoji) | Decorative; always visible at top left |
| **Kahani** brand name | Decorative; always visible |
| "Story time with signs" tagline | Decorative; always visible at top right |

The header uses `z-index: 10` so it always sits above the scene backdrop.

### 1.2 Persistent Footer
| Element | What it does |
|---|---|
| INCLUDE dataset credit link | Opens `zenodo.org/records/4010759` in a new tab; required by CC-BY-4.0 |
| CC-BY-4.0 license link | Opens Creative Commons page |
| "Kahani prototype · local dev only" notice | Status indicator |

**Status:** Working. Present on every screen.

---

## Module 2 — Upload Screen (`UploadScreen`)

Entry point. The user arrives here on first load and after pressing **New story** from Playback.

### 2.1 Mascot
- Inline SVG bunny mascot in **happy** mood (round eyes, rosy cheeks, lavender gradient).
- 110 px size on this screen.
- No interaction — purely decorative / welcoming.

### 2.2 Mode Toggle
Two toggle buttons side by side: **Upload file** and **Paste text**.

| Toggle | What it does |
|---|---|
| Upload file | Shows the drag-and-drop zone (default mode) |
| Paste text | Shows the textarea + "Read to me!" button |

Active mode is highlighted with a light lavender background and purple border.

### 2.3 File Upload Mode (`mode === 'upload'`)

#### Drop Zone
| Element | What it does |
|---|---|
| 📖 big emoji | Visual affordance; non-interactive |
| "Drag a story file here" | Hint text |
| **Choose a file** button (label wrapping `<input type="file">`) | Opens native OS file picker |
| File type hint: `.txt · .pdf · .docx` | Informational; shown below button |

- `accept=".txt,.md,.pdf,.docx"` — the OS picker filters to these types (`.md` is accepted by the backend as plain text).
- Drag-over visual: drop zone gains `dragover` CSS class (purple border).
- On drop or file pick: `POST /api/upload` (multipart). On success → Preview screen.

#### Upload Behaviour
- 5 MB upload limit enforced by the backend (returns HTTP 413 if exceeded).
- All parsing is in-memory; nothing is stored server-side.
- `busy` state: button becomes semi-transparent; "Getting the story ready…" message appears below.

### 2.4 Paste Text Mode (`mode === 'paste'`)

| Element | What it does |
|---|---|
| `<textarea>` (8 rows) | Multi-line text input; placeholder: "Paste your story here…" |
| **Read to me!** button | Disabled and semi-transparent until textarea has non-whitespace content |

- On click: `POST /api/tokenize` (JSON). On success → Preview screen.
- Button label changes to "Reading…" while the request is in flight.

### 2.5 Error Banner
- `⚠️ {error}` styled in a red-bordered card if the API call fails.
- Clears on next attempt.

**Preconditions:** None (entry screen).
**Status:** Working.

---

## Module 3 — Preview Screen (`PreviewScreen`)

Shown after a successful upload or text paste. Lets the user review the word list before committing to playback.

### 3.1 Story Title Bar
- Displays: "Ready to read: *{filename}*" where filename is either the uploaded file's name or "Pasted story".

### 3.2 Word Statistics Pills
Three summary pills in a row:

| Pill | What it shows |
|---|---|
| `{N} words` | Total token count |
| `{N} have sign videos` (green) | Tokens with a match in the dictionary |
| `{N} will be fingerspelled` (yellow if > 60% of total) | Tokens falling back to fingerspelling |

The "fingerspelled" pill turns yellow when more than 60% of words will be fingerspelled (expected for most stories, since the current dictionary has only 22 entries).

### 3.3 Word Inventory
A wrapping row of all tokens, each displayed as a small chip:

| Style | Meaning |
|---|---|
| Green chip (`.has-sign`) | Word has a dictionary sign video |
| Muted chip (`.fingerspell`) | Word will be fingerspelled |

Hovering a chip shows a tooltip: "Has a sign video" or "Will be fingerspelled letter by letter".

### 3.4 Actions
| Button | What it does |
|---|---|
| **▶ Play story** (primary, large) | Transitions to the Playback screen |
| **Pick a different story** (secondary) | Returns to the Upload screen (clears the current story) |

**Preconditions:** Requires a successfully parsed story.
**Status:** Working.

---

## Module 4 — Playback Screen (`PlaybackScreen`)

The core experience. Two-column layout (left: video + scene; right: text + controls).

### 4.1 Scene Backdrop (full-screen)
- A `position: fixed; z-index: 0` full-screen gradient div behind all panels.
- Gradient is determined by the **mood** of the current scene (sentence).
- Transitions with `transition: background 0.6s ease` — smoothly changes at each sentence boundary.
- 24 mood entries in [`moods.json`](../frontend/src/scenes/moods.json): morning, afternoon, evening, night, summer, spring, winter, fall, monsoon, season, forest, tree, river, sun, horse, mouse, animal, bird, flower, house, child, wind, and a `"default"` fallback (pink-sky gradient).
- Matching: iterates `moods.json` keys in order; first key found among the active scene's token lemmas wins; falls back to `"default"`.

**Status:** Working (implemented in `feat/storyscenes`, now current).

### 4.2 Left Column — `playback-left`

#### 4.2.1 Sign Video Panel (`.video-panel`)
| State | What is shown |
|---|---|
| Before pressing Play | Thinking-bunny mascot + "Press Play to begin" text |
| Playing a dictionary word | `<video>` element playing the INCLUDE clip for that lemma |
| Playing a fingerspelled word | `<video>` element playing the ISL alphabet/digit clip for the active letter |

- Video element: `autoPlay muted playsInline preload="auto"`, loops.
- Explicit `.src = …; .load(); .play()` is called on every unit transition (not relying on `<source>` swap alone).

#### Video Caption (below video)
- Bold display word (e.g. "horse").
- Label: "Fingerspelling…" or "Sign video".
- For fingerspelling tokens: a row of **letter chips**.

#### Letter Chip Row
Each character in the current word appears as a chip:

| Chip type | CSS class | Color | When active |
|---|---|---|---|
| Letter (a–z) | `.letter-chip.letter` | Pastel yellow (#fff4c2) | Scales up + drop shadow |
| Digit (0–9) | `.letter-chip.digit` | Pastel cyan | Scales up + drop shadow |

Active chip is the letter/digit currently being spoken and displayed.

#### 4.2.2 Scene Illustration Panel (`.scene-panel`)
- Shown below the sign video panel in the left column.
- Displays a keyword-matched SVG illustration for the current sentence/scene.
- 22 illustrations bundled in `frontend/public/scenes/` (stub SVGs — pastel rounded-rect cards with emoji + label).
- Matching: iterates [`illustrations.json`](../frontend/src/scenes/illustrations.json) keys in order against the current scene's lemma set; first match wins.
- Hold-previous: `lastIllustrationRef` — never shows blank; keeps last illustration until a new match is found.
- Before any token is active: shows thinking-bunny mascot.
- Shows "Scene N" label when a scene is active.

**Status:** Working (stub SVG illustrations; expandable with real artwork).

### 4.3 Right Column — Text Panel (`.text-panel`)

#### 4.3.1 Story Text Flow (`.text-flow`)
- All tokens rendered as inline `<span>` elements in source order.
- **Active word**: highlighted with `active` class (gradient underline, drop shadow, scale).
- **Past words**: opacity 0.55.
- **Future / unplayed words**: full opacity.
- Words are color-coded: `.sign-hit` (green tint) or `.fingerspell` (muted tint).

#### 4.3.2 Controls

| Control | Type | What it does |
|---|---|---|
| **▶ Play** | Button (large, green) | Starts playback from unit 0; shown when not playing |
| **⏸ Pause** | Button (large) | Cancels `cancelledRef`, cancels TTS, clears gap timer; shown while playing |
| **↻ Restart** | Button (large, orange/restart) | Cancels current playback, resets video element, starts fresh after 60ms |
| 🤟 Sign duration slider | Range input (1000–5000ms, step 500) | Sets `signDurationMs` — how long each sign-video unit is displayed (default 3500ms) |
| 🔡 Letter duration slider | Range input (500–1500ms, step 250) | Sets `fsDurationMs` — how long each fingerspell-letter unit is displayed (default 900ms) |
| **New story** | Alt-toggle button | Exits playback, clears story, returns to Upload screen |

Duration values are shown live in seconds next to each slider (e.g. "3.5s", "0.90s").

**Preconditions:** Requires a parsed story from Preview screen.
**Status:** Working.

---

## Module 5 — Sync Engine (internal, user-visible effects)

### 5.1 Per-Unit Utterance Scheduler
- Builds `spokenUnits[]` — one entry per spoken unit:
  - Sign-video tokens: one unit per word (`surface = display_word`)
  - Fingerspell tokens: one unit per character (`surface = "T"`, `"H"`, `"E"`, …)
- Each unit is spoken via `SpeechSynthesisUtterance`:
  - `rate = 0.9` (fixed; deliberate accessibility choice for ages 4–10)
  - `pitch = 1.05` (slightly warmer voice)
  - `lang = 'en-US'`
- On `onstart`: atomically sets `activeIdx` and `activeLetter` — text highlight, chip row, and video all update in lockstep.
- Advance is timer-driven only (`setTimeout`) — never reliant on `onend` or `<video>.onEnded` (documented to be unreliable in some browsers).

### 5.2 Timing
| Parameter | Default | Adjustable |
|---|---|---|
| Sign-video unit duration (`signDurationMs`) | 3500 ms | Yes (slider, 1000–5000 ms) |
| Fingerspell-letter unit duration (`fsDurationMs`) | 900 ms | Yes (slider, 500–1500 ms) |
| TTS utterance rate | 0.9× | No (fixed) |
| Post-roll hold after last unit | 700 ms | No (hardcoded `POST_ROLL_MS`) |

After the last unit, the final word/letter stays visible for 700 ms before the screen resets.

### 5.3 Scene Layer Derivation
- `activeSceneIdx` = `tokens[activeIdx].scene_idx` (inline, no extra state)
- `sceneL` (lemma set for scene) = `useMemo` over tokens sharing the same `scene_idx`
- Both illustration and mood use the same `sceneL` memo as input

---

## Module 6 — Fingerspelling Fallback

### 6.1 Coverage
- 26 ISL alphabet clips: `_letters/a.mp4` … `_letters/z.mp4`
- 9 ISL digit clips: `_digits/1.mp4` … `_digits/9.mp4`
- **No clip for digit 0** — stories containing `0` will get a 404 on that clip; other letters of the same word continue to work.

### 6.2 Clip Quality
- Real ISL hand signs from the Hemg/Indian_sign_language_dataset (HuggingFace).
- Each: 320×320 px, 0.6 s h264 single-frame looped MP4, letterboxed on a pastel background.
- Generated by [`backend/signs/build_fingerspelling_clips_from_hemg.py`](../backend/signs/build_fingerspelling_clips_from_hemg.py).

---

## Module 7 — Sign Dictionary

### 7.1 Current Entries (22 words from INCLUDE)
afternoon, animal, evening, fall, good evening, good night, horse, monsoon, morning, mouse, night, pleased, season, second, spring, summer, thank you, they, time, we, winter, you (plural).

### 7.2 Expansion
- Drop additional INCLUDE category zip files into `backend/.cache/include/`.
- Re-run `backend/signs/build_sign_dictionary.py`.
- **Restart** the backend (the dictionary is `lru_cache`d at startup).

---

## Module 8 — Backend API (developer-facing)

| Method | Path | Purpose | Auth |
|---|---|---|---|
| `GET` | `/healthz` | Liveness probe; returns `{"status":"ok"}` | None |
| `POST` | `/api/upload` | Multipart file upload (`.txt`/`.pdf`/`.docx`) → token list | None |
| `POST` | `/api/tokenize` | JSON `{"text":"…"}` → token list | None |
| `GET` | `/api/signs/{lemma}` | Single-lemma dictionary lookup | None |
| `GET` | `/static/signs/*.mp4` | Serves INCLUDE whole-word sign clips | None |
| `GET` | `/static/signs/_letters/*.mp4` | Serves Hemg alphabet clips | None |
| `GET` | `/static/signs/_digits/*.mp4` | Serves Hemg digit clips | None |

### Token Response Shape
```json
[
  {
    "display_word": "horse",
    "lemma": "horse",
    "sign_video": "/static/signs/horse.mp4",
    "is_fingerspelling": false,
    "scene_idx": 0
  }
]
```

---

## Non-Features (Explicitly Decided Out-of-Scope)

| Feature | Status |
|---|---|
| ISL → text (webcam gesture recognition) | **Removed.** Was in the original repo; deleted in the rebuild. |
| Multilingual / Hindi input | **Deferred.** `# TODO` comment left in `backend/main.py`. |
| User accounts / auth | **Out of scope.** Local-only prototype. |
| Cloud storage / analytics | **Out of scope.** No persistence, no telemetry. |
| ISL grammar reordering | **Removed.** Word order preserved = video and text always in sync. |
| SiGML/avatar rendering | **Removed.** Replaced with real video clips. |
| Mobile app | **Out of scope.** Web only (works on tablets). |
| Service worker / offline mode | **Not implemented.** |

---

## Known Limitations

| Issue | Impact | Mitigation |
|---|---|---|
| Dictionary has only 22 words | Most story words fall back to fingerspelling | By design; expandable via INCLUDE build script |
| No digit-0 clip | Stories with `0` get a 404 on that one clip | Word continues, other letters work |
| Safari TTS less reliable | `onstart` may fire late; letter-by-letter advance less crisp | Timer-driven advance still works; word is still spoken |
| Long INCLUDE clips (~11 MB, 1080p) | First-frame latency 100–500 ms | Acceptable for read-along cadence |
| CORS is open (`*`) | Development convenience; not production-safe | Lock down `allow_origins` before deploying |

---

## Notes / Discrepancies Found

1. **`frontend/README.md` (stale — sync mechanism description):** States "SpeechSynthesisUtterance.onboundary drives both the text highlight and the video swap" — this was the original design and was replaced by the per-unit utterance scheduler. The actual code in [`App.jsx`](../frontend/src/App.jsx) uses `onstart` per unit + `setTimeout` for advance, not `onboundary`. **Trust the code.**

2. **`RUN.md` references `build_fingerspelling_clips.py`** as generating "real ISL clips" (section 2, optional step) — in reality that script generates **placeholder pastel cards**. The real ISL clips come from `build_fingerspelling_clips_from_hemg.py`. **Trust the code/context.md.**

3. **`RUN.md` section 6** ("Processes that are still running") lists specific PIDs — this is a snapshot from a single session and is not generally applicable.

4. **`PRESENTATION.md` Slide 9** shows `UNIT_DURATION_MS = 1350` as the single timer value — the code now has two separate values: `signDurationMs` (default 3500 ms) and `fsDurationMs` (default 900 ms). **Trust the code.**

5. **`storyscenes-plan.md` Sub-Task 1** is marked `[ ] pending` but the implementation is **complete** in the current codebase (`segment_sentences()` in `main.py`, `scene_idx` in `payload.py`). Sub-Task 2 is `[x] done`. Sub-Task 3 is marked `[ ] pending` but is also **complete** in the current `App.jsx`. The plan doc is stale post-merge.

6. **`backend/signs/ATTRIBUTION.md`** credits spaCy for "sentence segmentation" — spaCy's sentence segmenter (parser) is deliberately disabled. Sentence segmentation is done by the custom `segment_sentences()` regex helper in `main.py`.
