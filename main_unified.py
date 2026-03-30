"""
Unified RAG System — Main Entry Point
Confluence + Stack Overflow Integration

Modes:
  1. Confluence RAG     — search Confluence docs
  2. Stack Overflow RAG — search SO Q&A
  3. Unified Mode       — search both + cross-linked suggestions
  4. Dashboard          — generate on-demand HTML dashboards from indexed data

Zero-hallucination: temperature=0.0, context-only prompts, grounding note on every answer.
Detailed logging: every retrieval, LLM call, latency, and confidence score is logged.
"""

import os
import sys
import logging
import webbrowser
from typing import List
from dotenv import load_dotenv

load_dotenv()

from src.fetch_confluence import fetch_pages, fetch_incremental_pages
from src.confluence_metadata import ConfluenceMetadataTracker
from src.fetch_stackoverflow import fetch_stackoverflow_questions
from src.embed_and_store import (
    create_vectorstore, load_vectorstore, vectorstore_exists,
    create_vectorstore_so, load_vectorstore_so, vectorstore_so_exists,
    add_documents, remove_documents, update_documents,
)
from src.tag_linker import TagLinker
from src.so_suggestions import SOSuggestionEngine
from src.query import build_qa_chain, ask, format_sources
from src.dashboard_generator import (
    generate_confluence_dashboard_data,
    generate_stackoverflow_dashboard_data,
)
from src.dashboard import render_dashboard
from langchain_core.documents import Document

# ── Logging setup ─────────────────────────────────────────────────────────────
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE   = os.getenv("LOG_FILE", "unified_rag.log")

logging.basicConfig(
    level=getattr(logging, LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s %(levelname)-8s %(name)s — %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(LOG_FILE, mode="a", encoding="utf-8"),
    ],
)

logger = logging.getLogger(__name__)
logger.info(f"Unified RAG starting | log_level={LOG_LEVEL} | log_file={LOG_FILE}")


# ── Banner & menus ────────────────────────────────────────────────────────────

def print_banner():
    print("\n" + "=" * 70)
    print("              UNIFIED RAG SYSTEM")
    print("         Confluence + Stack Overflow Integration")
    print("    Powered by Local Ollama — Zero Hallucination Mode")
    print("=" * 70)


def show_mode_menu() -> int:
    print("\n" + "-" * 70)
    print("SELECT MODE:")
    print("-" * 70)
    print("  1. Confluence RAG       — Search Confluence documentation")
    print("  2. Stack Overflow RAG   — Search Stack Overflow Q&A")
    print("  3. Unified Mode         — Search both + cross-linked suggestions")
    print("  4. Dashboard            — Generate on-demand HTML dashboards")
    print("  5. Exit")
    print("-" * 70)
    while True:
        try:
            choice = input("\nEnter your choice (1-5): ").strip()
            if choice in ["1", "2", "3", "4", "5"]:
                return int(choice)
            print("Invalid choice. Enter 1–5.")
        except KeyboardInterrupt:
            return 5


def show_dashboard_menu() -> int:
    print("\n" + "-" * 70)
    print("DASHBOARD — Select data source:")
    print("-" * 70)
    print("  1. Confluence Dashboard")
    print("  2. Stack Overflow Dashboard")
    print("  3. Both (generate two dashboards)")
    print("  4. Back")
    print("-" * 70)
    while True:
        try:
            choice = input("\nEnter your choice (1-4): ").strip()
            if choice in ["1", "2", "3", "4"]:
                return int(choice)
            print("Invalid choice. Enter 1–4.")
        except KeyboardInterrupt:
            return 4


# ── Vectorstore helpers ───────────────────────────────────────────────────────

def _get_confluence_docs_from_vectorstore(vectorstore) -> List[Document]:
    """
    Reconstruct Document objects from all stored Confluence chunks.
    Used by the suggestion engine — does NOT call the LLM.
    """
    try:
        collection = vectorstore._collection
        results = collection.get(include=["documents", "metadatas"])
        docs = []
        for content, meta in zip(
            results.get("documents") or [],
            results.get("metadatas") or [],
        ):
            docs.append(Document(page_content=content or "", metadata=meta or {}))
        logger.info(f"[Suggestions] Loaded {len(docs)} Confluence chunks for cross-linking")
        return docs
    except Exception as e:
        logger.warning(f"[Suggestions] Could not load Confluence docs: {e}")
        return []


