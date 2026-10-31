import sys

from PySide6.QtWidgets import (
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from app.core.dependency_manager import DependencyManager
from app.models.dependency_status import DependencyInfo, SystemStatus
from app.workers.dependency_worker import DependencyWorker, ToolDownloadWorker


class DependencyWindow(QDialog):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.manager = DependencyManager()
        self._status: SystemStatus | None = None
        self._download_worker: ToolDownloadWorker | None = None
        self.setWindowTitle("Setup")
        self.setMinimumSize(700, 560)
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        title = QLabel("Setup")
        title.setObjectName("pageTitle")
        layout.addWidget(title)

        self.summary = QLabel(
            "FFmpeg merges audio and video. Deno runs YouTube's JavaScript. "
            "Both install into this app's data folder and can be removed at any time."
        )
        self.summary.setObjectName("muted")
        self.summary.setWordWrap(True)
        layout.addWidget(self.summary)

        scroll = QScrollArea()
        scroll.setObjectName("plainScroll")
        scroll.setWidgetResizable(True)
        self.content = QWidget()
        self.content_layout = QVBoxLayout(self.content)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(8)
        scroll.setWidget(self.content)
        layout.addWidget(scroll, 1)

        actions = QHBoxLayout()
        actions.setSpacing(8)

        self.check_btn = QPushButton("Check again")
        self.check_btn.setObjectName("ghostButton")
        self.check_btn.clicked.connect(self._check)
        actions.addWidget(self.check_btn)

        self.download_ffmpeg_btn = QPushButton("Install FFmpeg")
        self.download_ffmpeg_btn.setObjectName("strongButton")
        self.download_ffmpeg_btn.clicked.connect(self._download_ffmpeg)
        self.download_ffmpeg_btn.setVisible(False)
        actions.addWidget(self.download_ffmpeg_btn)

        self.download_deno_btn = QPushButton("Install Deno")
        self.download_deno_btn.setObjectName("strongButton")
        self.download_deno_btn.clicked.connect(self._download_deno)
        self.download_deno_btn.setVisible(False)
        actions.addWidget(self.download_deno_btn)

        self.download_aria2_btn = QPushButton("Install aria2c")
        self.download_aria2_btn.setObjectName("ghostButton")
        self.download_aria2_btn.clicked.connect(self._download_aria2)
        self.download_aria2_btn.setVisible(False)
        actions.addWidget(self.download_aria2_btn)

        self.update_ytdlp_btn = QPushButton("Update yt-dlp")
        self.update_ytdlp_btn.setObjectName("ghostButton")
        self.update_ytdlp_btn.clicked.connect(self._update_ytdlp)
        self.update_ytdlp_btn.setVisible(not getattr(sys, "frozen", False))
        actions.addWidget(self.update_ytdlp_btn)

        actions.addStretch()

        close_btn = QPushButton("Close")
        close_btn.setObjectName("ghostButton")
        close_btn.clicked.connect(self.accept)
        actions.addWidget(close_btn)
        layout.addLayout(actions)

        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(False)
        self.progress_bar.hide()
        layout.addWidget(self.progress_bar)

    def showEvent(self, event) -> None:
        super().showEvent(event)
        self._check()

    def _check(self) -> None:
        if getattr(self, "_worker", None) and self._worker.isRunning():
            return
        self.check_btn.setEnabled(False)
        self.check_btn.setText("Checking")

        self._worker = DependencyWorker()
        self._worker.finished.connect(self._on_check_done)
        self._worker.error.connect(self._on_check_error)
        self._worker.start()

    def _on_check_done(self, status: SystemStatus) -> None:
        self._status = status
        self.check_btn.setEnabled(True)
        self.check_btn.setText("Check again")

        self._clear_content()
        for dep in status.dependencies:
            self._add_dep_card(dep)

        self._add_separator()

        general = QLabel(
            f"Version {status.app_version} · Python {status.python_version.split()[0]} · "
            f"{status.platform}\n"
            f"Download folder: {status.download_folder} "
            f"({'writable' if status.download_folder_writable else 'not writable'})"
        )
        general.setObjectName("faint")
        general.setWordWrap(True)
        self.content_layout.addWidget(general)

        can_convert = status.can_convert
        deno_missing = any(d.name == "Deno" and not d.installed for d in status.dependencies)
        self.download_ffmpeg_btn.setVisible(not can_convert)
        self.download_deno_btn.setVisible(deno_missing)
        self.download_aria2_btn.setVisible(False)

        missing = [d.name for d in status.dependencies if not d.installed and not d.optional]
        if missing:
            self.summary.setText(
                "Not ready yet: " + ", ".join(missing) + ". Install what you need below."
            )
        else:
            self.summary.setText(
                "Everything needed is installed. FFmpeg merges audio and video; "
                "Deno runs YouTube's JavaScript."
            )

    def _on_check_error(self, msg: str) -> None:
        self.check_btn.setEnabled(True)
        self.check_btn.setText("Check again")
        self._clear_content()
        error_label = QLabel(f"Could not check dependencies: {msg}")
        error_label.setObjectName("errorLabel")
        error_label.setWordWrap(True)
        self.content_layout.addWidget(error_label)

    def _add_dep_card(self, dep: DependencyInfo) -> None:
        card = QFrame()
        card.setObjectName("card")
        card_layout = QHBoxLayout(card)
        card_layout.setContentsMargins(14, 12, 14, 12)
        card_layout.setSpacing(12)

        info_layout = QVBoxLayout()
        info_layout.setSpacing(3)

        name_label = QLabel(dep.name)
        name_label.setObjectName("sectionTitle")
        info_layout.addWidget(name_label)

        if dep.version:
            version_label = QLabel(dep.version)
            version_label.setObjectName("faint")
            version_label.setWordWrap(True)
            info_layout.addWidget(version_label)

        message_label = QLabel(dep.status_message)
        message_label.setObjectName("muted")
        message_label.setWordWrap(True)
        info_layout.addWidget(message_label)

        if dep.path:
            path_label = QLabel(dep.path)
            path_label.setObjectName("pathLabel")
            path_label.setWordWrap(True)
            path_label.setToolTip(dep.path)
            info_layout.addWidget(path_label)

        card_layout.addLayout(info_layout, 1)

        status_label = QLabel("Installed" if dep.installed else "Missing")
        status_label.setObjectName("successLabel" if dep.installed else "errorLabel")
        card_layout.addWidget(status_label, 0)

        self.content_layout.addWidget(card)

    def _add_separator(self) -> None:
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        self.content_layout.addWidget(sep)

    def _clear_content(self) -> None:
        while self.content_layout.count():
            item = self.content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def _download_ffmpeg(self) -> None:
        self._start_tool_download("ffmpeg")

    def _download_deno(self) -> None:
        self._start_tool_download("deno")

    def _download_aria2(self) -> None:
        self._start_tool_download("aria2c")

    def _start_tool_download(self, tool: str) -> None:
        if self._download_worker and self._download_worker.isRunning():
            return

        self.progress_bar.show()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self._set_download_buttons_enabled(False)

        worker = ToolDownloadWorker(tool)
        worker.progress.connect(self._on_download_progress)
        worker.finished.connect(self._on_download_finished)
        worker.error.connect(self._on_download_error)
        self._download_worker = worker
        worker.start()

    def _on_download_progress(self, value: float) -> None:
        self.progress_bar.setValue(int(value))

    def _on_download_finished(self, ok: bool, message: str) -> None:
        self._set_download_buttons_enabled(True)
        self.progress_bar.hide()

        if not ok:
            self.summary.setText(f"Install failed. {message}")
            return

        if self._download_worker and self._download_worker.tool == "yt-dlp":
            self.summary.setText("yt-dlp updated. Restart the app to use the new version.")
            return

        self.summary.setText("Installed. Checking the tools again...")
        self._check()

    def _on_download_error(self, message: str) -> None:
        self._on_download_finished(False, message)

    def _set_download_buttons_enabled(self, enabled: bool) -> None:
        self.check_btn.setEnabled(enabled)
        self.download_ffmpeg_btn.setEnabled(enabled)
        self.download_deno_btn.setEnabled(enabled)
        self.download_aria2_btn.setEnabled(enabled)
        self.update_ytdlp_btn.setEnabled(enabled)

    def _update_ytdlp(self) -> None:
        self._start_tool_download("yt-dlp")
        self.progress_bar.setRange(0, 0)

    def done(self, result: int) -> None:
        if any(
            worker and worker.isRunning()
            for worker in (getattr(self, "_worker", None), self._download_worker)
        ):
            return
        super().done(result)
