"""
Confluence RAG - Main Entry Point

A local RAG system that connects Confluence documentation to Ollama LLM.
- Auto-detects existing ChromaDB on startup
- Fetches and embeds Confluence pages if needed
- Supports incremental updates on each run
- Provides interactive Q&A in terminal
"""

import os
import sys
import logging
from dotenv import load_dotenv

load_dotenv()

from src.fetch_confluence import fetch_pages, fetch_incremental_pages
from src.confluence_metadata import ConfluenceMetadataTracker
from src.embed_and_store import (
    create_vectorstore,
    load_vectorstore,
    vectorstore_exists,       # fixed: was vectorstore_so_exists (wrong function for confluence DB)
    add_documents,
    remove_documents,
    update_documents,
)
from src.query import build_qa_chain, ask

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("confluence_rag.log", mode="a"),
    ],
)

logger = logging.getLogger(__name__)


def print_banner():
    """Print application banner."""
    print("\n" + "=" * 60)
    print("       Confluence RAG - Local Q&A System")
    print("       Powered by Ollama (llama3.1:8b)")
    print("=" * 60)


def ingest_documents():
    """
    Fetch Confluence pages and create the vector store (initial ingestion).

    Returns:
        Chroma vector store instance, or None if no documents.
    """
    print("\n[1/3] Fetching pages from Confluence...")
    try:
        documents = fetch_pages()

        if not documents:
            print("WARNING: No documents fetched from Confluence.")
            print("Please check your Confluence credentials and space access.")
            return None

        print(f"      Fetched {len(documents)} pages from Confluence.")

        print("\n[2/3] Chunking and embedding documents...")
        print("      (This may take a few minutes depending on the number of pages)")

        vectorstore = create_vectorstore(documents)

        metadata_tracker = ConfluenceMetadataTracker()
        print("\n[3/3] Saving metadata for incremental updates...")
        for doc in documents:
            metadata = doc.metadata
            metadata_tracker.add_or_update_page(
                page_id=metadata.get('page_id', ''),
                title=metadata.get('title', ''),
                version=metadata.get('version', 1),
                modified=metadata.get('modified', ''),
                url=metadata.get('url', ''),
                space_key=metadata.get('space_key', ''),
                chunk_count=0,
            )
        metadata_tracker.save()

        print(f"      Vector store created and saved!")
        print(f"      Location: ./confluence_db/")

        return vectorstore

    except EnvironmentError as e:
        logger.error(f"Configuration error: {e}")
        print(f"\nERROR: {e}")
        return None
    except Exception as e:
        logger.error(f"Ingestion failed: {e}")
        print(f"\nERROR: Failed to ingest documents: {e}")
        return None


def update_documents_incremental(vectorstore):
    """
    Check for new/modified/deleted pages and update vector store incrementally.

    Args:
        vectorstore: Existing Chroma vector store instance

    Returns:
        Updated vectorstore
    """
    print("\nChecking for updates from Confluence...")

    try:
        metadata_tracker = ConfluenceMetadataTracker()

        new_docs, modified_docs, deleted_ids = fetch_incremental_pages(metadata_tracker)

        if not new_docs and not modified_docs and not deleted_ids:
            print("✓ No changes detected. Confluence documentation is up-to-date.")
            return vectorstore

        changes_made = False

        if deleted_ids:
            print(f"  - Removing {len(deleted_ids)} deleted pages...")
            vectorstore = remove_documents(deleted_ids, vectorstore)
            changes_made = True

        if modified_docs:
            print(f"  - Updating {len(modified_docs)} modified pages...")
            modified_ids = [doc.metadata.get('page_id') for doc in modified_docs]
            vectorstore = update_documents(modified_docs, modified_ids, vectorstore)
            changes_made = True

        if new_docs:
            print(f"  - Adding {len(new_docs)} new pages...")
            vectorstore = add_documents(new_docs, vectorstore)
            changes_made = True

        if changes_made:
            print("✓ Confluence documentation updated successfully!")

        return vectorstore

    except Exception as e:
        logger.error(f"Incremental update failed: {e}")
        print(f"⚠ Failed to check for updates: {e}")
        print("  Continuing with cached data...")
        return vectorstore


def run_interactive_mode(vectorstore):
    """
    Run interactive Q&A loop.

    Args:
        vectorstore: ChromaDB vector store instance.
    """
    print("\n" + "-" * 60)
    print("Interactive Q&A Mode")
    print("Type your questions and press Enter.")
    print("Type 'exit' or 'quit' to stop.")
    print("-" * 60)

    try:
        qa_chain = build_qa_chain(vectorstore)
    except Exception as e:
        logger.error(f"Failed to build QA chain: {e}")
        print(f"\nERROR: Failed to initialize QA chain: {e}")
        print("Make sure Ollama is running with llama3.1:8b model.")
        return

    while True:
        try:
            print()
            question = input("You: ").strip()

            if not question:
                continue

            if question.lower() in ("exit", "quit"):
                print("\nGoodbye! Happy documenting!")
                break

            print("\nThinking...")
            answer, _ = ask(question, qa_chain)
            print(f"\nAssistant: {answer}")

        except KeyboardInterrupt:
            print("\n\nGoodbye! Happy documenting!")
            break
        except Exception as e:
            logger.error(f"Error processing question: {e}")
            print(f"\nERROR: {e}")
            print("Please try again with a different question.")


def main():
    """Main entry point."""
    print_banner()

    print("\nChecking for existing vector store...")

    if vectorstore_exists():
        print("Found existing ChromaDB! Loading...")
        try:
            vectorstore = load_vectorstore()
            print("Vector store loaded successfully.")

            vectorstore = update_documents_incremental(vectorstore)

        except Exception as e:
            logger.error(f"Failed to load vector store: {e}")
            print(f"\nERROR: Failed to load existing vector store: {e}")
            print("Attempting to create a new one...")
            vectorstore = ingest_documents()
            if vectorstore is None:
                print("\nFailed to create vector store. Exiting.")
                sys.exit(1)
    else:
        print("No existing vector store found.")
        print("Starting fresh ingestion from Confluence...\n")

        vectorstore = ingest_documents()

        if vectorstore is None:
            print("\nNo documents to query. Please check your Confluence setup.")
            print("\nTroubleshooting tips:")
            print("  1. Verify CONFLUENCE_URL, CONFLUENCE_EMAIL, CONFLUENCE_API_TOKEN in .env")
            print("  2. Make sure your API token has read access to Confluence")
            print("  3. Check if CONFLUENCE_SPACE_KEY is set correctly (or leave empty for all spaces)")
            sys.exit(1)

    run_interactive_mode(vectorstore)


if __name__ == "__main__":
    main()
