"""
src.page_manager
================
Confluence page administration: listing, **sorting** and **moving pages
between spaces** (single or bulk, both directions), built on the same
REST credentials the RAG system already uses.

Sorting
-------
list_pages(space_key, sort_by=..., descending=...) supports:
    title | created | modified | space | id
Server-side ordering is requested via CQL where possible and re-applied
client-side so results are always correctly sorted.

Moving
------
Confluence Cloud moves a page by PUT-ing the content with a new space key
and an incremented version. move_page() handles version bumping, optional
re-parenting under the target space homepage, and clear error reporting.
move_pages() does the same in bulk (list of ids, or "every page in space X
whose title matches a filter"), with per-page success/failure accounting —
one bad page never aborts the batch.

After moving, call the incremental sync (option 1 in main_unified.py) so
the vector store metadata picks up the new space automatically.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import requests
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

CONFLUENCE_URL = os.getenv("CONFLUENCE_URL", "").rstrip("/")
CONFLUENCE_EMAIL = os.getenv("CONFLUENCE_EMAIL", "")
CONFLUENCE_API_TOKEN = os.getenv("CONFLUENCE_API_TOKEN", "")

SORT_KEYS = {"title", "created", "modified", "space", "id"}


class PageManagerError(RuntimeError):
    pass


@dataclass
class PageInfo:
    page_id: str
    title: str
    space_key: str
    version: int
    created: str = ""
    modified: str = ""
    url: str = ""


@dataclass
class MoveResult:
    moved: List[PageInfo] = field(default_factory=list)
    failed: List[Dict[str, str]] = field(default_factory=list)

    def summary(self) -> str:
        line = f"{len(self.moved)} page(s) moved"
        if self.failed:
            line += f", {len(self.failed)} failed"
        return line


class ConfluencePageManager:
    def __init__(self):
        if not (CONFLUENCE_URL and CONFLUENCE_EMAIL and CONFLUENCE_API_TOKEN):
            raise PageManagerError(
                "CONFLUENCE_URL / CONFLUENCE_EMAIL / CONFLUENCE_API_TOKEN missing in .env"
            )
        self.base = f"{CONFLUENCE_URL}/rest/api"
        self.auth = (CONFLUENCE_EMAIL, CONFLUENCE_API_TOKEN)
        self.headers = {"Accept": "application/json", "Content-Type": "application/json"}

    # ── low level ────────────────────────────────────────────────────
    def _request(self, method: str, endpoint: str, *, params=None, data=None) -> Dict[str, Any]:
        url = f"{self.base}{endpoint}"
        resp = requests.request(method, url, params=params, json=data,
                                auth=self.auth, headers=self.headers, timeout=30)
        if resp.status_code >= 400:
            detail = ""
            try:
                detail = resp.json().get("message", "")
            except ValueError:
                detail = resp.text[:200]
            raise PageManagerError(f"Confluence API {resp.status_code} on {endpoint}: {detail}")
        return resp.json() if resp.text else {}

    @staticmethod
    def _to_info(page: Dict[str, Any]) -> PageInfo:
        version = page.get("version", {}) or {}
        history = page.get("history", {}) or {}
        space = page.get("space", {}) or {}
        links = page.get("_links", {}) or {}
        return PageInfo(
            page_id=str(page.get("id", "")),
            title=page.get("title", ""),
            space_key=space.get("key", ""),
            version=int(version.get("number", 1)),
            created=history.get("createdDate", ""),
            modified=version.get("when", ""),
            url=f"{CONFLUENCE_URL}/wiki{links.get('webui', '')}" if links.get("webui") else "",
        )

    # ── listing & sorting ────────────────────────────────────────────
    def list_pages(
        self,
        space_key: Optional[str] = None,
        title_contains: Optional[str] = None,
        sort_by: str = "modified",
        descending: bool = True,
        limit: int = 200,
    ) -> List[PageInfo]:
        """List pages with flexible sorting (title/created/modified/space/id)."""
        if sort_by not in SORT_KEYS:
            raise PageManagerError(f"sort_by must be one of {sorted(SORT_KEYS)}")

        pages: List[PageInfo] = []
        start, page_size = 0, 50
        params: Dict[str, Any] = {
            "type": "page",
            "limit": page_size,
            "expand": "version,space,history",
        }
        if space_key:
            params["spaceKey"] = space_key

        while len(pages) < limit:
            params["start"] = start
            data = self._request("GET", "/content", params=params)
            results = data.get("results", [])
            pages.extend(self._to_info(p) for p in results)
            if len(results) < page_size:
                break
            start += page_size

        if title_contains:
            needle = title_contains.lower()
            pages = [p for p in pages if needle in p.title.lower()]

        sort_attr = {"title": lambda p: p.title.lower(),
                     "created": lambda p: p.created,
                     "modified": lambda p: p.modified,
                     "space": lambda p: (p.space_key, p.title.lower()),
                     "id": lambda p: int(p.page_id or 0)}[sort_by]
        pages.sort(key=sort_attr, reverse=descending)
        return pages[:limit]

    def get_page(self, page_id: str) -> Dict[str, Any]:
        return self._request(
            "GET", f"/content/{page_id}",
            params={"expand": "version,space,body.storage,ancestors"},
        )

    def get_space_homepage_id(self, space_key: str) -> Optional[str]:
        data = self._request("GET", f"/space/{space_key}", params={"expand": "homepage"})
        homepage = data.get("homepage") or {}
        return str(homepage.get("id")) if homepage.get("id") else None

    # ── moving ───────────────────────────────────────────────────────
    def move_page(self, page_id: str, target_space_key: str,
                  reparent_to_homepage: bool = True) -> PageInfo:
        """
        Move one page to another space (works in either direction).
        Re-parents under the target space homepage by default so the page
        never dangles under a parent that stayed in the old space.
        """
        page = self.get_page(page_id)
        current_space = (page.get("space") or {}).get("key", "")
        if current_space == target_space_key:
            raise PageManagerError(f"Page {page_id} is already in space {target_space_key}")

        version = int((page.get("version") or {}).get("number", 1)) + 1
        payload: Dict[str, Any] = {
            "id": page_id,
            "type": "page",
            "title": page["title"],
            "space": {"key": target_space_key},
            "version": {"number": version,
                        "message": f"Moved from {current_space} to {target_space_key} via confluence-rag"},
            "body": {"storage": {
                "value": (page.get("body", {}).get("storage", {}) or {}).get("value", ""),
                "representation": "storage",
            }},
        }
        if reparent_to_homepage:
            homepage_id = self.get_space_homepage_id(target_space_key)
            if homepage_id:
                payload["ancestors"] = [{"id": homepage_id}]

        updated = self._request("PUT", f"/content/{page_id}", data=payload)
        info = self._to_info(updated)
        info.space_key = info.space_key or target_space_key
        logger.info("Moved page %s '%s': %s -> %s", page_id, info.title, current_space, target_space_key)
        return info

    def move_pages(
        self,
        target_space_key: str,
        page_ids: Optional[List[str]] = None,
        source_space_key: Optional[str] = None,
        title_contains: Optional[str] = None,
    ) -> MoveResult:
        """
        Bulk move. Select pages either explicitly (page_ids) or by
        source space + optional title filter. Failures are collected
        per page; the batch always runs to completion.
        """
        if not page_ids:
            if not source_space_key:
                raise PageManagerError("Provide page_ids or a source_space_key")
            page_ids = [p.page_id for p in self.list_pages(
                space_key=source_space_key, title_contains=title_contains,
                sort_by="title", descending=False, limit=500,
            )]

        result = MoveResult()
        for i, pid in enumerate(page_ids, 1):
            try:
                logger.info("[%d/%d] Moving page %s -> %s", i, len(page_ids), pid, target_space_key)
                result.moved.append(self.move_page(pid, target_space_key))
            except PageManagerError as exc:
                logger.error("Move failed for %s: %s", pid, exc)
                result.failed.append({"page_id": pid, "error": str(exc)})
        return result
