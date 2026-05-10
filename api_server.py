"""
Confluence RAG — Web API Server

FastAPI application serving a dark-themed browser UI and REST endpoints for:
  - Querying Confluence / Stack Overflow local ChromaDB
  - Triggering Confluence page fetch/refresh (full or incremental)
  - Listing indexed pages and vectorstore statistics
  - System health/status checks

Run with:
    python api_server.py
    # or
    uvicorn api_server:app --port 8000
"""

import json
import logging
import os
import sys
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests as _requests
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, field_validator

load_dotenv()

# ── Logging ────────────────────────────────────────────────────────────────────
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s %(levelname)-8s %(name)s — %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("confluence_rag.log", mode="a", encoding="utf-8"),
    ],
)
logger = logging.getLogger(__name__)

# ── App ────────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="Confluence RAG API",
    description="Local RAG system for Confluence + Stack Overflow, powered by Ollama",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

STATIC_DIR = Path(__file__).parent / "static"

# ── In-memory state ────────────────────────────────────────────────────────────
_vectorstores: Dict[str, Any] = {}
_qa_chains: Dict[str, Any] = {}
_fetch_status: Dict[str, Any] = {
    "running": False,
    "mode": None,
    "started_at": None,
    "last_run": None,
    "last_result": None,
    "error": None,
}
_state_lock = threading.Lock()

# ── Config map ─────────────────────────────────────────────────────────────────
# Maps UI field names → .env key names.
CONFIG_MAP: Dict[str, str] = {
    "confluence_url":       "CONFLUENCE_URL",
    "confluence_email":     "CONFLUENCE_EMAIL",
    "confluence_api_token": "CONFLUENCE_API_TOKEN",
    "confluence_space_key": "CONFLUENCE_SPACE_KEY",
    "ollama_base_url":      "OLLAMA_BASE_URL",
    "ollama_llm_model":     "OLLAMA_LLM_MODEL",
    "ollama_embed_model":   "OLLAMA_EMBED_MODEL",
    "chunk_size":           "CHUNK_SIZE",
    "chunk_overlap":        "CHUNK_OVERLAP",
    "retriever_k":          "RETRIEVER_K",
    "log_level":            "LOG_LEVEL",
}
# Values for these keys are masked in GET /api/config responses.
SENSITIVE_KEYS = {"confluence_api_token", "confluence_email"}


# ── Vectorstore helpers ────────────────────────────────────────────────────────

def _load_confluence_vs():
    if "confluence" in _vectorstores:
        return _vectorstores["confluence"]
    try:
        from src.embed_and_store import load_vectorstore, vectorstore_exists
        if not vectorstore_exists():
            raise HTTPException(
                status_code=404,
                detail="Confluence vector store not found. Use 'Fetch Pages' to ingest data first.",
            )
        vs = load_vectorstore()
        _vectorstores["confluence"] = vs
        return vs
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[VS] Failed to load Confluence vectorstore: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Could not load Confluence database: {e}",
        )


def _load_so_vs():
    if "stackoverflow" in _vectorstores:
        return _vectorstores["stackoverflow"]
    try:
        from src.embed_and_store import load_vectorstore_so, vectorstore_so_exists
        if not vectorstore_so_exists():
            raise HTTPException(
                status_code=404,
                detail="Stack Overflow vector store not found.",
            )
        vs = load_vectorstore_so()
        _vectorstores["stackoverflow"] = vs
        return vs
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[VS] Failed to load SO vectorstore: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Could not load Stack Overflow database: {e}",
        )


def _get_chain(source: str):
    if source in _qa_chains:
        return _qa_chains[source]
    try:
        from src.query import build_qa_chain
        vs = _load_confluence_vs() if source == "confluence" else _load_so_vs()
        chain = build_qa_chain(vs)
        _qa_chains[source] = chain
        return chain
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[Chain] Failed to build chain for '{source}': {e}")
        model = os.getenv("OLLAMA_LLM_MODEL", "llama3.1:8b")
        raise HTTPException(
            status_code=503,
            detail=(
                f"Could not initialize LLM chain for {source}. "
                f"Ensure Ollama is running with model '{model}' pulled "
                f"(run: ollama pull {model}). Error: {e}"
            ),
        )


