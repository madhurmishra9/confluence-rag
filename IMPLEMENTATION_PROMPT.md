# Prompt: Implement Confluence RAG Enhancement with Stack Overflow Integration

## Context
You have an existing Confluence RAG system (local LLM + ChromaDB + LangChain) that currently:
- Fetches ALL Confluence pages once on first run
- Requires manual DB deletion to update
- Has no incremental update capability
- Is limited to single source (Confluence only)

Reference: [ENHANCEMENT_PLAN.md](ENHANCEMENT_PLAN.md)

## Objective
Implement a **3-phase enhancement** to enable:
1. **Automatic incremental Confluence updates** (detect & fetch only new/modified pages)
2. **Independent Stack Overflow integration** (fetch Q&A from public Stack Exchange API)
3. **Smart cross-linking** (suggest related Confluence articles when querying Stack Overflow)

## Phase 1: Incremental Confluence Updates
**Goal:** Make the system fetch only changed pages on each run, reducing update time from 2-5 min to 5-30 seconds

**New/Modified Files:**
- `src/confluence_metadata.py` - Track page versions, modification times, fetch timestamps
- `src/fetch_confluence.py` - Compare metadata, return (new_docs, modified_docs, deleted_ids)
- `src/embed_and_store.py` - Add/remove/update documents incrementally
- `main.py` - Load metadata on startup, handle incremental updates

**Key Requirements:**
- Store `confluence_metadata.json` with page_id → {title, version, modified_time, fetched_at}
- Detect 3 types of changes: NEW pages, MODIFIED pages (version increased), DELETED pages (in metadata but not in API)
- Only embed new/modified docs, remove deleted docs from ChromaDB
- Preserve all page metadata (title, page_id, url, space_key)
- Error handling: gracefully handle API failures, metadata corruption, partial fetches

**Success Criteria:**
- First run: full fetch → embed → store (as current)
- Second run: incremental fetch (only changed) → embed (only new) → add to store (< 30 sec)
- Can detect page deletion and remove from vector store
- Metadata persists across sessions

---

## Phase 2: Stack Overflow Integration
**Goal:** Create independent SO fetcher that works standalone or integrated with Confluence

**New Files:**
- `src/fetch_stackoverflow.py` - Stack Exchange API client for Q&A
- `src/embed_and_store.py` - Extend with `stackoverflow_db/` collection
- `src/tag_linker.py` - Map SO tags to Confluence content
- `src/so_suggestions.py` - Generate Confluence suggestions for SO articles
- `main_so.py` - Independent SO RAG entry point
- `.env` - Add SO-specific settings

**Key Requirements:**
- Fetch by tags (e.g., "python", "api", "rest") from Stack Exchange API
- Extract: question title, body, answers, tags, score, link, answered_date
- Clean HTML (similar to Confluence fetcher)
- Store in separate ChromaDB collection: `stackoverflow_db/`
- Tag-to-Confluence mapping: When user asks about SO article, suggest related Confluence pages
- Respect API rate limits (300 req/month unauthenticated, 10k/month with key)
- Independent mode: `main_so.py` runs SO-only RAG
- Integrated mode: Can link SO articles to Confluence suggestions

**Success Criteria:**
- `main_so.py` fetches & queries Stack Overflow Q&A independently
- Separate vector store doesn't affect Confluence DB
- Tag matching finds Confluence articles related to SO questions
- Returns suggestions: "Based on this SO article, see these Confluence docs"
- No dependencies on Confluence being available

---

## Phase 3: Unified System
**Goal:** Create menu-driven interface to choose Confluence/SO/Both modes

**New Files:**
- `main_unified.py` - Main entry point with mode selection
- Updated `src/query.py` - Support querying both collections
- Updated documentation

**Key Requirements:**
- Interactive menu on startup:
  ```
  Select mode:
  1. Confluence RAG (search Confluence docs)
  2. Stack Overflow RAG (search Stack Overflow Q&A)
  3. Unified Mode (search both, show cross-linked suggestions)
  ```
- Mode 1: Current behavior (Confluence only)
- Mode 2: SO-only RAG
- Mode 3: Query both collections, show:
  - Primary answer from selected source
  - Suggestions from other source
  - Cross-referenced links
- All modes support incremental updates for their respective sources

**Success Criteria:**
- Single entry point for all modes
- Seamless switching between Confluence/SO/Unified
- Cross-source suggestions ranked by relevance
- Both sources stay synchronized with latest content

---

## Implementation Strategy

