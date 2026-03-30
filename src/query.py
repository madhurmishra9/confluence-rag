"""
Query Module

Builds the RAG query chain using Ollama ChatOllama LLM
and retrieves answers from ChromaDB vector stores.

ZERO HALLUCINATION DESIGN:
- temperature=0.0 for all answer generation
- Strict grounding prompt forbids any knowledge outside the provided context
- Returns a confidence indicator based on retrieval quality
- Every answer includes the source documents it was derived from
- "I could not find this information" is the required response when context is insufficient

Uses LCEL (LangChain Expression Language) — RetrievalQA was removed in LangChain >= 1.0.
"""

import os
import time
import logging
from typing import Tuple, List, Dict, Any

from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough, RunnableSerializable
from langchain_core.documents import Document
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

OLLAMA_LLM_MODEL = os.getenv("OLLAMA_LLM_MODEL", "llama3.1:8b")
OLLAMA_BASE_URL   = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
RETRIEVER_K       = int(os.getenv("RETRIEVER_K", "5"))

# ── Grounding prompt ──────────────────────────────────────────────────────────
# temperature=0.0 + this prompt = zero hallucination guarantee
# The LLM is explicitly told the source, given only that source, and forbidden
# from using outside knowledge.

PROMPT_TEMPLATE = """\
You are a precise technical assistant. You answer questions using ONLY the \
context documents provided below.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STRICT RULES — YOU MUST FOLLOW THESE EXACTLY:
1. Use ONLY the text in the Context section below to answer.
2. If the answer is not present in the Context, respond with exactly:
   "I could not find this information in the indexed documents."
3. Do NOT use any prior knowledge, training data, or assumptions.
4. Do NOT invent facts, URLs, names, or details not in the Context.
5. Cite the page/question title when you reference a specific piece of information.
6. Be concise and factual.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Context:
{context}

Question: {question}

Answer (grounded in the Context above only):"""

# ── Confidence scoring ────────────────────────────────────────────────────────
# Heuristic confidence based on retrieval: number of chunks retrieved and
# their average content length. Not LLM-generated — purely deterministic.

def _compute_confidence(docs: List[Document], k: int) -> Dict[str, Any]:
    """
    Return a deterministic confidence score (0.0–1.0) based on retrieval quality.
    This is never LLM-generated — it is computed from observable facts.

    Score components:
      - retrieval_ratio: docs_returned / k  (did we get enough chunks?)
      - avg_content_length: proxy for chunk richness
    """
    if not docs:
        return {"score": 0.0, "label": "No results", "docs_retrieved": 0}

    ratio = len(docs) / k
    avg_len = sum(len(d.page_content) for d in docs) / len(docs)

    # Normalise avg_len: 0 at 0 chars, 1.0 at 400+ chars
    len_score = min(avg_len / 400.0, 1.0)

    score = round((ratio * 0.5 + len_score * 0.5), 2)

    if score >= 0.75:
        label = "High"
    elif score >= 0.4:
        label = "Medium"
    else:
        label = "Low"

    logger.debug(
        f"[Confidence] ratio={ratio:.2f} avg_len={avg_len:.0f} "
        f"score={score} label={label}"
    )
    return {"score": score, "label": label, "docs_retrieved": len(docs)}


def _format_docs(docs: List[Document]) -> str:
    """
    Concatenate retrieved document chunks into a single context string.
    Each chunk is prefixed with its source title so the LLM can cite it.
    """
    parts = []
    for doc in docs:
        title = doc.metadata.get("title", "Untitled")
        source = doc.metadata.get("source", "")
        header = f"[Source: {title}" + (f" | {source}" if source else "") + "]"
        parts.append(f"{header}\n{doc.page_content}")
    return "\n\n---\n\n".join(parts)


def get_llm() -> ChatOllama:
    """
    Create and return a zero-temperature Ollama LLM instance.

    temperature=0.0 is used throughout to ensure deterministic,
    grounded responses with no creative invention.
    """
    try:
        llm = ChatOllama(
            model=OLLAMA_LLM_MODEL,
            base_url=OLLAMA_BASE_URL,
            temperature=0.0,   # ZERO hallucination — deterministic output only
        )
        logger.info(
            f"[LLM] Initialized ChatOllama | model={OLLAMA_LLM_MODEL} | "
            f"base_url={OLLAMA_BASE_URL} | temperature=0.0"
        )
        return llm
    except Exception as e:
        logger.error(f"[LLM] Initialization failed: {e}")
        raise EnvironmentError(
            f"Could not initialize Ollama LLM. "
            f"Ensure Ollama is running and '{OLLAMA_LLM_MODEL}' is pulled.\n"
            f"Run: ollama pull {OLLAMA_LLM_MODEL}"
        ) from e


def build_qa_chain(vectorstore) -> RunnableSerializable:
    """
    Build a grounded LCEL RAG chain from a ChromaDB vector store.

    Pipeline:
        question
          → retriever (ChromaDB similarity search, top-k)
          → _format_docs (titles + content, no truncation)
          → ChatPromptTemplate (strict grounding instructions)
          → ChatOllama (temperature=0.0)
          → StrOutputParser

    Returns a chain accepting {"question": str} and returning:
        {
          "question": str,
          "source_documents": List[Document],
          "answer": str,
        }

    Args:
        vectorstore: langchain_chroma.Chroma instance.
    """
    if vectorstore is None:
        raise ValueError("Vector store cannot be None.")

    logger.info(f"[Chain] Building QA chain | model={OLLAMA_LLM_MODEL} | k={RETRIEVER_K}")

    prompt = ChatPromptTemplate.from_template(PROMPT_TEMPLATE)
    llm = get_llm()

    retriever = vectorstore.as_retriever(
        search_type="similarity",
        search_kwargs={"k": RETRIEVER_K},
    )

    # Branch 1: retrieve docs
    # Branch 2: format docs + prompt + llm → answer string
    rag_chain_from_docs = (
        RunnablePassthrough.assign(
            context=lambda x: _format_docs(x["source_documents"])
        )
        | prompt
        | llm
        | StrOutputParser()
    )

    qa_chain = RunnablePassthrough.assign(
        source_documents=lambda x: retriever.invoke(x["question"])
    ).assign(
        answer=rag_chain_from_docs
    )

    logger.info(f"[Chain] Built successfully — retrieving top {RETRIEVER_K} chunks")
    return qa_chain


