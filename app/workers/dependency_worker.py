from typing import Callable

from PySide6.QtCore import QThread, Signal

from app.core.dependency_manager import DependencyManager


class DependencyWorker(QThread):
    finished = Signal(object)
    error = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        self.manager = DependencyManager()

    def run(self) -> None:
        try:
            status = self.manager.check_all()
            self.finished.emit(status)
        except Exception as e:
            self.error.emit(str(e))


class ToolDownloadWorker(QThread):
    """Download FFmpeg or aria2c off the UI thread with progress updates."""

    progress = Signal(float)
    finished = Signal(bool, str)
    error = Signal(str)

    def __init__(self, tool: str) -> None:
        super().__init__()
        self.tool = tool
        self.manager = DependencyManager()

    def run(self) -> None:
        try:
            callback: Callable[[float], None] = self.progress.emit
            if self.tool == "ffmpeg":
                ok, message = self.manager.download_ffmpeg(callback)
            elif self.tool == "deno":
                ok, message = self.manager.download_deno(callback)
            elif self.tool == "aria2c":
                ok, message = self.manager.download_aria2(callback)
            elif self.tool == "yt-dlp":
                ok, message = self.manager.update_ytdlp()
            else:
                self.finished.emit(False, f"Unknown tool: {self.tool}")
                return
            self.finished.emit(ok, message)
        except Exception as e:
            self.error.emit(str(e))
