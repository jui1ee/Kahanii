# Storybook Scene Layer — Implementation Plan

## Overview

Add two synchronized scene-level features to Kahani's playback screen:

1. **Scene illustrations** — show a matched SVG illustration during each sentence-level scene
2. **Mood backdrop** — animate a full-screen gradient behind `PlaybackScreen` as scenes change

Both features are scene-boundary-driven (not per-word). The backend derives scene boundaries
via a new `segment_sentences()` helper and stamps each `StoryToken` with a `scene_idx` field.
The frontend derives `activeSceneIdx` reactively from `activeIdx` — no changes to the
timer loop, video reuse, or Safari TTS workaround logic.

---

## Unchanged Invariants

- `UNIT_DURATION_MS` timer loop: untouched
- Single `<video>` element reuse with explicit `.src` / `.load()` / `.play()`: untouched
- Safari TTS workaround (timer-driven, not `onboundary`/`onended`): untouched
- `lru_cache` singleton loaders: untouched
- Existing `/api/tokenize` and `/api/upload` response shape is extended (additive), not changed

---

## Sub-Task 1 — Backend: `segment_sentences()` + `scene_idx` on `StoryToken`

**Intent**
Add sentence-boundary detection to the backend pipeline without enabling spaCy's `parser`.
Each `StoryToken` gains a `scene_idx: int` field (0-based) derived before the sign-lookup pass.

