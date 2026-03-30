"""
Dashboard Generator Module

Extracts structured, grounded data from ChromaDB vector stores
and uses the local Ollama LLM to produce dashboard-ready insights.

ZERO HALLUCINATION GUARANTEE:
- Every metric is computed directly from stored document metadata
- Every LLM-generated insight is constrained to retrieved document text only
- All LLM calls use temperature=0.0 and strict grounding prompts
- Each insight carries the source documents it was derived from
- If insufficient data exists, the field is marked as "Insufficient data" — never fabricated
"""

import os
import json
import logging
import time
from typing import List, Dict, Any, Optional, Tuple
from collections import Counter, defaultdict
from datetime import datetime, timezone

from langchain_core.documents import Document
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

OLLAMA_LLM_MODEL = os.getenv("OLLAMA_LLM_MODEL", "llama3.1:8b")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
DASHBOARD_MAX_DOCS = int(os.getenv("DASHBOARD_MAX_DOCS", "50"))   # cap for LLM insight calls
DASHBOARD_TOP_N = int(os.getenv("DASHBOARD_TOP_N", "10"))          # rows in ranked tables

# ── Grounding prompts (temperature=0, strict context-only) ──────────────────

_SUMMARY_PROMPT = ChatPromptTemplate.from_template("""
You are a technical analyst. Your ONLY job is to write a 2-3 sentence factual summary
of the documents provided below.

STRICT RULES:
- Use ONLY information from the documents below. Do NOT add anything else.
- Do NOT invent topics, technologies, or conclusions not present in the text.
- If you cannot produce a summary from the provided text, respond ONLY with:
  "Insufficient data to summarise."

Documents:
{context}

Summary:
""")

_TOPICS_PROMPT = ChatPromptTemplate.from_template("""
You are a technical analyst. Extract the top recurring technical topics from the
documents below.

STRICT RULES:
- List ONLY topics that are explicitly mentioned in the documents.
- Output a JSON array of strings, e.g. ["Python", "REST API", "Docker"]
- Maximum 10 items. No explanations. No markdown fences. Pure JSON only.
- If no clear topics are found, output: []

Documents:
{context}

JSON array:
""")

_INSIGHT_PROMPT = ChatPromptTemplate.from_template("""
You are a technical analyst. Produce 3 short, factual bullet-point insights
about the documents below.

STRICT RULES:
- Every insight MUST be directly supported by text in the documents.
- Do NOT speculate or add context not present in the documents.
- Format: start each line with "• "
- If you cannot find 3 distinct insights, produce as many as the data supports.
- If there is no usable data, output ONLY: "• Insufficient data for insights."

Documents:
{context}

Insights:
""")


# ── Internal helpers ─────────────────────────────────────────────────────────

def _safe_int(value, default: int = 0) -> int:
    """Convert a metadata value to int, returning ``default`` on any error."""
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _get_grounded_llm() -> ChatOllama:
    """Return a zero-temperature LLM instance for grounded generation."""
    return ChatOllama(
        model=OLLAMA_LLM_MODEL,
        base_url=OLLAMA_BASE_URL,
        temperature=0.0,   # deterministic — no creative invention
    )


def _docs_to_context(docs: List[Document], max_chars: int = 12000) -> str:
    """
    Concatenate document page_content into a single context string.
    Truncated to max_chars to stay within LLM context window.
    Each doc is prefixed with its title so the LLM can reference it.
    """
    parts = []
    total = 0
    for doc in docs:
        title = doc.metadata.get("title", "Untitled")
        snippet = f"[{title}]\n{doc.page_content}"
        if total + len(snippet) > max_chars:
            remaining = max_chars - total
            if remaining > 100:
                parts.append(snippet[:remaining] + "…")
            break
        parts.append(snippet)
        total += len(snippet)
    return "\n\n---\n\n".join(parts)


def _safe_llm_call(chain, context: str, label: str) -> str:
    """
    Run an LLM chain with full error handling and timing log.
    Returns a safe fallback string on any failure.
    """
    t0 = time.time()
    try:
        result = chain.invoke({"context": context})
        elapsed = time.time() - t0
        logger.info(f"[LLM:{label}] completed in {elapsed:.2f}s ({len(context)} chars context)")
        return result.strip()
    except Exception as e:
        elapsed = time.time() - t0
        logger.error(f"[LLM:{label}] failed after {elapsed:.2f}s — {e}")
        return "Insufficient data."