def _invalidate_chain(source: str):
    _qa_chains.pop(source, None)


def _reload_src_modules():
    """
    Reload the three src modules that cache env vars at module level.
    Must be called after os.environ is updated so the new values are picked up.
    Always call inside _state_lock.
    """
    import importlib
    import src.fetch_confluence
    import src.embed_and_store
    import src.query
    importlib.reload(src.fetch_confluence)
    importlib.reload(src.embed_and_store)
    importlib.reload(src.query)
    _vectorstores.clear()
    _qa_chains.clear()
    logger.info("[Config] src modules reloaded; vectorstore and chain caches cleared")


# ── Fetch background worker ────────────────────────────────────────────────────

def _fetch_worker(incremental: bool):
    with _state_lock:
        if _fetch_status["running"]:
            return
        _fetch_status.update(
            running=True,
            mode="incremental" if incremental else "full",
            started_at=datetime.now(timezone.utc).isoformat(),
            error=None,
            last_result=None,
        )

    try:
        if incremental:
            _do_incremental_fetch()
        else:
            _do_full_fetch()
    except Exception as e:
        logger.error(f"[Fetch] Worker error: {e}", exc_info=True)
        with _state_lock:
            _fetch_status.update(
                running=False,
                error=str(e),
                last_run=datetime.now(timezone.utc).isoformat(),
            )


def _do_full_fetch():
    from src.confluence_metadata import ConfluenceMetadataTracker
    from src.embed_and_store import create_vectorstore
    from src.fetch_confluence import fetch_pages

    logger.info("[Fetch] Starting full Confluence fetch…")
    documents = fetch_pages()

    if not documents:
        raise RuntimeError(
            "No documents fetched from Confluence. "
            "Check CONFLUENCE_URL, CONFLUENCE_EMAIL, CONFLUENCE_API_TOKEN in .env "
            "and verify your API token has read access to the space."
        )

    vs = create_vectorstore(documents)

    tracker = ConfluenceMetadataTracker()
    for doc in documents:
        m = doc.metadata
        tracker.add_or_update_page(
            page_id=m.get("page_id", ""),
            title=m.get("title", ""),
            version=m.get("version", 1),
            modified=m.get("modified", ""),
            url=m.get("url", ""),
            space_key=m.get("space_key", ""),
            chunk_count=0,
        )
    tracker.save()

    _vectorstores["confluence"] = vs
    _invalidate_chain("confluence")

    ts = datetime.now(timezone.utc).isoformat()
    result = {"pages": len(documents), "mode": "full", "ts": ts}
    with _state_lock:
        _fetch_status.update(running=False, last_run=ts, last_result=result, error=None)
    logger.info(f"[Fetch] Full fetch complete: {len(documents)} pages ingested")


def _do_incremental_fetch():
    from src.embed_and_store import (
        add_documents,
        load_vectorstore,
        remove_documents,
        update_documents,
        vectorstore_exists,
    )
    from src.fetch_confluence import fetch_incremental_pages
    from src.confluence_metadata import ConfluenceMetadataTracker

    logger.info("[Fetch] Starting incremental Confluence fetch…")

    if "confluence" not in _vectorstores:
        if not vectorstore_exists():
            raise RuntimeError("No existing vector store — run a full fetch first.")
        _vectorstores["confluence"] = load_vectorstore()

    vs = _vectorstores["confluence"]
    tracker = ConfluenceMetadataTracker()
    new_docs, modified_docs, deleted_ids = fetch_incremental_pages(tracker)

    stats = {
        "new": len(new_docs),
        "modified": len(modified_docs),
        "deleted": len(deleted_ids),
    }

    if deleted_ids:
        vs = remove_documents(deleted_ids, vs)
    if modified_docs:
        ids = [d.metadata.get("page_id") for d in modified_docs]
        vs = update_documents(modified_docs, ids, vs)
    if new_docs:
        vs = add_documents(new_docs, vs)

    _vectorstores["confluence"] = vs
    _invalidate_chain("confluence")

    ts = datetime.now(timezone.utc).isoformat()
    result = {**stats, "mode": "incremental", "ts": ts}
    with _state_lock:
        _fetch_status.update(running=False, last_run=ts, last_result=result, error=None)
    logger.info(f"[Fetch] Incremental fetch complete: {stats}")