**Approach**
A pure-Python regex helper `segment_sentences(text: str) -> list[str]` splits on sentence
terminals (`. `, `? `, `! `, and end-of-string variants), with a simple abbreviation guard
(don't split after a single uppercase letter like "Mr.", "Dr.", "U.S."). The text is split
into sentence strings first; then `tokenize()` iterates over those segments, assigning the
same `scene_idx` to all tokens produced from the same segment.

**`segment_sentences()` rules**
- Split on `[.?!]` followed by whitespace or end-of-string
- Abbreviation guard: don't split when the period is preceded by a single capital letter
  (`[A-Z]\.`) — covers "Mr.", "Dr.", "U.", etc.
- Empty segments after strip are discarded
- Returns list of sentence strings in original order

**`StoryToken` change**
Add `scene_idx: int = Field(0, ...)` to `backend/payload.py`. Default 0 means
single-sentence stories and old callers get a safe fallback.

**`tokenize()` refactor**
Wrap the existing loop: for each segment string from `segment_sentences(text)`, run the
same spaCy loop, appending tokens with the current `scene_idx`. The inner loop body
(lemma extraction, skip logic, `attach_sign_video`) is unchanged.

**Expected Outcomes**
- `GET /api/tokenize` with multi-sentence input returns tokens where `scene_idx` increments
  at each sentence boundary
- Smoke test: `{"text": "The horse ran. The mouse hid."}` → first 3 tokens have
  `scene_idx: 0`, next 3 have `scene_idx: 1`
- Single-sentence input: all tokens have `scene_idx: 0`

**Todo List**
- [ ] Add `scene_idx: int = Field(0, description="0-based sentence/scene index.")` to
      `StoryToken` in `backend/payload.py`
- [ ] Implement `segment_sentences(text: str) -> list[str]` in `backend/main.py` above
      `tokenize()`. Use `re.split` with a lookbehind that excludes single-capital-letter
      abbreviations.
- [ ] Refactor `tokenize(text)` to call `segment_sentences(text)`, iterate over segments,
      run the existing per-token spaCy loop per segment, and pass `scene_idx=i` when
      constructing each `StoryToken`. Keep `attach_sign_video()` call at the end over the
      full list (no change there).
- [ ] Smoke-test the endpoint manually with a two-sentence input

**Relevant Context**
- `backend/payload.py` lines 5–16 — `StoryToken` model
- `backend/main.py` lines 128–171 — `_SKIP_LEMMAS`, `_PUNCT_ONLY`, `tokenize()`
- Punctuation tokens (`.`, `?`, `!`) are already filtered by `_PUNCT_ONLY` — they never
  reach the frontend, so boundary markers must come from the backend

**Status** `[ ] pending`

---

## Sub-Task 2 — Static data: `illustrations.json`, `moods.json`, stub SVG files

**Intent**
Create the two lookup tables and a set of stub SVG illustration files that let the feature
run end-to-end before real art is available.

**`frontend/src/scenes/illustrations.json` structure**
```json
{
  "horse": "/scenes/horse.svg",
  "mouse": "/scenes/mouse.svg",
  "morning": "/scenes/morning.svg",
  "night": "/scenes/night.svg",
  "forest": "/scenes/forest.svg",
  "animal": "/scenes/animal.svg"
}
```
Keys are lemmas (matching `StoryToken.lemma`). Values are paths under `frontend/public/`
(Vite serves `public/` as the static root at `/`). The set of initial entries should cover
the lemmas already in `signs/dictionary.json` (horse, mouse, morning, night, animal,
seasonal words) plus a small set of common storybook nouns.

**`frontend/src/scenes/moods.json` structure**
```json
{
  "morning":  { "gradient": "linear-gradient(135deg, #fff9c4, #ffe082)", "accentColor": "#f9a825" },
  "night":    { "gradient": "linear-gradient(135deg, #1a237e, #283593)", "accentColor": "#7986cb" },
  "forest":   { "gradient": "linear-gradient(135deg, #c8e6c9, #a5d6a7)", "accentColor": "#388e3c" },
  "horse":    { "gradient": "linear-gradient(135deg, #ffe0b2, #ffcc80)", "accentColor": "#ef6c00" },
  "default":  { "gradient": "linear-gradient(135deg, #ffd6e7, #c7e9ff)", "accentColor": "#a78bd9" }
}
```
A `"default"` key is always present as the fallback (used on first scene / no match).
Matching: iterate `moods.json` keys in order; first key found among scene lemmas wins.
If no keyword matches, use `"default"`.

**Stub SVG format**
Pastel rounded-rect card with centred keyword label. Each SVG is ~20 lines, self-contained,
no external dependencies. Example for `horse.svg`:
```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 240 240">
  <rect width="240" height="240" rx="32" fill="#ffe0b2"/>
  <text x="120" y="130" text-anchor="middle" font-family="sans-serif"
        font-size="28" font-weight="bold" fill="#ef6c00">🐴 horse</text>
</svg>
```
Emoji + label, matching the pastel chip style already used for fingerspelling cards.

**Files to create**
- `frontend/src/scenes/illustrations.json`
- `frontend/src/scenes/moods.json`
- `frontend/public/scenes/<keyword>.svg` — one per key in `illustrations.json`

**Expected Outcomes**
- Importing `illustrations.json` in JSX resolves without error
- Fetching `/scenes/horse.svg` in the browser returns the stub SVG

**Todo List**
- [ ] Create `frontend/src/scenes/illustrations.json` with lemma → `/scenes/<lemma>.svg`
      entries for all lemmas in `signs/dictionary.json` plus ~8 common storybook nouns
      (sun, tree, house, river, child, bird, flower, wind)
- [ ] Create `frontend/src/scenes/moods.json` with gradient/accentColor entries for the
      same set of keywords, plus a `"default"` entry
- [ ] Create `frontend/public/scenes/` directory and generate one stub SVG per key

**Relevant Context**
- `backend/signs/dictionary.json` — lemma list to seed initial coverage
- Fingerspelling chip style (`letter-chip`, `#fff4c2`, `font-family: Fredoka`) in
  `frontend/src/App.css` lines 395–418 — visual reference for stub SVG palette

**Status** `[x] done`

---

## Sub-Task 3 — Frontend: `activeSceneIdx`, illustration panel, mood backdrop

**Intent**
Wire `scene_idx` from tokens into a derived `activeSceneIdx` state. Add a dedicated
illustration panel beside the sign-video panel. Apply the matched mood gradient as a
full-screen backdrop. No changes to the timer loop, the video element, or `.video-panel`.

**Layout change: two columns, left column stacked**

The existing `.playback` flex row gains a `<div className="playback-left">` wrapper
around `.video-panel` and the new `.scene-panel`. The right column (`.text-panel`)
is completely unchanged in markup and CSS.

Wide (≥ 820px):
```
┌──────────────────────┬──────────────────────────────────┐
│  .video-panel        │  .text-panel  (unchanged)        │
│  [sign video]        │  [word highlight + controls]     │
├──────────────────────┤                                  │
│  .scene-panel        │                                  │
│  [illustration]      │                                  │
└──────────────────────┴──────────────────────────────────┘
```

Narrow (< 820px) — existing `flex-direction: column` breakpoint at 820px already
stacks everything in DOM order: `.playback-left` (which contains `.video-panel` then
`.scene-panel`), then `.text-panel`. No new breakpoint needed.

**New CSS**
```css
/* Left column wrapper — stacks sign and scene panels */
.playback-left {
  flex: 0.9;
  display: flex;
  flex-direction: column;
  gap: 24px;
}

/* Illustration panel — same card style as video-panel */
.scene-panel {
  background: white;
  border-radius: 32px;
  padding: 28px;
  box-shadow: 0 12px 40px rgba(167, 139, 217, 0.18);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 200px;
}

/* Illustration image inside the panel */
.scene-illustration {
  width: 100%;
  max-width: 280px;
  aspect-ratio: 1 / 1;
  border-radius: 20px;
  object-fit: contain;
}

/* Backdrop — full-screen, behind everything */
.scene-backdrop {
  position: fixed;
  inset: 0;
  z-index: 0;
  transition: background 0.6s ease;
  pointer-events: none;
}
```

The `.video-panel` CSS (lines 309–317) is not modified — its `flex: 0.9` moves to
`.playback-left`, but the panel's own styles are untouched.

**JSX structure change (playback layout only)**
```jsx
<div className="playback">
  <div className="playback-left">
    <div className="video-panel"> {/* unchanged internals */} </div>
    <div className="scene-panel">
      {illustrationSrc
        ? <img className="scene-illustration" src={illustrationSrc} alt="scene illustration" />
        : <Mascot small mood="thinking" />}
      {activeSceneIdx !== null && (
        <div className="video-caption" style={{ marginTop: 10 }}>Scene {activeSceneIdx + 1}</div>
      )}
    </div>
  </div>
  <div className="text-panel"> {/* completely unchanged */} </div>
</div>
```

**`activeSceneIdx` derivation**
```js
const activeSceneIdx = activeIdx >= 0 ? tokens[activeIdx].scene_idx : null
```
Plain derived value — no `useState`, no `useEffect`. Recalculated on every render from
the existing `activeIdx` state.

**Illustration matching**
`useMemo` keyed on `[activeSceneIdx, tokens]`:
1. Collect the unique lemma set for all tokens where `scene_idx === activeSceneIdx`
2. Iterate `Object.keys(illustrations)` in dictionary order
3. Return the first path whose key is in the lemma set, or `null`

`lastIllustrationRef` (a `useRef`) holds the previous non-null result so the panel
never goes blank if the new scene has no match.

**Mood backdrop**
`useMemo` keyed on `[activeSceneIdx, tokens]`, same lookup pattern against `moods.json`.
Falls back to `moods["default"]` when no key matches.

Rendered as the first child of the outer `.screen` div:
```jsx
<div className="screen">
  <div className="scene-backdrop" style={{ background: activeMood.gradient }} />
  <div className="playback"> ... </div>
</div>
```

The `.app-header` has `z-index: 10`; the backdrop has `z-index: 0`. All panel cards
have white backgrounds, so they sit visually above the backdrop with no z-index changes.

**Import changes in `App.jsx`**
```js
import illustrations from './scenes/illustrations.json'
import moods from './scenes/moods.json'
```

**Expected Outcomes**
- Wide viewport: three visible zones — sign/fingerspelling panel, illustration panel,
  text+controls — left two stacked vertically, right column full height
- Narrow viewport: single-column stack, illustration appears between sign panel and text
- Playing a two-scene story: backdrop gradient transitions at the sentence boundary,
  illustration swaps; word highlight and video continue at per-word cadence unchanged
- Before play: illustration panel shows the thinking-bunny mascot; backdrop shows `"default"` gradient
- `npm run lint` passes

**Todo List**
- [ ] Add `import illustrations from './scenes/illustrations.json'` and
      `import moods from './scenes/moods.json'` at the top of `App.jsx`
- [ ] Remove `flex: 0.9` from `.video-panel` CSS (it moves to `.playback-left`)
- [ ] Add `.playback-left`, `.scene-panel`, `.scene-illustration`, `.scene-backdrop`
      CSS rules to `App.css`
- [ ] Wrap `.video-panel` in `<div className="playback-left">` in `PlaybackScreen` JSX,
      add `.scene-panel` as second child of that wrapper
- [ ] Derive `activeSceneIdx` inline in `PlaybackScreen`
- [ ] Add `illustrationSrc` `useMemo` and `lastIllustrationRef` hold-previous logic
- [ ] Add `activeMood` `useMemo` with `moods["default"]` fallback
- [ ] Add `.scene-backdrop` div as first child of the `.screen` div in `PlaybackScreen`
- [ ] Verify: `.video-panel` internals (video element, caption, letter chips) untouched;
      header `z-index: 10` still above backdrop `z-index: 0`

**Relevant Context**
- `frontend/src/App.jsx` lines 276–649 — `PlaybackScreen` component
- `frontend/src/App.jsx` lines 336–352 — `spokenUnits` memo (not modified)
- `frontend/src/App.jsx` lines 397–471 — `playFromStart` / `speakUnit` (not modified)
- `frontend/src/App.jsx` lines 549–648 — `PlaybackScreen` return JSX (layout changes here)
- `frontend/src/App.css` lines 17–28 — `.app-header` with `z-index: 10`
- `frontend/src/App.css` lines 283–317 — `.playback`, `.video-panel` (move `flex: 0.9`
  from `.video-panel` to new `.playback-left`)

**Status** `[ ] pending`

---

## File Change Summary

| File | Change |
|---|---|
| `backend/payload.py` | Add `scene_idx: int = Field(0, ...)` to `StoryToken` |
| `backend/main.py` | Add `segment_sentences()`, refactor `tokenize()` to iterate segments |
| `frontend/src/scenes/illustrations.json` | New — lemma → SVG path map |
| `frontend/src/scenes/moods.json` | New — keyword → {gradient, accentColor} map |
| `frontend/public/scenes/*.svg` | New — one stub SVG per key in illustrations.json |
| `frontend/src/App.jsx` | Add imports; wrap `.video-panel` in `.playback-left`; add `.scene-panel`; add `activeSceneIdx`, `illustrationSrc` memo, `activeMood` memo, backdrop div |
| `frontend/src/App.css` | Move `flex: 0.9` from `.video-panel` to new `.playback-left`; add `.playback-left`, `.scene-panel`, `.scene-illustration`, `.scene-backdrop` rules |

No changes to:
- `vite.config.js` (no new backend paths — JSON is bundled, SVGs served from `public/`)
- `backend/signs/` or `backend/static/` (no new sign assets)
- `.video-panel` internals (video element, letter chips, caption) — untouched
- The timer loop, `speakUnit`, `gapTimerRef`, `cancelledRef`, `UNIT_DURATION_MS` — untouched
- The `<video>` element reuse pattern — untouched
