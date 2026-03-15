"""
Unified RAG System - Main Entry Point
Confluence + Stack Overflow Integration
Choose between Confluence-only, SO-only, or Unified mode with cross-linking.
"""

import os
import sys
import logging
from dotenv import load_dotenv

# Load environment variables first
load_dotenv()

# Import modules after env vars are loaded
from src.fetch_confluence import fetch_pages, fetch_incremental_pages
from src.confluence_metadata import ConfluenceMetadataTracker
from src.fetch_stackoverflow import fetch_stackoverflow_questions
from src.embed_and_store import (
    create_vectorstore, load_vectorstore, vectorstore_exists,
    create_vectorstore_so, load_vectorstore_so, vectorstore_so_exists,
    add_documents, remove_documents, update_documents
)
from src.tag_linker import TagLinker
from src.so_suggestions import SOSuggestionEngine
from src.query import build_qa_chain, ask

# Configure logging
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
        Selected mode (1, 2, or 3)
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


def initialize_confluence_vectorstore() -> object:
    """Initialize and return Confluence vector store."""
    print("\n📖 CONFLUENCE MODE")
    print("=" * 70)
    print("\nInitializing Confluence documentation store...")
    
    if vectorstore_exists():
        print("Found existing Confluence database. Loading...")
        try:
            vectorstore = load_vectorstore()
            print("✓ Confluence vector store loaded.")
            
            # Check for updates
            print("\nChecking for updates...")
            metadata_tracker = ConfluenceMetadataTracker()
            new_docs, modified_docs, deleted_ids = fetch_incremental_pages(metadata_tracker)
            
            if not new_docs and not modified_docs and not deleted_ids:
                print("✓ Confluence documentation is up-to-date.")
            else:
                print(f"Found updates: {len(new_docs)} new, {len(modified_docs)} modified, {len(deleted_ids)} deleted")
                if deleted_ids:
                    vectorstore = remove_documents(deleted_ids, vectorstore)
                if modified_docs:
                    modified_ids = [doc.metadata.get('page_id') for doc in modified_docs]
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
            if documents:
                vectorstore = create_vectorstore(documents)
                
                # Initialize metadata
                metadata_tracker = ConfluenceMetadataTracker()
                for doc in documents:
                    metadata = doc.metadata
                    metadata_tracker.add_or_update_page(
                        page_id=metadata.get('page_id', ''),
                        title=metadata.get('title', ''),
                        version=metadata.get('version', 1),
                        modified=metadata.get('modified', ''),
                        url=metadata.get('url', ''),
                        space_key=metadata.get('space_key', ''),
                    )
                metadata_tracker.save()
                
                print("✓ Confluence database created!")
                return vectorstore
            else:
                print("No Confluence documents found.")
                return None
        except Exception as e:
            logger.error(f"Failed to create Confluence store: {e}")
            print(f"Error: {e}")
            return None


def initialize_stackoverflow_vectorstore() -> object:
    """Initialize and return Stack Overflow vector store."""
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
            
            if documents:
                vectorstore = create_vectorstore_so(documents)
                print("✓ Stack Overflow database created!")
                return vectorstore
            else:
                print("No Stack Overflow documents found.")
                return None
        except Exception as e:
            logger.error(f"Failed to create SO store: {e}")
            print(f"Error: {e}")
            return None


def run_confluence_mode(vectorstore):
    """Run Confluence-only Q&A mode."""
    print("\n" + "-" * 70)
    print("Confluence Q&A Mode")
    print("Type your questions about your documentation.")
    print("Type 'back' to return to mode menu or 'exit' to quit.")
    print("-" * 70)
    
    try:
        qa_chain = build_qa_chain(vectorstore)
    except Exception as e:
        print(f"Error: {e}")
        return
    
    while True:
        try:
            print()
            question = input("You: ").strip()
            
            if not question:
                continue
            
            if question.lower() == "back":
                return  # Return to main menu
            
            if question.lower() == "exit":
                sys.exit(0)
            
            print("\nThinking...")
            answer, sources = ask(question, qa_chain)
            print(f"\nAssistant: {answer}")
            
            # Show sources
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
    """Run Stack Overflow-only Q&A mode."""
    print("\n" + "-" * 70)
    print("Stack Overflow Q&A Mode")
    print("Type your questions about programming topics.")
    print("Type 'back' to return to mode menu or 'exit' to quit.")
    print("-" * 70)
    
    try:
        qa_chain = build_qa_chain(vectorstore)
    except Exception as e:
        print(f"Error: {e}")
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
            
            # Show sources
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
    """Run unified Q&A mode with cross-linking."""
    print("\n" + "-" * 70)
    print("Unified Q&A Mode - Search Both Sources")
    print("Receive answers with suggestions from related docs.")
    print("Type 'back' to return to mode menu or 'exit' to quit.")
    print("-" * 70)
    
    try:
        conf_chain = build_qa_chain(conf_vectorstore)
        so_chain = build_qa_chain(so_vectorstore)
    except Exception as e:
        print(f"Error initializing chains: {e}")
        return
    
    # Load Confluence docs for suggestions
    try:
        conf_docs = conf_vectorstore._collection.get()
        # This is simplified - in production would need proper doc retrieval
        suggestion_engine = SOSuggestionEngine([])
    except:
        suggestion_engine = None
    
    while True:
        try:
            print()
            print("Select source (or '0' for both):")
            print("  1. Query Confluence")
            print("  2. Query Stack Overflow")
            print("  0. Query Both")
            
            source_choice = input("Source (0-2): ").strip()
            
            if source_choice == "back":
                return
            if source_choice == "exit":
                sys.exit(0)
            
            if not source_choice:
                continue
            
            question = input("\nYour question: ").strip()
            
            if not question:
                continue
            
            if question.lower() == "back":
                return
            
            if question.lower() == "exit":
                sys.exit(0)
            
            print("\nThinking...")
            
            # Query based on choice
            if source_choice in ["0", "1"]:
                print("\n" + "=" * 70)
                print("📖 CONFLUENCE ANSWER:")
                print("=" * 70)
                answer, sources = ask(question, conf_chain)
                print(f"\n{answer}")
                
                if sources:
                    print("\n📚 CONFLUENCE SOURCES:")
                    for i, src in enumerate(sources, 1):
                        print(f"{i}. {src.metadata.get('title', 'Unknown')}")
            
            if source_choice in ["0", "2"]:
                print("\n" + "=" * 70)
                print("💻 STACK OVERFLOW ANSWER:")
                print("=" * 70)
                answer, sources = ask(question, so_chain)
                print(f"\n{answer}")
                
                if sources:
                    print("\n📚 STACK OVERFLOW SOURCES:")
                    for i, src in enumerate(sources, 1):
                        print(f"{i}. {src.metadata.get('title', 'Unknown')}")
        
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
            # Confluence mode
            vs = initialize_confluence_vectorstore()
            if vs:
                run_confluence_mode(vs)
        
        elif mode == 2:
            # Stack Overflow mode
            vs = initialize_stackoverflow_vectorstore()
            if vs:
                run_stackoverflow_mode(vs)
        
        elif mode == 3:
            # Unified mode
            print("\nInitializing unified system...")
            conf_vs = initialize_confluence_vectorstore()
            so_vs = initialize_stackoverflow_vectorstore()
            
            if conf_vs and so_vs:
                run_unified_mode(conf_vs, so_vs)
            else:
                print("Error: Could not initialize both systems for unified mode.")
        
        elif mode == 4:
            # Exit
            print("\nGoodbye! 👋")
            sys.exit(0)


if __name__ == "__main__":
    main()
