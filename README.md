# Confluence + Stack Overflow RAG System

A local RAG (Retrieval-Augmented Generation) system that connects your Confluence documentation **and** Stack Overflow Q&A to a locally running Ollama LLM, enabling you to query both sources and get answers derived purely from that content — with zero cloud dependency.

## Features

- 🔗 **Confluence Integration**: Fetches all pages from your Confluence space using REST API
- 💻 **Stack Overflow Integration**: Fetches top questions and answers by tag from the Stack Exchange API
- 🧠 **Local LLM**: Uses Ollama with llama3.1:8b for completely private, offline processing
- 📚 **Smart Chunking**: RecursiveCharacterTextSplitter with configurable chunk size and overlap
- 🔍 **Vector Search**: ChromaDB for fast semantic search with persistent storage
- 🎯 **Zero Hallucination**: temperature=0.0 + strict context-only prompts — LLM never invents facts
- 🔄 **Incremental Updates**: Detects new, modified, and deleted Confluence pages — no full re-ingestion needed
- 🔀 **Cross-Linking**: Unified mode suggests related Confluence pages alongside Stack Overflow answers
- 📊 **On-Demand Dashboards**: Generates rich HTML dashboards with LLM-grounded summaries, topic extraction, bar charts, and cross-link mapping — opens automatically in your browser
- 📱 **Four Run Modes**: Confluence-only, Stack Overflow-only, Unified with cross-linking, or Dashboard
- ⚡ **Resumable**: Detects existing vector stores and skips fetch/embed on subsequent runs
- 📝 **Detailed Logging**: Every retrieval, LLM call, latency, and confidence score is logged

## Tech Stack

- **LLM**: Ollama via `langchain-ollama` (`ChatOllama`) — model: `llama3.1:8b`
- **Embeddings**: Ollama via `langchain-ollama` (`OllamaEmbeddings`) — model: `nomic-embed-text`
- **Vector Store**: ChromaDB via `langchain-chroma` (persisted locally, auto-persistence)
- **RAG Framework**: LangChain >= 1.0 with LCEL (LangChain Expression Language) chains
- **Confluence Client**: Requests + REST API
- **Stack Overflow Client**: Requests + Stack Exchange API v2.3
- **HTML Parsing**: BeautifulSoup4 + lxml
- **Secret Management**: python-dotenv

---

## Entry Points

| File | Purpose |
|---|---|
| `main_unified.py` | Unified interactive menu — Confluence, Stack Overflow, or both with cross-linking + dashboard |

> **Note**: `main_unified.py` is the single entry point for all modes. The older `main.py` and `main_so.py` are superseded by the unified runner.

---

## Prerequisites

### 1. Ollama Installation

**Mac** (Using Homebrew):
```bash
brew install ollama
ollama serve
```

**Linux** (Ubuntu/Debian):
```bash
curl -fsSL https://ollama.ai/install.sh | sh
ollama serve
```

**Windows**:
- Download the installer from https://ollama.ai/download/windows
- Run the installer — Ollama starts automatically

### 2. Pull Required Models

In a new terminal (while Ollama is running):

```bash
ollama pull llama3.1:8b
ollama pull nomic-embed-text
```

Verify:
```bash
ollama list
```

Expected output:
```
llama3.1:8b           ...
nomic-embed-text      ...
```

### 3. Python 3.9+

```bash
python --version
```

> **Note**: Python 3.9+ is required. `langchain-ollama` and `langchain-chroma` do not support Python 3.8.

### 4. Confluence API Token

1. Go to https://id.atlassian.com/manage-profile/security/api-tokens
2. Create a new API token
3. Save the token — you'll need it in `.env`

### 5. Stack Exchange API Key (Optional)

Without a key, the Stack Exchange API allows ~300 requests/day per IP. With a key, this increases to 10,000/day.

Register at https://stackapps.com/apps/oauth/register to get a key, then set `SO_RATE_LIMIT_KEY` in `.env`.

---

## Setup Instructions

### Windows

```bash
cd C:\Users\YourUsername\Desktop\confluence-rag
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

Edit `.env` and fill in your values (see Configuration section below).

Verify Ollama is running:
```bash
curl http://localhost:11434/api/tags
```

### Mac/Linux

```bash
cd ~/Desktop/confluence-rag
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Edit `.env`:
```bash
nano .env
```

---

## Running the System

### Mode 1 — Confluence Only

```bash
python main.py
```

