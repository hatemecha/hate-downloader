from PySide6.QtCore import QThread, Signal

from app.core.error_mapper import classify_error
from app.core.ytdlp_service import YtDlpService
from app.utils.logger import logger


class AnalyzeWorker(QThread):
    finished = Signal(object)
    error = Signal(str, str)

    def __init__(self, url: str, settings: dict | None = None) -> None:
        super().__init__()
        self.url = url
        self.settings = settings or {}
        self.ytdlp = YtDlpService()

    def run(self) -> None:
        try:
            raw = self.ytdlp.extract_info(self.url, self.settings)
            info = self.ytdlp.parse_media_info(raw)
            self.finished.emit(info)
        except Exception as e:
            logger.error(f"Analyze failed: {e}")
            err = classify_error(e)
            self.error.emit(err.message, "\n".join(filter(None, (err.action, err.detail))))
