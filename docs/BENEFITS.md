# Benefits — Enhanced Confluence Tooling vs Manual

## Content quality management

| Activity | Manual | With v2.3 |
| --- | --- | --- |
| Judge whether a page is understandable to a customer | subjective, page-by-page reading | consistent 0–100 score + A–F grade, heuristic + LLM rubric |
| Find the worst pages in a space | nobody does it | one command → ranked report with findings |
| Improve a page without losing detail | risky hand-editing, ~30–60 min/page | LLM rewrite with hard preservation rules, backup + version history + publish guard |
| Document a code repo in Confluence | 1–3 h of writing | repo scan → grounded draft in minutes, dry-run review |
| Reorganise pages across spaces | click-per-page, error-prone | bulk move with preview, confirmation and per-page failure reporting |
| Keep an index of what's stale | tribal knowledge | freshness scoring + "days since update" in every report |

## Why ratings are trustworthy

Half the score is **deterministic heuristics** (structure, scanability, intro,
length, freshness) that anyone can verify against the page; the LLM half is
judged at temperature 0 against a fixed end-user rubric and degrades
gracefully to heuristic-only when the model is unavailable. Scores are
comparable across pages and over time — so a clean-up sprint can show measured
improvement, not vibes.

## Why optimization is safe

Nothing can be lost by design: the original is backed up locally **before**
any call; Confluence keeps the prior version in page history (instant
restore); the prompt forbids dropping facts/links/code; and a length guard
blocks publishing a rewrite that shrank suspiciously. Default dry-run keeps a
human in the loop.

## Privacy & cost

All generation, auditing and embedding run on your local Ollama models. No
page content leaves your machine; no per-token bills.
