# Kahani — Backend

FastAPI service for the Kahani read-along app.

## Endpoints

| Method | Path                | Purpose                                                         |
|--------|---------------------|-----------------------------------------------------------------|
| GET    | `/healthz`          | Liveness probe                                                  |
| POST   | `/api/upload`       | Multipart upload (.txt/.pdf/.docx) → ordered token JSON         |
| POST   | `/api/tokenize`     | JSON `{ "text": "..." }` → ordered token JSON                   |
| GET    | `/api/signs/{lemma}`| Lookup one lemma in the dictionary                              |
| GET    | `/static/signs/...` | Sign video clips + per-letter fingerspelling clips              |

## Request shape (both tokenize endpoints)

```json
[
  { "display_word": "The",  "lemma": "the",  "sign_video": null,                 "is_fingerspelling": true  },
  { "display_word": "cat",  "lemma": "cat",  "sign_video": "/static/signs/cat.mp4", "is_fingerspelling": false }
]
```

Word order is preserved exactly as in the source. No reordering.

## One-time setup

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python -m spacy download en_core_web_sm
.venv/bin/python signs/build_fingerspelling_clips.py     # generates letter clips
.venv/bin/python signs/build_sign_dictionary.py          # downloads INCLUDE subset
```

`build_sign_dictionary.py` writes:
- `static/signs/<lemma>.mp4` — one clip per word
- `signs/dictionary.json` — lemma → filename map

## Run

```bash
.venv/bin/python main.py
# default port 3002, override with PORT env var
```

## Notes

- spaCy is loaded **once** (LRU cache) and used only for tokenization
  and lemmatization. No parsing, no reordering.
- `tokenize()` is pure — same input → same output, no shared state,
  safe under concurrent requests.
- All file parsing happens in-memory; uploads are not persisted.
- 5 MB upload limit. Children's stories are tiny; this just stops
  abuse.