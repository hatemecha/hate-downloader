from PySide6.QtCore import QEvent, QSize, Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.models.download_job import DownloadJob, JobStatus

_STATUS_TEXT = {
    JobStatus.PENDING: "Waiting",
    JobStatus.DOWNLOADING: "Downloading",
    JobStatus.POSTPROCESSING: "Processing",
    JobStatus.COMPLETED: "Done",
    JobStatus.FAILED: "Failed",
    JobStatus.CANCELLED: "Cancelled",
}

_STATUS_ROLE = {
    JobStatus.DOWNLOADING: "activeLabel",
    JobStatus.POSTPROCESSING: "warningLabel",
    JobStatus.COMPLETED: "successLabel",
    JobStatus.FAILED: "errorLabel",
}


def _status_text(status: JobStatus) -> str:
    return _STATUS_TEXT.get(status, status.value.capitalize())


class QueuePanel(QFrame):
    cancel_requested = Signal(int)
    retry_requested = Signal(int)
    open_folder_requested = Signal(str)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("queuePanel")
        self._rows: dict[int, dict] = {}
        self._order: list[int] = []
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(10)

        header = QHBoxLayout()
        title = QLabel("Queue")
        title.setObjectName("sectionTitle")
        header.addWidget(title)

        self.count_label = QLabel("0 items")
        self.count_label.setObjectName("muted")
        header.addWidget(self.count_label)
        header.addStretch()
        layout.addLayout(header)

        self.empty_label = QLabel("Nothing queued yet.")
        self.empty_label.setObjectName("muted")
        self.empty_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.empty_label)

        self.queue_list = QListWidget()
        self.queue_list.setObjectName("queueList")
        self.queue_list.setMinimumHeight(150)
        self.queue_list.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.queue_list.setWordWrap(True)
        self.queue_list.setFocusPolicy(Qt.NoFocus)
        self.queue_list.viewport().installEventFilter(self)
        layout.addWidget(self.queue_list, 1)
        self.queue_list.hide()

    def update_queue(self, jobs: list[DownloadJob]) -> None:
        ids = [j.id for j in jobs]
        if ids != self._order:
            self._rebuild(jobs)
        else:
            for job in jobs:
                self.update_job(job)
        count = len(jobs)
        self.count_label.setText(f"{count} {'item' if count == 1 else 'items'}")
        self.queue_list.setVisible(count > 0)
        self.empty_label.setVisible(count == 0)

    def update_job(self, job: DownloadJob) -> None:
        row = self._rows.get(job.id)
        if row is None:
            return

        row["status"].setText(_status_text(job.status))
        self._set_status_role(row["status"], job.status)

        details = " · ".join(
            part for part in (job.speed, f"ETA {job.eta}" if job.eta else "") if part
        )
        row["details"].setText(details)

        progress = row["progress"]
        if job.status == JobStatus.POSTPROCESSING:
            progress.setVisible(True)
            progress.setRange(0, 0)
        elif job.status == JobStatus.DOWNLOADING:
            progress.setVisible(True)
            progress.setRange(0, 100)
            progress.setValue(int(job.progress))
        else:
            progress.setVisible(False)

        error = row["error"]
        if job.status == JobStatus.FAILED and job.error_message:
            error.setVisible(True)
            error.setText(job.error_message)
            error.setToolTip(job.error_message)
        else:
            error.setVisible(False)

        self._update_buttons(row, job)

        widget = row.get("widget")
        item = row.get("item")
        if widget is not None and item is not None:
            self._apply_size_hint(item, widget)

    def _rebuild(self, jobs: list[DownloadJob]) -> None:
        self.queue_list.clear()
        self._rows.clear()
        self._order = [j.id for j in jobs]

        for job in jobs:
            widget, row = self._build_row(job)
            item = QListWidgetItem()
            self.queue_list.addItem(item)
            self.queue_list.setItemWidget(item, widget)
            row["widget"] = widget
            row["item"] = item
            self._rows[job.id] = row
            self._apply_size_hint(item, widget)

    def _apply_size_hint(self, item: QListWidgetItem, widget: QWidget) -> None:
        """Size rows to the real viewport width so wrapped titles aren't clipped."""
        width = self.queue_list.viewport().width()
        if width <= 0:
            item.setSizeHint(widget.sizeHint())
            return
        height = widget.heightForWidth(width)
        if height <= 0:
            height = widget.sizeHint().height()
        item.setSizeHint(QSize(width, height))

    def eventFilter(self, obj, event) -> bool:
        if obj is self.queue_list.viewport() and event.type() == QEvent.Resize:
            self._refresh_size_hints()
        return super().eventFilter(obj, event)

    def _refresh_size_hints(self) -> None:
        for row in self._rows.values():
            widget = row.get("widget")
            item = row.get("item")
            if widget is not None and item is not None:
                self._apply_size_hint(item, widget)

    def _build_row(self, job: DownloadJob) -> tuple[QWidget, dict]:
        widget = QFrame()
        widget.setObjectName("queueRow")
        info_layout = QVBoxLayout(widget)
        info_layout.setContentsMargins(2, 10, 2, 10)
        info_layout.setSpacing(5)

        title = QLabel(job.title or job.url[:70])
        title.setTextFormat(Qt.PlainText)
        title.setWordWrap(True)
        info_layout.addWidget(title)

        meta_row = QHBoxLayout()
        meta_row.setSpacing(6)

        status_label = QLabel(_status_text(job.status))
        self._set_status_role(status_label, job.status)
        meta_row.addWidget(status_label)

        details = QLabel(
            " · ".join(
                part for part in (job.speed, f"ETA {job.eta}" if job.eta else "") if part
            )
        )
        details.setObjectName("muted")
        meta_row.addWidget(details)
        meta_row.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setObjectName("ghostButton")
        cancel_btn.clicked.connect(
            lambda checked=False, jid=job.id: self.cancel_requested.emit(jid)
        )
        retry_btn = QPushButton("Retry")
        retry_btn.setObjectName("ghostButton")
        retry_btn.clicked.connect(lambda checked=False, jid=job.id: self.retry_requested.emit(jid))
        open_btn = QPushButton("Open folder")
        open_btn.setObjectName("ghostButton")
        open_btn.clicked.connect(lambda checked=False, jid=job.id: self._emit_open(jid))

        meta_row.addWidget(cancel_btn)
        meta_row.addWidget(retry_btn)
        meta_row.addWidget(open_btn)
        info_layout.addLayout(meta_row)

        progress = QProgressBar()
        progress.setMaximum(100)
        progress.setValue(int(job.progress))
        progress.setTextVisible(False)
        progress.setVisible(job.status in (JobStatus.DOWNLOADING, JobStatus.POSTPROCESSING))
        info_layout.addWidget(progress)

        error = QLabel("")
        error.setTextFormat(Qt.PlainText)
        error.setObjectName("errorLabel")
        error.setWordWrap(True)
        if job.status == JobStatus.FAILED and job.error_message:
            error.setText(job.error_message)
            error.setToolTip(job.error_message)
        else:
            error.setVisible(False)
        info_layout.addWidget(error)

        row = {
            "status": status_label,
            "details": details,
            "progress": progress,
            "error": error,
            "cancel": cancel_btn,
            "retry": retry_btn,
            "open": open_btn,
            "output_path": job.output_path,
        }
        self._update_buttons(row, job)
        return widget, row

    @staticmethod
    def _set_status_role(label: QLabel, status: JobStatus) -> None:
        label.setObjectName(_STATUS_ROLE.get(status, "muted"))
        label.style().unpolish(label)
        label.style().polish(label)

    def _update_buttons(self, row: dict, job: DownloadJob) -> None:
        row["output_path"] = job.output_path
        row["cancel"].setVisible(
            job.status in (JobStatus.DOWNLOADING, JobStatus.PENDING, JobStatus.POSTPROCESSING)
        )
        row["retry"].setVisible(job.status in (JobStatus.FAILED, JobStatus.CANCELLED))
        row["open"].setVisible(job.status == JobStatus.COMPLETED and bool(job.output_path))

    def _emit_open(self, job_id: int) -> None:
        row = self._rows.get(job_id)
        if row and row.get("output_path"):
            self.open_folder_requested.emit(row["output_path"])

    def clear(self) -> None:
        self.queue_list.clear()
        self._rows.clear()
        self._order = []
        self.count_label.setText("0 items")
        self.queue_list.hide()
        self.empty_label.show()
