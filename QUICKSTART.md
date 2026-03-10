# Quick Start Guide

Get your Confluence RAG system running in 5 minutes.

## Prerequisites

- Ollama installed and running: `ollama serve`
- Models pulled: `ollama pull llama3.1:8b` and `ollama pull nomic-embed-text`
- Python 3.8+
- Confluence API token from https://id.atlassian.com/manage-profile/security/api-tokens

## Setup (Windows)

```bash
# Activate virtual environment
cd confluence-rag
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Edit .env file with your Confluence details
# - CONFLUENCE_URL: https://your-domain.atlassian.net
# - CONFLUENCE_EMAIL: your-email@example.com
# - CONFLUENCE_API_TOKEN: your-api-token-here

# Run the system
python main.py
```

## Setup (Mac/Linux)

```bash
# Activate virtual environment
cd confluence-rag
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Edit .env file with your Confluence details
nano .env
# - CONFLUENCE_URL: https://your-domain.atlassian.net
# - CONFLUENCE_EMAIL: your-email@example.com
# - CONFLUENCE_API_TOKEN: your-api-token-here

# Run the system
python main.py
```

## First Run

The first run will:
1. ✅ Fetch all Confluence pages
2. ✅ Create embeddings (takes a few minutes)
3. ✅ Save to `confluence_db/`
4. ✅ Open query loop

## Query Loop

```
📝 Your Question: What is the project structure?
⏳ Searching and generating answer...
📋 ANSWER:
[LLM answer based on Confluence docs]

📚 SOURCES:
1. Documentation Page
   URL: https://your-domain.atlassian.net/wiki/spaces/...
   Page ID: 123456

📝 Your Question: exit
```

Type `exit` to quit.

## Subsequent Runs

Just run:
```bash
python main.py
```

It will detect the existing vector store and skip to queries immediately.

## Reset if Needed

Delete the vector database and refetch:

**Windows:**
```bash
rmdir /s /q confluence_db
python main.py
```

**Mac/Linux:**
```bash
rm -rf confluence_db
python main.py
```

---

For detailed documentation, see [README.md](README.md)
