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

## Tech Stack

- **LLM**: Ollama (llama3.1:8b)
- **Embeddings**: Ollama (nomic-embed-text)
- **Vector Store**: ChromaDB (persisted locally)
- **Framework**: LangChain
- **API Client**: Requests
- **Secret Management**: python-dotenv

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
# Download and install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Start Ollama
ollama serve
```

**Windows**:
- Download the installer from https://ollama.ai/download/windows
- Run the installer and follow the steps
- Ollama will start automatically

### 2. Pull Required Models

In a new terminal (while Ollama is running):

```bash
# Pull the LLM
ollama pull llama3.1:8b

# Pull the embedding model
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

### 3. Python 3.8+

Check your Python version:
```bash
python --version
```

### 4. Confluence API Token

1. Go to https://id.atlassian.com/manage-profile/security/api-tokens
2. Create a new API token
3. Copy the token (save it somewhere safe)
4. You'll also need your Confluence URL and email

## Setup Instructions

### Windows

#### Step 1: Create Project Directory
```bash
cd C:\Users\YourUsername\Desktop
```

The `confluence-rag` folder is already created.

#### Step 2: Create Virtual Environment
```bash
cd confluence-rag
python -m venv venv
venv\Scripts\activate
```

You should see `(venv)` in your terminal.

#### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

#### Step 4: Configure Environment Variables

Edit the `.env` file (already created) and fill in your values:

```
CONFLUENCE_URL=https://your-domain.atlassian.net
CONFLUENCE_EMAIL=your-email@example.com
CONFLUENCE_API_TOKEN=your-api-token-here
```

Leave the other values as default (they should already be set correctly).

#### Step 5: Verify Ollama is Running

Make sure Ollama is running by checking:
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
2. Creates embeddings (this takes a few minutes depending on document size)
3. Saves to `confluence_db/`
4. Opens interactive query loop

**Subsequent runs**:
1. Loads existing vector store
2. Goes straight to query loop

#### Step 7: Query Your Documentation

Once the system is ready, type your questions:

```
📝 Your Question: What is the project architecture?
⏳ Searching and generating answer...
```

Type `exit` or `quit` to quit.

---

### Mac/Linux

#### Step 1: Ensure Ollama is Running

In one terminal:
```bash
ollama serve
```

In the models correctly installed.

#### Step 2: Navigate to Project
```bash
cd ~/Desktop/confluence-rag
```

(Or wherever you placed the `confluence-rag` folder)

#### Step 3: Create Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate
```

You should see `(venv)` in your terminal.

#### Step 4: Install Dependencies
```bash
pip install -r requirements.txt
```

#### Step 5: Configure Environment Variables

Edit the `.env` file and fill in your values:

```bash
nano .env
```

Or use your preferred editor:

```
CONFLUENCE_URL=https://your-domain.atlassian.net
CONFLUENCE_EMAIL=your-email@example.com
CONFLUENCE_API_TOKEN=your-api-token-here
```

Leave the other values as default.

#### Step 6: Verify Ollama is Running

In another terminal:
```bash
curl http://localhost:11434/api/tags
```

You should see your models listed.

#### Step 7: Run the System

Back in your project terminal:
```bash
python main.py
```

**First run**:
1. Fetches Confluence pages
2. Creates embeddings
3. Saves to `confluence_db/`
4. Opens query loop

**Subsequent runs**:
1. Loads vector store
2. Ready for queries

#### Step 8: Start Querying

Once ready:
```
📝 Your Question: How do I set up the development environment?
⏳ Searching and generating answer...
```

Type `exit` to quit.

---

## Detailed Configuration

### .env File Settings

```
# Confluence Connection
CONFLUENCE_URL=https://your-domain.atlassian.net
CONFLUENCE_EMAIL=your-email@example.com
CONFLUENCE_API_TOKEN=your-api-token-from-atlassian

# Ollama Configuration
OLLAMA_BASE_URL=http://localhost:11434  # Change if Ollama runs elsewhere
LLM_MODEL=llama3.1:8b                   # LLM model to use
EMBEDDING_MODEL=nomic-embed-text        # Embedding model to use

# Vector Database
CHROMA_DB_PATH=./confluence_db          # Local storage for vectors

# RAG Settings
RETRIEVAL_K=5                           # Number of chunks to retrieve
CHUNK_SIZE=500                          # Document chunk size
CHUNK_OVERLAP=50                        # Overlap between chunks
```

### Customizing Settings

#### Retrieve More Context
Increase `RETRIEVAL_K` to retrieve more chunks (slower but more context):
```
RETRIEVAL_K=10
```

#### Smaller/Larger Chunks
- **Smaller chunks** (e.g., `CHUNK_SIZE=250`): More precise but more retrieval overhead
- **Larger chunks** (e.g., `CHUNK_SIZE=1000`): Less precise but faster

#### Different Models

Use different Ollama models:
```
LLM_MODEL=mistral:7b        # Faster, good balance
LLM_MODEL=neural-chat       # Fast, good quality
LLM_MODEL=llama2:7b         # Basic model
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
1. Check your email is correct
2. Verify API token hasn't expired
3. Create a new API token at https://id.atlassian.com/manage-profile/security/api-tokens

### "Confluence URL not found" Error

**Problem**: Confluence API returns 404  
**Solution**: 
1. Check your CONFLUENCE_URL format: `https://your-domain.atlassian.net`
2. Make sure you're using the cloud URL, not on-premise
3. Verify you have access to the space

### No Documents Fetched

**Problem**: Fetching completes but no documents found  
**Solution**:
1. Verify Confluence credentials
2. Check that pages exist in your Confluence space
3. Check Confluence API permissions allow reading pages
4. Look at debug logs for specific errors

### ChromaDB Issues

