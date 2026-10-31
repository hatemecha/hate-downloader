from typing import Optional

import httpx
from PySide6.QtCore import QSize, Qt, QThread, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app import __version__
from app.models.media_info import MediaFormat, MediaInfo
from app.utils.logger import logger

_THUMB_SIZE = QSize(192, 108)


class _ThumbnailLoader(QThread):
    loaded = Signal(bytes)

    def __init__(self, url: str) -> None:
        super().__init__()
        self.url = url

    def run(self) -> None:
        try:
            resp = httpx.get(
                self.url,
                timeout=6.0,
                follow_redirects=True,
                headers={"User-Agent": f"HateDownloader/{__version__}"},
            )
            if resp.status_code == 200 and resp.content:
                self.loaded.emit(resp.content)
        except Exception as e:
            logger.debug(f"Thumbnail load failed: {e}")


FRIENDLY_PRESETS: list[tuple[str, str]] = [
    ("best_mp4", "Best quality · MP4"),
    ("1080p_mp4", "1080p · MP4"),
    ("720p_mp4", "720p · MP4"),
    ("480p_mp4", "480p · MP4"),
    ("max_quality", "Maximum quality · original container"),
    ("mp3_320", "MP3 · 320 kbps"),
    ("mp3_192", "MP3 · 192 kbps"),
    ("best_audio", "Audio · best original quality"),
    ("wav", "WAV · uncompressed"),
    ("flac", "FLAC · lossless"),
]

_VIDEO_PRESETS = {"best_mp4", "1080p_mp4", "720p_mp4", "480p_mp4", "max_quality"}

_EXTRACTOR_NAMES = {
    "youtube": "YouTube",
    "archive": "Internet Archive",
    "generic": "Direct link",
}


def _extractor_name(value: str) -> str:
    lowered = (value or "").lower()
    for key, name in _EXTRACTOR_NAMES.items():
        if key in lowered:
            return name
    return value or ""


def _duration_text(seconds: int) -> str:
    if not seconds:
        return ""
    minutes, secs = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    if hours:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    return f"{minutes}:{secs:02d}"


