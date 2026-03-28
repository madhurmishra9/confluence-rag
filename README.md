# Confluence RAG System

A local RAG (Retrieval-Augmented Generation) system that connects your Confluence documentation to a locally running Ollama LLM, enabling you to query your Confluence pages and get answers derived purely from that content.

## Features

- 🔗 **Confluence Integration**: Fetches all pages from your Confluence space using REST API
- 🧠 **Local LLM**: Uses Ollama with llama3.1:8b for completely private processing
- 📚 **Smart Chunking**: RecursiveCharacterTextSplitter with configurable chunk size and overlap
- 🔍 **Vector Search**: ChromaDB for fast semantic search with persistent storage
- 🎯 **Context-Aware**: Custom prompt template ensures answers are derived only from Confluence content
- 📱 **Interactive Query Loop**: Simple terminal interface for asking questions
- ⚡ **Resumable**: Detects existing vector store and skips fetch/embed on subsequent runs
- 🔄 **Incremental Updates**: Detects new, modified, and deleted pages on each run — no full re-ingestion needed

## Tech Stack

- **LLM**: Ollama via `langchain-ollama` (`ChatOllama`)
- **Embeddings**: Ollama via `langchain-ollama` (`OllamaEmbeddings`) — model: `nomic-embed-text`
- **Vector Store**: ChromaDB via `langchain-chroma` (persisted locally)
- **Framework**: LangChain >= 1.0 with LCEL (LangChain Expression Language) chains
- **API Client**: Requests
- **Secret Management**: python-dotenv

---

## Prerequisites

### 1. Ollama Installation

**Mac** (Using Homebrew):
```bash
brew install ollama
```

Then start Ollama:
```bash
ollama serve
```

**Linux** (Ubuntu/Debian):
```bash
curl -fsSL https://ollama.ai/install.sh | sh
ollama serve
```

**Windows**:
- Download the installer from https://ollama.ai/download/windows
- Run the installer and follow the steps
- Ollama will start automatically

### 2. Pull Required Models

In a new terminal (while Ollama is running):

```bash
ollama pull llama3.1:8b
ollama pull nomic-embed-text
```

Verify the models are available:
```bash
ollama list
```

You should see:
```
llama3.1:8b           ...
nomic-embed-text      ...
```

### 3. Python 3.9+

Check your Python version:
```bash
python --version
```

> **Note**: Python 3.9+ is required. `langchain-ollama` and `langchain-chroma` do not support Python 3.8.

### 4. Confluence API Token

1. Go to https://id.atlassian.com/manage-profile/security/api-tokens
2. Create a new API token
3. Copy the token (save it somewhere safe)
4. You'll also need your Confluence URL and email

---

## Setup Instructions

### Windows

#### Step 1: Navigate to Project Directory
```bash
cd C:\Users\YourUsername\Desktop\confluence-rag
```

#### Step 2: Create Virtual Environment
```bash
python -m venv .venv
.venv\Scripts\activate
```

You should see `(.venv)` in your terminal.

#### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

#### Step 4: Configure Environment Variables

Edit the `.env` file and fill in your values:

```
CONFLUENCE_URL=https://your-domain.atlassian.net
CONFLUENCE_EMAIL=your-email@example.com
CONFLUENCE_API_TOKEN=your-api-token-here
```

Leave the other values as default.

#### Step 5: Verify Ollama is Running

```bash
curl http://localhost:11434/api/tags
```

You should see your models listed in the response.

#### Step 6: Run the System

```bash
python main.py
```

**First run** (initialization):
1. Fetches all Confluence pages
2. Creates embeddings (a few minutes depending on page count)
3. Saves to `confluence_db/`
4. Opens interactive query loop

**Subsequent runs**:
1. Loads existing vector store
2. Checks for new/modified/deleted pages — updates incrementally
3. Goes straight to query loop

#### Step 7: Query Your Documentation

```
You: What is the project architecture?
Thinking...
Assistant: The project architecture consists of...

--- Sources ---
  - Architecture Overview
    https://your-domain.atlassian.net/wiki/spaces/ENG/pages/123456
```

Type `exit` or `quit` to stop.

---

### Mac/Linux

#### Step 1: Ensure Ollama is Running

In one terminal:
```bash
ollama serve
```

#### Step 2: Navigate to Project

```bash
cd ~/Desktop/confluence-rag
```

#### Step 3: Create Virtual Environment
```bash
python3 -m venv .venv
source .venv/bin/activate
```

#### Step 4: Install Dependencies
```bash
pip install -r requirements.txt
```

#### Step 5: Configure Environment Variables

```bash
nano .env
```

Fill in:
```
CONFLUENCE_URL=https://your-domain.atlassian.net
CONFLUENCE_EMAIL=your-email@example.com
CONFLUENCE_API_TOKEN=your-api-token-here
```

#### Step 6: Verify Ollama is Running

```bash
curl http://localhost:11434/api/tags
```

#### Step 7: Run the System

```bash
python main.py
```

---

## Detailed Configuration

