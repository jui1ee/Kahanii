# Kahani — Frontend

React (Vite) UI for the Kahani read-along app.

## Run

```bash
npm install
npm run dev
```

Vite proxies `/api` and `/static` to the backend on `localhost:3002`
(see `vite.config.js`). If you need a different backend URL, set
`VITE_API_BASE` at build time.

## Build for production

```bash
npm run build
# outputs static assets in dist/
```

## Files

- `src/main.jsx` — entry point
- `src/App.jsx` — three screens: UploadScreen, PreviewScreen,
  PlaybackScreen + mascot SVG
- `src/App.css` — pastel kid-friendly styling
- `src/index.css` — global resets + typography
- `index.html` — root document (loads Fredoka + Quicksand fonts)

## Sync mechanism

`SpeechSynthesisUtterance.onboundary` drives both the text highlight
and the video swap in lock-step. There is no separate timer that can
drift away from the audio. See `PlaybackScreen` in `App.jsx` for the
binary-search mapping from `charIndex` → token index.

## Out of scope

- No analytics, no telemetry, no auth.
- No service worker / offline mode yet.