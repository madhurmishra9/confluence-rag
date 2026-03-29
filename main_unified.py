"""
Unified RAG System - Main Entry Point
Confluence + Stack Overflow Integration

Choose between Confluence-only, SO-only, or Unified mode with cross-linking.

Updated to use:
- langchain-ollama  (ChatOllama)
- langchain-chroma  (Chroma, auto-persistence)
- LCEL chain        (replaces removed RetrievalQA)
- Fixed unified mode suggestion engine (was passing empty list and silently broken)
"""

import os
import sys
import logging
from typing import List
from dotenv import load_dotenv

load_dotenv()

from src.fetch_confluence import fetch_pages, fetch_incremental_pages
from src.confluence_metadata import ConfluenceMetadataTracker
from src.fetch_stackoverflow import fetch_stackoverflow_questions
from src.embed_and_store import (
    create_vectorstore,
    load_vectorstore,
    vectorstore_exists,
    create_vectorstore_so,
    load_vectorstore_so,
    vectorstore_so_exists,
    add_documents,
    remove_documents,
    update_documents,
)
from src.tag_linker import TagLinker
from src.so_suggestions import SOSuggestionEngine
from src.query import build_qa_chain, ask
from langchain_core.documents import Document

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("unified_rag.log", mode="a"),
    ],
)

logger = logging.getLogger(__name__)


def print_banner():
    """Print application banner."""
    print("\n" + "=" * 70)
    print("              UNIFIED RAG SYSTEM")
    print("         Confluence + Stack Overflow Integration")
    print("              Powered by Local Ollama LLM")
    print("=" * 70)


def show_mode_menu() -> int:
    """
    Show mode selection menu.

    Returns:
        Selected mode (1-4)
    """
    print("\n" + "-" * 70)
    print("SELECT MODE:")
    print("-" * 70)
    print("  1. Confluence RAG       (Search your Confluence documentation)")
    print("  2. Stack Overflow RAG   (Search Stack Overflow Q&A)")
    print("  3. Unified Mode         (Search both + cross-linked suggestions)")
    print("  4. Exit")
    print("-" * 70)

    while True:
        try:
            choice = input("\nEnter your choice (1-4): ").strip()
            if choice in ["1", "2", "3", "4"]:
                return int(choice)
            print("Invalid choice. Please enter 1, 2, 3, or 4.")
        except KeyboardInterrupt:
            return 4
        except Exception as e:
            print(f"Error: {e}")


def _get_confluence_docs_from_vectorstore(vectorstore) -> List[Document]:
    """
    Retrieve all Confluence documents stored in the vector store as Document objects.
    Used by the suggestion engine in unified mode.

    Returns:
        List of Document objects reconstructed from ChromaDB collection data.
    """
    try:
        collection = vectorstore._collection
        results = collection.get(include=["documents", "metadatas"])
        docs = []
        for content, meta in zip(results.get("documents", []), results.get("metadatas", [])):
            docs.append(Document(page_content=content or "", metadata=meta or {}))
        logger.info(f"Retrieved {len(docs)} documents from Confluence vector store for suggestions")
        return docs
    except Exception as e:
        logger.warning(f"Could not retrieve Confluence docs for suggestion engine: {e}")
        return []


def initialize_confluence_vectorstore():
    """
    Initialize and return the Confluence vector store.
    Handles both loading existing DB and creating a fresh one.

    Returns:
        Chroma vector store instance, or None on failure.
    """
    print("\n📖 CONFLUENCE MODE")
    print("=" * 70)
    print("\nInitializing Confluence documentation store...")

    if vectorstore_exists():
        print("Found existing Confluence database. Loading...")
        try:
            vectorstore = load_vectorstore()
            print("✓ Confluence vector store loaded.")

            # Incremental update check
            print("\nChecking for updates...")
            metadata_tracker = ConfluenceMetadataTracker()
            new_docs, modified_docs, deleted_ids = fetch_incremental_pages(metadata_tracker)

            if not new_docs and not modified_docs and not deleted_ids:
                print("✓ Confluence documentation is up-to-date.")
            else:
                print(
                    f"Found updates: {len(new_docs)} new, "
                    f"{len(modified_docs)} modified, {len(deleted_ids)} deleted"
                )
                if deleted_ids:
                    vectorstore = remove_documents(deleted_ids, vectorstore)
                if modified_docs:
                    modified_ids = [doc.metadata.get("page_id") for doc in modified_docs]
                    vectorstore = update_documents(modified_docs, modified_ids, vectorstore)
                if new_docs:
                    vectorstore = add_documents(new_docs, vectorstore)
                print("✓ Confluence documentation updated!")

            return vectorstore

        except Exception as e:
            logger.error(f"Failed to load Confluence: {e}")
            print(f"Error loading Confluence: {e}")
            return None

    else:
        print("Creating fresh Confluence database...")
        try:
            documents = fetch_pages()
            if not documents:
                print("No Confluence documents found.")
                return None

            vectorstore = create_vectorstore(documents)

            # Initialise metadata tracker
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

            print("✓ Confluence database created!")
            return vectorstore

        except Exception as e:
            logger.error(f"Failed to create Confluence store: {e}")
            print(f"Error: {e}")
            return None


