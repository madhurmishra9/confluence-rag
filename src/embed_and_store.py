"""
Embedding and Vector Store Module
 
Chunks documents, creates embeddings with Ollama nomic-embed-text,
and persists to ChromaDB.
"""
 
import os
import logging
from typing import List, Optional
from langchain_core.documents import Document
from langchain_community.embeddings import OllamaEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter
from dotenv import load_dotenv
 
load_dotenv()
 
logger = logging.getLogger(__name__)
 
# Configuration from environment
CHROMA_PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR", "./confluence_db")
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
   
    This will chunk the documents, embed them using Ollama nomic-embed-text,
    and persist to the local ChromaDB directory.
   
    Args:
        documents: List of LangChain Documents to embed and store.
       
    Returns:
        Chroma vector store instance.
    """
    if not documents:
        raise ValueError("No documents provided to create vector store.")
   
    logger.info("Creating new vector store...")
   
    # Chunk documents
    chunks = chunk_documents(documents)
   
    if not chunks:
        raise ValueError("No chunks generated from documents.")
   
    # Get embeddings
    embeddings = get_embeddings()
   
    try:
        # Create ChromaDB vector store
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
   
    # Check if the directory has content
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
       
        # Verify the collection has documents
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
    """
    Check if a ChromaDB vector store already exists.
   
    Returns:
        True if vector store exists and has documents, False otherwise.
    """
    if not os.path.exists(CHROMA_PERSIST_DIR):
        return False
   
    chroma_files = os.listdir(CHROMA_PERSIST_DIR)
    if not chroma_files:
        return False
   
    try:
        # Try to load and check if it has documents
        embeddings = get_embeddings()
        vectorstore = Chroma(
            persist_directory=CHROMA_PERSIST_DIR,
            embedding_function=embeddings,
            collection_name="confluence_docs"
        )
        count = vectorstore._collection.count()
        return count > 0
    except Exception:
        return False
 
 
if __name__ == "__main__":
    # Test loading the vector store
    logging.basicConfig(level=logging.INFO)
   
    if vectorstore_exists():
        print("Vector store exists!")
        vs = load_vectorstore()
        print(f"Document count: {vs._collection.count()}")
    else:
        print("No vector store found. Run ingestion first.")