### File Organization
```
confluence-rag/
├── src/
│   ├── __init__.py
│   ├── fetch_confluence.py       (MODIFY - add incremental logic)
│   ├── fetch_stackoverflow.py     (CREATE - new SO fetcher)
│   ├── confluence_metadata.py     (CREATE - version tracking)
│   ├── embed_and_store.py         (MODIFY - add SO collection)
│   ├── tag_linker.py              (CREATE - tag mapping)
│   ├── so_suggestions.py          (CREATE - suggestion engine)
│   └── query.py                   (MODIFY - support both sources)
├── main.py                        (MODIFY - incremental updates)
├── main_so.py                     (CREATE - standalone SO mode)
├── main_unified.py                (CREATE - unified menu)
├── .env                           (MODIFY - add SO settings)
├── confluence_metadata.json       (CREATE at runtime)
├── stackoverflow_db/              (CREATE at runtime)
└── confluence_db/                 (existing)
```

### Dependencies Update
Add to `requirements.txt`:
- No new major dependencies (requests already present for SO API)
- All existing packages support the enhancements

### Environment Variables (.env additions)
```
# Stack Overflow
STACKOVERFLOW_TAGS=python,rest-api,json,api-design
STACKOVERFLOW_FETCH_LIMIT=1000
SO_RATE_LIMIT_KEY=              # Optional: your Stack Exchange API key
```

---

## Testing Checklist

### Phase 1 Tests
- [ ] First run creates metadata.json with all pages
- [ ] Second run detects zero changes (0 new, 0 modified)
- [ ] Modify Confluence doc, second run detects it
- [ ] Delete Confluence doc, system removes from vector store
- [ ] New Confluence doc, system embeds and adds
- [ ] Metadata corruption handled gracefully
- [ ] API failure doesn't corrupt existing DB

### Phase 2 Tests
- [ ] Stack Overflow fetcher retrieves Q&A by tag
- [ ] HTML parsing works correctly
- [ ] SO metadata captured (tags, score, link)
- [ ] ChromaDB SO collection independent
- [ ] Tag linker finds Confluence articles by SO tags
- [ ] Suggestion engine ranks by relevance
- [ ] Rate limit handling works

### Phase 3 Tests
- [ ] Menu displays correctly
- [ ] Mode 1 (Confluence) works
- [ ] Mode 2 (SO) works
- [ ] Mode 3 (Unified) shows cross-links
- [ ] Switching modes preserves both DBs

---

## Success Metrics

| Metric | Target |
|--------|--------|
| Incremental update time | < 30 sec |
| SO article fetch time | < 30 sec |
| Cross-suggestion latency | < 100 ms |
| Code coverage | > 80% |
| Documentation | Complete with examples |
| Error messages | Clear & actionable |

---

## Additional Notes

### Security
- Never expose API tokens in logs or errors
- Validate Stack Exchange API responses
- Rate limit protection for SO API
- All processing happens locally

### Performance
- Metadata lookups: O(1) hash lookup
- Tag matching: O(n) but cached in memory
- Suggestions: In-memory rank, no DB queries

### Extensibility
- Same pattern works for GitHub Docs, GitLab Wiki, etc.
- Pluggable tag linker (can add semantic matching)
- Modular design allows optional features

---

## Implementation Order (Recommended)
1. **Phase 1 Step 1:** Create `confluence_metadata.py` (version tracking)
2. **Phase 1 Step 2:** Update `fetch_confluence.py` (change detection)
3. **Phase 1 Step 3:** Update `embed_and_store.py` (incremental operations)
4. **Phase 1 Step 4:** Update `main.py` (orchestration)
5. **Phase 2 Step 1:** Create `fetch_stackoverflow.py` (SO API client)
6. **Phase 2 Step 2:** Create `embed_and_store.py` SO functions (SO collection)
7. **Phase 2 Step 3:** Create `tag_linker.py` (tag mapping)
8. **Phase 2 Step 4:** Create `so_suggestions.py` (suggestions)
9. **Phase 2 Step 5:** Create `main_so.py` (standalone SO entry)
10. **Phase 3 Step 1:** Create `main_unified.py` (unified menu)
11. **Phase 3 Step 2:** Update docs
12. **Testing & optimization**

---

## Questions to Guide Implementation

1. **Metadata tracking:** How to handle deleted pages that were never fetched? (Solution: Only delete from ChronoB if they exist)
2. **Incremental embeddings:** Should we re-chunk modified docs or assume chunk count stable? (Solution: Re-chunk, remove old chunks, add new)
3. **SO tags:** Fixed list or dynamic fetch from Stack Exchange tag API? (Solution: Fixed list in .env, user can extend)
4. **Suggestion ranking:** Keyword match or semantic similarity? (Solution: Start with keyword match, extend to semantic if needed)
5. **Rate limiting:** Cache SO responses or always fresh? (Solution: Cache with TTL, refresh on demand)

---

## Go/No-Go Decision
**Proceed with all 3 phases?**
- ✅ **GO** - Implement full enhancement (all files)
- ⚠️ **Phased** - Implement Phase 1 only, add SO later
- ⛔ **Stop** - Not proceeding at this time

**Recommended: GO** - All phases are independent and additive. Can deploy Phase 1, test, then add Phase 2.
