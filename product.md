# Kahani — Product

A kid-friendly web app that turns any children's story into a synchronized read-along experience for hearing-impaired children.

## The promise

A parent or teacher uploads a story (`.txt` / `.pdf` / `.docx`). The child watches a friendly bunny mascot play the story back with three things happening in lockstep:

1. **The story text scrolls word by word**, with the current word highlighted in a pastel gradient
2. **An Indian Sign Language (ISL) video** plays for that word — a real human signing
3. **Audio narration** reads the story aloud via browser text-to-speech

When a word has no sign video, the UI falls back to **letter-by-letter fingerspelling** so the child never sees a blank screen. The fallback is the load-bearing feature, not a nice-to-have.

## Who it's for

- **Primary**: hearing-impaired children (ages 4-10) learning to read with sign support
- **Secondary**: parents/teachers preparing a story session
- **Tertiary**: deaf schools that need a quick way to convert any printed story into signed narration

## Core features

### Upload & parse
- Drag-and-drop or click-to-pick file upload
- Paste text as an alternative input
- Supports `.txt`, `.pdf`, `.docx`
- 5 MB upload limit (plenty for any children's story)
- Server-side text extraction with `pypdf` (PDF) and `python-docx` (DOCX)
- All parsing happens in-memory, nothing is persisted

### Read-along playback
- Three screens: upload → preview → play
- **Word-by-word text highlight** — past words fade to 55% opacity, active word is gradient-scaled with a drop shadow
- **Synchronized audio** — browser's `SpeechSynthesisUtterance` reads the story
- **Word-by-word video** — the ISL clip matches the audio word-by-word
- **Single timing source** — `onboundary` event drives both text and video simultaneously. No drift between audio and video, ever.
- **Pause / Restart** controls
- **Speed toggle** — Slow (0.8×) for kids still learning to read; Normal (1.0×) for everyone else

### Sign video dictionary
- 22 real INCLUDE sign video clips serving right now (animal, mouse, horse, we, they, you, good evening, good night, thank you, pleased, morning, afternoon, evening, night, time, second, summer, spring, winter, fall, monsoon, season)
- CC-BY-4.0 licensed, credited in the app footer
- Designed to grow — dropping more INCLUDE data into `static/signs/` instantly adds words to the dictionary

### Fingerspelling fallback
- Letter-by-letter playback for any word not in the dictionary
- Active letter highlighted as a chip below the video
- Per-letter pastel cards (placeholder for real ISL alphabet — highest-value follow-up)

### Kid-friendly UX
- **Pastel palette** — pink, sky, mint, yellow, lavender. Never harsh or saturated.
- **Rounded everything** — 12-32px border radius, no sharp corners
- **Bunny mascot** — happy on upload, thinking in empty states
- **Big tap targets** — ≥56px, works on tablets
- **One clear action per screen** — upload → preview → play
- **Large readable story text** — 28px, generous line spacing
- **No dark theme**
- **Disabled state** on action buttons until input is present
- **Friendly error messages** with visual cues

### Accessibility
- Speech synthesis uses slightly higher pitch (1.05) so narration feels less robotic
- All controls reachable via keyboard
- ARIA labels on icon-only buttons
- `<noscript>` fallback would be trivial to add (full SPA blocks without JS)

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│  Browser (React + Vite)                                         │
│  ├─ UploadScreen → PreviewScreen → PlaybackScreen               │
│  └─ PlaybackScreen:                                              │
│     SpeechSynthesisUtterance.onboundary (single timing source) │
│       ├─ text highlight (binary-search charIndex → token)       │
│       ├─ video swap (token.sign_video)                          │
│       └─ fingerspell letters (token.is_fingerspelling)         │
└─────────────────────────────────────────────────────────────────┘
                            │ HTTP
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│  FastAPI (Python 3.12)                            port :3002    │
│  ├─ POST /api/upload   (multipart file → token JSON)           │
│  ├─ POST /api/tokenize  (raw text → token JSON)                │
│  ├─ GET  /api/signs/{lemma}                                     │
│  ├─ GET  /static/signs/...                                      │
│  └─ spaCy en_core_web_sm: tokenize + lemmatize ONLY             │
│       (parser, tagger, NER disabled — pure function)           │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│  Data                                                            │
│  ├─ signs/dictionary.json (22 lemma → video-filename entries)   │
│  ├─ static/signs/*.mp4 (curated INCLUDE clips)                  │
│  └─ static/signs/_letters/*.mp4 (fingerspelling clips)          │
└─────────────────────────────────────────────────────────────────┘
```

## Tech stack

| Layer | Tech | Why |
|---|---|---|
| Backend | Python 3.12, FastAPI 0.115, uvicorn | Async-friendly, fast, OpenAPI built-in |
| NLP | spaCy 3.8 + en_core_web_sm | Tokenize + lemmatize only — no parser, no reordering |
| File parsing | pypdf 5.1, python-docx 1.1 | Industry-standard, no system deps |
| Validation | pydantic 2.10 | Type-safe request/response |
| Frontend | React 19, Vite 8 | Fast HMR, no build step needed in dev |
| Sync | Web Speech API (`SpeechSynthesisUtterance`) | Built into every browser, no external dep |
| Typography | Fredoka + Quicksand (Google Fonts) | Rounded friendly sans |
| Mascot | Inline SVG | No asset deps, scales with the UI |
| Data | INCLUDE dataset (Zenodo 4010759, CC-BY-4.0) | Real ISL video, openly licensed |

## What makes the sync work

The classic three-channel sync problem (text + audio + video) usually drifts because each channel has its own timer. Kahani solves it by using **one source of truth**:

1. Build a `SpeechSynthesisUtterance` from `tokens.map(t => t.display_word).join(' ')`
2. The browser fires `onboundary(charIndex)` for every word boundary
3. Map `charIndex` → token index via binary search (token offsets pre-computed once)
4. On change of token index, atomically update:
   - Text highlight (active word gets gradient + scale)
   - Video `<source>` (token's `sign_video` or per-letter finger clips)
   - Letters chips (active letter in the fingerspelling sequence)

There is no separate timer. There is no drift. The audio IS the timeline.

## Upgrade paths

### Easy (next sprint)
- Add the remaining INCLUDE halves (Animals_1of2, Greetings_1of2, Colours_1of2, Pronouns_1of2, Days_and_Time_1of3 + 2of3) — 5-7 GB more downloads, ~100 more dictionary entries
- Replace placeholder fingerspelling clips with real ISL alphabet footage from `Hemg/Indian_sign_language_dataset` (HuggingFace, 292MB, 35 alphabet classes)
- Smart clip selection: instead of "first file wins", inspect frames for open eyes + sign in frame + no blur
- Hot-reload dictionary: file-watch on `signs/dictionary.json` to invalidate the lru_cache without backend restart

### Medium
- Safari onboundary fallback: pre-compute per-word timestamps from `utterance.rate` and `text.length`
- Per-content-word dictionary expansion: scrape, with permission, additional ISL resources (Indian government ISL data, AI4Bharat extensions)
- Story library for parents/teachers: pre-loaded stories so the upload step is optional
- Slow/normal speed toggle: intermediate levels (0.6, 0.7, 0.9, 1.0, 1.1, 1.2)

### Hard
- Real-time AI-generated sign avatar for any word (out of scope, but architecturally possible: generate per-word video on demand, cache)
- Two-handed ISL signs (current dict is single-hand)
- Continuous fingerspelling (auto-advance per real letter, not per fixed-duration)
- Multi-language support: Hindi input → English translation → ISL (deferred per spec)

## Non-features (decided)

- **No accounts, no auth** — local-only prototype
- **No cloud storage** — uploads are in-memory, never persisted
- **No analytics** — no telemetry, no tracking
- **No mobile app** — web only, but works on tablets
- **No ISL→text gesture recognition** — explicitly out of scope
- **No multilingual input** — English only in this pass
- **No ISL grammar reordering** — word order preserved so the video references the right word
- **No SiGML/avatar rendering** — replaced with real video clips

## License

- **Code**: see LICENSE (project default)
- **Sign clips**: CC-BY-4.0 (INCLUDE dataset, Sridhar et al., ACM MM 2020)
- **spaCy model**: MIT
- **App**: prototype, no production deployment yet