# ── Request / response models ──────────────────────────────────────────────────

class QueryRequest(BaseModel):
    question: str
    source: str = "confluence"

    @field_validator("question")
    @classmethod
    def question_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Question cannot be empty.")
        return v.strip()

    @field_validator("source")
    @classmethod
    def valid_source(cls, v: str) -> str:
        if v not in ("confluence", "stackoverflow", "both"):
            raise ValueError("source must be 'confluence', 'stackoverflow', or 'both'")
        return v


class SourceDoc(BaseModel):
    title: str
    url: str
    space_key: str
    snippet: str


class QueryResponse(BaseModel):
    question: str
    source: str
    answer: str
    confidence: float
    confidence_label: str
    sources: List[SourceDoc]
    chunks_retrieved: int
    latency_ms: float


# ── Query helper (runs in thread executor) ─────────────────────────────────────

def _run_query_sync(question: str, source: str) -> Dict[str, Any]:
    from src.query import RETRIEVER_K, _compute_confidence, ask

    chain = _get_chain(source)
    t0 = time.monotonic()
    try:
        answer, source_docs = ask(question, chain)
    except Exception as e:
        logger.error(f"[Query:{source}] LLM invocation failed: {e}")
        model = os.getenv("OLLAMA_LLM_MODEL", "llama3.1:8b")
        raise HTTPException(
            status_code=503,
            detail=(
                f"Query failed on {source}. "
                f"Ensure Ollama is running with model '{model}'. "
                f"Error: {e}"
            ),
        )

    elapsed_ms = (time.monotonic() - t0) * 1000
    conf = _compute_confidence(source_docs, RETRIEVER_K)

    seen_urls: set = set()
    formatted_sources: List[SourceDoc] = []
    for doc in source_docs:
        url = doc.metadata.get("url", "")
        if url and url in seen_urls:
            continue
        seen_urls.add(url)
        formatted_sources.append(
            SourceDoc(
                title=doc.metadata.get("title", "Unknown"),
                url=url,
                space_key=doc.metadata.get("space_key", ""),
                snippet=doc.page_content[:400],
            )
        )

    return {
        "answer": answer or "I could not find this information in the indexed documents.",
        "confidence": conf["score"],
        "confidence_label": conf["label"],
        "sources": formatted_sources,
        "chunks_retrieved": len(source_docs),
        "latency_ms": round(elapsed_ms, 1),
    }


# ── Routes ─────────────────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse, include_in_schema=False)
async def root():
    html_path = STATIC_DIR / "index.html"
    if html_path.exists():
        return HTMLResponse(html_path.read_text(encoding="utf-8"))
    return HTMLResponse(
        "<h1>Confluence RAG</h1>"
        "<p>Frontend not found — place <code>index.html</code> in <code>static/</code>.</p>"
    )


