from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

_ALLOWED_YDL_KEYS = {
    "format_sort",
    "merge_output_format",
    "postprocessors",
    "writesubtitles",
    "writeautomaticsub",
    "subtitleslangs",
    "writethumbnail",
}


class FormatSelector(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self) -> None:
        scroll = QScrollArea()
        scroll.setObjectName("plainScroll")
        scroll.setWidgetResizable(True)
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(4, 12, 8, 4)
        layout.setSpacing(16)

        note = QLabel("These choices apply to the next download only.")
        note.setObjectName("muted")
        layout.addWidget(note)

        video_form = self._section(layout, "Video")
        self.vcodec_combo = QComboBox()
        self.vcodec_combo.addItems(["Default", "h264", "av1", "vp9", "hevc"])
        self.resolution_combo = QComboBox()
        self.resolution_combo.addItems(
            ["Default", "2160p", "1440p", "1080p", "720p", "480p", "360p"]
        )
        self.container_combo = QComboBox()
        self.container_combo.addItems(["Default", "mp4", "mkv", "webm"])
        video_form.addRow("Codec", self.vcodec_combo)
        video_form.addRow("Resolution", self.resolution_combo)
        video_form.addRow("Container", self.container_combo)

        audio_form = self._section(layout, "Audio")
        self.acodec_combo = QComboBox()
        self.acodec_combo.addItems(["Default", "mp3", "aac", "opus", "flac", "wav"])
        self.quality_combo = QComboBox()
        self.quality_combo.addItems(["Default", "320", "256", "192", "128", "64"])
        audio_form.addRow("Codec", self.acodec_combo)
        audio_form.addRow("Bitrate (kbps)", self.quality_combo)

        subs_form = self._section(layout, "Subtitles")
        self.subs_check = QCheckBox("Download subtitles")
        self.auto_subs_check = QCheckBox("Download automatic captions")
        self.subs_lang = QLineEdit()
        self.subs_lang.setPlaceholderText("en, es, fr")
        subs_form.addRow(self.subs_check)
        subs_form.addRow(self.auto_subs_check)
        subs_form.addRow("Languages", self.subs_lang)

        extras_form = self._section(layout, "Extras")
        self.thumbnail_check = QCheckBox("Keep the thumbnail image file")
        self.embed_thumb_check = QCheckBox("Embed the thumbnail in the file")
        self.metadata_check = QCheckBox("Write title and artist metadata")
        self.embed_subs_check = QCheckBox("Embed subtitles in the video")
        extras_form.addRow(self.thumbnail_check)
        extras_form.addRow(self.embed_thumb_check)
        extras_form.addRow(self.metadata_check)
        extras_form.addRow(self.embed_subs_check)

        layout.addStretch()

        scroll.setWidget(content)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

    @staticmethod
    def _section(layout: QVBoxLayout, title: str) -> QFormLayout:
        label = QLabel(title)
        label.setObjectName("sectionTitle")
        layout.addWidget(label)

        form = QFormLayout()
        form.setSpacing(8)
        form.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        layout.addLayout(form)
        return form

    def get_settings(self) -> dict:
        """Return yt-dlp option overlays for this download only.

        Unchecked boxes are omitted so global Settings still apply.
        """
        settings: dict = {}
        format_sort: list[str] = []
        postprocessors: list[dict] = []

        vcodec = self.vcodec_combo.currentText()
        if vcodec != "Default":
            format_sort.append(f"vcodec:{vcodec}")

        resolution = self.resolution_combo.currentText()
        if resolution != "Default":
            format_sort.append(f"res:{resolution.replace('p', '')}")

        if format_sort:
            settings["format_sort"] = format_sort

        container = self.container_combo.currentText()
        if container != "Default":
            settings["merge_output_format"] = container

        acodec = self.acodec_combo.currentText()
        if acodec != "Default":
            audio_pp: dict = {
                "key": "FFmpegExtractAudio",
                "preferredcodec": acodec,
            }
            quality = self.quality_combo.currentText()
            if quality != "Default":
                audio_pp["preferredquality"] = quality
            postprocessors.append(audio_pp)

        if self.subs_check.isChecked():
            settings["writesubtitles"] = True
        if self.auto_subs_check.isChecked():
            settings["writeautomaticsub"] = True
        langs = [part.strip() for part in self.subs_lang.text().split(",") if part.strip()]
        if langs:
            settings["subtitleslangs"] = langs

        if self.thumbnail_check.isChecked():
            settings["writethumbnail"] = True
        if self.embed_thumb_check.isChecked():
            postprocessors.append(
                {
                    "key": "EmbedThumbnail",
                    "already_have_thumbnail": self.thumbnail_check.isChecked(),
                }
            )
            if not self.thumbnail_check.isChecked():
                # Embedding needs a thumbnail on disk; the postprocessor
                # removes it again because it is a temporary file.
                settings["writethumbnail"] = True
        if self.metadata_check.isChecked():
            postprocessors.append({"key": "FFmpegMetadata"})
        if self.embed_subs_check.isChecked():
            postprocessors.append({"key": "FFmpegEmbedSubtitle"})

        if postprocessors:
            settings["postprocessors"] = postprocessors

        return {key: value for key, value in settings.items() if key in _ALLOWED_YDL_KEYS}
