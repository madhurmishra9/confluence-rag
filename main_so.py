"""
Stack Overflow RAG - Main Entry Point (Independent SO Mode)
A local RAG system for querying Stack Overflow Q&A using Ollama.

Updated to use:
- langchain-ollama  (ChatOllama)
- langchain-chroma  (Chroma, auto-persistence)
- LCEL chain        (replaces removed RetrievalQA)
"""

import os
import sys
import logging
from dotenv import load_dotenv

load_dotenv()

from src.fetch_stackoverflow import fetch_stackoverflow_questions
from src.embed_and_store import (
    create_vectorstore_so,
    load_vectorstore_so,
    vectorstore_so_exists,
)
from src.query import build_qa_chain, ask

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("stackoverflow_rag.log", mode="a"),
    ],
)

logger = logging.getLogger(__name__)


def print_banner():
    """Print application banner."""
    print("\n" + "=" * 60)
    print("    Stack Overflow RAG - Q&A System")
    print("    Local Search using Ollama (llama3.1:8b)")
    print("=" * 60)


def ingest_stackoverflow():
    """
    Fetch Stack Overflow Q&A and create the vector store.

    Returns:
        Chroma vector store instance, or None if error.
    """
    print("\n[1/2] Fetching Stack Overflow questions...")

    try:
        so_tags = os.getenv("STACKOVERFLOW_TAGS", "python,json,api,rest-api,database")

        documents = fetch_stackoverflow_questions(tags=so_tags, include_answers=True)

        if not documents:
            print("WARNING: No Stack Overflow documents fetched.")
            print("Please check STACKOVERFLOW_TAGS in your .env file.")
            return None

        print(f"      Fetched {len(documents)} Stack Overflow Q&A pairs.")

        print("\n[2/2] Chunking and embedding documents...")
        print("      (This may take a few minutes depending on the number of questions)")

        vectorstore = create_vectorstore_so(documents)

        print("      Vector store created and saved!")
        print("      Location: ./stackoverflow_db/")

        return vectorstore

    except Exception as e:
        logger.error(f"Ingestion failed: {e}")
        print(f"\nERROR: Failed to ingest Stack Overflow documents: {e}")
        return None


def run_interactive_mode(vectorstore):
    """
    Run interactive Q&A loop for Stack Overflow content.

    Args:
        vectorstore: ChromaDB vector store instance.
    """
    print("\n" + "-" * 60)
    print("Interactive Q&A Mode - Stack Overflow")
    print("Type your questions and press Enter.")
    print("Type 'exit' or 'quit' to stop.")
    print("-" * 60)

    try:
        qa_chain = build_qa_chain(vectorstore)
    except Exception as e:
        logger.error(f"Failed to build QA chain: {e}")
        print(f"\nERROR: Failed to initialize QA chain: {e}")
        print("Make sure Ollama is running with the llama3.1:8b model.")
        return

    while True:
        try:
            print()
            question = input("You: ").strip()

            if not question:
                continue

            if question.lower() in ("exit", "quit"):
                print("\nGoodbye! Happy learning!")
                break

            print("\nThinking...")
            answer, _ = ask(question, qa_chain)
            print(f"\nAssistant: {answer}")

        except KeyboardInterrupt:
            print("\n\nGoodbye! Happy learning!")
            break
        except Exception as e:
            logger.error(f"Error processing question: {e}")
            print(f"\nERROR: {e}")
            print("Please try again with a different question.")


def main():
    """Main entry point for Stack Overflow RAG."""
    print_banner()

    print("\nChecking for existing Stack Overflow vector store...")

    if vectorstore_so_exists():
        print("Found existing Stack Overflow database! Loading...")
        try:
            vectorstore = load_vectorstore_so()
            print("Vector store loaded successfully.")
            print("\nTo refresh data, delete the './stackoverflow_db/' folder and restart.")
        except Exception as e:
            logger.error(f"Failed to load vector store: {e}")
            print(f"\nERROR: Failed to load existing vector store: {e}")
            print("Attempting to create a new one...")
            vectorstore = ingest_stackoverflow()
            if vectorstore is None:
                print("\nFailed to create vector store. Exiting.")
                sys.exit(1)
    else:
        print("No existing vector store found.")
        print("Starting fresh ingestion from Stack Overflow...\n")

        vectorstore = ingest_stackoverflow()

        if vectorstore is None:
            print("\nFailed to create vector store.")
            print("\nTroubleshooting tips:")
            print("  1. Check your internet connection")
            print("  2. Verify STACKOVERFLOW_TAGS in .env file")
            print("  3. Check Stack Exchange API rate limits")
            sys.exit(1)

    run_interactive_mode(vectorstore)


if __name__ == "__main__":
    main()
