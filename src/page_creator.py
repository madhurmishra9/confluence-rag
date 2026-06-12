"""
src.page_creator
================
Create a brand-new Confluence page **by referring to a code repository or
other implementation source** — scan the source, generate grounded
documentation with the local Ollama LLM, and publish it as a page.

Sources supported
-----------------
* Local directory (a checked-out repo, a module folder, etc.)
* A single source file
The scanner extracts: directory tree, README content, dependency manifests
(requirements.txt / package.json / go.mod / *.tf), and the head of each
significant code file (capped so prompts stay within local-LLM context).

Grounding
---------
The LLM prompt forbids inventing components: it may only document what is
visible in the scanned excerpts (same zero-hallucination philosophy as the
RAG query chain — temperature 0.0).

Output
------
* publish=True  -> page created in the target space via REST (storage format)
* publish=False -> dry-run, HTML written to ./generated_pages/ for review
"""

from __future__ import annotations

import html
import logging
import os
import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import requests
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

CONFLUENCE_URL = os.getenv("CONFLUENCE_URL", "").rstrip("/")
CONFLUENCE_EMAIL = os.getenv("CONFLUENCE_EMAIL", "")
CONFLUENCE_API_TOKEN = os.getenv("CONFLUENCE_API_TOKEN", "")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_LLM_MODEL = os.getenv("OLLAMA_LLM_MODEL", "llama3.1:8b")

PAGEGEN_MAX_FILES = int(os.getenv("PAGEGEN_MAX_FILES", "25"))
PAGEGEN_MAX_CHARS_PER_FILE = int(os.getenv("PAGEGEN_MAX_CHARS_PER_FILE", "2500"))
PAGEGEN_MAX_TOTAL_CHARS = int(os.getenv("PAGEGEN_MAX_TOTAL_CHARS", "28000"))
PAGEGEN_OUTPUT_DIR = os.getenv("PAGEGEN_OUTPUT_DIR", "./generated_pages")

CODE_EXTENSIONS = {
    ".py", ".js", ".ts", ".tsx", ".jsx", ".go", ".java", ".kt", ".rb",
    ".tf", ".tfvars", ".yaml", ".yml", ".sh", ".sql", ".rs", ".c", ".cpp", ".cs",
}
MANIFESTS = {"requirements.txt", "package.json", "go.mod", "pyproject.toml",
             "pom.xml", "build.gradle", "Dockerfile", "Makefile"}
SKIP_DIRS = {".git", ".venv", "venv", "node_modules", "__pycache__", "dist",
             "build", ".terraform", "confluence_db", "stackoverflow_db", ".idea"}


class PageCreatorError(RuntimeError):
    pass


@dataclass
class RepoDigest:
    name: str
    tree: str
    readme: str
    manifests: Dict[str, str]
    file_excerpts: Dict[str, str]
    files_scanned: int
    files_total: int


# ── 1. Repository scanning ────────────────────────────────────────────
def scan_source(source_path: str) -> RepoDigest:
    root = Path(source_path).expanduser().resolve()
    if not root.exists():
        raise PageCreatorError(f"Source path not found: {root}")

    if root.is_file():
        text = _read_capped(root, PAGEGEN_MAX_CHARS_PER_FILE * 4)
        return RepoDigest(name=root.stem, tree=root.name, readme="",
                          manifests={}, file_excerpts={root.name: text},
                          files_scanned=1, files_total=1)

    tree_lines: List[str] = []
    code_files: List[Path] = []
    readme, manifests = "", {}

    for path in sorted(root.rglob("*")):
        rel = path.relative_to(root)
        if any(part in SKIP_DIRS for part in rel.parts):
            continue
        depth = len(rel.parts) - 1
        if path.is_dir():
            if depth < 3:
                tree_lines.append("  " * depth + f"{path.name}/")
            continue
        if depth < 4:
            tree_lines.append("  " * depth + path.name)
        lower = path.name.lower()
        if lower.startswith("readme") and not readme:
            readme = _read_capped(path, 4000)
        elif path.name in MANIFESTS:
            manifests[str(rel)] = _read_capped(path, 1200)
        elif path.suffix.lower() in CODE_EXTENSIONS:
            code_files.append(path)

    # Prefer shallow, larger files first — usually the most informative
    code_files.sort(key=lambda p: (len(p.relative_to(root).parts), -p.stat().st_size))
    excerpts: Dict[str, str] = {}
    budget = PAGEGEN_MAX_TOTAL_CHARS
    for path in code_files[:PAGEGEN_MAX_FILES]:
        if budget <= 0:
            break
        chunk = _read_capped(path, min(PAGEGEN_MAX_CHARS_PER_FILE, budget))
        excerpts[str(path.relative_to(root))] = chunk
        budget -= len(chunk)

    return RepoDigest(
        name=root.name, tree="\n".join(tree_lines[:200]), readme=readme,
        manifests=manifests, file_excerpts=excerpts,
        files_scanned=len(excerpts), files_total=len(code_files),
    )