def initialize_stackoverflow_vectorstore():
    """
    Initialize and return the Stack Overflow vector store.
    Handles both loading existing DB and creating a fresh one.

    Returns:
        Chroma vector store instance, or None on failure.
    """
    print("\n💻 STACK OVERFLOW MODE")
    print("=" * 70)
    print("\nInitializing Stack Overflow Q&A store...")

    if vectorstore_so_exists():
        print("Found existing Stack Overflow database. Loading...")
        try:
            vectorstore = load_vectorstore_so()
            print("✓ Stack Overflow vector store loaded.")
            return vectorstore
        except Exception as e:
            logger.error(f"Failed to load SO: {e}")
            print(f"Error loading Stack Overflow: {e}")
            return None

    else:
        print("Creating fresh Stack Overflow database...")
        try:
            so_tags = os.getenv("STACKOVERFLOW_TAGS", "python,json,api,rest-api,database")
            documents = fetch_stackoverflow_questions(tags=so_tags, include_answers=True)

            if not documents:
                print("No Stack Overflow documents found.")
                return None

            vectorstore = create_vectorstore_so(documents)
            print("✓ Stack Overflow database created!")
            return vectorstore

        except Exception as e:
            logger.error(f"Failed to create SO store: {e}")
            print(f"Error: {e}")
            return None


def run_confluence_mode(vectorstore):
    """Run Confluence-only interactive Q&A mode."""
    print("\n" + "-" * 70)
    print("Confluence Q&A Mode")
    print("Type your questions about your documentation.")
    print("Type 'back' to return to mode menu or 'exit' to quit.")
    print("-" * 70)

    try:
        qa_chain = build_qa_chain(vectorstore)
    except Exception as e:
        print(f"Error initializing chain: {e}")
        return

    while True:
        try:
            print()
            question = input("You: ").strip()

            if not question:
                continue
            if question.lower() == "back":
                return
            if question.lower() == "exit":
                sys.exit(0)

            print("\nThinking...")
            answer, sources = ask(question, qa_chain)
            print(f"\nAssistant: {answer}")

            if sources:
                print("\n" + "=" * 70)
                print("📚 SOURCES:")
                for i, source in enumerate(sources, 1):
                    title = source.metadata.get("title", "Unknown")
                    url = source.metadata.get("url", "")
                    print(f"\n{i}. {title}")
                    if url:
                        print(f"   {url}")

        except KeyboardInterrupt:
            print("\nReturning to mode menu...")
            return
        except Exception as e:
            logger.error(f"Error: {e}")
            print(f"Error: {e}")


def run_stackoverflow_mode(vectorstore):
    """Run Stack Overflow-only interactive Q&A mode."""
    print("\n" + "-" * 70)
    print("Stack Overflow Q&A Mode")
    print("Type your questions about programming topics.")
    print("Type 'back' to return to mode menu or 'exit' to quit.")
    print("-" * 70)

    try:
        qa_chain = build_qa_chain(vectorstore)
    except Exception as e:
        print(f"Error initializing chain: {e}")
        return

    while True:
        try:
            print()
            question = input("You: ").strip()

            if not question:
                continue
            if question.lower() == "back":
                return
            if question.lower() == "exit":
                sys.exit(0)

            print("\nThinking...")
            answer, sources = ask(question, qa_chain)
            print(f"\nAssistant: {answer}")

            if sources:
                print("\n" + "=" * 70)
                print("📚 SOURCES (Stack Overflow):")
                for i, source in enumerate(sources, 1):
                    title = source.metadata.get("title", "Unknown")
                    url = source.metadata.get("url", "")
                    score = source.metadata.get("score", 0)
                    print(f"\n{i}. {title}")
                    if score:
                        print(f"   Score: {score}")
                    if url:
                        print(f"   {url}")

        except KeyboardInterrupt:
            print("\nReturning to mode menu...")
            return
        except Exception as e:
            logger.error(f"Error: {e}")
            print(f"Error: {e}")


