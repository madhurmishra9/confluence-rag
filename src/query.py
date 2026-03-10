"""
Query Module
 
Builds the RAG query chain using Ollama llama3.1:8b LLM
and retrieves answers from the ChromaDB vector store.
"""
 
import os
import logging
from typing import Tuple, List
from langchain_community.llms import Ollama
from langchain.chains.retrieval_qa.base import RetrievalQA
from langchain_core.prompts import PromptTemplate
from langchain_core.documents import Document
from dotenv import load_dotenv
 
load_dotenv()
 
logger = logging.getLogger(__name__)
 
# Configuration from environment
OLLAMA_LLM_MODEL = os.getenv("OLLAMA_LLM_MODEL", "llama3.1:8b")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
RETRIEVER_K = int(os.getenv("RETRIEVER_K", "5"))
 
# Custom prompt template that instructs the LLM to answer ONLY from Confluence context
PROMPT_TEMPLATE = """You are a helpful assistant that answers questions based ONLY on the provided Confluence documentation context.
 
IMPORTANT INSTRUCTIONS:
1. Answer the question using ONLY the information provided in the Context below.
2. If the answer cannot be found in the Context, you MUST respond with: "I could not find this information in the Confluence documents."
3. Do NOT use any outside knowledge or make assumptions beyond what is explicitly stated in the Context.
4. Be concise and direct in your answers.
5. If the Context contains relevant information, provide a clear and helpful answer.
 
Context:
{context}
 
Question: {question}
 
Answer:"""
 
 
def get_llm() -> Ollama:
    """
    Create and return Ollama LLM instance.
   
    Returns:
        Ollama LLM configured with llama3.1:8b model.
    """
    try:
        llm = Ollama(
            model=OLLAMA_LLM_MODEL,
            base_url=OLLAMA_BASE_URL,
            temperature=0.1,  # Low temperature for more focused answers
        )
        logger.info(f"Initialized Ollama LLM with model: {OLLAMA_LLM_MODEL}")
        return llm
    except Exception as e:
        logger.error(f"Failed to initialize Ollama LLM: {e}")
        raise EnvironmentError(
            f"Could not initialize Ollama LLM. "
            f"Make sure Ollama is running and the '{OLLAMA_LLM_MODEL}' model is pulled. "
            f"Run: ollama pull {OLLAMA_LLM_MODEL}"
        ) from e
 
 
def build_qa_chain(vectorstore) -> RetrievalQA:
    """
    Build a RetrievalQA chain from the vector store.
   
    Args:
        vectorstore: ChromaDB vector store instance.
       
    Returns:
        RetrievalQA chain configured with Ollama LLM and custom prompt.
    """
    if vectorstore is None:
        raise ValueError("Vector store cannot be None.")
   
    logger.info("Building QA chain...")
   
    # Create the prompt template
    prompt = PromptTemplate(
        template=PROMPT_TEMPLATE,
        input_variables=["context", "question"]
    )
   
    # Get the LLM
    llm = get_llm()
   
    # Create the retriever with top-k results
    retriever = vectorstore.as_retriever(
        search_type="similarity",
        search_kwargs={"k": RETRIEVER_K}
    )
   
    # Build the RetrievalQA chain
    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=retriever,
        return_source_documents=True,
        chain_type_kwargs={"prompt": prompt}
    )
   
    logger.info(f"QA chain built successfully (retrieving top {RETRIEVER_K} chunks)")
   
    return qa_chain
 
 
def format_sources(source_documents: List[Document]) -> str:
    """
    Format source documents for display.
   
    Args:
        source_documents: List of source Document objects.
       
    Returns:
        Formatted string of sources.
    """
    if not source_documents:
        return "No sources found."
   
    # Deduplicate by URL
    seen_urls = set()
    unique_sources = []
   
    for doc in source_documents:
        url = doc.metadata.get("url", "")
        if url and url not in seen_urls:
            seen_urls.add(url)
            unique_sources.append(doc)
   
    lines = ["\n--- Sources ---"]
    for doc in unique_sources:
        title = doc.metadata.get("title", "Unknown Title")
        url = doc.metadata.get("url", "No URL")
        lines.append(f"  - {title}")
        lines.append(f"    {url}")
   
    return "\n".join(lines)
 
 
def ask(question: str, qa_chain: RetrievalQA) -> Tuple[str, List[Document]]:
    """
    Ask a question using the QA chain and return the answer with sources.
   
    Args:
        question: The question to ask.
        qa_chain: The RetrievalQA chain.
       
    Returns:
        Tuple of (answer string, list of source documents).
    """
    if not question or not question.strip():
        raise ValueError("Question cannot be empty.")
   
    if qa_chain is None:
        raise ValueError("QA chain cannot be None.")
   
    logger.info(f"Processing question: {question}")
   
    try:
        # Run the query
        result = qa_chain.invoke({"query": question})
       
        answer = result.get("result", "").strip()
        source_documents = result.get("source_documents", [])
       
        logger.info(f"Answer generated. Source documents: {len(source_documents)}")
       
        # Print sources
        print(format_sources(source_documents))
       
        return answer, source_documents
       
    except Exception as e:
        logger.error(f"Error during QA invocation: {e}")
        raise
 
 
if __name__ == "__main__":
    # Test the query module
    logging.basicConfig(level=logging.INFO)
   
    from src.embed_and_store import load_vectorstore
   
    try:
        vectorstore = load_vectorstore()
        qa_chain = build_qa_chain(vectorstore)
       
        question = "What is this documentation about?"
        answer, sources = ask(question, qa_chain)
        print(f"\nAnswer: {answer}")
    except FileNotFoundError as e:
        print(f"Error: {e}")
    except Exception as e:
        print(f"Error: {e}")
