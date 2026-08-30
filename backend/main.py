"""
Kahani — Story to Indian Sign Language playback backend.

Endpoints
---------
POST /api/upload
    Accept a multipart file upload (.txt / .pdf / .docx). Extracts plain
    text, runs spaCy tokenize + lemmatize, and returns an ordered JSON
    list of tokens with sign_video / is_fingerspelling hints attached.

POST /api/tokenize
    Accept a JSON body with raw text. Same pipeline as /api/upload but
    for text that was already extracted client-side.

GET  /api/signs/{lemma}
    Return whether a given lemma has a single-word sign video and the
    path to it. Used by the frontend for re-lookups.

GET  /healthz
    Liveness probe.

Design notes
------------
* No googletrans / multilingual translation in this pass (TODO).
* No ISL grammar reordering — words are returned in the order they
  appear in the source text so the UI's text highlight and sign video
  always refer to the same word.
* No module-level mutable state — tokenize() takes text as a parameter
  and returns a result, safe under concurrent FastAPI requests.
"""
from __future__ import annotations

import io
import logging
import os
import re
from functools import lru_cache
from typing import List, Optional

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

import spacy

from payload import StoryToken


# -----------------------------------------------------------------------------
# Config
# -----------------------------------------------------------------------------

logger = logging.getLogger("kahani")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s :: %(message)s")

# Where the curated sign clips live, served as static files at /static/signs/.
SIGNS_DIR = os.path.join(os.path.dirname(__file__), "signs")
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")

# Absolute-size limit on uploaded story files. ~5 MB is plenty for a
# children's storybook even in plain text and stops abusive uploads.
MAX_UPLOAD_BYTES = 5 * 1024 * 1024


# -----------------------------------------------------------------------------
# spaCy loader — module-level singleton, but read-only / idempotent.
# This is the only state we share across requests and it is safe.
# -----------------------------------------------------------------------------

@lru_cache(maxsize=1)
def get_nlp():
    """Load the small English spaCy model once and cache it."""
    try:
        nlp = spacy.load("en_core_web_sm")
    except OSError as exc:
        raise RuntimeError(
            "spaCy model 'en_core_web_sm' is not installed. Run:\n"
            "    python -m spacy download en_core_web_sm\n"
        ) from exc
    return nlp


# -----------------------------------------------------------------------------
# Sign-dictionary loader
# -----------------------------------------------------------------------------

@lru_cache(maxsize=1)
def get_sign_dict() -> dict[str, str]:
    """
    Load the lemma -> video-filename mapping from signs/dictionary.json.

    Returned values are bare filenames (e.g. 'run.mp4'); the caller
    decides whether to prefix with /static/signs/.
    """
    dict_path = os.path.join(SIGNS_DIR, "dictionary.json")
    if not os.path.exists(dict_path):
        logger.warning("No signs/dictionary.json found yet — all words will fall back to fingerspelling.")
        return {}
    import json

    with open(dict_path, "r", encoding="utf-8") as f:
        raw = json.load(f)
    # Normalize keys: lowercase, strip whitespace.
    return {str(k).strip().lower(): str(v).strip() for k, v in raw.items()}


def attach_sign_video(tokens: List[StoryToken]) -> List[StoryToken]:
    """Annotate each token with its sign video (or fingerspelling flag)."""
    sign_dict = get_sign_dict()
    for tok in tokens:
        key = tok.lemma.lower().strip()
        if key in sign_dict:
            tok.sign_video = f"/static/signs/{sign_dict[key]}"
            tok.is_fingerspelling = False
        else:
            tok.sign_video = None
            tok.is_fingerspelling = True
    return tokens


# -----------------------------------------------------------------------------
# Core tokenize function — pure, no module state.
# -----------------------------------------------------------------------------

# Tokens whose ISL gloss is just a single character — no point in
# fingerspelling them letter-by-letter. We skip them in the token
# stream so the UI doesn't have to deal with empty sign slots.
_SKIP_LEMMAS = {"", " "}