def run_unified_mode(conf_vectorstore, so_vectorstore):
    """
    Run unified Q&A mode with cross-linked Confluence suggestions.

    The suggestion engine is now properly initialised with actual Confluence
    documents retrieved from the vector store (fixes the original bug where
    an empty list was always passed).
    """
    print("\n" + "-" * 70)
    print("Unified Q&A Mode - Search Both Sources")
    print("Answers include suggestions from related Confluence docs.")
    print("Type 'back' to return to mode menu or 'exit' to quit.")
    print("-" * 70)

    try:
        conf_chain = build_qa_chain(conf_vectorstore)
        so_chain = build_qa_chain(so_vectorstore)
    except Exception as e:
        print(f"Error initializing chains: {e}")
        return

    # Build suggestion engine with real Confluence docs
    confluence_docs = _get_confluence_docs_from_vectorstore(conf_vectorstore)
    suggestion_engine = SOSuggestionEngine(confluence_docs) if confluence_docs else None

    if not suggestion_engine:
        print("⚠ Warning: Could not load Confluence docs for suggestions. Cross-linking disabled.")

    while True:
        try:
            print()
            print("Select source:")
            print("  1. Query Confluence")
            print("  2. Query Stack Overflow")
            print("  0. Query Both")

            source_choice = input("Source (0-2, or 'back'/'exit'): ").strip().lower()

            if source_choice == "back":
                return
            if source_choice == "exit":
                sys.exit(0)
            if source_choice not in ("0", "1", "2"):
                continue

            question = input("\nYour question: ").strip()

            if not question:
                continue
            if question.lower() == "back":
                return
            if question.lower() == "exit":
                sys.exit(0)

            print("\nThinking...")

            if source_choice in ("0", "1"):
                print("\n" + "=" * 70)
                print("📖 CONFLUENCE ANSWER:")
                print("=" * 70)
                answer, sources = ask(question, conf_chain)
                print(f"\n{answer}")

                if sources:
                    print("\n📚 CONFLUENCE SOURCES:")
                    for i, src in enumerate(sources, 1):
                        print(f"  {i}. {src.metadata.get('title', 'Unknown')}")
                        url = src.metadata.get("url", "")
                        if url:
                            print(f"     {url}")

            if source_choice in ("0", "2"):
                print("\n" + "=" * 70)
                print("💻 STACK OVERFLOW ANSWER:")
                print("=" * 70)
                so_answer, so_sources = ask(question, so_chain)
                print(f"\n{so_answer}")

                if so_sources:
                    print("\n📚 STACK OVERFLOW SOURCES:")
                    for i, src in enumerate(so_sources, 1):
                        title = src.metadata.get("title", "Unknown")
                        url = src.metadata.get("url", "")
                        print(f"  {i}. {title}")
                        if url:
                            print(f"     {url}")

                    # Cross-link: suggest Confluence pages relevant to the top SO result
                    if suggestion_engine and so_sources:
                        top_so_doc = so_sources[0]
                        suggestions = suggestion_engine.suggest_confluence_articles(
                            top_so_doc, max_suggestions=3
                        )
                        if suggestions:
                            print(suggestion_engine.format_suggestions(suggestions))

        except KeyboardInterrupt:
            print("\nReturning to mode menu...")
            return
        except Exception as e:
            logger.error(f"Error: {e}")
            print(f"Error: {e}")


def main():
    """Main entry point for unified system."""
    print_banner()

    while True:
        mode = show_mode_menu()

        if mode == 1:
            vs = initialize_confluence_vectorstore()
            if vs:
                run_confluence_mode(vs)

        elif mode == 2:
            vs = initialize_stackoverflow_vectorstore()
            if vs:
                run_stackoverflow_mode(vs)

        elif mode == 3:
            print("\nInitializing unified system...")
            conf_vs = initialize_confluence_vectorstore()
            so_vs = initialize_stackoverflow_vectorstore()

            if conf_vs and so_vs:
                run_unified_mode(conf_vs, so_vs)
            else:
                print("Error: Could not initialize both systems for unified mode.")
                if not conf_vs:
                    print("  ✗ Confluence vector store failed to initialize.")
                if not so_vs:
                    print("  ✗ Stack Overflow vector store failed to initialize.")

        elif mode == 4:
            print("\nGoodbye!")
            sys.exit(0)


if __name__ == "__main__":
    main()
