from typing import Any

import httpx

from app import __version__
from app.models.search_result import SearchResult
from app.utils.logger import logger

SEARCH_URL = "https://archive.org/advancedsearch.php"


def _first_str(value: Any) -> str:
    if isinstance(value, list):
        value = value[0] if value else ""
    if value is None:
        return ""
    return str(value).strip()


class InternetArchiveProvider:
    def search(self, query: str, limit: int = 20) -> list[SearchResult]:
        query = query.strip()
        if not query:
            return []

        try:
            params: list[tuple[str, str]] = [
                ("q", query),
                ("fl[]", "identifier"),
                ("fl[]", "title"),
                ("fl[]", "creator"),
                ("fl[]", "description"),
                ("rows", str(max(1, min(limit, 50)))),
                ("page", "1"),
                ("output", "json"),
            ]
            with httpx.Client(timeout=15.0, follow_redirects=True) as client:
                resp = client.get(
                    SEARCH_URL,
                    params=params,
                    headers={"User-Agent": f"HateDownloader/{__version__}"},
                )
                resp.raise_for_status()
                data = resp.json()
        except Exception as e:
            logger.error(f"Internet Archive search failed: {e}")
            return []

        docs = ((data.get("response") or {}).get("docs")) or []
        results: list[SearchResult] = []
        for item in docs[:limit]:
            identifier = _first_str(item.get("identifier"))
            if not identifier:
                continue
            results.append(
                SearchResult(
                    title=_first_str(item.get("title")) or identifier,
                    url=f"https://archive.org/details/{identifier}",
                    uploader=_first_str(item.get("creator")),
                    thumbnail=f"https://archive.org/services/img/{identifier}",
                    source="Internet Archive",
                    identifier=identifier,
                    description=_first_str(item.get("description")),
                )
            )
        return results