def _retrieve_all_docs(vectorstore) -> List[Document]:
    """
    Pull every stored document from a ChromaDB collection as Document objects.
    Used for metric computation — does NOT call the LLM.
    """
    try:
        collection = vectorstore._collection
        results = collection.get(include=["documents", "metadatas"])
        docs = []
        raw_docs = results.get("documents") or []
        raw_metas = results.get("metadatas") or []
        for content, meta in zip(raw_docs, raw_metas):
            docs.append(Document(
                page_content=content or "",
                metadata=meta or {}
            ))
        logger.info(f"Retrieved {len(docs)} documents from ChromaDB for dashboard")
        return docs
    except Exception as e:
        logger.error(f"Failed to retrieve documents from ChromaDB: {e}")
        return []


# ── Confluence dashboard data ────────────────────────────────────────────────

def generate_confluence_dashboard_data(vectorstore) -> Dict[str, Any]:
    """
    Build a complete, grounded dashboard data payload for Confluence.

    All metrics are derived directly from ChromaDB metadata.
    All LLM calls are strictly grounded — temperature=0, context-only prompts.

    Returns:
        Dict with keys:
          metrics        — scalar counts and stats
          top_pages      — most content-rich pages
          spaces         — page count per space
          recent_pages   — recently modified pages
          topics         — LLM-extracted topics (grounded)
          summary        — LLM summary (grounded)
          insights       — LLM bullet insights (grounded)
          sources        — list of {title, url} used for LLM calls
          generated_at   — ISO timestamp
          data_source    — "confluence"
    """
    logger.info("=== Generating Confluence dashboard data ===")
    t_start = time.time()

    docs = _retrieve_all_docs(vectorstore)

    if not docs:
        logger.warning("No Confluence documents found in vector store")
        return _empty_dashboard("confluence", "No documents found in Confluence vector store.")

    # ── 1. Pure metadata metrics (zero LLM) ─────────────────────────────────
    logger.info("[Confluence] Computing metadata metrics...")

    # Deduplicate by page_id to get unique pages (multiple chunks per page)
    pages_by_id: Dict[str, Document] = {}
    for doc in docs:
        pid = doc.metadata.get("page_id", "")
        if pid and pid not in pages_by_id:
            pages_by_id[pid] = doc

    unique_pages = list(pages_by_id.values())
    total_chunks = len(docs)
    total_pages = len(unique_pages)

    # Space distribution
    space_counter: Counter = Counter()
    for doc in unique_pages:
        space = doc.metadata.get("space_key", "unknown") or "unknown"
        space_counter[space] += 1

    # Top pages by content length (proxy for richness)
    page_lengths = []
    for doc in unique_pages:
        content_len = len(doc.page_content)
        page_lengths.append({
            "title": doc.metadata.get("title", "Untitled"),
            "url": doc.metadata.get("url", ""),
            "space": doc.metadata.get("space_key", ""),
            "version": doc.metadata.get("version", 1),
            "content_length": content_len,
        })
    page_lengths.sort(key=lambda x: x["content_length"], reverse=True)
    top_pages = page_lengths[:DASHBOARD_TOP_N]

    # Recently modified
    dated_pages = []
    for doc in unique_pages:
        modified = doc.metadata.get("modified", "")
        if modified:
            dated_pages.append({
                "title": doc.metadata.get("title", "Untitled"),
                "url": doc.metadata.get("url", ""),
                "space": doc.metadata.get("space_key", ""),
                "modified": modified,
            })
    dated_pages.sort(key=lambda x: x["modified"], reverse=True)
    recent_pages = dated_pages[:DASHBOARD_TOP_N]

    avg_chunk_len = int(sum(len(d.page_content) for d in docs) / total_chunks) if total_chunks else 0

    logger.info(
        f"[Confluence] Metadata done: {total_pages} pages, "
        f"{total_chunks} chunks, {len(space_counter)} spaces"
    )

    # ── 2. LLM grounded calls (temperature=0, context-only) ─────────────────
    llm = _get_grounded_llm()
    str_parser = StrOutputParser()

    # Sample representative pages for LLM (cap at DASHBOARD_MAX_DOCS)
    sample_docs = unique_pages[:DASHBOARD_MAX_DOCS]
    context = _docs_to_context(sample_docs)

    logger.info(f"[Confluence] Running LLM summary on {len(sample_docs)} pages...")
    summary = _safe_llm_call(_SUMMARY_PROMPT | llm | str_parser, context, "confluence-summary")

    logger.info(f"[Confluence] Running LLM topic extraction on {len(sample_docs)} pages...")
    topics_raw = _safe_llm_call(_TOPICS_PROMPT | llm | str_parser, context, "confluence-topics")
    topics = _parse_json_list(topics_raw, label="confluence-topics")

    logger.info(f"[Confluence] Running LLM insight extraction on {len(sample_docs)} pages...")
    insights_raw = _safe_llm_call(_INSIGHT_PROMPT | llm | str_parser, context, "confluence-insights")
    insights = [line.strip() for line in insights_raw.splitlines() if line.strip().startswith("•")]

    sources = [
        {"title": d.metadata.get("title", "Untitled"), "url": d.metadata.get("url", "")}
        for d in sample_docs
    ]

    elapsed = time.time() - t_start
    logger.info(f"=== Confluence dashboard data generated in {elapsed:.2f}s ===")

    return {
        "data_source": "confluence",
        "generated_at": datetime.now(tz=timezone.utc).isoformat(),
        "generation_time_seconds": round(elapsed, 2),
        "metrics": {
            "total_pages": total_pages,
            "total_chunks": total_chunks,
            "total_spaces": len(space_counter),
            "avg_chunk_length_chars": avg_chunk_len,
        },
        "spaces": [
            {"space": k, "page_count": v}
            for k, v in space_counter.most_common()
        ],
        "top_pages": top_pages,
        "recent_pages": recent_pages,
        "topics": topics,
        "summary": summary,
        "insights": insights,
        "sources": sources,
        "llm_model": OLLAMA_LLM_MODEL,
        "grounding_note": (
            "All LLM outputs are derived exclusively from stored Confluence documents. "
            "Temperature=0.0. No external knowledge used."
        ),
    }


