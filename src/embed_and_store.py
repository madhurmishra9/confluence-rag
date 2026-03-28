"""
Embedding and Vector Store Module

Chunks documents, creates embeddings with Ollama nomic-embed-text,
and persists to ChromaDB.
"""

import os
import logging
from typing import List, Optional
from langchain_core.documents import Document
from langchain_ollama import OllamaEmbeddings          # replaces langchain_community.embeddings.OllamaEmbeddings
from langchain_chroma import Chroma                    # replaces langchain_community.vectorstores.Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# Configuration from environment
CHROMA_PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR", "./confluence_db")
STACKOVERFLOW_DB_PATH = os.getenv("STACKOVERFLOW_DB_PATH", "./stackoverflow_db")
OLLAMA_EMBED_MODEL = os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "500"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "50"))


def get_embeddings() -> OllamaEmbeddings:
    """
    Create and return Ollama embeddings instance.

    Returns:
        OllamaEmbeddings configured with nomic-embed-text model.
    """
    try:
        embeddings = OllamaEmbeddings(
            model=OLLAMA_EMBED_MODEL,
            base_url=OLLAMA_BASE_URL,
        )
        logger.info(f"Initialized Ollama embeddings with model: {OLLAMA_EMBED_MODEL}")
        return embeddings
    except Exception as e:
        logger.error(f"Failed to initialize Ollama embeddings: {e}")
        raise EnvironmentError(
            f"Could not initialize Ollama embeddings. "
            f"Make sure Ollama is running and the '{OLLAMA_EMBED_MODEL}' model is pulled. "
            f"Run: ollama pull {OLLAMA_EMBED_MODEL}"
        ) from e


def chunk_documents(documents: List[Document]) -> List[Document]:
    """
    Split documents into smaller chunks for embedding.

    Args:
        documents: List of LangChain Documents to chunk.

    Returns:
        List of chunked Documents with preserved metadata.
    """
    if not documents:
        logger.warning("No documents provided for chunking.")
        return []

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        length_function=len,
        separators=["\n\n", "\n", ". ", " ", ""]
    )

    chunks = text_splitter.split_documents(documents)
    logger.info(f"Split {len(documents)} documents into {len(chunks)} chunks "
                f"(chunk_size={CHUNK_SIZE}, overlap={CHUNK_OVERLAP})")

    return chunks


def create_vectorstore(documents: List[Document]) -> Chroma:
    """
    Create a new ChromaDB vector store from documents.

    Args:
        documents: List of LangChain Documents to embed and store.

    Returns:
        Chroma vector store instance.
    """
    if not documents:
        raise ValueError("No documents provided to create vector store.")

    logger.info("Creating new vector store...")

    chunks = chunk_documents(documents)

    if not chunks:
        raise ValueError("No chunks generated from documents.")

    embeddings = get_embeddings()

    try:
        vectorstore = Chroma.from_documents(
            documents=chunks,
            embedding=embeddings,
            persist_directory=CHROMA_PERSIST_DIR,
            collection_name="confluence_docs"
        )

        logger.info(f"Vector store created and persisted to '{CHROMA_PERSIST_DIR}'")
        logger.info(f"Total chunks embedded: {len(chunks)}")

        return vectorstore

    except Exception as e:
        logger.error(f"Failed to create vector store: {e}")
        raise


def load_vectorstore() -> Chroma:
    """
    Load an existing ChromaDB vector store from disk.

    Returns:
        Chroma vector store instance.

    Raises:
        FileNotFoundError: If the ChromaDB directory doesn't exist.
    """
    if not os.path.exists(CHROMA_PERSIST_DIR):
        raise FileNotFoundError(
            f"ChromaDB not found at '{CHROMA_PERSIST_DIR}'. "
            "Please run the ingestion pipeline first to fetch and embed Confluence pages."
        )

    chroma_files = os.listdir(CHROMA_PERSIST_DIR)
    if not chroma_files:
        raise FileNotFoundError(
            f"ChromaDB directory '{CHROMA_PERSIST_DIR}' is empty. "
            "Please run the ingestion pipeline first."
        )

    logger.info(f"Loading vector store from '{CHROMA_PERSIST_DIR}'...")

    try:
        embeddings = get_embeddings()

        vectorstore = Chroma(
            persist_directory=CHROMA_PERSIST_DIR,
            embedding_function=embeddings,
            collection_name="confluence_docs"
        )

        collection = vectorstore._collection
        count = collection.count()

        if count == 0:
            raise FileNotFoundError(
                "ChromaDB collection is empty. "
                "Please run the ingestion pipeline first to fetch and embed Confluence pages."
            )

        logger.info(f"Vector store loaded successfully. Documents in store: {count}")

        return vectorstore

    except FileNotFoundError:
        raise
    except Exception as e:
        logger.error(f"Failed to load vector store: {e}")
        raise


