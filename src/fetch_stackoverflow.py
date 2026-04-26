"""
Stack Overflow Fetcher
Fetches questions and answers from Stack Exchange API.
Returns LangChain Document objects.

No deprecated LangChain imports — uses langchain_core.documents.Document only.
"""

import os
import time
import logging
import requests
from typing import List, Dict
from datetime import datetime, timezone
from bs4 import BeautifulSoup
from langchain_core.documents import Document
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# Environment variables
STACKOVERFLOW_TAGS = os.getenv("STACKOVERFLOW_TAGS", "python,api,rest-api,json,database")
STACKOVERFLOW_FETCH_LIMIT = int(os.getenv("STACKOVERFLOW_FETCH_LIMIT", "1000"))
SO_RATE_LIMIT_KEY = os.getenv("SO_RATE_LIMIT_KEY", "")  # Optional — raises API rate limits

# Stack Exchange API endpoint
STACK_EXCHANGE_API = "https://api.stackexchange.com/2.3"


def strip_html(html_content: str) -> str:
    """Strip HTML tags and return clean text."""
    if not html_content:
        return ""

    soup = BeautifulSoup(html_content, "html.parser")

    for element in soup(["script", "style"]):
        element.decompose()

    text = soup.get_text(separator=" ")
    lines = (line.strip() for line in text.splitlines())
    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
    text = " ".join(chunk for chunk in chunks if chunk)

    return text


def fetch_questions_by_tag(tag: str, min_answers: int = 1, limit: int = None) -> List[Dict]:
    """
    Fetch questions from Stack Overflow by tag.

    Args:
        tag: Tag to search for (e.g., "python", "api")
        min_answers: Only return questions with at least this many answers
        limit: Max number of questions (default: STACKOVERFLOW_FETCH_LIMIT)

    Returns:
        List of question dictionaries
    """
    if limit is None:
        limit = STACKOVERFLOW_FETCH_LIMIT

    url = f"{STACK_EXCHANGE_API}/questions"

    params = {
        "site": "stackoverflow",
        "tagged": tag,
        "sort": "votes",
        "order": "desc",
        "pagesize": 100,
        "filter": "withbody",  # Include body content
    }

    if SO_RATE_LIMIT_KEY:
        params["key"] = SO_RATE_LIMIT_KEY

    questions = []
    page = 1

    logger.info(f"Fetching Stack Overflow questions for tag: {tag}")

    try:
        while len(questions) < limit:
            params["page"] = page

            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()

            data = response.json()
            results = data.get("items", [])

            if not results:
                logger.info(f"No more questions found for tag: {tag}")
                break

            # Filter by minimum answers
            filtered = [q for q in results if q.get("answer_count", 0) >= min_answers]

            if not filtered and results:
                logger.debug(f"Filtered out {len(results)} questions with <{min_answers} answers")
                break

            questions.extend(filtered)
            logger.info(f"Fetched {len(questions)} questions so far (tag: {tag})...")

            if not data.get("has_more", False):
                break

            page += 1
            time.sleep(0.5)  # Respect Stack Exchange rate limits

        questions = questions[:limit]
        logger.info(f"Total questions fetched for tag '{tag}': {len(questions)}")

        return questions

    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching Stack Overflow questions: {e}")
        raise


def fetch_answers_for_question(question_id: int) -> List[Dict]:
    """
    Fetch answers for a specific question.

    Args:
        question_id: Stack Overflow question ID

    Returns:
        List of answer dictionaries
    """
    url = f"{STACK_EXCHANGE_API}/questions/{question_id}/answers"

    params = {
        "site": "stackoverflow",
        "sort": "votes",
        "order": "desc",
        "pagesize": 100,
        "filter": "withbody",
    }

    if SO_RATE_LIMIT_KEY:
        params["key"] = SO_RATE_LIMIT_KEY

    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()

        data = response.json()
        answers = data.get("items", [])

        logger.debug(f"Fetched {len(answers)} answers for question {question_id}")
        return answers

    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching answers for question {question_id}: {e}")
        return []


def questions_to_documents(questions: List[Dict], include_answers: bool = True) -> List[Document]:
    """
    Convert Stack Overflow questions to LangChain Document objects.

    Args:
        questions: List of question dictionaries from API
        include_answers: Whether to include top answers in content

    Returns:
        List of LangChain Document objects
    """
    documents = []

    for question in questions:
        try:
            question_id = question.get("question_id")
            title = question.get("title", "Untitled")

            body_html = question.get("body", "")
            body_text = strip_html(body_html)

            tags = question.get("tags", [])
            score = question.get("score", 0)
            answer_count = question.get("answer_count", 0)
            view_count = question.get("view_count", 0)
            link = question.get("link", "")
            created_date = question.get("creation_date", "")
            owner = question.get("owner", {})

            # Convert Unix timestamp to ISO string
            try:
                created_dt = (
                    datetime.fromtimestamp(created_date, tz=timezone.utc).isoformat()
                    if created_date else ""
                )
            except Exception:
                created_dt = ""

            content = f"Q: {title}\n\n{body_text}"

            # Include top 2 answers if requested
            if include_answers and answer_count > 0:
                logger.debug(f"Fetching answers for question {question_id}...")
                answers = fetch_answers_for_question(question_id)

                for i, answer in enumerate(answers[:2]):
                    answer_text = strip_html(answer.get("body", ""))
                    answer_score = answer.get("score", 0)
                    content += f"\n\nA{i + 1} (Score: {answer_score}):\n{answer_text}"

            doc = Document(
                page_content=content,
                metadata={
                    "question_id": str(question_id),
                    "title": title,
                    "tags": tags,
                    "score": score,
                    "answer_count": answer_count,
                    "view_count": view_count,
                    "url": link,
                    "created_at": created_dt,
                    "owner": owner.get("display_name", "Anonymous"),
                    "source": "stackoverflow",
                }
            )
            documents.append(doc)
            logger.debug(f"Created document: {title} (Q:{question_id})")

        except Exception as e:
            logger.warning(f"Error processing question {question.get('question_id', 'unknown')}: {e}")
            continue

    return documents


def fetch_stackoverflow_questions(tags: str = None, include_answers: bool = True) -> List[Document]:
    """
    Fetch Stack Overflow questions and convert to LangChain Documents.

    Args:
        tags: Comma-separated tags (default: STACKOVERFLOW_TAGS from .env)
        include_answers: Whether to include answers in document content

    Returns:
        List of LangChain Document objects
    """
    if tags is None:
        tags = STACKOVERFLOW_TAGS

    if not tags:
        logger.warning("No Stack Overflow tags specified")
        return []

    tag_list = [t.strip() for t in tags.split(",") if t.strip()]
    all_documents = []

    for tag in tag_list:
        try:
            logger.info(f"Fetching Stack Overflow questions for tag: {tag}")
            questions = fetch_questions_by_tag(tag, min_answers=1)

            if questions:
                documents = questions_to_documents(questions, include_answers=include_answers)
                all_documents.extend(documents)
                logger.info(f"Created {len(documents)} documents from tag: {tag}")

        except Exception as e:
            logger.error(f"Failed to fetch tag '{tag}': {e}")
            continue

    logger.info(f"Total Stack Overflow documents created: {len(all_documents)}")

    if not all_documents:
        logger.warning("No Stack Overflow documents were created")

    return all_documents


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    docs = fetch_stackoverflow_questions("python,api", include_answers=False)
    print(f"\nFetched {len(docs)} Stack Overflow documents:")
    for doc in docs[:3]:
        print(f"  - {doc.metadata['title']}")