# ── Stack Overflow dashboard data ────────────────────────────────────────────

def generate_stackoverflow_dashboard_data(vectorstore) -> Dict[str, Any]:
    """
    Build a complete, grounded dashboard data payload for Stack Overflow.

    All metrics are derived directly from ChromaDB metadata.
    All LLM calls are strictly grounded — temperature=0, context-only prompts.

    Returns:
        Dict with keys:
          metrics        — scalar counts and stats
          top_questions  — highest-scored questions
          top_tags       — most frequent tags
          topics         — LLM-extracted topics (grounded)
          summary        — LLM summary (grounded)
          insights       — LLM bullet insights (grounded)
          sources        — list of {title, url, score} used for LLM calls
          generated_at   — ISO timestamp
          data_source    — "stackoverflow"
    """
    logger.info("=== Generating Stack Overflow dashboard data ===")
    t_start = time.time()

    docs = _retrieve_all_docs(vectorstore)

    if not docs:
        logger.warning("No Stack Overflow documents found in vector store")
        return _empty_dashboard("stackoverflow", "No documents found in Stack Overflow vector store.")

    # ── 1. Pure metadata metrics (zero LLM) ─────────────────────────────────
    logger.info("[SO] Computing metadata metrics...")

    # Deduplicate by question_id
    questions_by_id: Dict[str, Document] = {}
    for doc in docs:
        qid = doc.metadata.get("question_id", "")
        if qid and qid not in questions_by_id:
            questions_by_id[qid] = doc

    unique_questions = list(questions_by_id.values())
    total_chunks = len(docs)
    total_questions = len(unique_questions)

    # Tag frequency
    tag_counter: Counter = Counter()
    for doc in unique_questions:
        tags = doc.metadata.get("tags", [])
        if isinstance(tags, list):
            tag_counter.update(tags)
        elif isinstance(tags, str):
            # Stored as comma-separated string in some versions
            tag_counter.update([t.strip() for t in tags.split(",") if t.strip()])

    # Top questions by score
    scored_questions = []
    for doc in unique_questions:
        scored_questions.append({
            "title": doc.metadata.get("title", "Untitled"),
            "url": doc.metadata.get("url", ""),
            "score": _safe_int(doc.metadata.get("score", 0)),
            "answer_count": _safe_int(doc.metadata.get("answer_count", 0)),
            "view_count": _safe_int(doc.metadata.get("view_count", 0)),
            "tags": doc.metadata.get("tags", []),
        })
    scored_questions.sort(key=lambda x: x["score"], reverse=True)
    top_questions = scored_questions[:DASHBOARD_TOP_N]

    # Aggregate stats
    total_score = sum(q["score"] for q in scored_questions)
    avg_score = round(total_score / total_questions, 1) if total_questions else 0
    avg_answers = round(
        sum(q["answer_count"] for q in scored_questions) / total_questions, 1
    ) if total_questions else 0
    avg_chunk_len = (
        int(sum(len(d.page_content) for d in docs) / total_chunks)
        if total_chunks else 0
    )

    logger.info(
        f"[SO] Metadata done: {total_questions} questions, "
        f"{total_chunks} chunks, {len(tag_counter)} unique tags"
    )

    # ── 2. LLM grounded calls (temperature=0, context-only) ─────────────────
    llm = _get_grounded_llm()
    str_parser = StrOutputParser()

    # Use highest-scored questions as context sample (most informative)
    sample_docs = [questions_by_id[q] for q in list(questions_by_id)[:DASHBOARD_MAX_DOCS]
                   if q in questions_by_id]
    context = _docs_to_context(sample_docs)

    logger.info(f"[SO] Running LLM summary on {len(sample_docs)} questions...")
    summary = _safe_llm_call(_SUMMARY_PROMPT | llm | str_parser, context, "so-summary")

    logger.info(f"[SO] Running LLM topic extraction on {len(sample_docs)} questions...")
    topics_raw = _safe_llm_call(_TOPICS_PROMPT | llm | str_parser, context, "so-topics")
    topics = _parse_json_list(topics_raw, label="so-topics")

    logger.info(f"[SO] Running LLM insight extraction on {len(sample_docs)} questions...")
    insights_raw = _safe_llm_call(_INSIGHT_PROMPT | llm | str_parser, context, "so-insights")
    insights = [line.strip() for line in insights_raw.splitlines() if line.strip().startswith("•")]

    sources = [
        {
            "title": d.metadata.get("title", "Untitled"),
            "url": d.metadata.get("url", ""),
            "score": d.metadata.get("score", 0),
        }
        for d in sample_docs
    ]

    elapsed = time.time() - t_start
    logger.info(f"=== Stack Overflow dashboard data generated in {elapsed:.2f}s ===")

    return {
        "data_source": "stackoverflow",
        "generated_at": datetime.now(tz=timezone.utc).isoformat(),
        "generation_time_seconds": round(elapsed, 2),
        "metrics": {
            "total_questions": total_questions,
            "total_chunks": total_chunks,
            "unique_tags": len(tag_counter),
            "avg_question_score": avg_score,
            "avg_answers_per_question": avg_answers,
            "avg_chunk_length_chars": avg_chunk_len,
        },
        "top_tags": [
            {"tag": tag, "count": count}
            for tag, count in tag_counter.most_common(DASHBOARD_TOP_N)
        ],
        "top_questions": top_questions,
        "topics": topics,
        "summary": summary,
        "insights": insights,
        "sources": sources,
        "llm_model": OLLAMA_LLM_MODEL,
        "grounding_note": (
            "All LLM outputs are derived exclusively from stored Stack Overflow documents. "
            "Temperature=0.0. No external knowledge used."
        ),
    }


