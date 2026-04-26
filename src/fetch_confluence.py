"""
Confluence Page Fetcher

Fetches all pages from Confluence using the REST API with pagination.
Strips HTML and returns LangChain Document objects.
Supports incremental fetching to detect new/modified/deleted pages.
"""

import os
import logging
import requests
from typing import List, Tuple, Dict
from bs4 import BeautifulSoup
from langchain_core.documents import Document
from dotenv import load_dotenv
from .confluence_metadata import ConfluenceMetadataTracker

load_dotenv()

logger = logging.getLogger(__name__)

# Environment variables
CONFLUENCE_URL = os.getenv("CONFLUENCE_URL")
CONFLUENCE_EMAIL = os.getenv("CONFLUENCE_EMAIL")
CONFLUENCE_API_TOKEN = os.getenv("CONFLUENCE_API_TOKEN")
CONFLUENCE_SPACE_KEY = os.getenv("CONFLUENCE_SPACE_KEY", "")  # Optional: filter by space


def validate_env_vars() -> None:
    """Validate required environment variables are set."""
    missing = []
    if not CONFLUENCE_URL:
        missing.append("CONFLUENCE_URL")
    if not CONFLUENCE_EMAIL:
        missing.append("CONFLUENCE_EMAIL")
    if not CONFLUENCE_API_TOKEN:
        missing.append("CONFLUENCE_API_TOKEN")

    if missing:
        raise EnvironmentError(
            f"Missing required environment variables: {', '.join(missing)}. "
            "Please check your .env file."
        )


def strip_html(html_content: str) -> str:
    """Strip HTML tags and return clean text."""
    if not html_content:
        return ""

    soup = BeautifulSoup(html_content, "lxml")

    for element in soup(["script", "style"]):
        element.decompose()

    text = soup.get_text(separator=" ")
    lines = (line.strip() for line in text.splitlines())
    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
    text = " ".join(chunk for chunk in chunks if chunk)

    return text


def get_base_url() -> str:
    """Extract base URL from Confluence URL."""
    url = CONFLUENCE_URL.rstrip("/")
    if "/wiki" in url:
        return url.split("/wiki")[0]
    return url


def fetch_raw_pages() -> List[Dict]:
    """
    Fetch all pages from Confluence REST API with pagination.

    Returns:
        List of raw page dictionaries from the Confluence API

    Raises:
        requests.exceptions.RequestException: If API call fails
    """
    validate_env_vars()

    all_pages = []
    start = 0
    limit = 50
    max_retries = 3

    api_url = f"{CONFLUENCE_URL.rstrip('/')}/rest/api/content"

    params = {
        "type": "page",
        "limit": limit,
        "expand": "body.storage,version,space",
    }

    if CONFLUENCE_SPACE_KEY:
        params["spaceKey"] = CONFLUENCE_SPACE_KEY
        logger.info(f"Fetching pages from space: {CONFLUENCE_SPACE_KEY}")
    else:
        logger.info("Fetching pages from all spaces")

    auth = (CONFLUENCE_EMAIL, CONFLUENCE_API_TOKEN)

    try:
        while True:
            params["start"] = start

            logger.info(f"Fetching pages (start={start}, limit={limit})...")

            for attempt in range(max_retries):
                try:
                    response = requests.get(
                        api_url,
                        params=params,
                        auth=auth,
                        timeout=30,
                        headers={"Accept": "application/json"}
                    )
                    response.raise_for_status()
                    break
                except requests.exceptions.RequestException as e:
                    if attempt < max_retries - 1:
                        logger.warning(f"Attempt {attempt + 1} failed: {e}. Retrying...")
                        continue
                    else:
                        raise

            data = response.json()
            pages = data.get("results", [])

            if not pages:
                logger.info(f"No more pages to fetch (total fetched: {len(all_pages)})")
                break

            logger.info(f"Fetched {len(pages)} pages (total so far: {len(all_pages) + len(pages)})")
            all_pages.extend(pages)

            if not data.get("_links", {}).get("next"):
                logger.info(f"All pages fetched. Total: {len(all_pages)}")
                break

            start += limit

        return all_pages

    except requests.exceptions.ConnectionError:
        logger.error(
            f"Failed to connect to Confluence at {CONFLUENCE_URL}. "
            "Please verify the URL and that Confluence is accessible."
        )
        raise
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 401:
            logger.error("Authentication failed. Please verify your email and API token in .env")
        elif e.response.status_code == 403:
            logger.error("Access denied. Your API token may not have permission to access Confluence.")
        elif e.response.status_code == 404:
            logger.error(
                f"Confluence URL not found: {CONFLUENCE_URL}. "
                "Please verify the URL in your .env file."
            )
        else:
            logger.error(f"HTTP Error {e.response.status_code}: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error fetching pages: {e}")
        raise