# Punctuation-only tokens that the UI should also drop.
_PUNCT_ONLY = set(".,!?;:\"'`()[]{}-—–_/\\…")

# Sentence boundary: [.?!]+ followed by whitespace+capital OR end-of-string.
# Splitting on this pattern handles normal sentences without enabling spaCy's parser.
_SENTENCE_SPLIT_RE = re.compile(r"[.?!]+(?=\s+[A-Z])|[.?!]+$", re.MULTILINE)

# A fragment whose last whitespace-delimited token is a title-case abbreviation
# (1–3 uppercase-starting chars, e.g. "Mr", "Dr", "St", "U", "vs").
# Lowercase endings like "ran", "hid" do NOT match — they are real sentence endings.
_ABBREV_TAIL_RE = re.compile(r"(?:^|\s)([A-Z][a-z]{0,2}|[A-Z]{1,3})$")


def segment_sentences(text: str) -> list[str]:
    """
    Split *text* into sentence-level segments without enabling spaCy's parser.

    Rules:
    - Split on [.?!] followed by whitespace+capital-letter or end-of-string.
    - Re-join fragments where the last word is a title-case abbreviation
      (e.g. "Mr", "Dr", "St", "U") — these are not real sentence boundaries.
    - Discard empty segments after stripping.

    Returns a list of non-empty sentence strings in source order.
    """
    parts = _SENTENCE_SPLIT_RE.split(text)
    parts = [p.strip() for p in parts if p and p.strip()]

    # Re-join abbreviation fragments: if a fragment ends with a title-case
    # abbreviation-shaped word, it was split at "Mr.", "Dr.", etc. — merge
    # it with the immediately following fragment.
    merged: list[str] = []
    i = 0
    while i < len(parts):
        frag = parts[i]
        if i + 1 < len(parts) and _ABBREV_TAIL_RE.search(frag):
            merged.append(frag + " " + parts[i + 1])
            i += 2
        else:
            merged.append(frag)
            i += 1
    return merged


def tokenize(text: str) -> List[StoryToken]:
    """
    Run spaCy (tokenize + lemmatize only — no reordering, no parsing)
    over the input text and return an ordered list of StoryToken.

    The text is first split into sentence-level segments by
    segment_sentences(); each segment's tokens are stamped with a
    scene_idx so the frontend can detect scene boundaries without
    needing the punctuation that was already stripped by _PUNCT_ONLY.

    The function is pure: same input → same output, no side effects,
    no shared mutable state. Safe under concurrent requests.
    """
    if not text or not text.strip():
        return []

    nlp = get_nlp()
    # Disable parser + NER + tagger. We only want tokenizer + lemmatizer.
    # This is ~5x faster on long stories and avoids accidentally
    # triggering any of the old ISL reordering logic.
    pipe = nlp.get_pipe("lemmatizer") if "lemmatizer" in nlp.pipe_names else None

    segments = segment_sentences(text)
    # Fall back to the full text as one segment if the splitter returns nothing
    # (e.g. a single word with no terminal punctuation).
    if not segments:
        segments = [text.strip()]

    tokens: List[StoryToken] = []
    for scene_idx, segment in enumerate(segments):
        doc = (
            nlp(segment, disable=["parser", "ner", "tagger", "attribute_ruler"])
            if pipe is None
            else nlp(segment)
        )
        for token in doc:
            surface = token.text
            lemma = (token.lemma_ or "").strip()
            if not surface or not lemma:
                continue
            # Skip pure-whitespace and pure-punctuation tokens.
            if lemma.lower() in _SKIP_LEMMAS:
                continue
            if all(ch in _PUNCT_ONLY for ch in surface):
                continue
            tokens.append(
                StoryToken(
                    display_word=surface,
                    lemma=lemma.lower(),
                    sign_video=None,        # filled in by attach_sign_video
                    is_fingerspelling=False,
                    scene_idx=scene_idx,
                )
            )
    return attach_sign_video(tokens)


# -----------------------------------------------------------------------------
# File parsers
# -----------------------------------------------------------------------------