@app.get("/api/status")
async def api_status():
    """System health: Ollama reachability, vectorstore presence, fetch state."""
    from src.embed_and_store import vectorstore_exists, vectorstore_so_exists

    ollama_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    ollama_ok = False
    ollama_models: List[str] = []
    try:
        r = _requests.get(f"{ollama_url}/api/tags", timeout=4)
        ollama_ok = r.status_code == 200
        if ollama_ok:
            ollama_models = [m["name"] for m in r.json().get("models", [])]
    except Exception as e:
        logger.debug(f"[Status] Ollama ping failed: {e}")

    conf_exists = conf_chunks = 0
    conf_exists = False
    try:
        conf_exists = vectorstore_exists()
        if conf_exists and "confluence" in _vectorstores:
            conf_chunks = _vectorstores["confluence"]._collection.count()
    except Exception:
        pass

    so_exists = False
    so_chunks = 0
    try:
        so_exists = vectorstore_so_exists()
        if so_exists and "stackoverflow" in _vectorstores:
            so_chunks = _vectorstores["stackoverflow"]._collection.count()
    except Exception:
        pass

    return {
        "ollama": {
            "ok": ollama_ok,
            "url": ollama_url,
            "models": ollama_models,
            "llm_model": os.getenv("OLLAMA_LLM_MODEL", "llama3.1:8b"),
            "embed_model": os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text"),
        },
        "confluence_db": {
            "exists": conf_exists,
            "chunks": conf_chunks,
            "path": os.getenv("CHROMA_PERSIST_DIR", "./confluence_db"),
        },
        "stackoverflow_db": {
            "exists": so_exists,
            "chunks": so_chunks,
            "path": os.getenv("STACKOVERFLOW_DB_PATH", "./stackoverflow_db"),
        },
        "fetch": dict(_fetch_status),
    }


@app.post("/api/query", response_model=QueryResponse)
async def api_query(req: QueryRequest):
    """
    Query local ChromaDB with a natural language question.
    source: 'confluence' | 'stackoverflow' | 'both'
    """
    import asyncio
    import concurrent.futures

    loop = asyncio.get_event_loop()

    if req.source != "both":
        result = await loop.run_in_executor(None, _run_query_sync, req.question, req.source)
        return QueryResponse(question=req.question, source=req.source, **result)

    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        futures = {
            "confluence": pool.submit(_run_query_sync, req.question, "confluence"),
            "stackoverflow": pool.submit(_run_query_sync, req.question, "stackoverflow"),
        }
        results: Dict[str, Any] = {}
        errors: Dict[str, str] = {}
        for src, fut in futures.items():
            try:
                results[src] = fut.result(timeout=120)
            except HTTPException as e:
                errors[src] = e.detail
            except Exception as e:
                errors[src] = str(e)

    if not results:
        detail = "; ".join(f"{s}: {msg}" for s, msg in errors.items())
        raise HTTPException(status_code=503, detail=f"All sources failed — {detail}")

    parts: List[str] = []
    merged_sources: List[SourceDoc] = []
    total_chunks = 0
    best_conf = 0.0
    best_label = "Low"
    total_ms = 0.0

    for src in ("confluence", "stackoverflow"):
        if src in results:
            r = results[src]
            parts.append(f"[{src.upper()}]\n{r['answer']}")
            merged_sources.extend(r["sources"])
            total_chunks += r["chunks_retrieved"]
            total_ms += r["latency_ms"]
            if r["confidence"] > best_conf:
                best_conf = r["confidence"]
                best_label = r["confidence_label"]
        elif src in errors:
            parts.append(f"[{src.upper()}] Error: {errors[src]}")

    return QueryResponse(
        question=req.question,
        source="both",
        answer="\n\n".join(parts),
        confidence=round(best_conf, 2),
        confidence_label=best_label,
        sources=merged_sources[:8],
        chunks_retrieved=total_chunks,
        latency_ms=round(total_ms, 1),
    )


@app.post("/api/fetch")
async def api_fetch(incremental: bool = False):
    """
    Trigger a background Confluence page fetch.
    - incremental=false (default): full re-fetch and re-embed
    - incremental=true: detect and apply only new/modified/deleted pages
    Poll /api/fetch/status for progress.
    """
    with _state_lock:
        if _fetch_status["running"]:
            raise HTTPException(status_code=409, detail="A fetch job is already running.")

    t = threading.Thread(
        target=_fetch_worker,
        kwargs={"incremental": incremental},
        daemon=True,
        name=f"fetch-{'incremental' if incremental else 'full'}",
    )
    t.start()

    return {
        "status": "started",
        "mode": "incremental" if incremental else "full",
        "message": "Fetch started. Poll /api/fetch/status for progress.",
    }


