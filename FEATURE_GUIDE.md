# Feature Guide: Incremental Updates & Stack Overflow Integration

A quick guide to the new features added to Confluence RAG.

---

## 🆕 Feature 1: Automatic Incremental Confluence Updates

### What's New?
Instead of fetching all Confluence pages every run, the system now:
- ✅ Detects which pages are NEW
- ✅ Detects which pages are MODIFIED (version increased)
- ✅ Detects which pages are DELETED
- ✅ Only embeds changed pages
- ✅ Updates vector store automatically

### Performance Impact
| Scenario | Time |
|----------|------|
| First run (initial fetch) | 2-5 minutes |
| Second run (no changes) | 10-20 seconds |
| Second run (5 new pages) | 1-2 minutes total |
| Second run (1 modified page) | 30-40 seconds total |

### How to Use
```bash
# Just run as before - incremental updates happen automatically!
python main.py
```

**That's it!** The system automatically:
1. Loads existing vector store
2. Checks for changes in Confluence
3. Updates only what changed
4. Persists metadata

### Metadata Tracking
The system creates `confluence_metadata.json`:
```json
{
  "last_fetch": "2026-03-15T10:35:00Z",
  "pages": {
    "123456": {
      "page_id": "123456",
      "title": "API Documentation",
      "version": 5,
      "modified": "2026-03-15T10:30:00Z",
      "url": "https://...",
      "space_key": "TECH",
      "fetched_at": "2026-03-15T10:35:00Z"
    }
  }
}
```

### Reset Metadata
If metadata gets corrupted:
```bash
# Delete both to reset completely
rm confluence_metadata.json
rm -rf confluence_db

# Re-initialize
python main.py
```

---

## 🆕 Feature 2: Stack Overflow Integration

### What's New?
Brand new Stack Overflow RAG system that:
- ✅ Fetches Q&A from Stack Overflow by topic tags
- ✅ Stores in separate vector database
- ✅ Works completely independently (without Confluence)
- ✅ Can suggest related Confluence articles by tags
- ✅ Respects API rate limits

### Structure
```
Confluence Database          Stack Overflow Database
./confluence_db/      OR     ./stackoverflow_db/
(Questions only)             (Q&A pairs)
```

### SO Configuration in .env
```env
# Which topics to fetch (comma-separated)
STACKOVERFLOW_TAGS=python,json,api,rest-api,database,javascript,testing

# Max questions per tag
STACKOVERFLOW_FETCH_LIMIT=1000

# Optional: Your Stack Exchange API key (for higher limits)
SO_RATE_LIMIT_KEY=
```

**Default tags:** python, json, api, rest-api, database, javascript, testing, authentication

### How to Use - Stack Overflow Only

**Run SO RAG in standalone mode:**
```bash
python main_so.py
```

**First run:**
1. Fetches Q&A by tags (~10-30 seconds)
2. Embeds documents (~1-2 minutes)
3. Saves to `./stackoverflow_db/`
4. Opens query loop

**Subsequent runs:**
1. Loads existing database (fast)
2. Opens query loop

**What you can ask:**
```
You: how do I parse JSON in Python?
Assistant: [Answers from Stack Overflow Q&A]
Sources: (relevant Stack Overflow questions)
```

---

## 🆕 Feature 3: Unified System (Confluence + Stack Overflow)

### What's New?
A menu-driven system that lets you:
- ✅ Query Confluence documentation
- ✅ Query Stack Overflow Q&A
- ✅ Query both simultaneously
- ✅ Get cross-linked suggestions

### How to Use - Unified Mode

**Run unified system:**
```bash
python main_unified.py
```

**You'll see a menu:**
```
============================================================
              UNIFIED RAG SYSTEM
         Confluence + Stack Overflow Integration
              Powered by Local Ollama LLM
============================================================

SELECT MODE:
  1. Confluence RAG       (Search your documentation)
  2. Stack Overflow RAG   (Search Stack Overflow Q&A)
  3. Unified Mode         (Search both + suggestions)
  4. Exit
```

