from datetime import datetime

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QSplitter,
    QStatusBar,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from app import __version__
from app.core.dependency_manager import DependencyManager
from app.core.download_manager import DownloadManager
from app.db.downloads_repository import DownloadsRepository
from app.db.migrations import run_migrations
from app.db.settings_repository import SettingsRepository
from app.models.app_settings import AppSettings
from app.models.download_job import DownloadJob, JobStatus
from app.ui.dependency_window import DependencyWindow
from app.ui.dialogs import ConfirmDialog, ErrorDialog, WelcomeDialog
from app.ui.format_selector import FormatSelector
from app.ui.icons import application_icon
from app.ui.queue_panel import QueuePanel
from app.ui.result_card import ResultCard
from app.ui.search_panel import SearchPanel
from app.ui.settings_window import SettingsWindow
from app.ui.theme import get_stylesheet
from app.ui.url_panel import UrlPanel
from app.utils.paths import ensure_dirs, get_default_download_dir
from app.utils.system import open_folder_in_explorer
from app.workers.analyze_worker import AnalyzeWorker
from app.workers.dependency_worker import DependencyWorker
from app.workers.search_worker import SearchWorker


class MainWindow(QMainWindow):
    deps_checked = Signal(object)

    def __init__(self) -> None:
        super().__init__()
        ensure_dirs()
        run_migrations()

        self.settings_repo = SettingsRepository()
        self.settings = self.settings_repo.load_app_settings()

        self.download_manager = DownloadManager(self.settings)
        self.dependency_manager = DependencyManager()
        self.downloads_repo = DownloadsRepository()

        self._setup_ui()
        self._apply_theme()
        self._connect_signals()
        self._restore_geometry()

    def _setup_ui(self) -> None:
        self.setWindowTitle("Hate Downloader")
        self.setWindowIcon(application_icon())
        self.setMinimumSize(900, 600)

        central = QWidget()
        central.setObjectName("appRoot")
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.url_panel = UrlPanel()
        main_layout.addWidget(self.url_panel)

        banner_row = QWidget()
        banner_layout = QHBoxLayout(banner_row)
        banner_layout.setContentsMargins(16, 12, 16, 0)
        banner_layout.setSpacing(0)
        self.setup_banner = QFrame()
        self.setup_banner.setObjectName("setupBanner")
        setup_layout = QHBoxLayout(self.setup_banner)
        setup_layout.setContentsMargins(14, 10, 10, 10)
        setup_layout.setSpacing(12)
        self.setup_label = QLabel("")
        self.setup_label.setObjectName("muted")
        self.setup_label.setWordWrap(True)
        setup_layout.addWidget(self.setup_label, 1)
        setup_btn = QPushButton("Set up")
        setup_btn.setObjectName("ghostButton")
        setup_btn.clicked.connect(self._open_dependencies)
        setup_layout.addWidget(setup_btn)
        self.setup_banner.hide()
        banner_layout.addWidget(self.setup_banner)
        main_layout.addWidget(banner_row)

        splitter = QSplitter(Qt.Horizontal)
        splitter.setChildrenCollapsible(False)

        left_panel = QWidget()
        left_panel.setMinimumWidth(440)
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(16, 12, 8, 16)
        left_layout.setSpacing(12)

        self.tabs = QTabWidget()
        self.tabs.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Ignored)
        self.search_panel = SearchPanel()
        self.result_card = ResultCard()
        self.result_card.set_download_folder(
            self.settings.default_folder or str(get_default_download_dir())
        )
        self.format_selector = FormatSelector()

        tabs_widget = QWidget()
        tabs_widget.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Ignored)
        tabs_layout = QVBoxLayout(tabs_widget)
        tabs_layout.setContentsMargins(0, 0, 0, 0)
        tabs_layout.addWidget(self.tabs)

        self.tabs.addTab(self.search_panel, "Search")
        self.tabs.addTab(self._create_history_tab(), "History")

        left_layout.addWidget(self.result_card)
        left_layout.addWidget(tabs_widget, 1)

        self.queue_panel = QueuePanel()
        self.queue_panel.setMinimumWidth(280)

        queue_container = QWidget()
        queue_layout = QVBoxLayout(queue_container)
        queue_layout.setContentsMargins(8, 12, 16, 16)
        queue_layout.addWidget(self.queue_panel)

        splitter.addWidget(left_panel)
        splitter.addWidget(queue_container)
        splitter.setStretchFactor(0, 2)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([650, 350])

        main_layout.addWidget(splitter, 1)

        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_label = QLabel("Ready")
        self.status_label.setObjectName("faint")
        self.status_bar.addWidget(self.status_label)

        self.status_dep = QLabel()
        self.status_dep.setObjectName("faint")
        self.status_bar.addPermanentWidget(self.status_dep)

        self._setup_menu()
        self._check_deps_async()

    def _setup_menu(self) -> None:
        menubar = self.menuBar()

        file_menu = menubar.addMenu("File")
        settings_action = QAction("Settings", self)
        settings_action.triggered.connect(self._open_settings)
        file_menu.addAction(settings_action)
        file_menu.addSeparator()
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        tools_menu = menubar.addMenu("Tools")
        deps_action = QAction("Dependencies", self)
        deps_action.triggered.connect(self._open_dependencies)
        tools_menu.addAction(deps_action)
        tools_menu.addSeparator()
        clear_action = QAction("Clear history", self)
        clear_action.triggered.connect(self._clear_history)
        tools_menu.addAction(clear_action)

        view_menu = menubar.addMenu("View")
        simple_action = QAction("Simple mode", self)
        simple_action.triggered.connect(lambda: self.url_panel.set_advanced(False))
        view_menu.addAction(simple_action)
        advanced_action = QAction("Advanced mode", self)
        advanced_action.triggered.connect(lambda: self.url_panel.set_advanced(True))
        view_menu.addAction(advanced_action)

        help_menu = menubar.addMenu("Help")
        about_action = QAction("About", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)

    def _create_history_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(4, 12, 4, 4)
        layout.setSpacing(8)

        header = QHBoxLayout()
        header.setSpacing(8)

        title = QLabel("History")
        title.setObjectName("sectionTitle")
        header.addWidget(title)

        self.history_count = QLabel("0 entries")
        self.history_count.setObjectName("faint")
        header.addWidget(self.history_count)
        header.addStretch()

        refresh_btn = QPushButton("Refresh")
        refresh_btn.setObjectName("ghostButton")
        refresh_btn.clicked.connect(self._load_history)
        header.addWidget(refresh_btn)

        self.delete_history_btn = QPushButton("Delete selected")
        self.delete_history_btn.setObjectName("ghostButton")
        self.delete_history_btn.setEnabled(False)
        self.delete_history_btn.setToolTip("Delete the selected history entries")
        self.delete_history_btn.clicked.connect(self._delete_selected_history)
        header.addWidget(self.delete_history_btn)

        self.clear_history_btn = QPushButton("Clear all")
        self.clear_history_btn.setObjectName("ghostButton")
        self.clear_history_btn.setEnabled(False)
        self.clear_history_btn.setToolTip("Clear the entire download history")
        self.clear_history_btn.clicked.connect(self._clear_history)
        header.addWidget(self.clear_history_btn)

        self.history_list = QListWidget()
        self.history_list.setObjectName("plainList")
        self.history_list.setWordWrap(True)
        self.history_list.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.history_list.setSelectionMode(QListWidget.ExtendedSelection)
        self.history_list.itemDoubleClicked.connect(self._on_history_click)
        self.history_list.itemSelectionChanged.connect(self._update_history_actions)

        layout.addLayout(header)
        layout.addWidget(self.history_list, 1)

        self._load_history()
        return widget

    def _connect_signals(self) -> None:
        self.url_panel.analyze_clicked.connect(self._on_analyze)
        self.url_panel.search_clicked.connect(self._on_search)
        self.url_panel.mode_changed.connect(self._on_mode_changed)
        self.url_panel.input.textChanged.connect(lambda _: self.result_card.clear())

        self.search_panel.result_selected.connect(self._on_result_selected)

        self.result_card.download_clicked.connect(self._on_download_result)
        self.result_card.change_folder_requested.connect(self._on_change_folder)

        self.queue_panel.cancel_requested.connect(self._on_cancel)
        self.queue_panel.retry_requested.connect(self._on_retry)
        self.queue_panel.open_folder_requested.connect(self._on_open_folder)

        self.download_manager.progress_updated.connect(self._on_dl_progress)
        self.download_manager.status_changed.connect(self._on_dl_status)
        self.download_manager.queue_changed.connect(self._on_queue_update)

        self.deps_checked.connect(self._on_deps_checked)

    def _apply_theme(self) -> None:
        stylesheet = get_stylesheet(self.settings.theme)
        self.setStyleSheet(stylesheet)

    def _restore_geometry(self) -> None:
        w = self.settings.window_width or 1100
        h = self.settings.window_height or 720
        self.resize(w, h)

    def _show_welcome_if_first_run(self) -> None:
        if self.settings.first_run:
            dlg = WelcomeDialog(self)
            if dlg.exec() == WelcomeDialog.Accepted:
                if dlg.dont_show.isChecked():
                    self.settings.first_run = False
                    self.settings_repo.save_app_settings(self.settings)

    def _check_deps_async(self) -> None:
        if getattr(self, "_dep_worker", None) and self._dep_worker.isRunning():
            return
        self._dep_worker = DependencyWorker()
        self._dep_worker.finished.connect(self.deps_checked.emit)
        self._dep_worker.start()

    def _on_deps_checked(self, status) -> None:
        missing = [d.name for d in status.dependencies if not d.installed and not d.optional]
        optional_missing = [d.name for d in status.dependencies if not d.installed and d.optional]
        if missing:
            self.status_dep.setText(f"Setup needed: {', '.join(missing)}")
            self.status_dep.setObjectName("errorLabel")
            self.setup_label.setText(
                f"Setup needed: {', '.join(missing)}. "
                "Downloads of separate audio and video use FFmpeg; YouTube uses Deno."
            )
            self.setup_banner.show()
        elif optional_missing:
            self.status_dep.setText(
                f"Ready · optional: {', '.join(optional_missing)}"
            )
            self.status_dep.setObjectName("faint")
            self.setup_banner.hide()
        else:
            self.status_dep.setText("All tools installed")
            self.status_dep.setObjectName("faint")
            self.setup_banner.hide()
        self.status_dep.style().unpolish(self.status_dep)
        self.status_dep.style().polish(self.status_dep)

    def _on_analyze(self, url: str) -> None:
        if getattr(self, "_analyze_worker", None) and self._analyze_worker.isRunning():
            return
        self.result_card.clear()
        self._analyzed_url = url.strip()
        self.url_panel.analyze_btn.setEnabled(False)
        self.status_label.setText("Analyzing...")

        ydl_settings = self._build_ydl_settings()

        self._analyze_worker = AnalyzeWorker(url, ydl_settings)
        self._analyze_worker.finished.connect(self._on_analyze_done)
        self._analyze_worker.error.connect(self._on_analyze_error)
        self._analyze_worker.finished.connect(
            lambda *_: self.url_panel.analyze_btn.setEnabled(True)
        )
        self._analyze_worker.error.connect(lambda *_: self.url_panel.analyze_btn.setEnabled(True))
        self._analyze_worker.start()

    def _on_analyze_done(self, info) -> None:
        if self.url_panel.input.text().strip() != self._analyzed_url:
            self.status_label.setText("Link changed. Press Analyze to load the new link.")
            return
        self.status_label.setText("Analysis complete")
        self.result_card.display_info(info)
        self.result_card.set_default_preset(self.settings.default_preset)
        self.result_card.set_download_folder(
            self.settings.default_folder or str(get_default_download_dir())
        )
        self.result_card.set_advanced(self.url_panel.is_advanced())

        if info.is_playlist:
            self.status_label.setText(
                f"Playlist detected ({info.playlist_count} items). "
                "Download one video at a time; batch playlist download is not supported."
            )

    def _on_analyze_error(self, message: str, detail: str) -> None:
        self.status_label.setText("Analysis failed")
        dlg = ErrorDialog(message, detail, parent=self)
        dlg.exec()

    def _on_search(self, query: str) -> None:
        if getattr(self, "_search_worker", None) and self._search_worker.isRunning():
            return
        provider = self.url_panel.get_provider()
        self.search_panel.set_status("Searching...")
        self.tabs.setCurrentWidget(self.search_panel)

        self._search_worker = SearchWorker(query, provider, self.settings.searxng_instance)
        self._search_worker.finished.connect(self._on_search_done)
        self._search_worker.error.connect(self._on_search_error)
        self._search_worker.start()

    def _on_search_done(self, results) -> None:
        self.search_panel.display_results(results)

    def _on_search_error(self, msg: str) -> None:
        self.search_panel.set_status(f"Search failed: {msg}")

    def _on_result_selected(self, result) -> None:
        self.url_panel.set_text(result.url)
        self._on_analyze(result.url)

    def _advanced_opts(self) -> dict:
        if self.url_panel.is_advanced():
            return self.format_selector.get_settings()
        return {}

    def _on_download_result(self) -> None:
        info = self.result_card.get_media_info()
        if not info:
            return

        preset = self.result_card.get_selected_preset()
        folder = (
            self.result_card.get_download_folder()
            or self.settings.default_folder
            or str(get_default_download_dir())
        )

        job = DownloadJob(
            url=info.webpage_url or info.url,
            webpage_url=info.webpage_url,
            title=info.title,
            extractor=info.extractor,
            uploader=info.uploader,
            duration=info.duration,
            thumbnail=info.thumbnail,
            selected_preset=preset,
            format_spec=self.result_card.get_selected_format(),
            folder=folder,
            status=JobStatus.PENDING,
            created_at=datetime.now().isoformat(),
            extra_opts=self._advanced_opts(),
        )

        self._start_download(job)

    def _start_download(self, job: DownloadJob) -> None:
        try:
            self.download_manager.add_to_queue(job)
        except Exception as exc:
            ErrorDialog("Could not add the download", str(exc), parent=self).exec()
            return
        self.status_label.setText(f"Downloading: {job.title[:40]}...")

    def _on_dl_progress(self, job: DownloadJob) -> None:
        self.queue_panel.update_job(job)

    def _on_dl_status(self, job: DownloadJob) -> None:
        if job.status == JobStatus.COMPLETED:
            self.status_label.setText(f"Completed: {job.title[:40]}")
        elif job.status == JobStatus.FAILED:
            self.status_label.setText(f"Failed: {job.title[:40]}")
        self._refresh_queue()
        self._load_history()

    def _on_queue_update(self, queue: list) -> None:
        self.queue_panel.update_queue(queue)

    def _refresh_queue(self) -> None:
        queue = self.download_manager.get_queue()
        self.queue_panel.update_queue(queue)

    def _on_cancel(self, job_id: int) -> None:
        self.download_manager.cancel_job(job_id)

    def _on_retry(self, job_id: int) -> None:
        self.download_manager.retry_job(job_id)

    def _on_open_folder(self, path: str) -> None:
        open_folder_in_explorer(path)

    def _on_mode_changed(self, advanced: bool) -> None:
        self.result_card.set_advanced(advanced)
        options_index = self.tabs.indexOf(self.format_selector)
        if advanced:
            if options_index < 0:
                self.tabs.addTab(self.format_selector, "Advanced options")
            self.tabs.setCurrentWidget(self.format_selector)
        else:
            if options_index >= 0:
                self.tabs.removeTab(options_index)
            self.tabs.setCurrentWidget(self.search_panel)

    def _on_change_folder(self) -> None:
        current = self.result_card.get_download_folder() or str(get_default_download_dir())
        folder = QFileDialog.getExistingDirectory(self, "Choose download folder", current)
        if not folder:
            return
        self.result_card.set_download_folder(folder)
        self.settings.default_folder = folder
        self.settings_repo.save_app_settings(self.settings)
        self.download_manager.set_settings(self.settings)
        self.status_label.setText(f"Download folder: {folder}")

    def _open_settings(self) -> None:
        dlg = SettingsWindow(self.settings, self)
        dlg.settings_changed.connect(self._on_settings_changed)
        dlg.exec()

    def _on_settings_changed(self, settings: AppSettings) -> None:
        self.settings = settings
        self.settings_repo.save_app_settings(settings)
        self._apply_theme()
        self.download_manager.set_settings(settings)
        self.result_card.set_download_folder(
            settings.default_folder or str(get_default_download_dir())
        )

    def _open_dependencies(self) -> None:
        dlg = DependencyWindow(self)
        dlg.exec()
        self._check_deps_async()

    def _load_history(self) -> None:
        self.history_list.clear()
        jobs = self.downloads_repo.get_all(50)
        for j in jobs:
            created = (j.created_at or "")[:16].replace("T", " ")
            text = f"{j.title or j.url[:50]} · {j.status.value} · {created}"
            item = QListWidgetItem(text)
            item.setData(Qt.UserRole, j)
            self.history_list.addItem(item)
        if hasattr(self, "history_count"):
            count = len(jobs)
            self.history_count.setText(f"{count} {'entry' if count == 1 else 'entries'}")
        self._update_history_actions()

    def _update_history_actions(self) -> None:
        selected = len(self.history_list.selectedItems())
        has_rows = self.history_list.count() > 0
        self.delete_history_btn.setEnabled(selected > 0)
        self.clear_history_btn.setEnabled(has_rows)

    def _on_history_click(self, item) -> None:
        job = item.data(Qt.UserRole)
        if job and job.url:
            self.url_panel.set_text(job.url)

    def _delete_selected_history(self) -> None:
        if self._history_busy():
            return
        items = self.history_list.selectedItems()
        if not items:
            return

        count = len(items)
        label = "item" if count == 1 else "items"
        dlg = ConfirmDialog(
            "Delete selected",
            f"Delete {count} selected history {label}? This cannot be undone.",
            confirm_text="Delete",
            parent=self,
        )
        if dlg.exec() != ConfirmDialog.Accepted:
            return

        try:
            for item in items:
                job = item.data(Qt.UserRole)
                if job and job.id:
                    self.downloads_repo.delete(job.id)
        except Exception as e:
            dlg = ErrorDialog("Could not delete history items", str(e), parent=self)
            dlg.exec()
            self._load_history()
            return

        self._load_history()
        self.status_label.setText(f"Deleted {count} history {label}")

    def _clear_history(self) -> None:
        if self._history_busy():
            return
        if self.history_list.count() == 0:
            return

        dlg = ConfirmDialog(
            "Clear history",
            "Clear the entire download history? This cannot be undone.",
            confirm_text="Clear all",
            parent=self,
        )
        if dlg.exec() != ConfirmDialog.Accepted:
            return

        try:
            self.downloads_repo.clear_history()
        except Exception as e:
            dlg = ErrorDialog("Could not clear history", str(e), parent=self)
            dlg.exec()
            return

        self._load_history()
        self.status_label.setText("History cleared")

    def _history_busy(self) -> bool:
        busy = any(
            job.status in (JobStatus.PENDING, JobStatus.DOWNLOADING, JobStatus.POSTPROCESSING)
            for job in self.download_manager.get_queue()
        )
        if busy:
            QMessageBox.information(
                self,
                "Downloads in progress",
                "Finish or cancel queued downloads before deleting history.",
            )
        return busy

    def _show_about(self) -> None:
        QMessageBox.about(
            self,
            "About Hate Downloader",
            f"Hate Downloader v{__version__}\n\n"
            "A desktop tool to search, analyze and download\n"
            "media from YouTube, Internet Archive and the web.\n\n"
            "Built with PySide6, yt-dlp, and Python.",
        )

    def _build_ydl_settings(self) -> dict:
        settings: dict = {
            "cookiefile": self.settings.cookiefile or None,
            "socket_timeout": self.settings.socket_timeout,
            "retries": self.settings.retries,
            "ignoreerrors": self.settings.ignoreerrors,
            "noplaylist": True,
        }
        if self.settings.cookies_from_browser:
            settings["cookiesfrombrowser"] = (self.settings.cookies_from_browser,)
        return settings

    def closeEvent(self, event) -> None:
        active = [
            job
            for job in self.download_manager.get_queue()
            if job.status in (JobStatus.PENDING, JobStatus.DOWNLOADING, JobStatus.POSTPROCESSING)
        ]
        if active:
            count = len(active)
            dlg = ConfirmDialog(
                "Downloads in progress",
                f"{count} {'download is' if count == 1 else 'downloads are'} still running. "
                "Cancel and quit?",
                confirm_text="Cancel and quit",
                cancel_text="Keep working",
                parent=self,
            )
            if dlg.exec() != ConfirmDialog.Accepted:
                event.ignore()
                return
            self.download_manager.cancel_all()

        workers = [
            getattr(self, name, None)
            for name in ("_analyze_worker", "_search_worker", "_dep_worker")
        ]
        if any(worker and worker.isRunning() for worker in workers):
            self.status_label.setText("Finishing the current task first. Try again in a moment.")
            event.ignore()
            return
        if self.result_card.thumbnail_busy():
            self.status_label.setText("Finishing image loading. Try again in a moment.")
            event.ignore()
            return

        self.settings.window_width = self.width()
        self.settings.window_height = self.height()
        self.settings_repo.save_app_settings(self.settings)
        super().closeEvent(event)
