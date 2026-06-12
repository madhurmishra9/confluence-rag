# Usage Guide — Confluence RAG Enhanced (v2.3)

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env
# Required: CONFLUENCE_URL, CONFLUENCE_EMAIL, CONFLUENCE_API_TOKEN
# Optional tuning: PAGEGEN_*, PAGE_BACKUP_DIR, PAGE_REPORT_DIR, OLLAMA_*
ollama serve && ollama pull llama3.1:8b && ollama pull nomic-embed-text
python main_unified.py
```

Modes 1–4 (RAG search and dashboards) are unchanged from v2.2.
Mode **5 — Page Tools** is the new suite.

## 1. Browse & sort pages

Pick a space (or all), a sort key — `title`, `created`, `modified`, `space`,
`id` — and order. Handles pagination automatically; prints ID, space, modified
timestamp and title.

## 2. Create a page from a code repo

Point it at any folder/repo/file. The scanner digests the tree, README and
manifests plus capped code excerpts (`PAGEGEN_MAX_FILES`,
`PAGEGEN_MAX_CHARS_PER_FILE`, `PAGEGEN_MAX_TOTAL_CHARS`), the local LLM writes
grounded documentation at temperature 0 (inventing content is forbidden in the
prompt), and the result is converted to Confluence storage format.
Choose **publish** to create the page, or **dry-run** to review the HTML in
`PAGEGEN_OUTPUT_DIR` first.

## 3 & 4. Move pages between spaces

Single page by ID, or bulk by source space + optional title filter — both
directions, with a preview list and confirmation before bulk moves. Each page
gets a version bump; failures are reported per page without aborting the batch.

## 5. Audit a page (quality rating)

Scores a page 0–100 with an A–F grade from two halves:

* **Heuristics** (always available, offline): structure (headings & hierarchy),
  scanability (lists/tables/code vs length), intro presence, length sanity,
  freshness.
* **LLM rubric** (when Ollama is up): clarity, completeness, structure and
  **audience fit for an end user/customer**, each 0–10 with a reviewer note
  and top suggested improvements.

## 6. Quality report for a space

Audits every page (up to your limit) and writes a Markdown report to
`PAGE_REPORT_DIR` containing the grade distribution, a **ranked best→worst
table**, per-page findings and the scoring rubric — ideal for content
clean-up sprints and identifying which pages confuse customers.

## 7. Optimize a page — without losing data

Rewrites a page for readability and end-user understanding under strict rules:
every fact, number, name, URL, table row, command and code block must be
preserved; code stays verbatim; links unchanged; structure is added (intro,
logical H2/H3 sections, lists).

Safety, in order:
1. Original storage XHTML is backed up to `PAGE_BACKUP_DIR/<id>_v<n>.html`.
2. Default is **dry-run** — optimized HTML lands in `PAGEGEN_OUTPUT_DIR` for review.
3. Publishing is a **version bump**; the previous version remains in
   Confluence page history and is restorable in one click.
4. A guard refuses to publish if the rewrite is much shorter than the original.

## Programmatic use

```python
from src.page_manager import ConfluencePageManager
from src.page_creator import create_page_from_source
from src.page_auditor import audit_page, generate_quality_report, optimize_page

pages = ConfluencePageManager().list_pages(space_key="PLAT", sort_by="modified")
create_page_from_source("~/repos/terrascope", "PLAT", publish=False)
a = audit_page("123456")                     # a.composite, a.grade, a.findings
generate_quality_report("PLAT", limit=200)   # ranked Markdown report
optimize_page("123456", publish=False)       # review preview, then publish=True
```
