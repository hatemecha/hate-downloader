from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QVBoxLayout,
)

from app.models.search_result import SearchResult


class SearchPanel(QFrame):
    result_selected = Signal(object)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 12, 4, 4)
        layout.setSpacing(8)

        header = QHBoxLayout()
        header.setSpacing(8)

        title = QLabel("Search results")
        title.setObjectName("sectionTitle")
        header.addWidget(title)

        self.status_label = QLabel("Double-click a result to analyze it")
        self.status_label.setObjectName("faint")
        header.addStretch()
        header.addWidget(self.status_label)

        self.results_list = QListWidget()
        self.results_list.setObjectName("plainList")
        self.results_list.setWordWrap(True)
        self.results_list.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.results_list.itemDoubleClicked.connect(self._on_result_clicked)

        layout.addLayout(header)
        layout.addWidget(self.results_list, 1)

    def display_results(self, results: list[SearchResult]) -> None:
        self.results_list.clear()
        if not results:
            self.status_label.setText("No results")
            return

        count = len(results)
        self.status_label.setText(f"{count} {'result' if count == 1 else 'results'}")
        for r in results:
            parts = [r.title]
            if r.duration:
                minutes, secs = divmod(r.duration, 60)
                parts.append(f"{minutes}:{secs:02d}")
            if r.uploader:
                parts.append(r.uploader)
            if r.source:
                parts.append(r.source)

            item = QListWidgetItem(" · ".join(parts))
            item.setData(Qt.UserRole, r)
            self.results_list.addItem(item)

    def set_status(self, text: str) -> None:
        self.status_label.setText(text)

    def _on_result_clicked(self, item: QListWidgetItem) -> None:
        result = item.data(Qt.UserRole)
        if result:
            self.result_selected.emit(result)
