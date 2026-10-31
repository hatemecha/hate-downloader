from app.core.ytdlp_service import YtDlpService
from app.models.search_result import SearchResult
from app.utils.logger import logger


class YouTubeSearchProvider:
    def __init__(self) -> None:
        self.ytdlp = YtDlpService()

    def search(self, query: str, limit: int = 20) -> list[SearchResult]:
        try:
            entries = self.ytdlp.search(query, limit)
            results = []
            for entry in entries:
                if not entry or not isinstance(entry, dict):
                    continue
                results.append(
                    SearchResult(
                        title=(entry.get("title") or "Unknown"),
                        url=entry.get("webpage_url") or entry.get("url", ""),
                        duration=int(entry.get("duration") or 0),
                        uploader=entry.get("uploader") or entry.get("channel", "") or "",
                        thumbnail=(entry.get("thumbnail") or ""),
                        source="YouTube",
                        extractor=entry.get("extractor", "youtube"),
                        description=entry.get("description", "") or "",
                    )
                )
            return results
        except Exception as e:
            logger.error(f"YouTube search failed: {e}")
            return []