### .env File Settings

```
# Confluence Connection
CONFLUENCE_URL=https://your-domain.atlassian.net
CONFLUENCE_EMAIL=your-email@example.com
CONFLUENCE_API_TOKEN=your-api-token-from-atlassian
CONFLUENCE_SPACE_KEY=ENG          # Optional: leave empty for all spaces

# Ollama Configuration
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_LLM_MODEL=llama3.1:8b
OLLAMA_EMBED_MODEL=nomic-embed-text

# Vector Database
CHROMA_PERSIST_DIR=./confluence_db

# RAG Settings
RETRIEVER_K=5         # Number of chunks to retrieve per query
CHUNK_SIZE=500        # Document chunk size (characters)
CHUNK_OVERLAP=50      # Overlap between adjacent chunks

# Logging
LOG_LEVEL=INFO
```

### Customizing Settings

#### Retrieve More Context
```
RETRIEVER_K=10
```

#### Smaller/Larger Chunks
- **Smaller** (`CHUNK_SIZE=250`): More precise retrieval, more chunks stored
- **Larger** (`CHUNK_SIZE=1000`): Broader context per chunk, fewer chunks

#### Different Models
```
OLLAMA_LLM_MODEL=mistral:7b        # Faster, good balance
OLLAMA_LLM_MODEL=qwen2.5:7b        # Strong reasoning
OLLAMA_LLM_MODEL=llama3.2:3b       # Lightweight, faster on CPU
```

Check available models:
```bash
ollama list
```

---

## Troubleshooting

### "Connection refused" Error

**Problem**: Can't connect to Ollama
**Solution**: Make sure Ollama is running
```bash
ollama serve
```

### "Authentication failed" Error

**Problem**: Confluence API returns 401
**Solution**:
1. Check your email is correct in `.env`
2. Verify API token hasn't expired
3. Create a new token at https://id.atlassian.com/manage-profile/security/api-tokens

### "Confluence URL not found" Error

**Problem**: Confluence API returns 404
**Solution**:
1. Use the format `https://your-domain.atlassian.net` (no trailing slash, no `/wiki`)
2. Confirm you're using a Confluence Cloud URL

### No Documents Fetched

**Problem**: Fetching completes but 0 documents found
**Solution**:
1. Verify credentials are correct
2. Check pages exist in the target space
3. Leave `CONFLUENCE_SPACE_KEY` empty to fetch from all spaces
4. Enable `LOG_LEVEL=DEBUG` for more detail

### ChromaDB Issues

**Problem**: "Vector store is empty" or "Vector database not found"
**Solution**:
```bash
# Windows
rmdir /s /q confluence_db

# Mac/Linux
rm -rf confluence_db
```
Then run `python main.py` again to reinitialize.

### Import Errors / ModuleNotFoundError

**Problem**: Errors like `cannot import name 'OllamaEmbeddings' from 'langchain_community'`
**Solution**: This project requires the new dedicated integration packages. Reinstall dependencies:
```bash
pip install -r requirements.txt
```

Key packages required:
- `langchain-ollama` — provides `ChatOllama` and `OllamaEmbeddings`
- `langchain-chroma` — provides the `Chroma` vector store

### Out of Memory

**Problem**: System runs out of memory during embedding
**Solution**:
1. Reduce chunk size: `CHUNK_SIZE=250`
2. Filter to a single space: `CONFLUENCE_SPACE_KEY=YOUR_SPACE`

### Slow Responses

**Problem**: Queries take a long time
**Solution**:
1. Reduce `RETRIEVER_K=3`
2. Try a smaller/faster model: `OLLAMA_LLM_MODEL=llama3.2:3b`

---

## Project Structure

```
confluence-rag/
├── .env                          # Configuration (secrets) — never commit this
├── .gitignore
├── requirements.txt              # Python dependencies
├── main.py                       # Entry point
├── README.md                     # This file
│
├── src/
│   ├── __init__.py
│   ├── fetch_confluence.py       # Confluence REST API client
│   ├── embed_and_store.py        # Chunking & ChromaDB operations
│   ├── query.py                  # LCEL RAG chain & querying
│   └── confluence_metadata.py   # Incremental update tracker
│
└── confluence_db/                # ChromaDB storage (auto-created on first run)
    └── [persisted vector data]
```

---

## How It Works

### Workflow Diagram

