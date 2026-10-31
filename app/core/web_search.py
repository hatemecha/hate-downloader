import httpx

from app import __version__
from app.models.search_result import SearchResult
from app.utils.logger import logger

DEFAULT_SEARXNG = "https://search.sapti.me"


class WebSearchProvider:
    def __init__(self, instance_url: str = "") -> None:
        self.instance_url = instance_url or DEFAULT_SEARXNG

    def set_instance(self, url: str) -> None:
        self.instance_url = url

    def search(self, query: str, limit: int = 20) -> list[SearchResult]:
        if not self.instance_url:
            return []

        try:
            params = {
                "q": query,
                "format": "json",
                "categories": "general",
                "language": "en",
                "pageno": 1,
            }

            with httpx.Client(timeout=15.0, follow_redirects=True) as client:
                resp = client.get(
                    f"{self.instance_url}/search",
                    params=params,
                    headers={"User-Agent": f"HateDownloader/{__version__}"},
                )

                if resp.status_code != 200:
                    logger.warning(f"SearXNG returned {resp.status_code}")
                    return []

                data = resp.json()
                results = []
                for r in data.get("results", [])[:limit]:
                    url = r.get("url", "")
                    if not url:
                        continue
                    results.append(
                        SearchResult(
                            title=r.get("title", "Unknown"),
                            url=url,
                            source="Web",
                            description=r.get("content", ""),
                        )
                    )
                return results

        except httpx.TimeoutException:
            logger.warning("SearXNG search timed out")
            return []
        except httpx.ConnectError:
            logger.warning(f"Could not connect to SearXNG instance {self.instance_url}")
            return []
        except Exception as e:
            logger.error(f"Web search failed: {e}")
            return []