**First run:**
1. Fetches all Confluence pages via REST API
2. Chunks and embeds them with `nomic-embed-text`
3. Saves to `./confluence_db/`
4. Opens interactive Q&A loop

**Subsequent runs:**
1. Loads existing `./confluence_db/`
2. Detects and syncs new/modified/deleted pages (incremental)
3. Opens Q&A immediately

```
You: What is the deployment process?
Thinking...
Assistant: The deployment process involves...

--- Sources ---
  - Deployment Guide
    https://your-domain.atlassian.net/wiki/spaces/ENG/pages/123456
```

Type `exit` or `quit` to stop.

---

### Mode 2 — Stack Overflow Only

```bash
python main_so.py
```

**First run:**
1. Fetches top-voted questions (and their answers) for the tags in `STACKOVERFLOW_TAGS`
2. Embeds and saves to `./stackoverflow_db/`
3. Opens interactive Q&A

**Subsequent runs:**
1. Loads existing `./stackoverflow_db/`
2. Opens Q&A immediately

> To refresh Stack Overflow data, delete `./stackoverflow_db/` and restart.

```
You: How do I handle pagination in REST APIs?
Thinking...
Assistant: Pagination in REST APIs is typically handled using...

--- Sources ---
  - How to implement pagination in a REST API?
    https://stackoverflow.com/questions/...
```

---

### Mode 3 — Unified Mode (Recommended)

```bash
python main_unified.py
```

Presents an interactive menu:

```
SELECT MODE:
  1. Confluence RAG       — Search Confluence documentation
  2. Stack Overflow RAG   — Search Stack Overflow Q&A
  3. Unified Mode         — Search both + cross-linked suggestions
  4. Dashboard            — Generate on-demand HTML dashboards
  5. Exit
```

**Unified Mode** queries both sources and shows:
- Answer from Confluence
- Answer from Stack Overflow
- Cross-linked Confluence page suggestions based on the SO result's tags

Type `back` to return to the menu, `exit` to quit.

---

### Mode 4 — Dashboard

Select **Dashboard** from the main menu. You will be prompted to choose:

```
  1. Confluence Dashboard
  2. Stack Overflow Dashboard
  3. Both (generate two dashboards)
  4. Back
```

The dashboard engine:
1. Retrieves all indexed documents from ChromaDB (no new API calls)
2. Computes metrics purely from metadata (page counts, tag frequencies, score distributions)
3. Runs grounded LLM calls (temperature=0.0) for executive summary, key topics, and bullet insights
4. Renders a self-contained HTML file in `./dashboards/` and opens it in your browser

Dashboard sections include:
- Stat cards (total pages/questions, chunks, spaces/tags, averages)
- Executive summary (LLM-generated, grounded in indexed content)
- Key topics (LLM-extracted, JSON array)
- Bar charts (top pages/tags by frequency, space/score distribution)
- Recently modified pages or highest-scored questions table
- Generation log (stage timings, doc counts, fallback notices)
- Cross-link tab (SO tags → related Confluence pages) when both sources are loaded

---

## Configuration

### Full `.env` Reference

```env
# ── Confluence ─────────────────────────────────────────────────────────────
CONFLUENCE_URL=https://your-domain.atlassian.net
CONFLUENCE_EMAIL=your-email@example.com
CONFLUENCE_API_TOKEN=your-api-token-from-atlassian
CONFLUENCE_SPACE_KEY=ENG          # Optional: leave empty to fetch all spaces

# ── Stack Overflow ──────────────────────────────────────────────────────────
STACKOVERFLOW_TAGS=python,api,rest-api,json,database   # Comma-separated tags
STACKOVERFLOW_FETCH_LIMIT=1000                          # Max questions per tag
SO_RATE_LIMIT_KEY=                                      # Optional Stack Exchange API key

# ── Ollama ──────────────────────────────────────────────────────────────────
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_LLM_MODEL=llama3.1:8b
OLLAMA_EMBED_MODEL=nomic-embed-text

# ── Vector Databases ────────────────────────────────────────────────────────
CHROMA_PERSIST_DIR=./confluence_db
STACKOVERFLOW_DB_PATH=./stackoverflow_db

# ── RAG Settings ────────────────────────────────────────────────────────────
RETRIEVER_K=5         # Chunks retrieved per query
CHUNK_SIZE=500        # Characters per chunk
CHUNK_OVERLAP=50      # Overlap between adjacent chunks

# ── Dashboard ───────────────────────────────────────────────────────────────
DASHBOARD_OUTPUT_DIR=./dashboards   # Where generated HTML dashboards are saved
DASHBOARD_MAX_DOCS=50               # Max docs fed to LLM for dashboard insights
DASHBOARD_TOP_N=10                  # Rows shown in ranked tables
LLM_SUMMARY_DOCS=20                 # Docs used for executive summary generation

# ── Logging ─────────────────────────────────────────────────────────────────
LOG_LEVEL=INFO
LOG_FILE=unified_rag.log
```

