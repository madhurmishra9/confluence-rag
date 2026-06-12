# Confluence RAG — Enhanced (v2.3)

Local-LLM Confluence + Stack Overflow intelligence platform (Ollama, ChromaDB,
LangChain), extended with a full **Page Tools** suite: sorting, AI page
creation from code repositories, cross-space moves, **content quality
auditing/rating**, space-wide **quality reports**, and **safe page
optimization that never loses information**.

## What's in v2.3 (this package)

| New module | Capability |
| --- | --- |
| `src/page_manager.py` | List & **sort** pages (title/created/modified/space/id, asc/desc), move a page or **bulk-move** pages between spaces in either direction |
| `src/page_creator.py` | **Create a Confluence page from a code repo**: scans the source (tree, README, manifests, code excerpts), generates grounded documentation with your local LLM, converts to Confluence storage format, publishes or dry-runs to local HTML |
| `src/page_auditor.py` | **Audit & rate pages** on information quality, structure and ease of understanding for end users/customers (heuristics + LLM rubric, 0–100 + A–F grade); generate a **ranked quality report** for a whole space; **optimize a page** for readability while preserving every fact, link, table and code block |
| `main_unified.py` | New mode **5 — Page Tools** exposing all of the above interactively |

Everything from v2.2 remains: Confluence RAG, Stack Overflow RAG, unified
cross-linked search, and HTML dashboards (modes 1–4).

## Quick start

```bash
pip install -r requirements.txt
cp .env.example .env          # fill CONFLUENCE_URL / EMAIL / API_TOKEN
ollama serve                  # llama3.1:8b + nomic-embed-text
python main_unified.py        # choose 5 → Page Tools
```

## Page Tools menu

```
1. Browse & sort pages        — by title/created/modified/space
2. Create page from code repo — LLM-generated, grounded docs
3. Move a single page         — between spaces (either direction)
4. Move pages in bulk         — by space + optional title filter
5. Audit a page               — quality/structure/clarity score
6. Quality report for a space — rank all pages A–F for end users
7. Optimize a page            — improve readability, never lose data
```

## Safety model for optimization

Before any change the original storage XHTML is backed up to
`PAGE_BACKUP_DIR`; publishing is a Confluence **version bump**, so the previous
content stays in page history (one-click restore); a guard refuses to publish
if the rewrite is significantly shorter than the original; and the default is
a **dry-run** that writes the optimized HTML locally for review.

See `docs/USAGE.md`, `docs/ARCHITECTURE.md`, `docs/BENEFITS.md` and
`docs/EXECUTION_SNAPSHOTS.md`.
