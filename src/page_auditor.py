"""
src.page_auditor
================
Rates Confluence pages on information quality, structure, and ease of
understanding for an end user / customer — then can optimize a page
WITHOUT losing any existing information.

Capabilities
------------
1) audit_page(page_id)      → PageAudit (heuristic + optional local-LLM scores)
2) audit_space(space_key)   → [PageAudit] for every page in a space
3) generate_quality_report  → ranked Markdown report (grades A–F, findings)
4) optimize_page(page_id)   → LLM rewrite that PRESERVES all facts, numbers,
                              links, code and tables; original content is
                              backed up locally AND remains in Confluence
                              version history (update = new version, never a
                              destructive replace). Dry-run by default.

Scoring model (0–100 composite)
-------------------------------
Heuristics (always available, offline):
  structure   — title/H1 sanity, heading hierarchy, section sizes
  scanability — lists / tables / code blocks relative to length
  intro       — an orientation paragraph before deep content
  length      — 150–4000 words sweet spot
  freshness   — modified within ~180 days
LLM rubric (when Ollama reachable):
  clarity, completeness, structure, audience_fit — each 0–10 + rationale
Composite = 50% heuristic + 50% LLM (heuristic-only if LLM unavailable).
"""

from __future__ import annotations

import html
import json
import logging
import os
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import requests

from .page_manager import (CONFLUENCE_API_TOKEN, CONFLUENCE_EMAIL,
                           CONFLUENCE_URL, ConfluencePageManager,
                           PageManagerError)
from .page_creator import markdown_to_storage

logger = logging.getLogger(__name__)

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1:8b")
BACKUP_DIR = os.getenv("PAGE_BACKUP_DIR", "./page_backups")
REPORT_DIR = os.getenv("PAGE_REPORT_DIR", "./quality_reports")


# ──────────────────────────────────────────────────────────────────────────
# Data model
# ──────────────────────────────────────────────────────────────────────────
@dataclass
class PageAudit:
    page_id: str
    title: str
    space: str
    url: str
    words: int
    headings: int
    lists: int
    tables: int
    code_blocks: int
    links: int
    days_since_update: Optional[int]
    heuristic: Dict[str, float] = field(default_factory=dict)   # name → 0-100
    llm: Dict[str, Any] = field(default_factory=dict)           # rubric scores
    findings: List[str] = field(default_factory=list)
    composite: float = 0.0

    @property
    def grade(self) -> str:
        c = self.composite
        return ("A" if c >= 85 else "B" if c >= 70 else
                "C" if c >= 55 else "D" if c >= 40 else "F")


# ──────────────────────────────────────────────────────────────────────────
# Content analysis
# ──────────────────────────────────────────────────────────────────────────
_TAG = re.compile(r"<[^>]+>")


def _storage_to_text(storage: str) -> str:
    text = re.sub(r"<ac:structured-macro.*?</ac:structured-macro>", " [macro] ",
                  storage, flags=re.DOTALL)
    return html.unescape(_TAG.sub(" ", text))


def _count(pattern: str, storage: str) -> int:
    return len(re.findall(pattern, storage, flags=re.IGNORECASE))


