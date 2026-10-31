from app.core.archive_service import InternetArchiveProvider
from app.core.media_scanner import DirectMediaScanner
from app.core.web_search import WebSearchProvider
from app.core.youtube_search import YouTubeSearchProvider
from app.models.search_result import SearchResult
from app.utils.logger import logger


class SearchManager:
    def __init__(self, searxng_instance: str = "") -> None:
        self.youtube = YouTubeSearchProvider()
        self.archive = InternetArchiveProvider()
        self.web = WebSearchProvider(searxng_instance)
        self.scanner = DirectMediaScanner()

    def set_searxng_instance(self, url: str) -> None:
        self.web.set_instance(url)

    def search_all(self, query: str, limit: int = 20) -> list[SearchResult]:
        results = []
        results.extend(self.youtube.search(query, limit))
        try:
            results.extend(self.archive.search(query, limit))
        except Exception as e:
            logger.warning(f"Archive.org search failed: {e}")
        try:
            results.extend(self.web.search(query, limit))
        except Exception as e:
            logger.warning(f"Web search failed: {e}")
        return results

    def search_youtube(self, query: str, limit: int = 20) -> list[SearchResult]:
        return self.youtube.search(query, limit)

    def search_archive(self, query: str, limit: int = 20) -> list[SearchResult]:
        return self.archive.search(query, limit)

    def search_web(self, query: str, limit: int = 20) -> list[SearchResult]:
        return self.web.search(query, limit)

    def scan_page(self, url: str) -> list[SearchResult]:
        return self.scanner.scan(url)

    def is_direct_media_url(self, url: str) -> bool:
        return self.scanner.is_direct_media_url(url)