def initialize_confluence_vectorstore():
    """Load or create the Confluence ChromaDB, running incremental updates."""
    logger.info("[Init] Initializing Confluence vector store...")
    print("\n📖 CONFLUENCE")
    print("=" * 70)

    if vectorstore_exists():
        print("Found existing Confluence database. Loading...")
        try:
            vectorstore = load_vectorstore()
            logger.info("[Init] Confluence vector store loaded")
            print("✓ Loaded.")

            print("\nChecking for Confluence updates...")
            metadata_tracker = ConfluenceMetadataTracker()
            new_docs, modified_docs, deleted_ids = fetch_incremental_pages(metadata_tracker)

            if not new_docs and not modified_docs and not deleted_ids:
                logger.info("[Init] Confluence: no changes detected")
                print("✓ Up-to-date — no changes.")
            else:
                logger.info(
                    f"[Init] Confluence changes: +{len(new_docs)} new, "
                    f"~{len(modified_docs)} modified, -{len(deleted_ids)} deleted"
                )
                print(
                    f"Changes: {len(new_docs)} new, "
                    f"{len(modified_docs)} modified, {len(deleted_ids)} deleted"
                )
                if deleted_ids:
                    vectorstore = remove_documents(deleted_ids, vectorstore)
                if modified_docs:
                    modified_ids = [d.metadata.get("page_id") for d in modified_docs]
                    vectorstore = update_documents(modified_docs, modified_ids, vectorstore)
                if new_docs:
                    vectorstore = add_documents(new_docs, vectorstore)
                print("✓ Updated.")

            return vectorstore

        except Exception as e:
            logger.error(f"[Init] Confluence load failed: {e}")
            print(f"Error: {e}")
            return None

    else:
        print("No existing database. Fetching from Confluence...")
        try:
            documents = fetch_pages()
            if not documents:
                logger.warning("[Init] Confluence: no documents fetched")
                print("No documents found.")
                return None

            logger.info(f"[Init] Confluence: embedding {len(documents)} pages")
            vectorstore = create_vectorstore(documents)

            metadata_tracker = ConfluenceMetadataTracker()
            for doc in documents:
                meta = doc.metadata
                metadata_tracker.add_or_update_page(
                    page_id=meta.get("page_id", ""),
                    title=meta.get("title", ""),
                    version=meta.get("version", 1),
                    modified=meta.get("modified", ""),
                    url=meta.get("url", ""),
                    space_key=meta.get("space_key", ""),
                    chunk_count=0,
                )
            metadata_tracker.save()
            print("✓ Created.")
            return vectorstore

        except Exception as e:
            logger.error(f"[Init] Confluence creation failed: {e}")
            print(f"Error: {e}")
            return None


def initialize_stackoverflow_vectorstore():
    """Load or create the Stack Overflow ChromaDB."""
    logger.info("[Init] Initializing Stack Overflow vector store...")
    print("\n💻 STACK OVERFLOW")
    print("=" * 70)

    if vectorstore_so_exists():
        print("Found existing Stack Overflow database. Loading...")
        try:
            vectorstore = load_vectorstore_so()
            logger.info("[Init] SO vector store loaded")
            print("✓ Loaded.")
            return vectorstore
        except Exception as e:
            logger.error(f"[Init] SO load failed: {e}")
            print(f"Error: {e}")
            return None
    else:
        print("No existing database. Fetching from Stack Overflow...")
        try:
            so_tags = os.getenv("STACKOVERFLOW_TAGS", "python,json,api,rest-api,database")
            logger.info(f"[Init] SO: fetching tags={so_tags}")
            documents = fetch_stackoverflow_questions(tags=so_tags, include_answers=True)
            if not documents:
                logger.warning("[Init] SO: no documents fetched")
                print("No documents found.")
                return None
            logger.info(f"[Init] SO: embedding {len(documents)} questions")
            vectorstore = create_vectorstore_so(documents)
            print("✓ Created.")
            return vectorstore
        except Exception as e:
            logger.error(f"[Init] SO creation failed: {e}")
            print(f"Error: {e}")
            return None


# ── Interactive Q&A modes ─────────────────────────────────────────────────────

def _qa_loop(qa_chain, source_label: str):
    """
    Shared Q&A loop for all modes.
    Prints answer, sources, and confidence on every query.
    Type 'back' to return, 'exit' to quit.
    """
    print(f"\n{'─' * 70}")
    print(f"{source_label} — Q&A Mode")
    print("Type your question and press Enter.")
    print("Commands: 'back' → return to menu | 'exit' → quit")
    print(f"{'─' * 70}")

    while True:
        try:
            print()
            question = input("You: ").strip()
            if not question:
                continue
            if question.lower() == "back":
                return
            if question.lower() == "exit":
                logger.info("[QA] User exited")
                sys.exit(0)

            logger.info(f"[QA:{source_label}] Question: {question!r}")
            print("\nThinking…")
            answer, sources = ask(question, qa_chain)
            print(f"\nAssistant: {answer}")

        except KeyboardInterrupt:
            print("\nReturning to menu…")
            return
        except Exception as e:
            logger.error(f"[QA:{source_label}] Error: {e}")
            print(f"Error: {e}")