def _read_capped(path: Path, cap: int) -> str:
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""
    return text[:cap]


# ── 2. Grounded LLM documentation generation ──────────────────────────
DOC_PROMPT = """You are a senior technical writer. Write a Confluence documentation page
in MARKDOWN for the implementation below.

STRICT RULES:
1. Document ONLY what is visible in the provided source material. Do NOT invent
   components, endpoints, configs or behaviours that are not in the excerpts.
2. Structure: # Overview, ## Architecture, ## Key Components, ## Configuration,
   ## Usage, ## Notes & Limitations.
3. In "Key Components", reference real file names from the excerpts.
4. Be concise and factual. No marketing language.

SOURCE MATERIAL
===============
Repository: {name}

Directory tree:
{tree}

README (may be empty):
{readme}

Dependency manifests:
{manifests}

Code excerpts ({scanned} of {total} code files):
{excerpts}

Now write the Markdown documentation page:"""


def generate_documentation(digest: RepoDigest, focus: str = "") -> str:
    manifests_block = "\n\n".join(f"--- {k} ---\n{v}" for k, v in digest.manifests.items()) or "(none)"
    excerpts_block = "\n\n".join(f"--- {k} ---\n{v}" for k, v in digest.file_excerpts.items()) or "(none)"
    prompt = DOC_PROMPT.format(
        name=digest.name, tree=digest.tree or "(flat)", readme=digest.readme or "(none)",
        manifests=manifests_block, excerpts=excerpts_block,
        scanned=digest.files_scanned, total=digest.files_total,
    )
    if focus:
        prompt += f"\n\nAdditional focus requested by the user: {focus}"

    try:
        resp = requests.post(f"{OLLAMA_BASE_URL}/api/generate", json={
            "model": OLLAMA_LLM_MODEL, "prompt": prompt, "stream": False,
            "options": {"temperature": 0.0},
        }, timeout=int(os.getenv("OLLAMA_TIMEOUT", "240")))
        resp.raise_for_status()
        markdown = (resp.json().get("response") or "").strip()
    except requests.exceptions.RequestException as exc:
        raise PageCreatorError(
            f"Ollama unavailable at {OLLAMA_BASE_URL} ({exc}). Start it with `ollama serve`."
        ) from exc

    if not markdown:
        raise PageCreatorError("LLM returned empty documentation")
    return markdown