### Tuning Tips

| Goal | Setting |
|---|---|
| More context per answer | `RETRIEVER_K=8` |
| Faster embedding on first run | `CHUNK_SIZE=1000` |
| More precise retrieval | `CHUNK_SIZE=250` |
| Faster queries | `RETRIEVER_K=3` + `OLLAMA_LLM_MODEL=llama3.2:3b` |
| Narrow Confluence scope | `CONFLUENCE_SPACE_KEY=YOUR_KEY` |
| More SO content | Increase `STACKOVERFLOW_FETCH_LIMIT` |

### Alternative Ollama Models

```env
OLLAMA_LLM_MODEL=mistral:7b        # Fast, good balance
OLLAMA_LLM_MODEL=qwen2.5:7b        # Strong reasoning
OLLAMA_LLM_MODEL=llama3.2:3b       # Lightweight, good for low-RAM machines
OLLAMA_LLM_MODEL=llama3.1:70b      # Best quality (needs 48GB+ RAM)
```

Check what's installed: `ollama list`

---

## Project Structure

```
confluence-rag/
├── .env                           # Secrets & config — never commit this
├── .gitignore
├── requirements.txt               # Python dependencies
├── README.md                      # This file
│
├── main_unified.py                # Unified entry point — all four modes
│
├── src/
│   ├── __init__.py
│   ├── fetch_confluence.py        # Confluence REST API client + incremental fetch
│   ├── fetch_stackoverflow.py     # Stack Exchange API client
│   ├── embed_and_store.py         # Chunking, ChromaDB create/load/update operations
│   ├── query.py                   # LCEL RAG chain + ask() + ask_structured() helpers
│   ├── confluence_metadata.py     # Page-version tracker for incremental updates
│   ├── tag_linker.py              # Maps SO tags → Confluence keywords for cross-linking
│   ├── so_suggestions.py          # Suggestion engine: SO doc → related Confluence pages
│   ├── dashboard_generator.py     # Extracts grounded metrics + LLM insights from ChromaDB
│   └── dashboard.py               # Renders metrics/insights → self-contained HTML dashboard
│
├── dashboards/                    # Generated HTML dashboards (auto-created)
│   └── dashboard_<timestamp>.html
│
├── confluence_db/                 # ChromaDB for Confluence (auto-created)
│   └── [persisted vector data]
│
└── stackoverflow_db/              # ChromaDB for Stack Overflow (auto-created)
    └── [persisted vector data]
```

---

## How It Works

### Ingestion Pipeline

```
Confluence / Stack Overflow API
           │
           ▼
  fetch_confluence.py / fetch_stackoverflow.py
  - Paginated API requests
  - HTML stripped via BeautifulSoup
  - Returns List[Document] with metadata
           │
           ▼
  embed_and_store.py
  - RecursiveCharacterTextSplitter (CHUNK_SIZE, CHUNK_OVERLAP)
  - OllamaEmbeddings (nomic-embed-text)
  - Chroma.from_documents() → auto-persisted to disk
           │
           ▼
  ChromaDB (confluence_db/ or stackoverflow_db/)
```

### Query Pipeline (LCEL)

```
User Question
      │
      ▼
  retriever.invoke(question)          ← ChromaDB similarity search (top-k chunks)
      │
      ▼
  ChatPromptTemplate                  ← context + question → structured prompt
      │
      ▼
  ChatOllama (llama3.1:8b)            ← local inference, no internet needed
      │
      ▼
  StrOutputParser()                   ← clean string answer
      │
      ▼
  Display answer + source page links
```

The LCEL chain replaces the removed `RetrievalQA` class:

```python
qa_chain = (
    RunnablePassthrough.assign(source_documents=lambda x: retriever.invoke(x["question"]))
    .assign(answer=rag_chain_from_docs)
)
result = qa_chain.invoke({"question": "your question"})
# result["answer"]           → string answer
# result["source_documents"] → List[Document] with metadata
```

### Cross-Linking (Unified Mode)

