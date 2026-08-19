# How to Run Kahani

## TL;DR

```bash
# Terminal 1 — backend
cd backend
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python -m spacy download en_core_web_sm
.venv/bin/python main.py                # serves on :3002

# Terminal 2 — frontend
cd frontend
npm install
npm run dev                             # serves on :5173
```

Open <http://localhost:5173/> in your browser.

Vite proxies `/api` and `/static` to the backend, so the React dev server works with no CORS or absolute-URL config.

---

## 1. Prerequisites

- **Linux or WSL** (Windows-native should also work, paths differ)
- **Python 3.10+** (tested on 3.12)
- **Node.js 18+** (tested on 22.x) and **npm**
- **Internet access** — to fetch spaCy model + INCLUDE dataset
- **~10 GB free disk** if you also download the full INCLUDE subset (only ~5 MB if you skip the dataset and use fingerspelling only)

---

## 2. Backend setup

### One-time install

```bash
cd backend
python3 -m venv .venv
.venv/bin/pip install --upgrade pip
.venv/bin/pip install -r requirements.txt
.venv/bin/python -m spacy download en_core_web_sm
```

`requirements.txt`:
```
fastapi==0.115.6
uvicorn[standard]==0.32.1
pydantic==2.10.3
spacy==3.8.3
pypdf==5.1.0
python-docx==1.1.2
python-multipart==0.0.20
```

### Optional: sign dictionary + fingerspelling clips

The app works without these — every word falls back to letter-by-letter fingerspelling using placeholder pastel cards. To add real ISL clips:

```bash
# Generate 26 letter clips (placeholder pastel cards with the letter)
.venv/bin/python signs/build_fingerspelling_clips.py

# Download INCLUDE subset and build the dictionary (~6 GB, 30-90 min)
.venv/bin/python signs/build_sign_dictionary.py
```

`build_sign_dictionary.py` writes:
- `signs/dictionary.json` — lemma → filename map (currently 22 entries)
- `static/signs/*.mp4` — one clip per lemma

To add more words later, drop more INCLUDE categories into `.cache/include/` and re-run the script.

### Run

```bash
.venv/bin/python main.py
```

Default port 3002. Override with `PORT=8080 .venv/bin/python main.py`.

You should see:
```
INFO:     Started server process [NNNN]
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:3002 (Press CTRL+C to quit)
```

Health check:
```bash
curl http://127.0.0.1:3002/healthz
# {"status":"ok"}
```

---

## 3. Frontend setup

### One-time install

```bash
cd frontend
npm install
```

### Run

```bash
npm run dev
```

Default port 5173. Override with `npm run dev -- --port 3000`.

You should see:
```
  VITE v8.2.1  ready in 267 ms
  ➜  Local:   http://localhost:5173/
  ➜  Network: http://10.x.x.x:5173/
```

### Build for production

```bash
npm run build
# Outputs static assets in dist/
```

The Vite proxy in `vite.config.js` forwards `/api` and `/static` to the backend during dev. For production, set `VITE_API_BASE` at build time:

```bash
VITE_API_BASE=https://api.kahani.example.com npm run build
```

---

## 4. End-to-end smoke test

```bash
# Backend healthy?
curl http://127.0.0.1:3002/healthz
# {"status":"ok"}

# Tokenize a phrase
curl -X POST -H 'Content-Type: application/json' \
  -d '{"text":"The horse ran in the morning."}' \
  http://127.0.0.1:3002/api/tokenize

# Look up a sign
curl http://127.0.0.1:3002/api/signs/summer
# {"lemma":"summer","found":true,"fingerspell":false,"video":"/static/signs/summer.mp4"}

# Verify a sign video actually serves
curl -o /dev/null -w "%{http_code}\n" http://127.0.0.1:3002/static/signs/summer.mp4
# 200
```

In the browser, you should see:
- Upload screen with bunny mascot, drag-and-drop, "Choose a file" button
- After uploading/pasting → preview screen with word inventory
- After clicking Play → playback screen with text highlight, video panel, controls

---

## 5. Production deployment (production-style)

Build the frontend for static serving:

```bash
cd frontend && npm run build
```

