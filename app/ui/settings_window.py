from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from app.models.app_settings import AppSettings
from app.ui.theme import resolve_theme


class SettingsWindow(QDialog):
    settings_changed = Signal(object)

    def __init__(self, settings: AppSettings, parent=None) -> None:
        super().__init__(parent)
        self.settings = settings
        self.setWindowTitle("Settings")
        self.setMinimumSize(680, 540)
        self._setup_ui()
        self._load_settings()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        tabs = QTabWidget()
        pages = (
            (self._create_general_tab(), "General"),
            (self._create_downloads_tab(), "Downloads"),
            (self._create_advanced_tab(), "Advanced"),
            (self._create_paths_tab(), "Paths"),
        )
        for page, title in pages:
            scroll = QScrollArea()
            scroll.setObjectName("plainScroll")
            scroll.setWidgetResizable(True)
            scroll.setWidget(page)
            tabs.addTab(scroll, title)
        layout.addWidget(tabs, 1)

        buttons = QHBoxLayout()
        buttons.setSpacing(8)
        buttons.addStretch()
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setObjectName("ghostButton")
        cancel_btn.clicked.connect(self.reject)
        save_btn = QPushButton("Save")
        save_btn.setObjectName("strongButton")
        save_btn.clicked.connect(self._save)
        buttons.addWidget(cancel_btn)
        buttons.addWidget(save_btn)
        layout.addLayout(buttons)

    @staticmethod
    def _make_page(description: str, widget: QWidget) -> QFormLayout:
        outer = QVBoxLayout(widget)
        outer.setContentsMargins(20, 20, 20, 20)
        outer.setSpacing(12)
        intro = QLabel(description)
        intro.setObjectName("muted")
        intro.setWordWrap(True)
        outer.addWidget(intro)

        form = QFormLayout()
        form.setSpacing(12)
        form.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        outer.addLayout(form)
        outer.addStretch()

        return form

    def _create_general_tab(self) -> QWidget:
        widget = QWidget()
        layout = self._make_page(
            "Appearance, where files go, and the quality used by default.", widget
        )

        self.theme_combo = QComboBox()
        self.theme_combo.addItem("Graphite", "hate_dark")
        self.theme_combo.addItem("Paper", "light")

        self.default_folder_input = QLineEdit()
        self.default_folder_input.setPlaceholderText("Downloads/HateDownloader")
        browse_btn = QPushButton("Browse")
        browse_btn.clicked.connect(self._browse_folder)
        folder_layout = QHBoxLayout()
        folder_layout.setSpacing(8)
        folder_layout.addWidget(self.default_folder_input)
        folder_layout.addWidget(browse_btn)

        self.default_preset_combo = QComboBox()
        self.default_preset_combo.addItem("Best quality · MP4", "best_mp4")
        self.default_preset_combo.addItem("Maximum quality", "max_quality")
        self.default_preset_combo.addItem("1080p · MP4", "1080p_mp4")
        self.default_preset_combo.addItem("720p · MP4", "720p_mp4")
        self.default_preset_combo.addItem("MP3 · 320 kbps", "mp3_320")
        self.default_preset_combo.addItem("Audio · best original quality", "best_audio")

        self.filename_template = QLineEdit()
        self.filename_template.setPlaceholderText("%(title)s.%(ext)s")

        layout.addRow("Theme", self.theme_combo)
        layout.addRow("Folder", folder_layout)
        layout.addRow("Default quality", self.default_preset_combo)
        layout.addRow("Filename", self.filename_template)
        return widget

    def _create_downloads_tab(self) -> QWidget:
        widget = QWidget()
        layout = self._make_page(
            "How many files run at once and how the app recovers from network errors.",
            widget,
        )

        self.max_concurrent = QSpinBox()
        self.max_concurrent.setRange(1, 10)
        self.concurrent_fragments = QSpinBox()
        self.concurrent_fragments.setRange(1, 20)
        self.retries = QSpinBox()
        self.retries.setRange(0, 50)
        self.fragment_retries = QSpinBox()
        self.fragment_retries.setRange(0, 50)
        self.socket_timeout = QSpinBox()
        self.socket_timeout.setRange(5, 120)

        self.ratelimit = QLineEdit()
        self.ratelimit.setPlaceholderText("Leave empty for no limit, or e.g. 5M")

        self.use_aria2c = QCheckBox("Use aria2c as the external downloader")
        self.continuedl = QCheckBox("Continue partial downloads")

        layout.addRow("Concurrent downloads", self.max_concurrent)
        layout.addRow("Fragments per download", self.concurrent_fragments)
        layout.addRow("Retries", self.retries)
        layout.addRow("Fragment retries", self.fragment_retries)
        layout.addRow("Socket timeout (s)", self.socket_timeout)
        layout.addRow("Rate limit", self.ratelimit)
        layout.addRow(self.use_aria2c)
        layout.addRow(self.continuedl)
        return widget

    def _create_advanced_tab(self) -> QWidget:
        widget = QWidget()
        layout = self._make_page(
            "Optional output extras. None of these are needed for a normal download.",
            widget,
        )

        self.writesubtitles = QCheckBox("Download subtitles")
        self.writeautomaticsub = QCheckBox("Download automatic captions")
        self.subtitleslangs = QLineEdit()
        self.subtitleslangs.setPlaceholderText("en, es, fr")

        self.writethumbnail = QCheckBox("Keep the thumbnail image file")
        self.embedthumbnail = QCheckBox("Embed the thumbnail in the file")
        self.addmetadata = QCheckBox("Write title and artist metadata")
        self.embedsubtitles = QCheckBox("Embed subtitles in the video")

        thumbnail_hint = QLabel(
            "Off by default: no image file is saved next to the video. "
            "Embedding works without keeping the file."
        )
        thumbnail_hint.setObjectName("faint")
        thumbnail_hint.setWordWrap(True)

        self.cookiefile = QLineEdit()
        self.cookiefile.setPlaceholderText("Path to cookies.txt")
        cookie_browse = QPushButton("Browse")
        cookie_browse.clicked.connect(lambda: self._browse_file(self.cookiefile))
        cookie_layout = QHBoxLayout()
        cookie_layout.setSpacing(8)
        cookie_layout.addWidget(self.cookiefile)
        cookie_layout.addWidget(cookie_browse)

        self.cookies_from_browser = QLineEdit()
        self.cookies_from_browser.setPlaceholderText("firefox, chrome, edge")

        self.searxng_instance = QLineEdit()
        self.searxng_instance.setPlaceholderText("https://search.sapti.me")

        self.download_archive_path = QLineEdit()
        archive_browse = QPushButton("Browse")
        archive_browse.clicked.connect(lambda: self._browse_file(self.download_archive_path))
        archive_layout = QHBoxLayout()
        archive_layout.setSpacing(8)
        archive_layout.addWidget(self.download_archive_path)
        archive_layout.addWidget(archive_browse)

        layout.addRow(self.writesubtitles)
        layout.addRow(self.writeautomaticsub)
        layout.addRow("Subtitle languages", self.subtitleslangs)
        layout.addRow(self.writethumbnail)
        layout.addRow(self.embedthumbnail)
        layout.addRow("", thumbnail_hint)
        layout.addRow(self.addmetadata)
        layout.addRow(self.embedsubtitles)
        layout.addRow("Cookie file", cookie_layout)
        layout.addRow("Cookies from browser", self.cookies_from_browser)
        layout.addRow("SearXNG instance", self.searxng_instance)
        layout.addRow("Download archive", archive_layout)
        return widget

    def _create_paths_tab(self) -> QWidget:
        widget = QWidget()
        layout = self._make_page(
            "Leave these empty to use the copies installed by the app or found on PATH.",
            widget,
        )

        self.ffmpeg_path = QLineEdit()
        ffmpeg_browse = QPushButton("Browse")
        ffmpeg_browse.clicked.connect(lambda: self._browse_file(self.ffmpeg_path))
        ffmpeg_layout = QHBoxLayout()
        ffmpeg_layout.setSpacing(8)
        ffmpeg_layout.addWidget(self.ffmpeg_path)
        ffmpeg_layout.addWidget(ffmpeg_browse)

        self.ffprobe_path = QLineEdit()
        ffprobe_browse = QPushButton("Browse")
        ffprobe_browse.clicked.connect(lambda: self._browse_file(self.ffprobe_path))
        ffprobe_layout = QHBoxLayout()
        ffprobe_layout.setSpacing(8)
        ffprobe_layout.addWidget(self.ffprobe_path)
        ffprobe_layout.addWidget(ffprobe_browse)

        self.aria2c_path = QLineEdit()
        aria2c_browse = QPushButton("Browse")
        aria2c_browse.clicked.connect(lambda: self._browse_file(self.aria2c_path))
        aria2c_layout = QHBoxLayout()
        aria2c_layout.setSpacing(8)
        aria2c_layout.addWidget(self.aria2c_path)
        aria2c_layout.addWidget(aria2c_browse)

        layout.addRow("FFmpeg", ffmpeg_layout)
        layout.addRow("FFprobe", ffprobe_layout)
        layout.addRow("aria2c", aria2c_layout)
        return widget

    def _load_settings(self) -> None:
        idx = self.theme_combo.findData(resolve_theme(self.settings.theme))
        if idx >= 0:
            self.theme_combo.setCurrentIndex(idx)

        self.default_folder_input.setText(self.settings.default_folder)
        self.filename_template.setText(self.settings.filename_template)

        idx = self.default_preset_combo.findData(self.settings.default_preset)
        if idx >= 0:
            self.default_preset_combo.setCurrentIndex(idx)

        self.max_concurrent.setValue(self.settings.max_concurrent)
        self.concurrent_fragments.setValue(self.settings.concurrent_fragments)
        self.retries.setValue(self.settings.retries)
        self.fragment_retries.setValue(self.settings.fragment_retries)
        self.socket_timeout.setValue(self.settings.socket_timeout)
        self.ratelimit.setText(self.settings.ratelimit)
        self.use_aria2c.setChecked(self.settings.use_aria2c)
        self.continuedl.setChecked(self.settings.continuedl)

        self.writesubtitles.setChecked(self.settings.writesubtitles)
        self.writeautomaticsub.setChecked(self.settings.writeautomaticsub)
        self.subtitleslangs.setText(self.settings.subtitleslangs)
        self.writethumbnail.setChecked(self.settings.writethumbnail)
        self.embedthumbnail.setChecked(self.settings.embedthumbnail)
        self.addmetadata.setChecked(self.settings.addmetadata)
        self.embedsubtitles.setChecked(self.settings.embedsubtitles)
        self.cookiefile.setText(self.settings.cookiefile)
        self.cookies_from_browser.setText(self.settings.cookies_from_browser)
        self.searxng_instance.setText(self.settings.searxng_instance)
        self.download_archive_path.setText(self.settings.download_archive)

        self.ffmpeg_path.setText(self.settings.ffmpeg_path)
        self.ffprobe_path.setText(self.settings.ffprobe_path)
        self.aria2c_path.setText(self.settings.aria2c_path)

    def _save(self) -> None:
        self.settings.theme = self.theme_combo.currentData()
        self.settings.default_folder = self.default_folder_input.text()
        self.settings.default_preset = self.default_preset_combo.currentData()
        self.settings.filename_template = self.filename_template.text()
        self.settings.max_concurrent = self.max_concurrent.value()
        self.settings.concurrent_fragments = self.concurrent_fragments.value()
        self.settings.retries = self.retries.value()
        self.settings.fragment_retries = self.fragment_retries.value()
        self.settings.socket_timeout = self.socket_timeout.value()
        self.settings.ratelimit = self.ratelimit.text()
        self.settings.use_aria2c = self.use_aria2c.isChecked()
        self.settings.continuedl = self.continuedl.isChecked()
        self.settings.writesubtitles = self.writesubtitles.isChecked()
        self.settings.writeautomaticsub = self.writeautomaticsub.isChecked()
        self.settings.subtitleslangs = self.subtitleslangs.text()
        self.settings.writethumbnail = self.writethumbnail.isChecked()
        self.settings.embedthumbnail = self.embedthumbnail.isChecked()
        self.settings.addmetadata = self.addmetadata.isChecked()
        self.settings.embedsubtitles = self.embedsubtitles.isChecked()
        self.settings.cookiefile = self.cookiefile.text()
        self.settings.cookies_from_browser = self.cookies_from_browser.text()
        self.settings.searxng_instance = self.searxng_instance.text()
        self.settings.download_archive = self.download_archive_path.text()
        self.settings.ffmpeg_path = self.ffmpeg_path.text()
        self.settings.ffprobe_path = self.ffprobe_path.text()
        self.settings.aria2c_path = self.aria2c_path.text()

        self.settings_changed.emit(self.settings)
        self.accept()

    def _browse_folder(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, "Select download folder")
        if folder:
            self.default_folder_input.setText(folder)

    def _browse_file(self, line_edit: QLineEdit) -> None:
        file_path, _ = QFileDialog.getOpenFileName(self, "Select file")
        if file_path:
            line_edit.setText(file_path)
