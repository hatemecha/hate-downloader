from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
)


class WelcomeDialog(QDialog):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Hate Downloader")
        self.setMinimumSize(480, 380)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(10)

        title = QLabel("Hate Downloader")
        title.setObjectName("pageTitle")

        subtitle = QLabel("Search, analyze, and download public media.")
        subtitle.setObjectName("muted")

        features = QLabel(
            "YouTube and other yt-dlp sites\n"
            "Internet Archive\n"
            "Direct media links on web pages"
        )
        features.setObjectName("muted")

        steps = QLabel(
            "Paste a link and press Analyze\n"
            "Pick a quality\n"
            "Press Download and watch the queue"
        )
        steps.setObjectName("faint")

        note = QLabel("Public media only. No DRM, paywalls, or private access.")
        note.setObjectName("faint")
        note.setWordWrap(True)

        self.dont_show = QCheckBox("Don't show this again")

        buttons = QHBoxLayout()
        buttons.addStretch()
        start_btn = QPushButton("Start")
        start_btn.setObjectName("strongButton")
        start_btn.setMinimumHeight(36)
        start_btn.clicked.connect(self.accept)
        buttons.addWidget(start_btn)

        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addSpacing(8)
        layout.addWidget(features)
        layout.addSpacing(8)
        layout.addWidget(steps)
        layout.addStretch()
        layout.addWidget(note)
        layout.addWidget(self.dont_show)
        layout.addSpacing(4)
        layout.addLayout(buttons)


class ErrorDialog(QDialog):
    def __init__(self, message: str, detail: str = "", action: str = "", parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Something went wrong")
        self.setMinimumWidth(480)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        msg_label = QLabel(message)
        msg_label.setObjectName("cardTitle")
        msg_label.setWordWrap(True)
        layout.addWidget(msg_label)

        self.detail_text = QTextEdit()
        self.detail_text.setPlainText(detail)
        self.detail_text.setReadOnly(True)
        self.detail_text.setMaximumHeight(140)
        self.detail_text.hide()

        if detail:
            toggle = QPushButton("Show details")
            toggle.setObjectName("ghostButton")
            toggle.clicked.connect(self._toggle_details)
            layout.addWidget(toggle, 0, Qt.AlignLeft)
            layout.addWidget(self.detail_text)

        layout.addStretch()

        buttons = QHBoxLayout()
        buttons.addStretch()
        if action:
            action_btn = QPushButton(action)
            action_btn.setObjectName("strongButton")
            action_btn.clicked.connect(self.accept)
            buttons.addWidget(action_btn)

        close_btn = QPushButton("Close")
        close_btn.setObjectName("ghostButton")
        close_btn.clicked.connect(self.reject)
        buttons.addWidget(close_btn)
        layout.addLayout(buttons)

    def _toggle_details(self) -> None:
        visible = not self.detail_text.isVisible()
        self.detail_text.setVisible(visible)
        self.sender().setText("Hide details" if visible else "Show details")


class ConfirmDialog(QDialog):
    def __init__(
        self,
        title: str,
        message: str,
        confirm_text: str = "Confirm",
        cancel_text: str = "Cancel",
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumWidth(420)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        msg = QLabel(message)
        msg.setWordWrap(True)
        layout.addWidget(msg)
        layout.addStretch()

        buttons = QHBoxLayout()
        buttons.setSpacing(8)
        buttons.addStretch()
        cancel_btn = QPushButton(cancel_text)
        cancel_btn.setObjectName("ghostButton")
        cancel_btn.clicked.connect(self.reject)
        confirm_btn = QPushButton(confirm_text)
        confirm_btn.setObjectName("strongButton")
        confirm_btn.clicked.connect(self.accept)

        buttons.addWidget(cancel_btn)
        buttons.addWidget(confirm_btn)
        layout.addLayout(buttons)