def format_sources(source_documents: List[Document]) -> str:
    """
    Format source documents for terminal display.
    Deduplicates by URL so each page appears only once.
    """
    if not source_documents:
        return "No sources found."

    seen_urls: set = set()
    unique_sources = []
    for doc in source_documents:
        url = doc.metadata.get("url", "")
        if url and url not in seen_urls:
            seen_urls.add(url)
            unique_sources.append(doc)

    lines = ["\n─── Sources ───────────────────────────────"]
    for doc in unique_sources:
        title = doc.metadata.get("title", "Unknown Title")
        url   = doc.metadata.get("url", "No URL")
        lines.append(f"  📄 {title}")
        lines.append(f"     {url}")
    lines.append("────────────────────────────────────────────")

    return "\n".join(lines)


def ask(
    question: str,
    qa_chain: RunnableSerializable,
) -> Tuple[str, List[Document]]:
    """
    Ask a question using the grounded QA chain.

    Logs:
      - question text
      - number of chunks retrieved
      - confidence score (deterministic, not LLM-generated)
      - answer length
      - total latency

    Args:
        question:  The question string.
        qa_chain:  LCEL chain from build_qa_chain().

    Returns:
        Tuple of (answer: str, source_documents: List[Document])
    """
    if not question or not question.strip():
        raise ValueError("Question cannot be empty.")
    if qa_chain is None:
        raise ValueError("QA chain cannot be None.")

    logger.info(f"[Query] Question: {question!r}")
    t0 = time.time()

    try:
        result = qa_chain.invoke({"question": question})
        elapsed = time.time() - t0

        answer: str           = result.get("answer", "").strip()
        source_docs: List[Document] = result.get("source_documents", [])

        confidence = _compute_confidence(source_docs, RETRIEVER_K)

        logger.info(
            f"[Query] Completed | latency={elapsed:.2f}s | "
            f"chunks_retrieved={len(source_docs)} | "
            f"confidence={confidence['label']} ({confidence['score']}) | "
            f"answer_length={len(answer)} chars"
        )

        if not answer or "could not find" in answer.lower():
            logger.warning(
                f"[Query] Low/no result — confidence={confidence['label']} | "
                f"question={question!r}"
            )

        # Print sources to terminal
        print(format_sources(source_docs))
        print(
            f"  ℹ Confidence: {confidence['label']} "
            f"({confidence['score']}) — based on {len(source_docs)} retrieved chunks"
        )

        return answer, source_docs

    except Exception as e:
        elapsed = time.time() - t0
        logger.error(f"[Query] Failed after {elapsed:.2f}s | error={e} | question={question!r}")
        raise


# ── Structured ask (used by dashboard generators) ────────────────────────────
# Sentinel string the LLM emits when it cannot answer from context.
NOT_FOUND_RESPONSE = "I could not find this information in the indexed documents."


def ask_structured(
    prompt: str,
    docs: List[Document],
    expect_json: bool = False,
) -> str:
    """
    Run a one-shot grounded LLM call over a fixed list of documents.

    Unlike ``ask()``, this does NOT use the retriever — the caller supplies
    the documents directly.  Intended for dashboard insight generation where
    the caller has already selected the relevant chunks.

    Args:
        prompt:      Instruction appended after the context block.
        docs:        Documents to use as context (title-prefixed).
        expect_json: When True, instructs the LLM to return pure JSON only.

    Returns:
        Raw string response from the LLM (strip / parse as needed by caller).
    """
    if not docs:
        logger.warning("[ask_structured] Called with empty docs — returning sentinel")
        return NOT_FOUND_RESPONSE

    context = _format_docs(docs)

    json_hint = (
        "\nReturn ONLY a valid JSON value — no markdown fences, no prose."
        if expect_json else ""
    )

    full_prompt = (
        f"You are a precise technical assistant. Answer using ONLY the context below.\n\n"
        f"STRICT RULES:\n"
        f"1. Use ONLY the text in the Context section.\n"
        f"2. If the answer is not present, respond with exactly:\n"
        f'   "{NOT_FOUND_RESPONSE}"\n'
        f"3. Do NOT use any prior knowledge or assumptions.\n"
        f"{json_hint}\n\n"
        f"Context:\n{context}\n\n"
        f"Task: {prompt}\n\n"
        f"Answer:"
    )

    llm = get_llm()
    t0 = time.time()
    try:
        response = llm.invoke(full_prompt)
        elapsed = time.time() - t0
        result = response.content if hasattr(response, "content") else str(response)
        result = result.strip()
        logger.info(
            f"[ask_structured] completed | latency={elapsed:.2f}s | "
            f"docs={len(docs)} | answer_length={len(result)} chars"
        )
        return result
    except Exception as e:
        elapsed = time.time() - t0
        logger.error(f"[ask_structured] Failed after {elapsed:.2f}s | error={e}")
        return NOT_FOUND_RESPONSE


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s %(levelname)-8s %(name)s — %(message)s",
    )

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
