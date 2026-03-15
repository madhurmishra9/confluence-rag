"""
Stack Overflow Suggestions Engine
Provides Confluence document suggestions based on SO articles.
"""

import logging
from typing import List, Dict, Tuple, Optional
from langchain_core.documents import Document
from .tag_linker import TagLinker

logger = logging.getLogger(__name__)


class SOSuggestionEngine:
    """Generates Confluence suggestions for Stack Overflow articles"""
    
    def __init__(self, confluence_docs: List[Document] = None):
        """
        Initialize suggestion engine.
        
        Args:
            confluence_docs: List of Confluence documents to match against
        """
        self.tag_linker = TagLinker()
        self.confluence_docs = confluence_docs or []
    
    def set_confluence_docs(self, confluence_docs: List[Document]) -> None:
        """
        Set or update the Confluence documents for matching.
        
        Args:
            confluence_docs: List of Confluence Document objects
        """
        self.confluence_docs = confluence_docs
        logger.info(f"Set {len(confluence_docs)} Confluence documents for suggestions")
    
    def suggest_confluence_articles(self, so_document: Document,
                                  max_suggestions: int = 5,
                                  threshold: float = 0.3) -> List[Dict]:
        """
        Suggest related Confluence articles for a Stack Overflow document.
        
        Args:
            so_document: Stack Overflow Document object
            max_suggestions: Maximum number of suggestions to return
            threshold: Minimum relevance score (0-1)
        
        Returns:
            List of suggestion dicts with {title, url, relevance, reasoning}
        """
        if not self.confluence_docs:
            logger.warning("No Confluence documents loaded for suggestions")
            return []
        
        suggestions = []
        
        # Get SO tags from metadata
        so_tags = so_document.metadata.get("tags", [])
        so_title = so_document.metadata.get("title", "")
        
        if not so_tags:
            logger.debug(f"No tags found in SO document: {so_title}")
            return []
        
        logger.debug(f"Finding suggestions for SO tags: {so_tags}")
        
        # Find related Confluence pages by tags
        related_docs = self.tag_linker.find_related_pages(
            so_tags,
            self.confluence_docs,
            threshold=threshold
        )
        
        # Convert to suggestions
        for doc, score in related_docs[:max_suggestions]:
            suggestion = {
                "title": doc.metadata.get("title", "Unknown"),
                "url": doc.metadata.get("url", ""),
                "page_id": doc.metadata.get("page_id", ""),
                "relevance": round(score, 2),
                "reasoning": f"Related to topics: {', '.join(so_tags)}"
            }
            suggestions.append(suggestion)
            logger.debug(f"Suggested: {suggestion['title']} (relevance: {suggestion['relevance']})")
        
        return suggestions
    
    def suggest_by_content_search(self, query: str,
                                 max_suggestions: int = 5) -> List[Dict]:
        """
        Suggest Confluence articles matching free-text query.
        
        Args:
            query: Search query string
            max_suggestions: Maximum suggestions
        
        Returns:
            List of suggestions
        """
        if not self.confluence_docs:
            return []
        
        suggestions = []
        query_lower = query.lower()
        query_words = set(query_lower.split())
        
        # Score documents by query match
        scored_docs: List[Tuple[Document, float]] = []
        
        for doc in self.confluence_docs:
            title = doc.metadata.get("title", "").lower()
            content = doc.page_content.lower()
            
            # Count word matches
            matches = 0
            for word in query_words:
                if len(word) > 2:  # Skip short words
                    matches += title.count(word) * 3
                    matches += content.count(word)
            
            if matches > 0:
                score = min(matches / (len(query_words) * 4), 1.0)
                scored_docs.append((doc, score))
        
        # Sort by score
        scored_docs.sort(key=lambda x: x[1], reverse=True)
        
        # Build suggestions
        for doc, score in scored_docs[:max_suggestions]:
            suggestion = {
                "title": doc.metadata.get("title", "Unknown"),
                "url": doc.metadata.get("url", ""),
                "page_id": doc.metadata.get("page_id", ""),
                "relevance": round(score, 2),
                "reasoning": "Matches your search terms"
            }
            suggestions.append(suggestion)
        
        return suggestions
    
    def format_suggestions(self, suggestions: List[Dict]) -> str:
        """
        Format suggestions for display.
        
        Args:
            suggestions: List of suggestion dicts
        
        Returns:
            Formatted string for display
        """
        if not suggestions:
            return "No related Confluence pages found."
        
        result = "\n📚 Suggested Confluence Articles:\n"
        result += "=" * 50 + "\n"
        
        for i, sug in enumerate(suggestions, 1):
            result += f"\n{i}. {sug['title']}\n"
            result += f"   Relevance: {sug['relevance']}\n"
            result += f"   Reason: {sug['reasoning']}\n"
            if sug['url']:
                result += f"   URL: {sug['url']}\n"
        
        return result


def create_suggestion_engine(confluence_docs: List[Document] = None) -> SOSuggestionEngine:
    """
    Convenience function to create suggestion engine.
    
    Args:
        confluence_docs: Optional list of Confluence documents
    
    Returns:
        SOSuggestionEngine instance
    """
    return SOSuggestionEngine(confluence_docs)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Example usage
    engine = create_suggestion_engine()
    
    # Create sample SO document
    sample_so_doc = Document(
        page_content="How to build REST APIs with Python?",
        metadata={
            "title": "Building REST APIs with Python",
            "tags": ["python", "rest-api", "api"],
            "url": "https://stackoverflow.com/questions/..."
        }
    )
    
    print("Suggestion Engine Created")