# ── 3. Markdown -> Confluence storage format ──────────────────────────
def markdown_to_storage(markdown: str) -> str:
    """
    Minimal, dependency-free Markdown -> Confluence storage (XHTML)
    converter covering the structures the doc prompt produces:
    headings, paragraphs, bullet/numbered lists, fenced code, inline code, bold.
    """
    out: List[str] = []
    in_code, code_lang, code_buf = False, "", []
    in_ul = in_ol = False

    def close_lists():
        nonlocal in_ul, in_ol
        if in_ul: out.append("</ul>"); in_ul = False
        if in_ol: out.append("</ol>"); in_ol = False

    def inline(text: str) -> str:
        text = html.escape(text)
        text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
        text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
        return text

    for line in markdown.splitlines():
        if line.strip().startswith("```"):
            if in_code:
                body = html.escape("\n".join(code_buf))
                lang = code_lang or "none"
                out.append(
                    f'<ac:structured-macro ac:name="code">'
                    f'<ac:parameter ac:name="language">{lang}</ac:parameter>'
                    f'<ac:plain-text-body><![CDATA[{"".join(c + chr(10) for c in code_buf)}]]>'
                    f"</ac:plain-text-body></ac:structured-macro>"
                )
                _ = body
                in_code, code_buf, code_lang = False, [], ""
            else:
                close_lists()
                in_code = True
                code_lang = line.strip()[3:].strip()
            continue
        if in_code:
            code_buf.append(line)
            continue

        heading = re.match(r"^(#{1,4})\s+(.*)", line)
        if heading:
            close_lists()
            level = min(len(heading.group(1)), 4)
            out.append(f"<h{level}>{inline(heading.group(2))}</h{level}>")
            continue
        bullet = re.match(r"^\s*[-*]\s+(.*)", line)
        if bullet:
            if in_ol: out.append("</ol>"); in_ol = False
            if not in_ul: out.append("<ul>"); in_ul = True
            out.append(f"<li>{inline(bullet.group(1))}</li>")
            continue
        numbered = re.match(r"^\s*\d+\.\s+(.*)", line)
        if numbered:
            if in_ul: out.append("</ul>"); in_ul = False
            if not in_ol: out.append("<ol>"); in_ol = True
            out.append(f"<li>{inline(numbered.group(1))}</li>")
            continue
        if line.strip():
            close_lists()
            out.append(f"<p>{inline(line.strip())}</p>")
    close_lists()
    if in_code and code_buf:  # unterminated fence
        out.append("<p><code>" + html.escape(" ".join(code_buf))[:500] + "</code></p>")
    return "".join(out)


# ── 4. Publish ────────────────────────────────────────────────────────
def publish_page(space_key: str, title: str, storage_html: str,
                 parent_page_id: Optional[str] = None) -> Tuple[str, str]:
    if not (CONFLUENCE_URL and CONFLUENCE_EMAIL and CONFLUENCE_API_TOKEN):
        raise PageCreatorError("Confluence credentials missing in .env")
    payload: Dict = {
        "type": "page",
        "title": title,
        "space": {"key": space_key},
        "body": {"storage": {"value": storage_html, "representation": "storage"}},
    }
    if parent_page_id:
        payload["ancestors"] = [{"id": parent_page_id}]
    resp = requests.post(f"{CONFLUENCE_URL}/rest/api/content", json=payload,
                         auth=(CONFLUENCE_EMAIL, CONFLUENCE_API_TOKEN),
                         headers={"Content-Type": "application/json"}, timeout=30)
    if resp.status_code >= 400:
        raise PageCreatorError(f"Confluence create failed ({resp.status_code}): {resp.text[:300]}")
    data = resp.json()
    webui = (data.get("_links") or {}).get("webui", "")
    return str(data.get("id")), f"{CONFLUENCE_URL}/wiki{webui}"


# ── 5. One-call orchestration ─────────────────────────────────────────
def create_page_from_source(
    source_path: str,
    space_key: str,
    title: Optional[str] = None,
    focus: str = "",
    publish: bool = True,
    parent_page_id: Optional[str] = None,
) -> Dict[str, str]:
    """
    Scan source -> LLM docs -> storage HTML -> publish (or dry-run to disk).
    Returns {title, page_id?, url?, local_file?}.
    """
    t0 = time.monotonic()
    digest = scan_source(source_path)
    logger.info("Scanned %s: %d/%d code files, readme=%s",
                digest.name, digest.files_scanned, digest.files_total, bool(digest.readme))

    markdown = generate_documentation(digest, focus=focus)
    storage = markdown_to_storage(markdown)
    page_title = title or f"{digest.name} — Implementation Documentation"

    result = {"title": page_title}
    if publish:
        page_id, url = publish_page(space_key, page_title, storage, parent_page_id)
        result.update({"page_id": page_id, "url": url})
        logger.info("Published '%s' -> %s (%.1fs)", page_title, url, time.monotonic() - t0)
    else:
        out_dir = Path(PAGEGEN_OUTPUT_DIR)
        out_dir.mkdir(parents=True, exist_ok=True)
        safe = re.sub(r"[^\w\-]+", "_", page_title)[:80]
        out_file = out_dir / f"{safe}.html"
        out_file.write_text(
            f"<html><head><meta charset='utf-8'><title>{html.escape(page_title)}</title></head>"
            f"<body>{storage}</body></html>", encoding="utf-8",
        )
        result["local_file"] = str(out_file)
        logger.info("Dry-run: wrote %s (%.1fs)", out_file, time.monotonic() - t0)
    return result