@app.get("/api/fetch/status")
async def api_fetch_status():
    """Current fetch job status."""
    return dict(_fetch_status)


@app.delete("/api/fetch/cancel")
async def api_fetch_cancel():
    """Clear a stale/stuck fetch status (the thread cannot be force-killed)."""
    with _state_lock:
        if not _fetch_status["running"]:
            raise HTTPException(status_code=400, detail="No fetch is currently running.")
        _fetch_status.update(
            running=False,
            error="Cancelled by user.",
            last_run=datetime.now(timezone.utc).isoformat(),
        )
    return {"status": "cancelled"}


@app.get("/api/pages")
async def api_pages(search: str = "", space: str = ""):
    """
    List all indexed Confluence pages from metadata.
    Optional: search (title filter), space (space_key filter).
    """
    metadata_file = os.getenv("CONFLUENCE_METADATA_FILE", "confluence_metadata.json")
    if not os.path.exists(metadata_file):
        return {"pages": [], "total": 0, "total_all": 0, "spaces": [], "last_fetch": None}

    try:
        with open(metadata_file, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"[Pages] Corrupt metadata file: {e}")
        raise HTTPException(status_code=500, detail=f"Metadata file is corrupt: {e}")
    except OSError as e:
        logger.error(f"[Pages] Cannot read metadata file: {e}")
        raise HTTPException(status_code=500, detail=f"Cannot read metadata: {e}")

    all_pages = list(data.get("pages", {}).values())
    pages = all_pages

    if search:
        q = search.lower()
        pages = [
            p for p in pages
            if q in p.get("title", "").lower() or q in p.get("space_key", "").lower()
        ]

    if space:
        pages = [p for p in pages if p.get("space_key", "").lower() == space.lower()]

    pages.sort(key=lambda p: p.get("title", "").lower())
    spaces = sorted({p.get("space_key", "") for p in all_pages if p.get("space_key")})

    return {
        "pages": pages,
        "total": len(pages),
        "total_all": len(all_pages),
        "spaces": spaces,
        "last_fetch": data.get("last_fetch"),
    }


@app.get("/api/stats")
async def api_stats():
    """Vectorstore chunk counts and configuration summary."""
    from src.embed_and_store import vectorstore_exists, vectorstore_so_exists

    conf_exists = False
    conf_chunks = 0
    try:
        conf_exists = vectorstore_exists()
        if conf_exists:
            vs = _load_confluence_vs()
            conf_chunks = vs._collection.count()
    except Exception:
        pass

    so_exists = False
    so_chunks = 0
    try:
        so_exists = vectorstore_so_exists()
        if so_exists:
            vs = _load_so_vs()
            so_chunks = vs._collection.count()
    except Exception:
        pass

    return {
        "confluence": {
            "exists": conf_exists,
            "chunks": conf_chunks,
            "path": os.getenv("CHROMA_PERSIST_DIR", "./confluence_db"),
        },
        "stackoverflow": {
            "exists": so_exists,
            "chunks": so_chunks,
            "path": os.getenv("STACKOVERFLOW_DB_PATH", "./stackoverflow_db"),
        },
        "settings": {
            "chunk_size": int(os.getenv("CHUNK_SIZE", "500")),
            "chunk_overlap": int(os.getenv("CHUNK_OVERLAP", "50")),
            "retriever_k": int(os.getenv("RETRIEVER_K", "5")),
            "llm_model": os.getenv("OLLAMA_LLM_MODEL", "llama3.1:8b"),
            "embed_model": os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text"),
        },
    }


# ── Config routes ─────────────────────────────────────────────────────────────