```
SO answer returned
      │
      └─► top source Document → metadata["tags"] (e.g. ["python", "rest-api"])
                │
                ▼
          TagLinker.get_keywords_for_tags()
          → expands tags to keyword set
                │
                ▼
          SOSuggestionEngine.suggest_confluence_articles()
          → scores all Confluence docs by keyword match (title weighted 2×)
          → returns top-N matches with relevance score
                │
                ▼
          Displayed as "📚 Suggested Confluence Articles"
```

### Incremental Updates (Confluence)

`ConfluenceMetadataTracker` persists each page's `page_id`, `version`, and `modified` timestamp. On subsequent runs:

1. Fetch current page list from Confluence API
2. Compare versions against stored metadata
3. **New pages** → embed and add to ChromaDB
4. **Modified pages** → remove old chunks by `page_id`, re-embed and add
5. **Deleted pages** → remove chunks from ChromaDB

Only changed pages are processed — large spaces update in seconds.

---

## Troubleshooting

### "Connection refused" — Ollama not running
```bash
ollama serve
```

### "Authentication failed" — Confluence 401
1. Verify `CONFLUENCE_EMAIL` is your Atlassian account email
2. Regenerate your API token at https://id.atlassian.com/manage-profile/security/api-tokens

### "Confluence URL not found" — 404
- Use format `https://your-domain.atlassian.net` (no trailing slash, no `/wiki`)
- Must be Confluence Cloud, not Server/Data Center

### No Confluence documents fetched
1. Check credentials in `.env`
2. Try leaving `CONFLUENCE_SPACE_KEY` empty to fetch all spaces
3. Set `LOG_LEVEL=DEBUG` for detailed output

### No Stack Overflow documents fetched
1. Check internet connectivity
2. Verify `STACKOVERFLOW_TAGS` in `.env` uses valid SO tag names
3. You may have hit the anonymous rate limit — register for a free API key at https://stackapps.com/apps/oauth/register and set `SO_RATE_LIMIT_KEY`

### `ModuleNotFoundError` / `cannot import name ... from 'langchain_community'`
The project no longer uses `langchain-community` for Ollama or ChromaDB. Reinstall:
```bash
pip install -r requirements.txt
```

Required packages: `langchain-ollama`, `langchain-chroma`

### ChromaDB issues — empty or corrupt store
```bash
# Windows
rmdir /s /q confluence_db
rmdir /s /q stackoverflow_db

# Mac/Linux
rm -rf confluence_db stackoverflow_db
```
Then re-run the relevant entry point.

### Out of memory during embedding
1. Reduce `CHUNK_SIZE=250`
2. Limit Confluence scope: `CONFLUENCE_SPACE_KEY=YOUR_SPACE`
3. Reduce `STACKOVERFLOW_FETCH_LIMIT=100`

### Slow query responses
1. Reduce `RETRIEVER_K=3`
2. Switch to a lighter model: `OLLAMA_LLM_MODEL=llama3.2:3b`

---

## Resetting the System

**Reset Confluence store only:**
```bash
# Windows
rmdir /s /q confluence_db

# Mac/Linux
rm -rf confluence_db
```

**Reset Stack Overflow store only:**
```bash
# Windows
rmdir /s /q stackoverflow_db

# Mac/Linux
rm -rf stackoverflow_db
```

**Reset everything:**
```bash
# Mac/Linux
rm -rf confluence_db stackoverflow_db
python main_unified.py
```

---

## SO Intelligence Module (Module 7)

The **SO Intelligence** submodule (`so_intelligence/`) provides an automated pipeline for advanced Stack Overflow analysis, pattern detection, and report generation powered by local Ollama LLMs.

### Features

- 🔍 **Pattern Detection** — LLM-driven identification of trends, pain points, and recurring solutions
- ✅ **Solution Verification** — Evidence-based confidence scoring for suggested solutions
- 📊 **Temporal Analysis** — Before/after comparison to measure intervention impact
- 📄 **Multi-format Reports** — PDF and DOCX generation with charts and insights
- 🖥️ **REST API + Dashboard** — Web-based exploration of findings
- ⚡ **Caching & Recovery** — SQLite persistence with TTL, automatic retry logic

### Entry Points

The SO Intelligence module provides a unified CLI with four subcommands:

| Command | Purpose |
|---------|---------|
| `python -m so_intelligence run` | Execute the full analysis pipeline |
| `python -m so_intelligence serve` | Start API + web dashboard |
| `python -m so_intelligence status` | View system status and last run |
| `python -m so_intelligence validate-config` | Health check all dependencies |