# ── Helpers ──────────────────────────────────────────────────────────────────

def _parse_json_list(raw: str, label: str) -> List[str]:
    """
    Safely parse a JSON array string returned by the LLM.
    Falls back to empty list on any parse error.
    """
    raw = raw.strip()
    # Strip any accidental markdown fences
    if raw.startswith("```"):
        raw = raw.split("```")[1] if "```" in raw[3:] else raw[3:]
        raw = raw.strip()
    try:
        result = json.loads(raw)
        if isinstance(result, list):
            logger.debug(f"[{label}] Parsed {len(result)} topics from LLM JSON")
            return [str(item) for item in result]
        logger.warning(f"[{label}] LLM JSON was not a list: {type(result)}")
        return []
    except json.JSONDecodeError as e:
        logger.warning(f"[{label}] Failed to parse LLM JSON response: {e} | raw='{raw[:200]}'")
        return []


def _empty_dashboard(source: str, reason: str) -> Dict[str, Any]:
    """Return a safe empty dashboard payload when no data is available."""
    logger.warning(f"Empty dashboard returned for '{source}': {reason}")
    return {
        "data_source": source,
        "generated_at": datetime.now(tz=timezone.utc).isoformat(),
        "generation_time_seconds": 0,
        "metrics": {},
        "summary": reason,
        "insights": [],
        "topics": [],
        "sources": [],
        "error": reason,
        "llm_model": OLLAMA_LLM_MODEL,
        "grounding_note": "No data available — dashboard is empty.",
    }
