"""
Confluence Metadata Tracker
Manages tracking of Confluence pages for incremental updates.
Persists metadata (page_id → version, modified time, fetch timestamp).
"""

import json
import logging
import os
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timezone
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class PageMetadata:
    """Metadata for a single Confluence page"""
    page_id: str
    title: str
    version: int
    modified: str  # ISO 8601 format
    url: str
    space_key: str
    fetched_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    chunk_count: int = 0


class ConfluenceMetadataTracker:
    """Tracks Confluence pages for incremental updates"""
    
    def __init__(self, metadata_file: str = "confluence_metadata.json"):
        """
        Initialize metadata tracker
        
        Args:
            metadata_file: Path to metadata JSON file
        """
        self.metadata_file = metadata_file
        self.metadata: Dict[str, Dict] = {}
        self.last_fetch = None
        self.load()
    
    def load(self) -> None:
        """Load existing metadata from file"""
        if os.path.exists(self.metadata_file):
            try:
                with open(self.metadata_file, 'r') as f:
                    data = json.load(f)
                    self.metadata = data.get('pages', {})
                    self.last_fetch = data.get('last_fetch')
                    logger.info(f"Loaded metadata for {len(self.metadata)} pages")
            except Exception as e:
                logger.warning(f"Failed to load metadata: {e}. Starting fresh.")
                self.metadata = {}
                self.last_fetch = None
        else:
            self.metadata = {}
            self.last_fetch = None
            logger.info("No existing metadata file. Starting fresh.")
    
    def save(self) -> None:
        """Save metadata to file"""
        try:
            data = {
                'last_fetch': datetime.now(timezone.utc).isoformat(),
                'pages': self.metadata
            }
            with open(self.metadata_file, 'w') as f:
                json.dump(data, f, indent=2)
            self.last_fetch = data['last_fetch']
            logger.info(f"Saved metadata for {len(self.metadata)} pages")
        except Exception as e:
            logger.error(f"Failed to save metadata: {e}")
    
    def add_or_update_page(self, page_id: str, title: str, version: int,
                          modified: str, url: str, space_key: str,
                          chunk_count: int = 0) -> None:
        """
        Add or update page metadata
        
        Args:
            page_id: Confluence page ID
            title: Page title
            version: Page version number
            modified: ISO 8601 modification timestamp
            url: Page URL
            space_key: Confluence space key
            chunk_count: Number of chunks created from this page
        """
        self.metadata[page_id] = {
            'page_id': page_id,
            'title': title,
            'version': version,
            'modified': modified,
            'url': url,
            'space_key': space_key,
            'fetched_at': datetime.now(timezone.utc).isoformat(),
            'chunk_count': chunk_count
        }
    
    def get_page_metadata(self, page_id: str) -> Optional[Dict]:
        """Get metadata for a specific page"""
        return self.metadata.get(page_id)
    
    def detect_changes(self, current_pages: List[Dict]) -> Tuple[List[Dict], List[Dict], List[str]]:
        """
        Detect new, modified, and deleted pages
        
        Args:
            current_pages: List of current pages from Confluence API
                          Each should have: {id, title, version, modified, url, space_key}
        
        Returns:
            Tuple of (new_pages, modified_pages, deleted_page_ids)
        """
        new_pages = []
        modified_pages = []
        
        # Build set of current page IDs
        current_ids = {page['id'] for page in current_pages}
        
        # Check for new and modified pages
        for page in current_pages:
            page_id = page['id']
            current_version = page.get('version', 1)
            current_modified = page.get('modified', '')
            
            if page_id not in self.metadata:
                # New page
                new_pages.append(page)
                logger.debug(f"Detected new page: {page['title']} (ID: {page_id})")
            else:
                # Check if modified
                stored_metadata = self.metadata[page_id]
                stored_version = stored_metadata.get('version', 0)
                
                if current_version > stored_version:
                    modified_pages.append(page)
                    logger.debug(f"Detected modified page: {page['title']} (ID: {page_id}, v{stored_version} → v{current_version})")
        
        # Check for deleted pages (in metadata but not in current API results)
        stored_ids = set(self.metadata.keys())
        deleted_ids = list(stored_ids - current_ids)
        
        if deleted_ids:
            for page_id in deleted_ids:
                logger.debug(f"Detected deleted page: {self.metadata[page_id]['title']} (ID: {page_id})")
        
        return new_pages, modified_pages, deleted_ids
    
    def remove_page(self, page_id: str) -> None:
        """Remove page metadata (when page is deleted from Confluence)"""
        if page_id in self.metadata:
            title = self.metadata[page_id]['title']
            del self.metadata[page_id]
            logger.info(f"Removed metadata for deleted page: {title}")
    
    def get_statistics(self) -> Dict:
        """Get metadata statistics"""
        return {
            'total_pages': len(self.metadata),
            'last_fetch': self.last_fetch,
            'pages': self.metadata
        }
    
    def clear(self) -> None:
        """Clear all metadata"""
        self.metadata = {}
        self.last_fetch = None
        logger.info("Cleared all metadata")
    
    def cleanup(self) -> None:
        """Remove metadata file"""
        if os.path.exists(self.metadata_file):
            try:
                os.remove(self.metadata_file)
                self.metadata = {}
                self.last_fetch = None
                logger.info(f"Removed metadata file: {self.metadata_file}")
            except Exception as e:
                logger.error(f"Failed to remove metadata file: {e}")


def create_metadata_tracker(metadata_file: str = "confluence_metadata.json") -> ConfluenceMetadataTracker:
    """Convenience function to create metadata tracker"""
    return ConfluenceMetadataTracker(metadata_file)
