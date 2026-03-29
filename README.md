# Confluence + Stack Overflow RAG System

A local RAG (Retrieval-Augmented Generation) system that connects your Confluence documentation **and** Stack Overflow Q&A to a locally running Ollama LLM, enabling you to query both sources and get answers derived purely from that content — with zero cloud dependency.

## Features

- 🔗 **Confluence Integration**: Fetches all pages from your Confluence space using REST API
- 💻 **Stack Overflow Integration**: Fetches top questions and answers by tag from the Stack Exchange API
- 🧠 **Local LLM**: Uses Ollama with llama3.1:8b for completely private, offline processing
- 📚 **Smart Chunking**: RecursiveCharacterTextSplitter with configurable chunk size and overlap
- 🔍 **Vector Search**: ChromaDB for fast semantic search with persistent storage
- 🎯 **Context-Aware**: Custom prompt ensures answers come only from your indexed content
- 🔄 **Incremental Updates**: Detects new, modified, and deleted Confluence pages — no full re-ingestion needed
- 🔀 **Cross-Linking**: Unified mode suggests related Confluence pages alongside Stack Overflow answers
- 📱 **Three Run Modes**: Confluence-only, Stack Overflow-only, or Unified with cross-linking
- ⚡ **Resumable**: Detects existing vector stores and skips fetch/embed on subsequent runs

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
| `main.py` | Confluence-only RAG with incremental updates |
| `main_so.py` | Stack Overflow-only RAG |
| `main_unified.py` | Interactive menu to choose Confluence, SO, or both with cross-linking |

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
  1. Confluence RAG       (Search your Confluence documentation)
  2. Stack Overflow RAG   (Search Stack Overflow Q&A)
  3. Unified Mode         (Search both + cross-linked suggestions)
  4. Exit
```

**Unified Mode** queries both sources and shows:
- Answer from Confluence
- Answer from Stack Overflow
- Cross-linked Confluence page suggestions based on the SO result's tags

Type `back` to return to the menu, `exit` to quit.

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

# ── Logging ─────────────────────────────────────────────────────────────────
LOG_LEVEL=INFO
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
├── main.py                        # Confluence-only entry point
├── main_so.py                     # Stack Overflow-only entry point
├── main_unified.py                # Unified mode with interactive menu
│
├── src/
│   ├── __init__.py
│   ├── fetch_confluence.py        # Confluence REST API client + incremental fetch
│   ├── fetch_stackoverflow.py     # Stack Exchange API client
│   ├── embed_and_store.py         # Chunking, ChromaDB create/load/update operations
│   ├── query.py                   # LCEL RAG chain + ask() helper
│   ├── confluence_metadata.py     # Page-version tracker for incremental updates
│   ├── tag_linker.py              # Maps SO tags → Confluence keywords for cross-linking
│   └── so_suggestions.py          # Suggestion engine: SO doc → related Confluence pages
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
