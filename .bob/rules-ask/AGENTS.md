# Ask Mode Context

## Non-Obvious Documentation Notes

- **`context.md`** (root) is a raw build session log, not product docs — it documents the INCLUDE dataset download saga and is the canonical record of why certain architectural decisions were made.
- **`product.md`** (root) is the product spec / design brief, not a README — check here first for intent behind UI choices.
- **`backend/signs/`** contains multiple overlapping build scripts (`_auto_build_dict.py`, `build_sign_dictionary_extend.py`, etc.) that are historical artifacts from iterative INCLUDE downloads — `build_sign_dictionary.py` is the canonical one.
- **Sign video files are NOT in the repo** — `backend/static/signs/` is gitignored. The app works without them (falls back to fingerspelling cards) but actual ISL sign videos require running the build scripts.
- **The INCLUDE dataset** (Zenodo 4010759) is CC-BY-4.0 and credited in the app footer. Only ~22 categories are downloaded by default out of ~50+ available.
