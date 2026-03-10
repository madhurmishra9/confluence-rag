"""
Confluence Page Fetcher
 
Fetches all pages from Confluence using the REST API with pagination.
Strips HTML and returns LangChain Document objects.
"""
 
import os
import logging
import requests
from typing import List, Optional
from bs4 import BeautifulSoup
from langchain_core.documents import Document
from dotenv import load_dotenv
 
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
   
    # Remove script and style elements
    for element in soup(["script", "style"]):
        element.decompose()
   
    # Get text and clean up whitespace
    text = soup.get_text(separator=" ")
    lines = (line.strip() for line in text.splitlines())
    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
    text = " ".join(chunk for chunk in chunks if chunk)
   
    return text
 
 
def get_base_url() -> str:
    """Extract base URL from Confluence URL."""
    url = CONFLUENCE_URL.rstrip("/")
    # Handle URLs like https://domain.atlassian.net/wiki/...
    if "/wiki" in url:
        return url.split("/wiki")[0]
    return url
 
 
def fetch_pages() -> List[Document]:
    """
    Fetch all Confluence pages with pagination.
   
    Returns:
        List of LangChain Document objects with page content and metadata.
    """
    validate_env_vars()
   
    base_url = get_base_url()
    api_url = f"{base_url}/wiki/rest/api/content"
   
    auth = (CONFLUENCE_EMAIL, CONFLUENCE_API_TOKEN)
   
    documents: List[Document] = []
    start = 0
    limit = 50  # Confluence default max is usually 100
   
    logger.info("Starting Confluence page fetch...")
   
    while True:
        params = {
            "start": start,
            "limit": limit,
            "expand": "body.storage,space",
            "type": "page",
        }
       
        # Optional: filter by space key
        if CONFLUENCE_SPACE_KEY:
            params["spaceKey"] = CONFLUENCE_SPACE_KEY
            logger.info(f"Filtering by space: {CONFLUENCE_SPACE_KEY}")
       
        try:
            response = requests.get(
                api_url,
                auth=auth,
                params=params,
                headers={"Accept": "application/json"},
                timeout=30
            )
            response.raise_for_status()
           
        except requests.exceptions.HTTPError as e:
            if response.status_code == 401:
                raise EnvironmentError(
                    "Authentication failed. Please check your CONFLUENCE_EMAIL and "
                    "CONFLUENCE_API_TOKEN in the .env file."
                )
            elif response.status_code == 403:
                raise EnvironmentError(
                    "Access forbidden. Your API token may not have permission to "
                    "access this Confluence instance."
                )
            elif response.status_code == 404:
                raise EnvironmentError(
                    f"Confluence API not found at {api_url}. "
                    "Please check your CONFLUENCE_URL in the .env file."
                )
            else:
                logger.error(f"HTTP error fetching pages: {e}")
                raise
               
        except requests.exceptions.ConnectionError as e:
            raise EnvironmentError(
                f"Could not connect to Confluence at {base_url}. "
                "Please check your CONFLUENCE_URL and network connection."
            ) from e
           
        except requests.exceptions.Timeout:
            logger.error("Request timed out while fetching Confluence pages.")
            raise
           
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching Confluence pages: {e}")
            raise
       
        data = response.json()
        results = data.get("results", [])
       
        if not results:
            if start == 0:
                logger.warning("No pages found in Confluence.")
            break
       
        for page in results:
            try:
                page_id = page.get("id", "")
                title = page.get("title", "Untitled")
               
                # Get page body
                body_storage = page.get("body", {}).get("storage", {})
                html_content = body_storage.get("value", "")
               
                # Strip HTML to get plain text
                text_content = strip_html(html_content)
               
                # Skip empty pages
                if not text_content.strip():
                    logger.debug(f"Skipping empty page: {title}")
                    continue
               
                # Build page URL
                space_key = page.get("space", {}).get("key", "")
                page_url = f"{base_url}/wiki/spaces/{space_key}/pages/{page_id}"
               
                # Create LangChain Document
                doc = Document(
                    page_content=text_content,
                    metadata={
                        "title": title,
                        "page_id": page_id,
                        "url": page_url,
                        "space_key": space_key,
                    }
                )
                documents.append(doc)
                logger.debug(f"Fetched page: {title}")
               
            except Exception as e:
                logger.warning(f"Error processing page {page.get('title', 'Unknown')}: {e}")
                continue
       
        # Check if there are more pages
        total_size = data.get("size", 0)
        logger.info(f"Fetched {start + len(results)} pages so far...")
       
        # Move to next batch
        if len(results) < limit:
            break  # No more pages
       
        start += limit
   
    logger.info(f"Total pages fetched: {len(documents)}")
   
    if not documents:
        logger.warning(
            "No documents were fetched from Confluence. "
            "This could mean your Confluence space is empty or the credentials "
            "don't have access to any pages."
        )
   
    return documents
 
 
if __name__ == "__main__":
    # Test the fetch function
    logging.basicConfig(level=logging.INFO)
    docs = fetch_pages()
    print(f"\nFetched {len(docs)} documents:")
    for doc in docs[:5]:  # Print first 5
        print(f"  - {doc.metadata['title']}")
