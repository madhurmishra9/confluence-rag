"""
Tag Linker: Map Stack Overflow tags to Confluence content
Enables cross-linking between SO articles and Confluence pages.

No deprecated LangChain imports — uses langchain_core.documents.Document only.
"""

import logging
from typing import Dict, List, Set, Tuple
from langchain_core.documents import Document

logger = logging.getLogger(__name__)


class TagLinker:
    """Links Stack Overflow tags to Confluence content via keyword matching."""

    def __init__(self):
        """Initialize tag linker with default tag-to-keyword mappings."""
        self.tag_mapping: Dict[str, Dict] = {
            "python": {
                "keywords": ["python", "django", "flask", "fastapi", "requests", "asyncio"],
                "score": 1.0,
            },
            "api": {
                "keywords": ["api", "endpoint", "rest", "graphql", "request", "response"],
                "score": 1.0,
            },
            "rest-api": {
                "keywords": ["rest api", "restful", "http", "json", "endpoint"],
                "score": 0.9,
            },
            "database": {
                "keywords": ["database", "sql", "postgresql", "mysql", "mongodb", "orm"],
                "score": 0.9,
            },
            "javascript": {
                "keywords": ["javascript", "nodejs", "react", "vue", "angular"],
                "score": 0.9,
            },
            "json": {
                "keywords": ["json", "parsing", "serialization"],
                "score": 0.8,
            },
            "authentication": {
                "keywords": ["auth", "jwt", "oauth", "security", "token"],
                "score": 1.0,
            },
            "websocket": {
                "keywords": ["websocket", "real-time", "socket.io"],
                "score": 0.85,
            },
            "testing": {
                "keywords": ["test", "unit test", "integration test", "pytest", "unittest"],
                "score": 0.8,
            },
            "performance": {
                "keywords": ["performance", "optimization", "cache", "scalability"],
                "score": 0.85,
            },
        }

    def get_keywords_for_tags(self, tags: List[str]) -> Set[str]:
        """
        Get all keywords from a list of SO tags.

        Args:
            tags: List of Stack Overflow tags

        Returns:
            Set of corresponding keywords
        """
        keywords: Set[str] = set()

        for tag in tags:
            tag_lower = tag.lower().replace(" ", "-")

            # Direct match
            if tag_lower in self.tag_mapping:
                keywords.update(self.tag_mapping[tag_lower]["keywords"])

            # Partial / substring matches
            for mapped_tag, data in self.tag_mapping.items():
                if tag_lower in mapped_tag or mapped_tag in tag_lower:
                    keywords.update(data["keywords"])

        return keywords

    def find_related_pages(
        self,
        so_tags: List[str],
        confluence_docs: List[Document],
        threshold: float = 0.5,
    ) -> List[Tuple[Document, float]]:
        """
        Find Confluence pages related to Stack Overflow tags.

        Args:
            so_tags: Stack Overflow tags from an article
            confluence_docs: List of Confluence Document objects
            threshold: Minimum relevance score (0-1)

        Returns:
            List of (Document, relevance_score) tuples, sorted descending by score
        """
        keywords = self.get_keywords_for_tags(so_tags)

        if not keywords:
            logger.debug(f"No keywords found for tags: {so_tags}")
            return []

        return self._score_documents(keywords, confluence_docs, threshold)

    def find_related_pages_by_keywords(
        self,
        keywords: Set[str],
        confluence_docs: List[Document],
        threshold: float = 0.3,
    ) -> List[Tuple[Document, float]]:
        """
        Find Confluence pages matching specific keywords.

        Args:
            keywords: Set of keywords to search for
            confluence_docs: List of Confluence documents
            threshold: Minimum relevance score

        Returns:
            List of (Document, relevance_score) tuples
        """
        if not keywords:
            return []

        return self._score_documents(keywords, confluence_docs, threshold)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _score_documents(
        self,
        keywords: Set[str],
        confluence_docs: List[Document],
        threshold: float,
    ) -> List[Tuple[Document, float]]:
        """
        Score Confluence docs against a set of keywords and filter by threshold.

        Title matches are weighted 2x compared to body matches.
        """
        related: List[Tuple[Document, float]] = []
        max_possible = len(keywords) * 3  # title-weight 2 + body-weight 1

        for doc in confluence_docs:
            title = doc.metadata.get("title", "").lower()
            content = doc.page_content.lower()

            matches = sum(
                title.count(kw.lower()) * 2 + content.count(kw.lower())
                for kw in keywords
            )

            if matches > 0:
                score = min(matches / max_possible, 1.0)
                if score >= threshold:
                    related.append((doc, score))

        related.sort(key=lambda x: x[1], reverse=True)
        return related


def create_tag_linker() -> TagLinker:
    """Convenience function to create a TagLinker instance."""
    return TagLinker()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    linker = create_tag_linker()
    so_tags = ["python", "rest-api", "json"]
    keywords = linker.get_keywords_for_tags(so_tags)
    print(f"\nTags: {so_tags}")
    print(f"Keywords: {keywords}")