def vectorstore_exists() -> bool:
    """Check if the main Confluence vector store exists and has documents."""
    if not os.path.exists(CHROMA_PERSIST_DIR):
        return False
    if not os.listdir(CHROMA_PERSIST_DIR):
        return False
    try:
        load_vectorstore()
        return True
    except Exception:
        return False


def add_documents(documents: List[Document], vectorstore: Chroma = None) -> Chroma:
    """
    Add new documents to an existing vector store (incremental update).

    Args:
        documents: List of new documents to add
        vectorstore: Optional existing Chroma vectorstore. If None, loads existing one.

    Returns:
        Updated Chroma vector store instance
    """
    if not documents:
        logger.warning("No documents to add.")
        return vectorstore if vectorstore else load_vectorstore()

    if vectorstore is None:
        vectorstore = load_vectorstore()

    logger.info(f"Adding {len(documents)} new documents to vector store...")

    chunks = chunk_documents(documents)

    if not chunks:
        logger.warning("No chunks generated from documents.")
        return vectorstore

    try:
        vectorstore.add_documents(chunks)
        # NOTE: langchain-chroma >= 0.1 auto-persists; no explicit .persist() needed
        logger.info(f"Successfully added {len(chunks)} chunks to vector store")
        return vectorstore

    except Exception as e:
        logger.error(f"Failed to add documents: {e}")
        raise


def remove_documents(page_ids: List[str], vectorstore: Chroma = None) -> Chroma:
    """
    Remove documents from vector store by page_id.

    Args:
        page_ids: List of page IDs to remove
        vectorstore: Optional existing Chroma vectorstore. If None, loads existing one.

    Returns:
        Updated Chroma vector store instance
    """
    if not page_ids:
        logger.warning("No page IDs to remove.")
        return vectorstore if vectorstore else load_vectorstore()

    if vectorstore is None:
        vectorstore = load_vectorstore()

    logger.info(f"Attempting to remove {len(page_ids)} pages from vector store...")

    try:
        collection = vectorstore._collection
        removed_count = 0

        for page_id in page_ids:
            results = collection.get(where={"page_id": page_id})

            if results and results['ids']:
                collection.delete(ids=results['ids'])
                removed_count += len(results['ids'])
                logger.debug(f"Removed {len(results['ids'])} chunks for page {page_id}")

        logger.info(f"Removed {removed_count} chunks total from vector store")

        return vectorstore

    except Exception as e:
        logger.error(f"Failed to remove documents: {e}")
        raise


def update_documents(documents: List[Document], page_ids_to_remove: List[str] = None,
                     vectorstore: Chroma = None) -> Chroma:
    """
    Update documents in vector store (remove old, add new).

    Args:
        documents: New version of documents to add
        page_ids_to_remove: Page IDs of old documents to remove.
        vectorstore: Optional existing Chroma vectorstore. If None, loads existing one.

    Returns:
        Updated Chroma vector store instance
    """
    if not documents:
        logger.warning("No documents to update.")
        return vectorstore if vectorstore else load_vectorstore()

    if vectorstore is None:
        vectorstore = load_vectorstore()

    if page_ids_to_remove is None:
        page_ids_to_remove = [doc.metadata.get('page_id') for doc in documents
                              if doc.metadata.get('page_id')]

    logger.info(f"Updating {len(documents)} documents...")

    if page_ids_to_remove:
        vectorstore = remove_documents(page_ids_to_remove, vectorstore)

    vectorstore = add_documents(documents, vectorstore)

    logger.info("Documents updated successfully")
    return vectorstore