### Mode 1: Confluence RAG
- Query your Confluence documentation
- Get answers from your internal docs
- See sources with links

**Example:**
```
You: What's the system architecture?
Assistant: [From Confluence docs]
Sources:
1. Architecture Design
   https://your-confluence.com/...
```

### Mode 2: Stack Overflow RAG
- Query Stack Overflow Q&A
- Get real-world programming solutions
- See source links and vote counts

**Example:**
```
You: How to optimize database queries?
Assistant: [From Stack Overflow answers]
Sources:
1. Query Optimization Techniques
   https://stackoverflow.com/questions/...
   Score: 1250
```

### Mode 3: Unified Mode (Recommended!)
- Choose source per query
- See answers from both
- Get automatic cross-suggestions

**Usage:**
```
SELECT MODE:
  1. Confluence RAG
  2. Stack Overflow RAG
  3. Unified Mode
  0. Query Both

Source (0-2): 3    # Query Stack Overflow

Select source (or '0' for both):
  1. Query Confluence
  2. Query Stack Overflow
  0. Query Both

Source (0-2): 2    # Stack Overflow

Your question: How to build a REST API?

========= STACK OVERFLOW ANSWER: =========
[Answer from SO Q&A]

📚 STACK OVERFLOW SOURCES:
1. REST API Best Practices
   https://stackoverflow.com/questions/...

📚 Suggested Confluence Articles:
1. Our API Design Guide
   https://our-confluence/...
   Relevance: 0.92
```

---

## 🔗 How Tag-Based Linking Works

### Tag Mapping System
Stack Overflow tags are automatically mapped to Confluence topics:

**SO Tag → Confluence Keywords:**
```
"python"      → ["python", "django", "flask", "fastapi"]
"api"         → ["api", "endpoint", "rest", "graphql"]
"database"    → ["database", "sql", "postgresql", "mongodb"]
"testing"     → ["test", "unit test", "pytest"]
"authentication" → ["auth", "jwt", "oauth", "security"]
```

### How Suggestions Work
1. You query a Stack Overflow article with tags: `["python", "api"]`
2. System extracts those tags
3. Maps to keywords: `["python", "django", "api", "endpoint", ...]`
4. Searches Confluence docs for matches
5. Ranks by relevance (0-1 score)
6. Shows top 5 suggestions

**Example:**
```
SO Question Tags: [python, json, api]
           ↓
Search Confluence for: python, django, json, api, endpoint, rest
           ↓
Found matches:
  1. "Python REST API Guide" - Score: 0.95
  2. "JSON Parsing Best Practices" - Score: 0.87
  3. "API Documentation" - Score: 0.82
```

---

## ⚙️ Configuration Tips

### Customize Stack Overflow Tags
Edit `.env`:
```env
# Fetch only Python and JavaScript questions
STACKOVERFLOW_TAGS=python,javascript

# Or more comprehensive
STACKOVERFLOW_TAGS=python,javascript,typescript,nodejs,rest-api,graphql
```

### Get Higher SO API Limits
By default, Stack Exchange API allows 300 requests/month (unauthenticated).

To get 10,000 requests/month:
1. Register app at: https://stackapps.com/apps/oauth/register
2. Get your API key
3. Add to `.env`:
```env
SO_RATE_LIMIT_KEY=your_key_here
```

### Adjust Chunking
For better results in SO Q&A, you might want smaller chunks:
```env
CHUNK_SIZE=300    # Smaller chunks for Q&A
CHUNK_OVERLAP=30
```

### Customize Retrieval
How many Sources to show:
```env
RETRIEVER_K=3     # Show top 3 sources (default: 5)
```

---

## 📊 Database Management

### Check Database Sizes
```bash
# Confluence
du -sh confluence_db/      # E.g., 150MB for 500 pages

# Stack Overflow
du -sh stackoverflow_db/    # E.g., 200MB for 1000 Q&A pairs

# Both
du -sh *.db/
```

### Clear Stack Overflow Cache
```bash
# Delete and rebuild SO database
rm -rf stackoverflow_db/
python main_so.py
```