class ResultCard(QFrame):
    download_clicked = Signal()
    change_folder_requested = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("resultCard")
        self._info: Optional[MediaInfo] = None
        self._thumb_loader: Optional[_ThumbnailLoader] = None
        self._thumb_loaders: list[_ThumbnailLoader] = []
        self._setup_ui()
        self.hide()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 16)
        layout.setSpacing(12)

        top = QHBoxLayout()
        top.setSpacing(14)

        self.thumbnail_label = QLabel("No thumbnail")
        self.thumbnail_label.setFixedSize(_THUMB_SIZE)
        self.thumbnail_label.setAlignment(Qt.AlignCenter)
        self.thumbnail_label.setObjectName("thumbnailLabel")

        details = QVBoxLayout()
        details.setSpacing(4)

        self.title_label = QLabel("")
        self.title_label.setTextFormat(Qt.PlainText)
        self.title_label.setObjectName("cardTitle")
        self.title_label.setWordWrap(True)

        self.spec_label = QLabel("")
        self.spec_label.setTextFormat(Qt.PlainText)
        self.spec_label.setObjectName("muted")

        details.addWidget(self.title_label)
        details.addWidget(self.spec_label)
        details.addStretch()

        action_row = QHBoxLayout()
        action_row.setSpacing(8)

        self.preset_combo = QComboBox()
        self.preset_combo.setSizeAdjustPolicy(QComboBox.AdjustToMinimumContentsLengthWithIcon)
        self.preset_combo.setMinimumContentsLength(18)
        self.preset_combo.setMinimumHeight(36)
        action_row.addWidget(self.preset_combo, 1)

        self.download_btn = QPushButton("Download")
        self.download_btn.setObjectName("primaryButton")
        self.download_btn.setMinimumHeight(38)
        self.download_btn.setMinimumWidth(128)
        self.download_btn.clicked.connect(self.download_clicked.emit)
        action_row.addWidget(self.download_btn)

        details.addLayout(action_row)

        top.addWidget(self.thumbnail_label)
        top.addLayout(details, 1)
        layout.addLayout(top)

        self.advanced_row = QWidget()
        advanced_layout = QHBoxLayout(self.advanced_row)
        advanced_layout.setContentsMargins(0, 0, 0, 0)
        advanced_layout.setSpacing(8)
        advanced_label = QLabel("Exact format")
        advanced_label.setObjectName("muted")
        advanced_label.setFixedWidth(80)
        advanced_layout.addWidget(advanced_label)
        self.format_combo = QComboBox()
        self.format_combo.setSizeAdjustPolicy(QComboBox.AdjustToMinimumContentsLengthWithIcon)
        self.format_combo.setMinimumContentsLength(18)
        advanced_layout.addWidget(self.format_combo, 1)
        layout.addWidget(self.advanced_row)
        self.advanced_row.hide()

        folder_row = QHBoxLayout()
        folder_row.setSpacing(8)
        folder_label = QLabel("Save to")
        folder_label.setObjectName("muted")
        folder_label.setFixedWidth(80)
        folder_row.addWidget(folder_label)
        self.folder_input = QLineEdit()
        self.folder_input.setReadOnly(True)
        self.folder_input.setMinimumHeight(32)
        self.folder_input.setToolTip("Folder where the file will be saved")
        folder_row.addWidget(self.folder_input, 1)
        self.change_folder_btn = QPushButton("Change")
        self.change_folder_btn.setObjectName("ghostButton")
        self.change_folder_btn.clicked.connect(self.change_folder_requested.emit)
        folder_row.addWidget(self.change_folder_btn)
        layout.addLayout(folder_row)

    def display_info(self, info: MediaInfo) -> None:
        self._info = info
        self.title_label.setText(info.title or "Untitled")
        self.spec_label.setText(self._spec_text(info))
        self.thumbnail_label.setText("No thumbnail")

        if info.thumbnail:
            self._load_thumbnail(info.thumbnail)

        self._populate_formats(info)
        self.show()

    @staticmethod
    def _spec_text(info: MediaInfo) -> str:
        parts = [
            _extractor_name(info.extractor),
            info.uploader,
            _duration_text(info.duration),
            f"{info.height}p" if info.height else "",
        ]
        return " · ".join(part for part in parts if part)

    def _populate_formats(self, info: MediaInfo) -> None:
        current_preset = self.get_selected_preset()
        self.preset_combo.clear()
        formats = self._usable_formats(info.formats)
        has_video = any(f.has_video for f in formats)
        has_audio = any(f.has_audio for f in formats)
        max_height = max((f.height or 0 for f in formats), default=0)
        for value, label in FRIENDLY_PRESETS:
            if formats:
                if value in _VIDEO_PRESETS and not has_video:
                    continue
                if value not in _VIDEO_PRESETS and not has_audio:
                    continue
                if value[0].isdigit() and max_height and int(value.split("p")[0]) > max_height:
                    continue
            self.preset_combo.addItem(label, value)
        self.download_btn.setEnabled(not info.is_playlist and self.preset_combo.count() > 0)
        idx = self.preset_combo.findData(current_preset)
        if idx >= 0:
            self.preset_combo.setCurrentIndex(idx)

        self.format_combo.clear()
        self.format_combo.addItem("Automatic (use quality above)", "")
        for f in formats:
            self.format_combo.addItem(self._format_label(f), self._format_spec(f))

    @staticmethod
    def _usable_formats(formats: list[MediaFormat]) -> list[MediaFormat]:
        usable = []
        for f in formats:
            if f.ext in ("mhtml", "") or "storyboard" in (f.format_note or "").lower():
                continue
            if not f.has_video and not f.has_audio:
                continue
            usable.append(f)
        usable.sort(key=lambda x: (x.has_video, x.height or 0, x.tbr or 0), reverse=True)
        return usable

    @staticmethod
    def _format_spec(f: MediaFormat) -> str:
        if f.has_video and not f.has_audio:
            return f"{f.format_id}+bestaudio/{f.format_id}"
        return f.format_id

    @staticmethod
    def _format_label(f: MediaFormat) -> str:
        if f.has_video:
            kind = f"{f.height}p" if f.height else (f.resolution or "Video")
        else:
            kind = "Audio"
        parts = [kind, f.ext.upper()]
        size = f.filesize or f.filesize_approx
        if size:
            parts.append(f"{size / 1_000_000:.1f} MB")
        if f.has_video and f.has_audio:
            parts.append("video + audio")
        return " · ".join(parts)

    def _load_thumbnail(self, url: str) -> None:
        if self._thumb_loader and self._thumb_loader.isRunning():
            self._thumb_loader.loaded.disconnect()
            self._thumb_loader.requestInterruption()
        loader = _ThumbnailLoader(url)
        loader.loaded.connect(self._on_thumbnail_loaded)
        self._thumb_loaders.append(loader)
        loader.finished.connect(lambda: self._thumb_loaders.remove(loader))
        self._thumb_loader = loader
        loader.start()

    def _on_thumbnail_loaded(self, data: bytes) -> None:
        if self.sender() is not self._thumb_loader or self._info is None:
            return
        pixmap = QPixmap()
        if not pixmap.loadFromData(data):
            return
        width, height = _THUMB_SIZE.width(), _THUMB_SIZE.height()
        scaled = pixmap.scaled(
            _THUMB_SIZE, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation
        )
        x = max(0, (scaled.width() - width) // 2)
        y = max(0, (scaled.height() - height) // 2)
        self.thumbnail_label.setPixmap(scaled.copy(x, y, width, height))

    def set_advanced(self, advanced: bool) -> None:
        self.advanced_row.setVisible(advanced)
        if not advanced:
            self.format_combo.setCurrentIndex(0)
        self.updateGeometry()

    def thumbnail_busy(self) -> bool:
        return any(loader.isRunning() for loader in self._thumb_loaders)

    def set_default_preset(self, preset: str) -> None:
        idx = self.preset_combo.findData(preset)
        if idx >= 0:
            self.preset_combo.setCurrentIndex(idx)

    def set_download_folder(self, folder: str) -> None:
        self.folder_input.setText(folder)
        self.folder_input.setCursorPosition(0)
        self.folder_input.setToolTip(folder)

    def get_download_folder(self) -> str:
        return self.folder_input.text().strip()

    def get_selected_format(self) -> str:
        return self.format_combo.currentData() or ""

    def get_selected_preset(self) -> str:
        return self.preset_combo.currentData() or "best_mp4"

    def get_media_info(self) -> Optional[MediaInfo]:
        return self._info

    def clear(self) -> None:
        self._info = None
        self.thumbnail_label.clear()
        self.thumbnail_label.setText("No thumbnail")
        self.hide()