### Quick Start

1. **Validate setup:**
   ```bash
   python -m so_intelligence validate-config
   ```
   All checks must pass before running the pipeline.

2. **Run analysis (default tags & last 30 days):**
   ```bash
   python -m so_intelligence run
   ```

3. **Run with specific tags and custom date range:**
   ```bash
   python -m so_intelligence run --tags cloudspanner alloydb --days 30
   ```

4. **Start dashboard:**
   ```bash
   python -m so_intelligence serve --open
   ```
   Opens browser at `http://localhost:8000`

### Configuration

SO Intelligence uses environment variables (same `.env` file). Required and optional settings:

| Variable | Default | Description |
|----------|---------|-------------|
| `SO_API_TOKEN` | *(none)* | **Required** — Stack Exchange API token |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama server URL |
| `OLLAMA_MODEL` | `llama3.1:70b` | Main LLM for analysis |
| `OLLAMA_EMBED_MODEL` | `nomic-embed-text` | Embedding model for semantic search |
| `OLLAMA_TEMPERATURE` | `0.0` | LLM temperature (0 = deterministic) |
| `OLLAMA_TIMEOUT` | `120` | Request timeout in seconds |
| `OLLAMA_MAX_RETRIES` | `3` | Retry attempts for failures |
| `DATE_RANGE_DAYS` | `30` | Historical data window |
| `CONFIDENCE_THRESHOLD` | `0.60` | Min. LLM confidence for findings |
| `CACHE_TTL_DAYS` | `90` | Cache validity duration |
| `LOG_LEVEL` | `INFO` | Logging verbosity |

Example `.env` additions:
```env
SO_API_TOKEN=your_stack_exchange_token
OLLAMA_MODEL=llama3.1:70b
CONFIDENCE_THRESHOLD=0.60
```

### Pipeline Stages

```
Fetch → Cache → Validate → Analyze → Verify → Compare → Report
```

1. **Fetch** — Retrieve SO questions/answers by tag from Stack Exchange API
2. **Cache** — Store in SQLite with TTL-based invalidation
3. **Validate** — Data quality checks; halt on critical anomalies
4. **Analyze** — LLM pattern detection (trends, pain points, solutions)
5. **Verify** — Evidence-based confidence scoring
6. **Compare** — Temporal analysis (before/after intervention date)
7. **Report** — Generate PDF/DOCX with charts and findings

### Advanced Usage

**Run with temporal comparison (measure intervention impact):**
```bash
python -m so_intelligence run --intervention 2024-01-15
```
Analyzes before vs. after the specified date and generates comparative insights.

**Force refresh (skip cache):**
```bash
python -m so_intelligence run --force-refresh
```

**Skip report generation:**
```bash
python -m so_intelligence run --no-report
```

**Custom port for dashboard:**
```bash
python -m so_intelligence serve --port 9000
```

### Troubleshooting

**Ollama not responding:**
```bash
curl http://localhost:11434/api/tags
# If fails, run: ollama serve
```

**Stack Overflow API token missing or invalid:**
1. Get a free token at https://stackapps.com/apps/oauth/register
2. Add to `.env`: `SO_API_TOKEN=your_token`
3. Run: `python -m so_intelligence validate-config`

**Rate limit hit (API error 429):**
- Stack Exchange allows 300 requests/day without a token, 10,000/day with one
- Cached data is reused for 90 days
- Wait 24 hours for quota reset or use cached results

**Models not found in Ollama:**
```bash
ollama pull llama3.1:70b
ollama pull nomic-embed-text
ollama list  # Verify
```

**Database locked error:**
- Ensure only one process is accessing the database
- Check for background Python processes: `ps aux | grep python`
- Reset if corrupted: `rm so_intelligence.db && python -m so_intelligence run`

### Output Files

After running the pipeline, outputs are generated:

| File | Description |
|------|-------------|
| `so_intelligence.db` | SQLite cache database |
| `analysis_report_*.pdf` | PDF report with findings and charts |
| `analysis_report_*.docx` | DOCX report (editable in Word) |
| `validation_errors_*.json` | Data validation issues (if halted) |

Reports are timestamped and include:
- Executive summary
- Pattern analysis by tag
- Top solutions with evidence scores
- Temporal comparison (if intervention date provided)
- Charts and statistics

---

## Security Notes