def _extract_text_from_txt(data: bytes) -> str:
    # Try utf-8 first, fall back to latin-1 (always decodes).
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        return data.decode("latin-1", errors="replace")


def _extract_text_from_pdf(data: bytes) -> str:
    # Imported lazily so the rest of the module loads even if pdf
    # libs aren't installed.
    try:
        from pypdf import PdfReader  # modern fork of PyPDF2
    except ImportError:
        try:
            from PyPDF2 import PdfReader  # type: ignore
        except ImportError as exc:
            raise HTTPException(
                status_code=500,
                detail="PDF support requires pypdf (or PyPDF2). pip install pypdf.",
            ) from exc
    reader = PdfReader(io.BytesIO(data))
    parts = []
    for page in reader.pages:
        try:
            parts.append(page.extract_text() or "")
        except Exception as exc:  # noqa: BLE001
            logger.warning("PDF page extract failed: %s", exc)
    return "\n".join(parts)


def _extract_text_from_docx(data: bytes) -> str:
    try:
        from docx import Document  # python-docx
    except ImportError as exc:
        raise HTTPException(
            status_code=500,
            detail="DOCX support requires python-docx. pip install python-docx.",
        ) from exc
    doc = Document(io.BytesIO(data))
    parts = []
    for para in doc.paragraphs:
        if para.text:
            parts.append(para.text)
    return "\n".join(parts)


def extract_text(filename: str, data: bytes) -> str:
    """Dispatch to the right parser based on file extension."""
    name = filename.lower()
    if name.endswith(".txt") or name.endswith(".md"):
        return _extract_text_from_txt(data)
    if name.endswith(".pdf"):
        return _extract_text_from_pdf(data)
    if name.endswith(".docx"):
        return _extract_text_from_docx(data)
    raise HTTPException(
        status_code=400,
        detail=f"Unsupported file type: {filename}. Use .txt, .pdf, or .docx.",
    )


# -----------------------------------------------------------------------------
# FastAPI app
# -----------------------------------------------------------------------------

app = FastAPI(title="Kahani — Story to ISL Playback", version="1.0")

# Permissive CORS for local dev. In production you'd lock this down.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve /static/signs/*  — the curated video clips and letter clips for
# fingerspelling. The directory is created lazily so the app boots even
# before step (b) has been run.
os.makedirs(os.path.join(STATIC_DIR, "signs"), exist_ok=True)
os.makedirs(SIGNS_DIR, exist_ok=True)
if os.path.isdir(os.path.join(STATIC_DIR, "signs")):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


class TokenizeRequest(BaseModel):
    text: str


@app.get("/healthz")
def healthz():
    return {"status": "ok"}


@app.post("/api/upload", response_model=List[StoryToken])
async def upload_story(file: UploadFile = File(...)):
    """
    Upload a story file (.txt / .pdf / .docx) and get back an ordered
    list of tokens with sign_video / is_fingerspelling annotations.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename in upload.")

    data = await file.read()
    if len(data) == 0:
        raise HTTPException(status_code=400, detail="Empty file.")
    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"File too large ({len(data)} bytes). Limit is {MAX_UPLOAD_BYTES}.",
        )

    logger.info("Received upload: %s (%d bytes)", file.filename, len(data))
    text = extract_text(file.filename, data)
    return tokenize(text)


@app.post("/api/tokenize", response_model=List[StoryToken])
def tokenize_raw(req: TokenizeRequest):
    """Same pipeline as /api/upload but accepts already-extracted text."""
    return tokenize(req.text)


@app.get("/api/signs/{lemma}")
def lookup_sign(lemma: str):
    """Look up a single lemma in the sign dictionary."""
    sign_dict = get_sign_dict()
    key = lemma.strip().lower()
    fname = sign_dict.get(key)
    if fname is None:
        return {"lemma": key, "found": False, "fingerspell": True, "video": None}
    return {"lemma": key, "found": True, "fingerspell": False, "video": f"/static/signs/{fname}"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=int(os.environ.get("PORT", 3002)), reload=False)