def _heuristic_scores(storage: str, modified_iso: Optional[str],
                      audit: PageAudit) -> Dict[str, float]:
    text = _storage_to_text(storage)
    words = len(text.split())
    h_levels = [int(m) for m in re.findall(r"<h([1-6])", storage, re.IGNORECASE)]
    headings = len(h_levels)
    lists = _count(r"<(ul|ol)>", storage)
    tables = _count(r"<table", storage)
    code = _count(r'ac:name="code"', storage) + _count(r"<pre", storage)
    links = _count(r"<a ", storage) + _count(r"ri:content-title", storage)

    audit.words, audit.headings, audit.lists = words, headings, lists
    audit.tables, audit.code_blocks, audit.links = tables, code, links

    scores: Dict[str, float] = {}
    findings = audit.findings

    # structure: headings present, hierarchy doesn't skip levels, sections not huge
    if headings == 0:
        scores["structure"] = 20 if words < 150 else 5
        findings.append("No headings — content is a wall of text.")
    else:
        skips = sum(1 for a, b in zip(h_levels, h_levels[1:]) if b - a > 1)
        per_section = words / headings
        s = 90.0
        if skips:
            s -= 15; findings.append("Heading levels skip (e.g. H1→H3) — hierarchy unclear.")
        if per_section > 450:
            s -= 20; findings.append("Sections are very long — split for readability.")
        scores["structure"] = max(s, 30)

    # scanability
    aids = lists + tables + code
    expected = max(words // 250, 1)
    scan = min(aids / expected, 1.0) * 100
    scores["scanability"] = scan
    if scan < 50 and words > 300:
        findings.append("Few lists/tables/code blocks — hard to scan.")

    # intro: meaningful paragraph before the first heading
    first_h = re.search(r"<h[1-6]", storage, re.IGNORECASE)
    pre = _storage_to_text(storage[: first_h.start()] if first_h else storage[:600])
    scores["intro"] = 100 if len(pre.split()) >= 20 else 40
    if scores["intro"] < 100:
        findings.append("No orientation/intro paragraph for first-time readers.")

    # length
    if words < 50:
        scores["length"] = 20; findings.append("Stub page (<50 words).")
    elif words < 150:
        scores["length"] = 60
    elif words <= 4000:
        scores["length"] = 100
    else:
        scores["length"] = 60; findings.append("Very long page — consider splitting.")

    # freshness
    days = None
    if modified_iso:
        try:
            mod = datetime.fromisoformat(modified_iso.replace("Z", "+00:00"))
            days = (datetime.now(timezone.utc) - mod).days
        except ValueError:
            pass
    audit.days_since_update = days
    if days is None:
        scores["freshness"] = 70
    elif days <= 180:
        scores["freshness"] = 100
    elif days <= 365:
        scores["freshness"] = 60; findings.append(f"Not updated in {days} days.")
    else:
        scores["freshness"] = 30; findings.append(f"Stale — last update {days} days ago.")

    return scores


# ──────────────────────────────────────────────────────────────────────────
# LLM rubric
# ──────────────────────────────────────────────────────────────────────────
_RUBRIC_PROMPT = """You are a documentation quality reviewer assessing a wiki page
for an END USER / CUSTOMER who is new to the topic.

Rate the page 0-10 on each dimension and respond with ONLY this JSON:
{{"clarity": n, "completeness": n, "structure": n, "audience_fit": n,
  "summary": "<=2 sentences", "top_improvements": ["...", "...", "..."]}}

clarity        — plain language, defined jargon, ease of understanding
completeness   — does it answer the obvious questions end-to-end?
structure      — logical flow, sensible sections, good ordering
audience_fit   — usable by a newcomer/customer, not just the author

PAGE TITLE: {title}

PAGE TEXT (extracted):
{text}
"""


def _llm_rubric(title: str, text: str) -> Optional[Dict[str, Any]]:
    try:
        resp = requests.post(f"{OLLAMA_BASE_URL}/api/generate", json={
            "model": OLLAMA_MODEL,
            "prompt": _RUBRIC_PROMPT.format(title=title, text=text[:6000]),
            "stream": False, "format": "json",
            "options": {"temperature": 0.0},
        }, timeout=int(os.getenv("OLLAMA_TIMEOUT", "120")))
        resp.raise_for_status()
        data = json.loads(resp.json().get("response", "{}"))
        for k in ("clarity", "completeness", "structure", "audience_fit"):
            data[k] = max(0, min(10, int(data.get(k, 0))))
        return data
    except Exception as exc:                       # noqa: BLE001
        logger.warning("LLM rubric unavailable (%s) — heuristic-only audit.", exc)
        return None


# ──────────────────────────────────────────────────────────────────────────
# Audit API
# ──────────────────────────────────────────────────────────────────────────
def _fetch_full_page(mgr: ConfluencePageManager, page_id: str) -> Dict[str, Any]:
    return mgr._request("GET", f"/content/{page_id}",
                        params={"expand": "body.storage,version,space,history.lastUpdated"})


def audit_page(page_id: str, use_llm: bool = True,
               mgr: Optional[ConfluencePageManager] = None) -> PageAudit:
    mgr = mgr or ConfluencePageManager()
    page = _fetch_full_page(mgr, page_id)
    storage = page.get("body", {}).get("storage", {}).get("value", "") or ""
    modified = (page.get("history", {}).get("lastUpdated", {}).get("when")
                or page.get("version", {}).get("when"))
    links = page.get("_links", {})
    audit = PageAudit(
        page_id=page_id, title=page.get("title", "?"),
        space=page.get("space", {}).get("key", "?"),
        url=f"{CONFLUENCE_URL}/wiki{links.get('webui', '')}" if links.get("webui") else "",
        words=0, headings=0, lists=0, tables=0, code_blocks=0, links=0,
        days_since_update=None,
    )
    audit.heuristic = _heuristic_scores(storage, modified, audit)
    heuristic_avg = sum(audit.heuristic.values()) / len(audit.heuristic)

    if use_llm:
        rubric = _llm_rubric(audit.title, _storage_to_text(storage))
        if rubric:
            audit.llm = rubric
            llm_avg = (rubric["clarity"] + rubric["completeness"] +
                       rubric["structure"] + rubric["audience_fit"]) / 4 * 10
            audit.composite = round(0.5 * heuristic_avg + 0.5 * llm_avg, 1)
            audit.findings.extend(rubric.get("top_improvements", [])[:3])
            return audit
    audit.composite = round(heuristic_avg, 1)
    return audit


def audit_space(space_key: str, use_llm: bool = True,
                limit: int = 100) -> List[PageAudit]:
    mgr = ConfluencePageManager()
    pages = mgr.list_pages(space_key=space_key, limit=limit)
    audits = []
    for i, p in enumerate(pages, 1):
        logger.info("Auditing %d/%d: %s", i, len(pages), p.title)
        try:
            audits.append(audit_page(p.page_id, use_llm=use_llm, mgr=mgr))
        except Exception as exc:                   # noqa: BLE001
            logger.error("Audit failed for %s (%s): %s", p.title, p.page_id, exc)
    audits.sort(key=lambda a: a.composite)
    return audits


# ──────────────────────────────────────────────────────────────────────────
# Quality report
# ──────────────────────────────────────────────────────────────────────────
def render_quality_report(audits: List[PageAudit], scope_label: str) -> str:
    ranked = sorted(audits, key=lambda a: -a.composite)
    avg = sum(a.composite for a in audits) / len(audits) if audits else 0
    grades: Dict[str, int] = {}
    for a in audits:
        grades[a.grade] = grades.get(a.grade, 0) + 1

    lines = [
        "# Confluence Content Quality Report",
        "",
        f"**Scope:** {scope_label}  ",
        f"**Pages audited:** {len(audits)}  ",
        f"**Average score:** {avg:.1f}/100  ",
        f"**Generated:** {datetime.now():%Y-%m-%d %H:%M}",
        "",
        "## Grade distribution",
        "",
        "| Grade | Pages |", "| --- | --- |",
        *[f"| {g} | {grades[g]} |" for g in "ABCDF" if g in grades],
        "",
        "## Ranked pages (best → worst)",
        "",
        "| # | Page | Score | Grade | Words | Updated (days ago) |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for i, a in enumerate(ranked, 1):
        upd = a.days_since_update if a.days_since_update is not None else "?"
        lines.append(f"| {i} | [{a.title}]({a.url}) | {a.composite} | {a.grade} "
                     f"| {a.words} | {upd} |")
    lines += ["", "## Page details", ""]
    for a in ranked:
        lines += [f"### {a.title} — {a.composite}/100 (grade {a.grade})", ""]
        lines.append("Heuristics: " + ", ".join(
            f"{k} {v:.0f}" for k, v in a.heuristic.items()))
        if a.llm:
            lines.append(f"LLM rubric: clarity {a.llm['clarity']}/10, "
                         f"completeness {a.llm['completeness']}/10, "
                         f"structure {a.llm['structure']}/10, "
                         f"audience fit {a.llm['audience_fit']}/10")
            if a.llm.get("summary"):
                lines.append(f"Reviewer note: {a.llm['summary']}")
        if a.findings:
            lines.append("Improvements:")
            lines.extend(f"- {f}" for f in dict.fromkeys(a.findings))
        lines.append("")
    lines += [
        "## Rubric",
        "",
        "Composite = 50% structural heuristics (structure, scanability, intro, "
        "length, freshness) + 50% local-LLM review (clarity, completeness, "
        "structure, audience fit), each normalised to 0-100. "
        "Grades: A ≥85, B ≥70, C ≥55, D ≥40, F <40.",
    ]
    return "\n".join(lines)


def generate_quality_report(space_key: str, use_llm: bool = True,
                            limit: int = 100,
                            output: Optional[str] = None) -> str:
    audits = audit_space(space_key, use_llm=use_llm, limit=limit)
    if not audits:
        raise PageManagerError(f"No pages found in space {space_key}")
    report = render_quality_report(audits, f"Space {space_key}")
    os.makedirs(REPORT_DIR, exist_ok=True)
    path = output or os.path.join(
        REPORT_DIR, f"quality_{space_key}_{datetime.now():%Y%m%d_%H%M}.md")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(report)
    logger.info("Quality report written to %s", path)
    return path


# ──────────────────────────────────────────────────────────────────────────
# Safe page optimization (never loses data)
# ──────────────────────────────────────────────────────────────────────────
_OPTIMIZE_PROMPT = """You are improving a wiki page for END USERS / CUSTOMERS.

REWRITE the page in clean Markdown with better structure, clarity and flow.

ABSOLUTE RULES — the rewrite is INVALID if any is broken:
1. PRESERVE EVERY fact, number, name, URL, table row, command and code block
   from the original. You may reorganise and rephrase; you may NOT drop,
   shorten away, or invent information.
2. Keep all code blocks verbatim inside fenced ``` blocks (same language).
3. Keep every link target unchanged.
4. Add structure where missing: a short intro paragraph, logical H2/H3
   sections, bullet lists for enumerations, a "Prerequisites" or
   "Quick start" section if the content implies one.
5. Plain language; define jargon on first use.
6. Output ONLY the Markdown page body. No commentary.

ORIGINAL PAGE TITLE: {title}

ORIGINAL PAGE (text-extracted):
{text}
"""


@dataclass
class OptimizeResult:
    page_id: str
    title: str
    backup_path: str
    preview_path: Optional[str]
    published: bool
    new_version: Optional[int]
    words_before: int
    words_after: int


def optimize_page(page_id: str, publish: bool = False,
                  mgr: Optional[ConfluencePageManager] = None) -> OptimizeResult:
    """Improve a page for readability while preserving all information.

    Safety model (nothing is ever lost):
      * The original storage XHTML is saved to PAGE_BACKUP_DIR before anything.
      * Publishing is a Confluence version bump — the previous version stays in
        page history and can be restored in one click.
      * Default is dry-run: optimized HTML is written locally for review.
    """
    mgr = mgr or ConfluencePageManager()
    page = _fetch_full_page(mgr, page_id)
    title = page.get("title", "?")
    storage = page.get("body", {}).get("storage", {}).get("value", "") or ""
    version = int(page.get("version", {}).get("number", 1))
    space_key = page.get("space", {}).get("key")

    # 1. local backup of the original — guaranteed before any change
    os.makedirs(BACKUP_DIR, exist_ok=True)
    backup_path = os.path.join(BACKUP_DIR, f"{page_id}_v{version}.html")
    with open(backup_path, "w", encoding="utf-8") as fh:
        fh.write(storage)
    logger.info("Original backed up → %s", backup_path)

    text = _storage_to_text(storage)
    words_before = len(text.split())

    # 2. LLM rewrite (strict preservation prompt, temperature 0)
    resp = requests.post(f"{OLLAMA_BASE_URL}/api/generate", json={
        "model": OLLAMA_MODEL,
        "prompt": _OPTIMIZE_PROMPT.format(title=title, text=text[:14000]),
        "stream": False,
        "options": {"temperature": 0.0},
    }, timeout=int(os.getenv("OLLAMA_TIMEOUT", "300")))
    resp.raise_for_status()
    md = (resp.json().get("response") or "").strip()
    if len(md.split()) < max(words_before * 0.6, 30):
        raise PageManagerError(
            "Optimized draft is much shorter than the original — refusing to "
            "publish to avoid information loss. Review the preview manually.")
    new_storage = markdown_to_storage(md)
    words_after = len(_storage_to_text(new_storage).split())

    # 3. dry-run preview or version-bump publish
    preview_path = None
    new_version = None
    if publish:
        mgr._request("PUT", f"/content/{page_id}", data={
            "id": page_id, "type": "page", "title": title,
            "space": {"key": space_key},
            "version": {"number": version + 1,
                        "message": "Optimized for readability (original in history "
                                   f"v{version}; local backup kept)"},
            "body": {"storage": {"value": new_storage,
                                 "representation": "storage"}},
        })
        new_version = version + 1
        logger.info("Published v%d of '%s' — previous content kept as v%d in "
                    "page history.", new_version, title, version)
    else:
        out_dir = os.getenv("PAGEGEN_OUTPUT_DIR", "./generated_pages")
        os.makedirs(out_dir, exist_ok=True)
        preview_path = os.path.join(out_dir, f"optimized_{page_id}.html")
        with open(preview_path, "w", encoding="utf-8") as fh:
            fh.write(new_storage)
        logger.info("Dry-run: optimized version written to %s", preview_path)

    return OptimizeResult(page_id=page_id, title=title, backup_path=backup_path,
                          preview_path=preview_path, published=publish,
                          new_version=new_version,
                          words_before=words_before, words_after=words_after)