def get_vectorstore(collection_name: str = "confluence_docs") -> Chroma:
    """
    Get a vector store for a specific collection.

    Args:
        collection_name: Name of the collection.

    Returns:
        Chroma vector store instance
    """
    if not os.path.exists(CHROMA_PERSIST_DIR):
        raise FileNotFoundError(f"ChromaDB directory not found at '{CHROMA_PERSIST_DIR}'")

    embeddings = get_embeddings()

    try:
        vectorstore = Chroma(
            persist_directory=CHROMA_PERSIST_DIR,
            embedding_function=embeddings,
            collection_name=collection_name
        )
        count = vectorstore._collection.count()
        logger.info(f"Loaded '{collection_name}' collection with {count} documents")
        return vectorstore
    except Exception as e:
        logger.error(f"Failed to load collection '{collection_name}': {e}")
        raise


def create_vectorstore_so(documents: List[Document], db_path: str = None) -> Chroma:
    """
    Create a new ChromaDB vector store for Stack Overflow documents.

    Args:
        documents: List of LangChain Documents to embed
        db_path: Optional custom path for SO database.

    Returns:
        Chroma vector store instance
    """
    if db_path is None:
        db_path = STACKOVERFLOW_DB_PATH

    if not documents:
        raise ValueError("No documents provided to create Stack Overflow vector store.")

    logger.info(f"Creating Stack Overflow vector store at {db_path}...")

    chunks = chunk_documents(documents)

    if not chunks:
        raise ValueError("No chunks generated from documents.")

    embeddings = get_embeddings()

    os.makedirs(db_path, exist_ok=True)

    try:
        vectorstore = Chroma.from_documents(
            documents=chunks,
            embedding=embeddings,
            persist_directory=db_path,
            collection_name="stackoverflow_docs"
        )

        logger.info(f"Stack Overflow vector store created at {db_path}")
        logger.info(f"Total chunks embedded: {len(chunks)}")

        return vectorstore

    except Exception as e:
        logger.error(f"Failed to create Stack Overflow vector store: {e}")
        raise


def load_vectorstore_so(db_path: str = None) -> Chroma:
    """
    Load an existing Stack Overflow vector store from disk.

    Args:
        db_path: Optional custom path.

    Returns:
        Chroma vector store instance

    Raises:
        FileNotFoundError: If the vector store directory doesn't exist.
    """
    if db_path is None:
        db_path = STACKOVERFLOW_DB_PATH

    if not os.path.exists(db_path):
        raise FileNotFoundError(
            f"Stack Overflow database not found at '{db_path}'. "
            "Please run the Stack Overflow ingestion first."
        )

    chroma_files = os.listdir(db_path)
    if not chroma_files:
        raise FileNotFoundError(f"Stack Overflow database directory '{db_path}' is empty.")

    logger.info(f"Loading Stack Overflow vector store from {db_path}...")

    try:
        embeddings = get_embeddings()

        vectorstore = Chroma(
            persist_directory=db_path,
            embedding_function=embeddings,
            collection_name="stackoverflow_docs"
        )

        collection = vectorstore._collection
        count = collection.count()

        if count == 0:
            raise FileNotFoundError("Stack Overflow collection is empty.")

        logger.info(f"Stack Overflow vector store loaded. Documents: {count}")

        return vectorstore

    except FileNotFoundError:
        raise
    except Exception as e:
        logger.error(f"Failed to load Stack Overflow vector store: {e}")
        raise


def vectorstore_so_exists(db_path: str = None) -> bool:
    """
    Check if a Stack Overflow vector store exists.

    Args:
        db_path: Optional custom path

    Returns:
        True if SO vector store exists and has documents
    """
    if db_path is None:
        db_path = STACKOVERFLOW_DB_PATH

    if not os.path.exists(db_path):
        return False

    if not os.listdir(db_path):
        return False

    try:
        load_vectorstore_so(db_path)
        return True
    except Exception:
        return False


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    if vectorstore_exists():
        print("Vector store exists!")
        vs = load_vectorstore()
        print(f"Document count: {vs._collection.count()}")
    else:
        print("No vector store found. Run ingestion first.")