### Clear Confluence Cache
```bash
# Delete both files to rebuild
rm confluence_metadata.json
rm -rf confluence_db/
python main.py
```

### Clear Everything
```bash
# Start fresh with both systems
rm confluence_metadata.json
rm -rf confluence_db/
rm -rf stackoverflow_db/

# Reinitialize
python main_unified.py  # Creates both on first use
```

---

## 🐛 Common Issues & Solutions

### "No Stack Overflow documents found"
- **Problem:** SO tags are invalid or no matching questions
- **Solution:** 
  ```bash
  # Check tags
  echo $STACKOVERFLOW_TAGS
  
  # Try popular tags
  # Good: python, javascript, api, json, rest-api, database
  # Bad: mycompany, obscure-topic-xyz
  ```

### Incremental fetch taking too long
- **Problem:** Changed many pages at once
- **Solution:** 
  ```bash
  # This is expected - embedding takes time
  # Try resetting to see improvement on next run
  rm confluence_metadata.json
  python main.py  # Fresh fetch, then next run will be fast
  ```

### Suggestions not showing
- **Problem:** Tags don't match Confluence content
- **Solution:**
  - SO articles with generic tags (python, api)
  - Confluence docs with very specific titles
  - Suggestions use keyword matching - similar content helps

### "Could not connect to Confluence"
- **Problem:** Incremental fetch failed after initial success
- **Solution:**
  ```bash
  # Check Confluence is online
  curl https://your-domain.atlassian.net/wiki/rest/api/content

  # Clear metadata and reinitialize
  rm confluence_metadata.json
  python main.py
  ```

---

## 📚 Which Mode Should I Use?

### Use `python main.py` (Confluence-only) if:
- You only need to search your internal documentation
- You want fastest setup (don't need internet)
- Your org prefers internal-only solutions

### Use `python main_so.py` (Stack Overflow-only) if:
- You only want real-world programming solutions
- You don't have internal documentation
- You want to built a public knowledge base

### Use `python main_unified.py` (Both) if:
- You want **both** internal docs + community knowledge 🎯
- You want automatic cross-suggestions
- You're building a comprehensive knowledge system
- **This is recommended!**

---

## 🚀 Getting Started

### With All Features
```bash
# 1. Update .env with your settings
nano .env

# 2. Run unified system (does everything automatically)
python main_unified.py

# 3. First load will:
#    - Create Confluence DB
#    - Create SO DB
#    - Show menu

# 4. Select mode and start querying!
```

### Quick Incremental Test
```bash
# 1. Run Confluence mode
python main.py

# 2. Make a small edit in Confluence
# 3. Run again - should detect the change!
python main.py

# 4. You'll see the update message:
#    "Found updates: 0 new, 1 modified, 0 deleted"
```

### SO Standalone Test
```bash
# 1. Run SO mode
python main_so.py

# 2. Ask a programming question
You: How to handle errors in async Python?

# 3. Get Stack Overflow answers!
```

---

## 📖 File Reference

| File | Purpose |
|------|---------|
| `confluence_metadata.json` | Tracks Confluence pages (auto-generated) |
| `confluence_db/` | Confluence vector database |
| `stackoverflow_db/` | Stack Overflow vector database |
| `main.py` | Confluence RAG with incremental updates |
| `main_so.py` | Stack Overflow RAG standalone |
| `main_unified.py` | Menu interface for both modes |

---

## ✨ Summary

**New Capabilities:**
```
Before:
  python main.py → Query Confluence (always refetch if you delete DB)

After:
  python main.py             → Query Confluence (auto-incremental!) ⚡
  python main_so.py          → Query Stack Overflow ⭐
  python main_unified.py     → Both + suggestions 🚀
```

**Performance:**
```
Before: Full refetch ~2-5 min every time
After:  Incremental updates ~5-30 sec, SO fetches ~10-30 sec
```

**Flexibility:**
```
Before: Confluence only
After:  Confluence | Stack Overflow | Both with cross-links
```

Enjoy your enhanced RAG system! 🎉