1. **Never commit `.env`** — it contains your Confluence API token
2. **API Tokens** — treat like passwords; rotate regularly
3. **Ollama** — runs on `localhost` only by default; not exposed to the network
4. **ChromaDB** — stored locally; no data leaves your machine
5. **Stack Exchange API** — read-only public data; no credentials required

---

## Limitations

- Confluence Cloud only (not Server/Data Center)
- Stack Overflow data is a point-in-time snapshot — delete `stackoverflow_db/` to refresh
- Requires Ollama models to be pulled manually before first run
- Terminal UI only — no web interface

---

## Support & Issues

1. Check Ollama is running: `ollama serve`
2. Verify models: `ollama list`
3. Check `.env` values
4. Enable verbose logging: `LOG_LEVEL=DEBUG`
5. Reset stores and retry (see Resetting section above)

---

## License

Free to use and modify

---

## Changelog

### v2.2.0
- **Bug fix — `query.py`**: Added `ask_structured()` and `NOT_FOUND_RESPONSE` exports that `dashboard.py` imports but were missing — would have caused `ImportError` at dashboard generation time
- **Bug fix — `dashboard.py`**: Added `OLLAMA_LLM_MODEL` config variable — it was referenced in the footer HTML template but never defined, causing `NameError` on render
- **Bug fix — `dashboard.py`**: Removed duplicate `from src.query import NOT_FOUND_RESPONSE` inside `_llm_generate_so_summary` (was imported twice in the same function)
- **Bug fix — `dashboard.py`**: Fixed bare `except: pass` clauses in `_extract_so_stats` — now correctly catches only `(TypeError, ValueError)` to avoid silently swallowing unrelated exceptions
- **Bug fix — `dashboard.py`**: Added proper `render_dashboard(data)` function — `main_unified.py` imports and calls `render_dashboard(data_dict)` but the module only had `generate_dashboard(vectorstore)`. The new function accepts pre-built data payloads from `dashboard_generator` and renders them to HTML
- **Bug fix — `dashboard_generator.py`**: Added `_safe_int()` helper and replaced all bare `int()` metadata casts — these would crash with `ValueError`/`TypeError` on malformed or missing metadata fields
- **README**: Updated entry points table (single `main_unified.py` entry point), project structure (added `dashboard.py`, `dashboard_generator.py`, `dashboards/` directory), running modes (added Mode 4 — Dashboard with full description), `.env` reference (added all dashboard and logging variables), and features list

### v2.1.0
- **Stack Overflow integration** — new `fetch_stackoverflow.py`, `main_so.py`
- **Unified mode** — new `main_unified.py` with interactive source selector
- **Cross-linking** — `tag_linker.py` maps SO tags to Confluence keywords; `so_suggestions.py` scores and surfaces related Confluence pages alongside SO answers
- **Fixed unified mode suggestion engine** — was always passing an empty document list; now correctly retrieves stored Confluence documents from ChromaDB using `collection.get(include=["documents","metadatas"])`
- **`fetch_stackoverflow.py`** — moved `import time` to top-level; cleaner timestamp handling; empty-tag guard on split
- **`tag_linker.py`** — extracted shared scoring into `_score_documents()` helper; removed duplicated loop logic
- **`so_suggestions.py`** — simplified scoring with `sum()` comprehension; stop-word filter applied at set construction time
- **New `.env` variables**: `STACKOVERFLOW_TAGS`, `STACKOVERFLOW_FETCH_LIMIT`, `SO_RATE_LIMIT_KEY`, `STACKOVERFLOW_DB_PATH`
- **Updated project structure** — two separate ChromaDB directories (`confluence_db/`, `stackoverflow_db/`)

### v2.0.0
- **Migrated to `langchain-ollama`** — replaces deprecated `langchain_community.llms.Ollama` and `langchain_community.embeddings.OllamaEmbeddings`
- **Migrated to `langchain-chroma`** — replaces deprecated `langchain_community.vectorstores.Chroma`
- **Replaced `RetrievalQA`** with LCEL pipeline — `RetrievalQA` was removed in LangChain >= 1.0
- **`ChatOllama`** replaces the old `Ollama` LLM class
- **Auto-persistence** — removed explicit `.persist()` calls (handled by `langchain-chroma`)
- **Incremental Confluence updates** — only changed pages are re-embedded
- **Python 3.9+ required**

### v1.0.0 (Initial Release)
- Confluence integration with pagination
- ChromaDB vector store with persistence
- Ollama LLM and embedding integration
- Interactive query loop
- Source document attribution
- Error handling and logging