```
First Run:
┌─────────────────────────────────────────┐
│ 1. Fetch Confluence Pages               │
│    - REST API with pagination           │
│    - Strip HTML, extract metadata       │
│    → Returns: List[Document]            │
└──────────────────┬──────────────────────┘
                   ↓
┌─────────────────────────────────────────┐
│ 2. Chunk Documents                      │
│    - RecursiveCharacterTextSplitter     │
│    - Configurable chunk_size & overlap  │
│    → Returns: List[Document]            │
└──────────────────┬──────────────────────┘
                   ↓
┌─────────────────────────────────────────┐
│ 3. Embed & Store                        │
│    - OllamaEmbeddings (nomic-embed-text)│
│    - Chroma.from_documents()            │
│    - Auto-persisted to ./confluence_db/ │
│    → Returns: Chroma instance           │
└──────────────────┬──────────────────────┘
                   ↓
        ┌──────────────────────┐
        │ Ready for Queries    │
        └──────────────────────┘

Subsequent Runs:
┌─────────────────────────────────────────┐
│ 1. Load existing ChromaDB               │
│ 2. Detect changes via metadata tracker  │
│    - Add new pages                      │
│    - Re-embed modified pages            │
│    - Remove deleted pages               │
│ 3. Build LCEL RAG chain                 │
└──────────────────┬──────────────────────┘
                   ↓
        ┌──────────────────────┐
        │ Ready for Queries    │
        └──────────────────────┘

Query Processing:
┌──────────────────────────────────────────┐
│ User Question                            │
└────────────┬─────────────────────────────┘
             ↓
┌──────────────────────────────────────────┐
│ 1. Semantic search in ChromaDB (k=5)     │
│    → Returns: Top-k related chunks       │
└────────────┬─────────────────────────────┘
             ↓
┌──────────────────────────────────────────┐
│ 2. Build prompt: context + question      │
│ 3. Send to ChatOllama (llama3.1:8b)      │
│    → Returns: Answer from context only   │
└────────────┬─────────────────────────────┘
             ↓
┌──────────────────────────────────────────┐
│ Display Answer + Source Page Links       │
└──────────────────────────────────────────┘
```

### RAG Chain (LCEL)

The query pipeline uses LangChain Expression Language (LCEL) instead of the removed `RetrievalQA` class:

```python
# Equivalent to the old RetrievalQA.from_chain_type(..., return_source_documents=True)
qa_chain = (
    RunnablePassthrough.assign(source_documents=retriever.invoke)
    .assign(answer=prompt | llm | StrOutputParser())
)
```

This gives full transparency into each step and makes it easy to swap any component.

### Key Design Decisions

- **`langchain-ollama`** is used instead of `langchain-community` for Ollama — the community wrappers are deprecated in LangChain >= 1.0
- **`langchain-chroma`** is used instead of `langchain-community` for ChromaDB — same reason
- **Auto-persistence** — `langchain-chroma >= 0.1` persists automatically; no `.persist()` calls needed
- **Incremental updates** — `ConfluenceMetadataTracker` stores page versions so only changed content is re-embedded
- **Context-only answers** — the prompt explicitly prohibits the LLM from using outside knowledge

---

## Performance Tips

### Faster Initial Setup
- Set `CHUNK_SIZE=1000` to create fewer chunks
- Filter to one space with `CONFLUENCE_SPACE_KEY`

### Faster Queries
- Lower `RETRIEVER_K=3`
- Use `OLLAMA_LLM_MODEL=llama3.2:3b` for a lighter model

### Better Quality
- Increase `RETRIEVER_K=8`
- Use `OLLAMA_LLM_MODEL=llama3.1:70b` if hardware allows

---

## Resetting the System

To completely reset and re-ingest from Confluence:

**Windows**:
```bash
rmdir /s /q confluence_db
python main.py
```

**Mac/Linux**:
```bash
rm -rf confluence_db
python main.py
```

---

## Security Notes

1. **Never commit `.env`** — it contains your Confluence API token
2. **API Tokens** — treat like passwords; rotate regularly
3. **Ollama** — runs on localhost by default, not exposed to the network
4. **ChromaDB** — stored locally, no cloud upload

---

## Limitations

- Only supports Confluence Cloud (not Server/Data Center)
- Requires Ollama models to be pulled manually before first run
- No web UI — terminal only

---

## Support & Issues

If you encounter issues:

1. Check that Ollama is running: `ollama serve`
2. Verify models are installed: `ollama list`
3. Check `.env` credentials
4. Enable debug logging: `LOG_LEVEL=DEBUG` in `.env`
5. Try resetting: `rm -rf confluence_db && python main.py`

---

## License

Free to use and modify

---

## Changelog

### v2.0.0
- **Migrated to `langchain-ollama`** — replaces deprecated `langchain_community.llms.Ollama` and `langchain_community.embeddings.OllamaEmbeddings`
- **Migrated to `langchain-chroma`** — replaces deprecated `langchain_community.vectorstores.Chroma`
- **Replaced `RetrievalQA`** with LCEL pipeline — `RetrievalQA` was removed in LangChain >= 1.0
- **`ChatOllama`** replaces the old `Ollama` LLM class for proper chat model support
- **Auto-persistence** — removed explicit `.persist()` calls (handled automatically by `langchain-chroma`)
- **Incremental updates** — new/modified/deleted Confluence pages are synced on every run without full re-ingestion
- **Python 3.9+ required** — updated minimum version requirement

### v1.0.0 (Initial Release)
- Confluence integration with pagination
- ChromaDB vector store with persistence
- Ollama LLM and embedding integration
- Interactive query loop
- Source document attribution
- Error handling and logging
