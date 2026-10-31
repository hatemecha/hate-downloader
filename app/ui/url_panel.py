from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
)

from app import __version__
from app.ui.icons import application_icon


class UrlPanel(QFrame):
    analyze_clicked = Signal(str)
    search_clicked = Signal(str)
    mode_changed = Signal(bool)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("urlPanel")
        self._advanced = False
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 14, 20, 14)
        layout.setSpacing(10)

        header = QHBoxLayout()
        header.setSpacing(8)

        logo = QLabel()
        logo.setPixmap(application_icon().pixmap(20, 20))
        header.addWidget(logo)

        title = QLabel("Hate Downloader")
        title.setObjectName("sectionTitle")
        header.addWidget(title)

        version = QLabel(__version__)
        version.setObjectName("faint")
        header.addWidget(version)
        header.addStretch()

        hint = QLabel("Paste a link, or type to search")
        hint.setObjectName("faint")
        header.addWidget(hint)

        input_row = QHBoxLayout()
        input_row.setSpacing(8)

        self.input = QLineEdit()
        self.input.setPlaceholderText("https://www.youtube.com/watch?v=...")
        self.input.setClearButtonEnabled(True)
        self.input.returnPressed.connect(self._on_action)
        self.input.setMinimumHeight(36)

        self.analyze_btn = QPushButton("Analyze")
        self.analyze_btn.setObjectName("strongButton")
        self.analyze_btn.setMinimumHeight(36)
        self.analyze_btn.setToolTip("Resolve the link and show what can be downloaded")
        self.analyze_btn.clicked.connect(self._on_analyze)

        self.search_btn = QPushButton("Search")
        self.search_btn.setObjectName("ghostButton")
        self.search_btn.setMinimumHeight(36)
        self.search_btn.setToolTip("Search by words instead of a link")
        self.search_btn.clicked.connect(self._on_search)

        input_row.addWidget(self.input, 1)
        input_row.addWidget(self.analyze_btn)
        input_row.addWidget(self.search_btn)

        options_row = QHBoxLayout()
        options_row.setSpacing(8)

        source_label = QLabel("Source")
        source_label.setObjectName("muted")
        options_row.addWidget(source_label)

        self.provider_combo = QComboBox()
        self.provider_combo.addItem("All sources", "all")
        self.provider_combo.addItem("YouTube", "youtube")
        self.provider_combo.addItem("Internet Archive", "archive")
        self.provider_combo.addItem("Web (SearXNG)", "web")
        self.provider_combo.addItem("Scan page for media", "scan")
        self.provider_combo.setToolTip("Where the Search button looks")
        self.provider_combo.setMinimumHeight(30)
        options_row.addWidget(self.provider_combo)
        options_row.addStretch()

        self.advanced_check = QCheckBox("Advanced options")
        self.advanced_check.setToolTip("Show format, codec and subtitle controls")
        self.advanced_check.toggled.connect(self._toggle_mode)
        options_row.addWidget(self.advanced_check)

        layout.addLayout(header)
        layout.addLayout(input_row)
        layout.addLayout(options_row)

    def _on_action(self) -> None:
        text = self.input.text().strip()
        if not text:
            return
        if self._is_url(text):
            self.analyze_clicked.emit(text)
        else:
            self.search_clicked.emit(text)

    def _on_analyze(self) -> None:
        text = self.input.text().strip()
        if text:
            self.analyze_clicked.emit(text)

    def _on_search(self) -> None:
        text = self.input.text().strip()
        if text:
            self.search_clicked.emit(text)

    def _toggle_mode(self, checked: bool) -> None:
        self._advanced = checked
        self.mode_changed.emit(checked)

    def set_advanced(self, advanced: bool) -> None:
        if self.advanced_check.isChecked() != advanced:
            self.advanced_check.setChecked(advanced)

    def _is_url(self, text: str) -> bool:
        lowered = text.lower()
        return (
            lowered.startswith("http://")
            or lowered.startswith("https://")
            or lowered.startswith("ytdl://")
        )

    def get_provider(self) -> str:
        return self.provider_combo.currentData() or "all"

    def get_text(self) -> str:
        return self.input.text().strip()

    def set_text(self, text: str) -> None:
        self.input.setText(text)

    def is_advanced(self) -> bool:
        return self._advanced