def run_confluence_mode(vectorstore):
    logger.info("[Mode] Confluence Q&A started")
    try:
        qa_chain = build_qa_chain(vectorstore)
    except Exception as e:
        logger.error(f"[Mode] Confluence chain build failed: {e}")
        print(f"Error: {e}")
        return
    _qa_loop(qa_chain, "📖 Confluence")
    logger.info("[Mode] Confluence Q&A ended")


def run_stackoverflow_mode(vectorstore):
    logger.info("[Mode] Stack Overflow Q&A started")
    try:
        qa_chain = build_qa_chain(vectorstore)
    except Exception as e:
        logger.error(f"[Mode] SO chain build failed: {e}")
        print(f"Error: {e}")
        return
    _qa_loop(qa_chain, "💻 Stack Overflow")
    logger.info("[Mode] Stack Overflow Q&A ended")


def run_unified_mode(conf_vectorstore, so_vectorstore):
    """
    Unified Q&A: query Confluence and/or SO, then show cross-linked
    Confluence suggestions based on the top SO source document's tags.
    """
    logger.info("[Mode] Unified Q&A started")
    print(f"\n{'─' * 70}")
    print("Unified Q&A — Confluence + Stack Overflow")
    print("Commands: 'back' → menu | 'exit' → quit")
    print(f"{'─' * 70}")

    try:
        conf_chain = build_qa_chain(conf_vectorstore)
        so_chain   = build_qa_chain(so_vectorstore)
    except Exception as e:
        logger.error(f"[Mode] Unified chain build failed: {e}")
        print(f"Error: {e}")
        return

    confluence_docs = _get_confluence_docs_from_vectorstore(conf_vectorstore)
    suggestion_engine = SOSuggestionEngine(confluence_docs) if confluence_docs else None
    if not suggestion_engine:
        logger.warning("[Mode] Suggestion engine disabled — no Confluence docs loaded")
        print("⚠ Cross-linking disabled: could not load Confluence docs.")

    while True:
        try:
            print()
            print("Source: (1) Confluence  (2) Stack Overflow  (0) Both")
            src = input("Source [0/1/2 or back/exit]: ").strip().lower()

            if src == "back":
                break
            if src == "exit":
                logger.info("[QA] User exited")
                sys.exit(0)
            if src not in ("0", "1", "2"):
                continue

            question = input("\nYour question: ").strip()
            if not question:
                continue
            if question.lower() == "back":
                break
            if question.lower() == "exit":
                sys.exit(0)

            logger.info(f"[QA:Unified] source={src} question={question!r}")
            print("\nThinking…")

            if src in ("0", "1"):
                logger.info("[QA:Unified] Querying Confluence…")
                print(f"\n{'═' * 70}")
                print("📖 CONFLUENCE ANSWER")
                print('═' * 70)
                c_answer, c_sources = ask(question, conf_chain)
                print(f"\n{c_answer}")
                if c_sources:
                    print("\n📚 Confluence Sources:")
                    for i, s in enumerate(c_sources, 1):
                        print(f"  {i}. {s.metadata.get('title','Unknown')}")
                        if s.metadata.get("url"):
                            print(f"     {s.metadata['url']}")

            if src in ("0", "2"):
                logger.info("[QA:Unified] Querying Stack Overflow…")
                print(f"\n{'═' * 70}")
                print("💻 STACK OVERFLOW ANSWER")
                print('═' * 70)
                so_answer, so_sources = ask(question, so_chain)
                print(f"\n{so_answer}")
                if so_sources:
                    print("\n📚 Stack Overflow Sources:")
                    for i, s in enumerate(so_sources, 1):
                        title = s.metadata.get("title", "Unknown")
                        score = s.metadata.get("score", "")
                        url   = s.metadata.get("url", "")
                        print(f"  {i}. {title}" + (f" (⭐{score})" if score else ""))
                        if url:
                            print(f"     {url}")

                # Cross-link: suggest Confluence pages based on top SO result
                if suggestion_engine and so_sources:
                    top_so = so_sources[0]
                    suggestions = suggestion_engine.suggest_confluence_articles(
                        top_so, max_suggestions=3
                    )
                    if suggestions:
                        logger.info(f"[Suggestions] {len(suggestions)} cross-links found")
                        print(suggestion_engine.format_suggestions(suggestions))

        except KeyboardInterrupt:
            print("\nReturning to menu…")
            break
        except Exception as e:
            logger.error(f"[QA:Unified] Error: {e}")
            print(f"Error: {e}")

    logger.info("[Mode] Unified Q&A ended")


