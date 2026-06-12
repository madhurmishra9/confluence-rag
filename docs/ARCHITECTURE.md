# Architecture — Confluence RAG Enhanced (v2.3)

## Overview

```
main_unified.py
 ├─ modes 1–4 (v2.2): Confluence RAG · SO RAG · Unified · Dashboards
 │     src/fetch_confluence.py  src/fetch_stackoverflow.py
 │     src/embed_and_store.py (ChromaDB + nomic-embed-text)
 │     src/query.py (LangChain LCEL + llama3.1:8b, strict grounding)
 │     src/dashboard*.py
 └─ mode 5 (v2.3): Page Tools
       src/page_manager.py   list/sort + single & bulk cross-space moves
       src/page_creator.py   repo → grounded docs → storage format → page
       src/page_auditor.py   quality rating · space report · safe optimize
```

All LLM work runs on local Ollama; nothing leaves the machine.

## page_manager.py

REST `/rest/api/content` wrapper with pagination. `list_pages()` filters by
space and title substring and sorts client-side by any of
title/created/modified/space/id. `move_page()` updates the page's space with a
version bump and re-parents to the target space homepage; `move_pages()`
batches by explicit IDs or by source-space+filter, with per-page failure
accounting (`MoveResult`) so one bad page never aborts a migration.

## page_creator.py

Three stages, deliberately separable:
1. `scan_source()` — bounded digest of a repo: tree, README, manifests and
   code excerpts under PAGEGEN_* caps (keeps the local-LLM context sane).
2. `generate_documentation()` — temperature-0 prompt that forbids invention;
   output is grounded purely in the digest.
3. `markdown_to_storage()` — dependency-free Markdown → Confluence storage
   XHTML (headings, lists, code macros, bold, inline code), then publish or
   dry-run to local HTML.

## page_auditor.py

**Audit:** `_heuristic_scores()` computes structure, scanability, intro,
length and freshness scores (0–100 each) from the storage XHTML — fully
offline. `_llm_rubric()` adds clarity / completeness / structure /
audience-fit (0–10 each, JSON-forced, temperature 0) judged for an end user
or customer. Composite = 50/50 blend; heuristic-only when Ollama is down, so
audits never fail. Grades: A ≥85, B ≥70, C ≥55, D ≥40, F <40.

**Report:** `audit_space()` walks every page; `render_quality_report()` emits
grade distribution, a ranked table and per-page findings.

**Optimize (data-preserving by construction):**
```
backup original → LLM rewrite (strict preservation prompt, temp 0)
   → length guard (refuse if suspiciously shorter)
   → dry-run preview  OR  PUT version+1 (old version stays in history)
```
Three independent layers protect the content: the local backup file, the
Confluence version history, and the publish guard.

## Design decisions

| Decision | Rationale |
| --- | --- |
| Heuristics + LLM blend | Ratings stay useful offline; LLM adds the "would a customer understand this?" judgement heuristics can't. |
| Audit sorted worst-first internally, report ranked best-first | Workflows differ: fixing wants worst-first, showcasing wants best-first. |
| Optimize defaults to dry-run | A human approves every published rewrite. |
| Version-bump updates only | Confluence history is the ultimate undo; we never DELETE+recreate. |
| Markdown as the LLM interchange format | Local models produce far more reliable Markdown than storage XHTML; conversion is deterministic. |