@app.get("/api/config")
async def api_config_get():
    """
    Return current configuration values from env vars.
    Sensitive fields (API token, email) are returned as '***' when set, '' when not set.
    """
    result: Dict[str, Any] = {}
    for field, env_key in CONFIG_MAP.items():
        val = os.getenv(env_key, "")
        if field in SENSITIVE_KEYS:
            result[field] = "***" if val else ""
        else:
            result[field] = val
    return result


class ConfigUpdateRequest(BaseModel):
    confluence_url:       Optional[str] = None
    confluence_email:     Optional[str] = None
    confluence_api_token: Optional[str] = None
    confluence_space_key: Optional[str] = None
    ollama_base_url:      Optional[str] = None
    ollama_llm_model:     Optional[str] = None
    ollama_embed_model:   Optional[str] = None
    chunk_size:           Optional[str] = None
    chunk_overlap:        Optional[str] = None
    retriever_k:          Optional[str] = None
    log_level:            Optional[str] = None


@app.post("/api/config")
async def api_config_post(req: ConfigUpdateRequest):
    """
    Update configuration values.
    - Validates input server-side.
    - Writes to .env (creates if absent).
    - Updates os.environ in-process.
    - Reloads src modules so module-level env var assignments pick up new values.
    - Clears vectorstore and chain caches.
    """
    from dotenv import set_key as dotenv_set_key

    payload = req.model_dump(exclude_none=True)
    if not payload:
        raise HTTPException(status_code=400, detail="No fields provided.")

    # ── Validation ──
    url_fields = {"confluence_url", "ollama_base_url"}
    int_fields = {
        "chunk_size": (50, 10000),
        "chunk_overlap": (0, 5000),
        "retriever_k": (1, 50),
    }
    valid_log_levels = {"DEBUG", "INFO", "WARNING", "ERROR"}

    errors: List[str] = []
    for field, val in payload.items():
        v = str(val).strip()
        if not v:
            continue  # empty = skip / keep current
        if field in url_fields and not v.lower().startswith("http"):
            errors.append(f"{field}: must start with http or https")
        if field in int_fields:
            try:
                n = int(v)
                lo, hi = int_fields[field]
                if not (lo <= n <= hi):
                    errors.append(f"{field}: must be between {lo} and {hi}")
            except ValueError:
                errors.append(f"{field}: must be a whole number")
        if field == "log_level" and v.upper() not in valid_log_levels:
            errors.append(f"log_level: must be one of {sorted(valid_log_levels)}")

    if errors:
        raise HTTPException(status_code=422, detail="; ".join(errors))

    # ── Persist to .env and update os.environ ──
    env_path = Path(".env")
    updated: List[str] = []
    for field, val in payload.items():
        v = str(val).strip()
        if not v:
            continue
        env_key = CONFIG_MAP[field]
        dotenv_set_key(str(env_path), env_key, v, quote_mode="never")
        os.environ[env_key] = v
        updated.append(field)
        logger.info(f"[Config] Set {env_key} ({'***' if field in SENSITIVE_KEYS else v})")

    # ── Reload modules + clear caches ──
    with _state_lock:
        _reload_src_modules()

    return {
        "ok": True,
        "updated": updated,
        "cleared": ["vectorstores", "chains"],
        "message": "Settings saved. Re-fetch Confluence pages if you changed credentials or chunk settings.",
    }


# ── Global error handler ───────────────────────────────────────────────────────

@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.error(f"[API] Unhandled error on {request.url}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": f"Internal server error: {exc}"},
    )


# ── Static files (must be mounted after all routes) ────────────────────────────
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


# ── Entrypoint ─────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("API_PORT", "8000"))
    host = os.getenv("API_HOST", "0.0.0.0")
    logger.info(f"Starting Confluence RAG API on http://{host}:{port}")
    uvicorn.run(app, host=host, port=port, reload=False, log_level=LOG_LEVEL.lower())
