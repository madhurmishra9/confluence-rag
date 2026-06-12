# Execution Snapshots

Real captured runs from the build environment. A live Confluence instance and
Ollama are not reachable from the sandbox, so snapshots exercise the
offline-capable parts (repo scanning, format conversion, sorting, heuristic
quality scoring, report rendering); network/LLM paths are the same code with
the endpoint swapped in.

## SNAP A — repo scan + Markdown→storage conversion (page creation pipeline)

```text
Repo: jira_suite | code files scanned: 14/15
Tree preview:
__init__.py
adf.py
base.py
bootstrap_env.py
bulk_loader.py
config.py
features.py
jira_api.py
Excerpt files: ['llm.py', 'base.py', 'jira_api.py', 'bootstrap_env.py', 'manage_common.py']

Storage-format output (first 300 chars):
<h1>Overview</h1><p>The <strong>jira_suite</strong> package automates ticket
creation.</p><h2>Key Components</h2><ul><li><code>tasks.py</code> — task
creation</li><li><code>llm.py</code> — Ollama enrichment</li></ul>
<ac:structured-macro ac:name="code"><ac:parameter ac:name="language">python</ac:para...
```

## SNAP B — page sorting

```text
Supported sort keys: ['created', 'id', 'modified', 'space', 'title']
sort_by=title    : Alpha overview (2026-06-10) | Module registry (2026-04-12) | Zeta runbook (2026-05-01)
sort_by=modified : Alpha overview (2026-06-10) | Zeta runbook (2026-05-01) | Module registry (2026-04-12)
```

## SNAP C — quality audit heuristics on three sample pages

```text
GCS Module Runbook     score= 98.0  grade=A  (structure 90, scanability 100, intro 100, length 100, freshness 100)
Old Notes              score= 47.0  grade=D  (structure 5, scanability 0, intro 100, length 100, freshness 30)
   • No headings — content is a wall of text.
   • Few lists/tables/code blocks — hard to scan.
   • Stale — last update 648 days ago.
Stub Page              score= 36.0  grade=F  (structure 20, scanability 0, intro 40, length 20, freshness 100)
   • No headings — content is a wall of text.
   • No orientation/intro paragraph for first-time readers.
   • Stub page (<50 words).
```

Ranked table from the generated space report:

```text
| Grade | Pages |
| A | 1 |
| D | 1 |
| F | 1 |
| # | Page | Score | Grade | Words | Updated (days ago) |
| 1 | GCS Module Runbook | 98.0 | A | 253 | 22  |
| 2 | Old Notes          | 47.0 | D | 900 | 648 |
| 3 | Stub Page          | 36.0 | F | 3   | 10  |
```

## SNAP D — new Page Tools menu (mode 5)

```text
1. Browse & sort pages        — by title/created/modified/space
2. Create page from code repo — LLM-generated, grounded docs
3. Move a single page         — between spaces (either direction)
4. Move pages in bulk         — by space + optional title filter
5. Audit a page               — quality/structure/clarity score
6. Quality report for a space — rank all pages A-F for end users
7. Optimize a page            — improve readability, never lose data
8. Back
```

All Python modules pass syntax verification (`ast.parse`) and the menu wiring
was validated end-to-end.