def pages_to_documents(pages: List[Dict], base_url: str = None) -> List[Document]:
    """
    Convert raw page data to LangChain Document objects.

    Args:
        pages: List of raw page dictionaries from API
        base_url: Base URL for building page URLs (auto-detected if None)

    Returns:
        List of LangChain Document objects
    """
    if base_url is None:
        base_url = get_base_url()

    documents: List[Document] = []

    for page in pages:
        try:
            page_id = page.get("id", "")
            title = page.get("title", "Untitled")

            body_storage = page.get("body", {}).get("storage", {})
            html_content = body_storage.get("value", "")

            text_content = strip_html(html_content)

            if not text_content.strip():
                logger.debug(f"Skipping empty page: {title}")
                continue

            space_key = page.get("space", {}).get("key", "")
            page_url = f"{base_url}/wiki/spaces/{space_key}/pages/{page_id}"

            version = page.get("version", {}).get("number", 1)
            modified = page.get("version", {}).get("when", "")

            doc = Document(
                page_content=text_content,
                metadata={
                    "title": title,
                    "page_id": page_id,
                    "url": page_url,
                    "space_key": space_key,
                    "version": version,
                    "modified": modified,
                }
            )
            documents.append(doc)
            logger.debug(f"Created document: {title}")

        except Exception as e:
            logger.warning(f"Error processing page {page.get('title', 'Unknown')}: {e}")
            continue

    return documents


def fetch_pages() -> List[Document]:
    """
    Fetch all Confluence pages with pagination.

    Returns:
        List of LangChain Document objects with page content and metadata.
    """
    validate_env_vars()
    base_url = get_base_url()

    raw_pages = fetch_raw_pages()

    if not raw_pages:
        logger.warning(
            "No documents were fetched from Confluence. "
            "This could mean your Confluence space is empty or the credentials "
            "don't have access to any pages."
        )
        return []

    documents = pages_to_documents(raw_pages, base_url)
    logger.info(f"Total documents created: {len(documents)}")

    return documents


def fetch_incremental_pages(
    metadata_tracker: ConfluenceMetadataTracker = None,
) -> Tuple[List[Document], List[Document], List[str]]:
    """
    Fetch Confluence pages and detect new, modified, and deleted pages.

    Args:
        metadata_tracker: Optional ConfluenceMetadataTracker. If None, creates one.

    Returns:
        Tuple of (new_documents, modified_documents, deleted_page_ids)
    """
    if metadata_tracker is None:
        metadata_tracker = ConfluenceMetadataTracker()

    validate_env_vars()
    base_url = get_base_url()

    logger.info("Starting incremental Confluence fetch...")

    raw_pages = fetch_raw_pages()

    if not raw_pages:
        logger.warning("No pages found in Confluence")
        return [], [], []

    logger.info("Detecting changes...")
    new_raw, modified_raw, deleted_ids = metadata_tracker.detect_changes(
        [
            {
                'id': p.get('id'),
                'title': p.get('title'),
                'version': p.get('version', {}).get('number', 1),
                'modified': p.get('version', {}).get('when', ''),
                'url': '',
                'space_key': p.get('space', {}).get('key', ''),
            }
            for p in raw_pages
        ]
    )

    new_docs = pages_to_documents(new_raw, base_url)
    modified_docs = pages_to_documents(modified_raw, base_url)

    logger.info(
        f"Change summary: {len(new_docs)} new, {len(modified_docs)} modified, "
        f"{len(deleted_ids)} deleted"
    )

    for page in new_raw + modified_raw:
        page_id = page.get('id', '')
        metadata_tracker.add_or_update_page(
            page_id=page_id,
            title=page.get('title', 'Untitled'),
            version=page.get('version', {}).get('number', 1),
            modified=page.get('version', {}).get('when', ''),
            url=f"{base_url}/wiki/spaces/{page.get('space', {}).get('key', '')}/pages/{page_id}",
            space_key=page.get('space', {}).get('key', ''),
            chunk_count=0,
        )

    for page_id in deleted_ids:
        metadata_tracker.remove_page(page_id)

    metadata_tracker.save()

    return new_docs, modified_docs, deleted_ids


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    docs = fetch_pages()
    print(f"\nFetched {len(docs)} documents:")
    for doc in docs[:5]:
        print(f"  - {doc.metadata['title']}")