# ── Dashboard mode ────────────────────────────────────────────────────────────

def run_dashboard_mode(conf_vectorstore=None, so_vectorstore=None):
    """
    On-demand dashboard generator.
    Extracts metrics + runs grounded LLM analysis, then renders an HTML file
    and opens it in the default browser.
    """
    logger.info("[Dashboard] Mode started")
    choice = show_dashboard_menu()

    if choice == 4:
        return

    def _generate_and_open(vectorstore, generator_fn, label):
        if vectorstore is None:
            print(f"\n⚠ {label} vector store not loaded. Initialize it first via mode 1 or 2.")
            logger.warning(f"[Dashboard] {label} vectorstore is None — skipping")
            return
        print(f"\n⏳ Generating {label} dashboard (this may take 1-2 minutes)…")
        logger.info(f"[Dashboard] Generating {label} data…")
        try:
            data = generator_fn(vectorstore)
            path = render_dashboard(data)
            print(f"\n✅ Dashboard saved: {path}")
            logger.info(f"[Dashboard] {label} written to {path}")
            try:
                webbrowser.open(f"file://{path}")
                print("   Opening in browser…")
            except Exception:
                print("   (Could not auto-open browser — open the file manually)")
        except Exception as e:
            logger.error(f"[Dashboard] {label} generation failed: {e}")
            print(f"Error generating dashboard: {e}")

    if choice == 1:
        _generate_and_open(
            conf_vectorstore,
            generate_confluence_dashboard_data,
            "Confluence",
        )
    elif choice == 2:
        _generate_and_open(
            so_vectorstore,
            generate_stackoverflow_dashboard_data,
            "Stack Overflow",
        )
    elif choice == 3:
        _generate_and_open(
            conf_vectorstore,
            generate_confluence_dashboard_data,
            "Confluence",
        )
        _generate_and_open(
            so_vectorstore,
            generate_stackoverflow_dashboard_data,
            "Stack Overflow",
        )

    logger.info("[Dashboard] Mode ended")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print_banner()
    logger.info("[Main] Startup complete")

    conf_vs = None
    so_vs   = None

    while True:
        mode = show_mode_menu()
        logger.info(f"[Main] Mode selected: {mode}")

        if mode == 1:
            if conf_vs is None:
                conf_vs = initialize_confluence_vectorstore()
            if conf_vs:
                run_confluence_mode(conf_vs)
            else:
                print("Could not initialize Confluence. Check your .env and Confluence access.")

        elif mode == 2:
            if so_vs is None:
                so_vs = initialize_stackoverflow_vectorstore()
            if so_vs:
                run_stackoverflow_mode(so_vs)
            else:
                print("Could not initialize Stack Overflow store.")

        elif mode == 3:
            if conf_vs is None:
                conf_vs = initialize_confluence_vectorstore()
            if so_vs is None:
                so_vs = initialize_stackoverflow_vectorstore()

            if conf_vs and so_vs:
                run_unified_mode(conf_vs, so_vs)
            else:
                if not conf_vs:
                    print("  ✗ Confluence store failed.")
                if not so_vs:
                    print("  ✗ Stack Overflow store failed.")

        elif mode == 4:
            # Dashboard — lazy-initialize whichever stores are needed
            if conf_vs is None and so_vs is None:
                print("\nNo data loaded yet. Choose which store to load:")
                print("  1. Load Confluence  2. Load Stack Overflow  3. Load both  4. Back")
                sub = input("Choice: ").strip()
                if sub == "1":
                    conf_vs = initialize_confluence_vectorstore()
                elif sub == "2":
                    so_vs = initialize_stackoverflow_vectorstore()
                elif sub == "3":
                    conf_vs = initialize_confluence_vectorstore()
                    so_vs   = initialize_stackoverflow_vectorstore()
                elif sub == "4":
                    continue
            run_dashboard_mode(conf_vs, so_vs)

        elif mode == 5:
            logger.info("[Main] Exiting")
            print("\nGoodbye!")
            sys.exit(0)


if __name__ == "__main__":
    main()