Serve `frontend/dist/` via any HTTP server (nginx, Caddy, S3+CloudFront, etc.). Point the frontend at your backend with `VITE_API_BASE` at build time.

Minimal nginx config:

```nginx
server {
  listen 80;
  server_name kahani.example.com;
  root /var/www/kahani/dist;
  index index.html;

  # SPA fallback
  location / { try_files $uri /index.html; }

  # Proxy API + static assets to backend
  location /api/    { proxy_pass http://127.0.0.1:3002; }
  location /static/ { proxy_pass http://127.0.0.1:3002; }
}
```

Run the backend with a production server (not Flask's debug mode):

```bash
cd backend
.venv/bin/uvicorn main:app --host 0.0.0.0 --port 3002 --workers 4
```

Or behind gunicorn:
```bash
.venv/bin/pip install gunicorn
.venv/bin/gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:3002
```

---

## 6. Processes that are still running

If the app is currently running on this machine:

```
Backend:  PID 13962  on :3002  (.venv/bin/python main.py)
Frontend: PID 5798   on :5173  (vite)
Keepalive: PID 9638  pings every 4 minutes
```

To stop the keepalive: `touch /tmp/keepalive.stop`

To kill the backend/frontend, find the PIDs with `ps -ef | grep -E "python.*main.py|vite"` and `kill <pid>`.

---

## 7. Troubleshooting

**`spacy.load('en_core_web_sm')` raises OSError**
Run `.venv/bin/python -m spacy download en_core_web_sm` again.

**`/api/upload` returns 413 on a story file**
Upload limit is 5 MB. Most children's stories fit easily; this just stops abuse.

**Browser shows sign videos that don't load**
Check that `.venv/bin/python main.py` is running (`curl http://127.0.0.1:3002/healthz`). If down, restart it. Note: `get_sign_dict()` is `lru_cache`d at backend startup, so after rebuilding `signs/dictionary.json` you must restart the backend process.

**Video doesn't sync with audio**
Make sure you're using Chrome or Edge. Safari fires `onboundary` only at sentence boundaries, not per-word — see the note in `frontend/README.md` for the pre-computed-timestamps fallback.

**Every word falls back to fingerspelling**
The dictionary is sparse (22 entries from a partial INCLUDE download). To grow it, run `.venv/bin/python signs/build_sign_dictionary.py` after adding more INCLUDE zip files to `.cache/include/`. See `context.md` for the download saga.

**Backend lru_cache doesn't see new dictionary**
`get_sign_dict()` caches the first read of `signs/dictionary.json`. Restart the backend process after any dictionary rebuild.

---

## 8. File layout

```
backend/
  main.py                  FastAPI app
  payload.py               Pydantic models
  requirements.txt
  .venv/                   Python venv (gitignored)
  signs/
    build_sign_dictionary.py
    build_fingerspelling_clips.py
    dictionary.json        (generated, 22 entries)
    ATTRIBUTION.md
  static/signs/            Served at /static/signs/
    *.mp4                  Curated INCLUDE clips
    _letters/*.mp4         Fingerspelling clips (a.mp4 ... z.mp4)
  .cache/include/          Downloaded INCLUDE zips (gitignored)

frontend/
  src/
    App.jsx                Three screens + mascot
    App.css                Pastel styling
    index.css              Global resets + typography
  index.html
  vite.config.js           Dev-server proxy config
  package.json

context.md                  Build session log
product.md                  Product spec
RUN.md                      This file
```

---

## 9. Quick reference

| Need | Command |
|---|---|
| Start backend | `cd backend && .venv/bin/python main.py` |
| Start frontend | `cd frontend && npm run dev` |
| Test backend | `curl http://127.0.0.1:3002/healthz` |
| Restart after dictionary change | kill backend process, re-run `cd backend && .venv/bin/python main.py` |
| Add more sign words | drop more INCLUDE zips into `backend/.cache/include/`, then `cd backend && .venv/bin/python signs/build_sign_dictionary.py` |
| Stop everything | `pkill -f "python.*main.py"; pkill -f vite` |
| Build production frontend | `cd frontend && npm run build` |
| Run production backend | `cd backend && .venv/bin/uvicorn main:app --workers 4` |