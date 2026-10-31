from pathlib import Path
from typing import Optional
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

from app import __version__
from app.models.search_result import SearchResult
from app.utils.logger import logger

MEDIA_EXTENSIONS = {
    ".mp4",
    ".webm",
    ".mkv",
    ".mov",
    ".avi",
    ".m4v",
    ".mp3",
    ".m4a",
    ".wav",
    ".ogg",
    ".opus",
    ".flac",
    ".aac",
    ".m3u8",
    ".mpd",
}


class DirectMediaScanner:
    def __init__(self) -> None:
        self._client: Optional[httpx.Client] = None

    @property
    def client(self) -> httpx.Client:
        if self._client is None:
            self._client = httpx.Client(
                timeout=15.0,
                follow_redirects=True,
                headers={"User-Agent": f"Mozilla/5.0 HateDownloader/{__version__}"},
            )
        return self._client

    def is_direct_media_url(self, url: str) -> bool:
        path = urlparse(url).path.lower()
        for ext in MEDIA_EXTENSIONS:
            if path.endswith(ext):
                return True
        return False

    def scan(self, url: str) -> list[SearchResult]:
        results: list[SearchResult] = []

        if self.is_direct_media_url(url):
            filename = Path(urlparse(url).path).name
            results.append(
                SearchResult(
                    title=filename,
                    url=url,
                    source="Direct Media",
                )
            )
            return results

        try:
            resp = self.client.get(url)
            resp.raise_for_status()
        except Exception as e:
            logger.error(f"Failed to fetch page: {e}")
            return []

        soup = BeautifulSoup(resp.text, "lxml")
        page_url = str(resp.url)

        video_tags = soup.find_all("video")
        for v in video_tags:
            src = v.get("src", "")
            if src:
                results.append(
                    SearchResult(
                        title=f"Video: {Path(src).name}",
                        url=urljoin(page_url, src),
                        source="Direct Media",
                    )
                )

        audio_tags = soup.find_all("audio")
        for a in audio_tags:
            src = a.get("src", "")
            if src:
                results.append(
                    SearchResult(
                        title=f"Audio: {Path(src).name}",
                        url=urljoin(page_url, src),
                        source="Direct Media",
                    )
                )

        source_tags = soup.find_all("source")
        for s in source_tags:
            src = s.get("src", "")
            if src:
                fmt = s.get("type", "")
                results.append(
                    SearchResult(
                        title=f"Source: {Path(src).name} ({fmt})",
                        url=urljoin(page_url, src),
                        source="Direct Media",
                    )
                )

        for tag in soup.find_all(["a", "video", "audio", "source"]):
            href = tag.get("href") or tag.get("src") or ""
            href_lower = urlparse(href).path.lower()
            for ext in MEDIA_EXTENSIONS:
                if href_lower.endswith(ext):
                    full_url = urljoin(page_url, href)
                    filename = Path(href).name
                    results.append(
                        SearchResult(
                            title=filename,
                            url=full_url,
                            source="Direct Media",
                            format=ext,
                        )
                    )
                    break

        seen = set()
        unique = []
        for r in results:
            if r.url not in seen:
                seen.add(r.url)
                unique.append(r)

        if not unique:
            logger.info(f"No media found on page: {url}")

        return unique