**Problem**: "Vector store is empty" or "Vector database not found"  
**Solution**: 
```bash
# On Windows:
rmdir /s /q confluence_db
# On Mac/Linux:
rm -rf confluence_db
```

Then run `python main.py` again to reinitialize.

### Out of Memory

**Problem**: System runs out of memory during embedding  
**Solution**:
1. Reduce `CHUNK_SIZE`:
   ```
   CHUNK_SIZE=250
   ```
2. Try a smaller embedding model (if available)
3. Reduce number of Confluence pages if possible

### Slow Responses

**Problem**: Queries take a long time  
**Solution**:
1. Reduce `RETRIEVAL_K`:
   ```
   RETRIEVAL_K=3
   ```
2. Check system resources
3. Try a faster model:
   ```
   LLM_MODEL=mistral:7b
   ```

---

## Project Structure

```
confluence-rag/
├── .env                          # Configuration (secrets)
├── .gitignore                    # Git ignore rules
├── requirements.txt              # Python dependencies
├── main.py                       # Entry point
├── README.md                     # This file
│
├── src/
│   ├── __init__.py              # Package initialization
│   ├── fetch_confluence.py      # Confluence API client + fetching
│   ├── embed_and_store.py       # Chunking & ChromaDB operations
│   └── query.py                 # RAG chain & querying
│
└── confluence_db/               # ChromaDB storage (created on first run)
    └── [persisted vector data]
```

---

## How It Works

### Workflow Diagram

```
First Run:
┌─────────────────────────────────────────┐
│ 1. Fetch Confluence Pages               │
│    - REST API call                      │
│    - Paginate through all pages         │
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
│    - OllamaEmbeddings                   │
│    - ChromaDB.from_documents()          │
│    - Persist to ./confluence_db/        │
│    → Returns: ChromaDB instance         │
└──────────────────┬──────────────────────┘
                   ↓
        ┌──────────────────────┐
        │ Ready for Queries    │
        └──────────────────────┘

Subsequent Runs:
┌─────────────────────────────────────────┐
│ 1. Check if ./confluence_db/ exists     │
│ 2. Load ChromaDB                        │
│ 3. Create RAG chain                     │
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
│ 1. Embed question with OllamaEmbeddings  │
│ 2. Semantic search in ChromaDB (k=5)     │
│    → Returns: Top 5 related chunks       │
└────────────┬─────────────────────────────┘
             ↓
┌──────────────────────────────────────────┐
│ 3. Create prompt: context + question     │
│ 4. Send to Ollama LLM                    │
│    → Returns: Answer from context only   │
└────────────┬─────────────────────────────┘
             ↓
┌──────────────────────────────────────────┐
│ Display Answer + Source Documents       │
└──────────────────────────────────────────┘
```

### Key Features Explained

#### 1. Confluence Pagination
Handles large numbers of pages by using Confluence API's `limit` and `start` parameters.

#### 2. HTML Stripping
BeautifulSoup removes all HTML tags while preserving text content.

#### 3. Metadata Preservation
Each document chunk retains:
- `title`: Page title
- `page_id`: Confluence page ID
- `url`: Link to original page
- `source`: "confluence"

#### 4. SmartChunking
RecursiveCharacterTextSplitter tries to split on sentences, then paragraphs, then words:
```
Separators: ["\n\n", "\n", " ", ""]
```

#### 5. Context-Only Answers
Custom prompt template instructs the LLM to:
- ONLY use the provided Confluence context
- Say "I could not find this information in the Confluence documents" if answer isn't there
- Never use external knowledge

#### 6. Source Attribution
After each answer, shows which Confluence pages were used:
```
📚 SOURCES:
1. API Documentation
   URL: https://your-domain.atlassian.net/wiki/spaces/...
   Page ID: 123456
```

---

## Performance Tips

### Faster Initial Setup
1. Use a smaller document set first to test
2. Set `CHUNK_SIZE=1000` to create fewer chunks
3. Reduce `CHUNK_OVERLAP` to `25`

### Faster Queries
1. Lower `RETRIEVAL_K` (default is 5)
2. Use faster model: `mistral:7b` instead of `llama3.1:8b`
3. Lower LLM token prediction: reduces quality but faster

### Better Quality
1. Increase `RETRIEVAL_K` to 7-10
2. Use larger `CHUNK_SIZE` but smaller `CHUNK_OVERLAP`
3. Use higher quality model: `neural-chat` or `llama2:70b` (if system supports)

---

## Resetting the System

To completely reset and refetch from Confluence:

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

1. **Never commit `.env`** - It contains API tokens
2. **API Tokens** - Treat like passwords
3. **Ollama Access** - Runs on localhost by default (not exposed to network)
4. **ChromaDB** - Stored locally, no cloud upload

---

## Limitations & Future Improvements

### Current Limitations
- Only supports Confluence Cloud (not on-premise)
- Single space only (not multiple spaces)
- Requires Ollama models to be pulled manually
- No incremental updates (full fetch on reset)

### Potential Improvements
- Support for Confluence Server/On-Premise
- Multi-space support
- Incremental updates (new/modified pages only)
- Web UI instead of CLI
- API mode for integration with other apps
- Support for multiple embedding models
- Batch processing for large document sets

---

## Support & Issues

If you encounter issues:

1. Check that Ollama is running: `ollama serve`
2. Verify models are installed: `ollama list`
3. Check `.env` file has correct credentials
4. Look at the log messages for specific errors
5. Try resetting: `rm -rf confluence_db && python main.py`

---

## License

Free to use and modify

## Changelog

### v1.0.0 (Initial Release)
- Confluence integration with pagination
- ChromaDB vector store with persistence
- Ollama LLM and embedding integration
- Interactive query loop
- Source document attribution
- Error handling and logging
