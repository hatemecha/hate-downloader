from PySide6.QtCore import QThread, Signal

from app.core.search_manager import SearchManager
from app.utils.logger import logger


class SearchWorker(QThread):
    finished = Signal(list)
    error = Signal(str)

    def __init__(self, query: str, provider: str = "all", searxng_instance: str = "") -> None:
        super().__init__()
        self.query = query
        self.provider = provider
        self.manager = SearchManager(searxng_instance)

    def run(self) -> None:
        try:
            match self.provider:
                case "youtube":
                    results = self.manager.search_youtube(self.query)
                case "archive":
                    results = self.manager.search_archive(self.query)
                case "web":
                    results = self.manager.search_web(self.query)
                case "scan":
                    results = self.manager.scan_page(self.query)
                case _:
                    results = self.manager.search_all(self.query)
            self.finished.emit(results)
        except Exception as e:
            logger.error(f"Search failed: {e}")
            self.error.emit(str(e))
