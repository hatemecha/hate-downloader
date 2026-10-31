"""Theme tokens and the application stylesheet.

The interface uses one graphite (or paper) neutral ramp and a single signal
red. Red marks the primary download action, the active section, the setup
banner and download progress. Nothing else is red.
"""

from pathlib import Path

THEMES = {
    "hate_dark": {
        "name": "Graphite",
        "colors": {
            "window": "#0f1012",
            "surface": "#15171a",
            "raised": "#1b1e22",
            "hover": "#23272c",
            "hairline": "#262a30",
            "hairline_strong": "#343941",
            "text": "#e8e9ea",
            "text_muted": "#9aa1a9",
            "text_faint": "#6c737c",
            "accent": "#e03e3e",
            "accent_hover": "#f05252",
            "accent_text": "#ffffff",
            "progress_bg": "#262a30",
            "success": "#7cc49a",
            "warning": "#d3aa62",
            "danger": "#e07a72",
            "check_bg": "#5b6067",
        },
    },
    "light": {
        "name": "Paper",
        "colors": {
            "window": "#f4f4f2",
            "surface": "#ffffff",
            "raised": "#ecece9",
            "hover": "#e3e3df",
            "hairline": "#d9d9d4",
            "hairline_strong": "#bfbfb8",
            "text": "#17181a",
            "text_muted": "#5b6067",
            "text_faint": "#858b92",
            "accent": "#d63a3a",
            "accent_hover": "#bd3131",
            "accent_text": "#ffffff",
            "progress_bg": "#deded8",
            "success": "#2f7d55",
            "warning": "#8a6417",
            "danger": "#b03a33",
            "check_bg": "#5b6067",
        },
    },
}

_THEME_ALIASES = {
    "hate_dark": "hate_dark",
    "clean_dark": "hate_dark",
    "dark": "hate_dark",
    "light": "light",
    "paper": "light",
}


def resolve_theme(theme_name: str) -> str:
    return _THEME_ALIASES.get(theme_name, "hate_dark")


def get_stylesheet(theme_name: str) -> str:
    theme = THEMES[resolve_theme(theme_name)]
    c = theme["colors"]
    icons = Path(__file__).resolve().parent.parent / "assets/icons"
    check_icon = (icons / "check.svg").as_posix()
    up_icon = (icons / "chevron-up.svg").as_posix()
    down_icon = (icons / "chevron-down.svg").as_posix()

    return f"""
    QWidget {{
        color: {c["text"]};
        font-family: "Segoe UI", "Inter", "Noto Sans", sans-serif;
        font-size: 13px;
    }}
    QMainWindow, QDialog, QWidget#appRoot {{
        background-color: {c["window"]};
    }}
    QLabel {{
        background: transparent;
    }}
    QLabel#pageTitle {{
        font-size: 20px;
        font-weight: 500;
    }}
    QLabel#sectionTitle {{
        font-size: 13px;
        font-weight: 500;
    }}
    QLabel#cardTitle {{
        font-size: 15px;
        font-weight: 500;
    }}
    QLabel#muted {{
        color: {c["text_muted"]};
        font-size: 12px;
    }}
    QLabel#activeLabel {{
        color: {c["text"]};
        font-size: 12px;
        font-weight: 500;
    }}
    QLabel#faint {{
        color: {c["text_faint"]};
        font-size: 12px;
    }}
    QLabel#successLabel {{
        color: {c["success"]};
        font-size: 12px;
    }}
    QLabel#warningLabel {{
        color: {c["warning"]};
        font-size: 12px;
    }}
    QLabel#errorLabel {{
        color: {c["danger"]};
        font-size: 12px;
    }}
    QLabel#pathLabel {{
        color: {c["text_faint"]};
        font-family: "Cascadia Mono", "Consolas", monospace;
        font-size: 11px;
    }}
    QLineEdit, QTextEdit, QPlainTextEdit, QSpinBox, QDoubleSpinBox, QComboBox {{
        background-color: {c["raised"]};
        color: {c["text"]};
        border: 1px solid {c["hairline"]};
        border-radius: 6px;
        padding: 6px 10px;
        min-height: 20px;
        selection-background-color: {c["hairline_strong"]};
        selection-color: {c["text"]};
    }}
    QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus, QComboBox:focus,
    QSpinBox:focus, QDoubleSpinBox:focus {{
        border-color: {c["hairline_strong"]};
    }}
    QLineEdit:disabled, QComboBox:disabled, QSpinBox:disabled {{
        color: {c["text_faint"]};
    }}
    QComboBox::drop-down {{
        subcontrol-origin: padding;
        subcontrol-position: center right;
        width: 22px;
        border: none;
    }}
    QComboBox QAbstractItemView {{
        background-color: {c["surface"]};
        color: {c["text"]};
        border: 1px solid {c["hairline_strong"]};
        padding: 4px;
        outline: none;
    }}
    QComboBox QAbstractItemView::item {{
        padding: 6px 8px;
        border-radius: 4px;
    }}
    QComboBox QAbstractItemView::item:selected {{
        background-color: {c["hover"]};
        color: {c["text"]};
    }}
    QSpinBox::up-button, QSpinBox::down-button,
    QDoubleSpinBox::up-button, QDoubleSpinBox::down-button {{
        background: transparent;
        border: none;
        width: 18px;
    }}
    QSpinBox::up-button:hover, QSpinBox::down-button:hover,
    QDoubleSpinBox::up-button:hover, QDoubleSpinBox::down-button:hover {{
        background-color: {c["hover"]};
    }}
    QSpinBox::up-arrow, QDoubleSpinBox::up-arrow {{
        image: url("{up_icon}");
        width: 12px;
        height: 12px;
    }}
    QSpinBox::down-arrow, QDoubleSpinBox::down-arrow {{
        image: url("{down_icon}");
        width: 12px;
        height: 12px;
    }}
    QPushButton {{
        background-color: {c["raised"]};
        color: {c["text"]};
        border: 1px solid {c["hairline"]};
        border-radius: 6px;
        padding: 7px 14px;
        font-weight: 500;
        min-height: 20px;
    }}
    QPushButton:hover {{
        background-color: {c["hover"]};
        border-color: {c["hairline_strong"]};
    }}
    QPushButton:pressed {{
        background-color: {c["hairline"]};
    }}
    QPushButton:disabled {{
        color: {c["text_faint"]};
        background-color: {c["raised"]};
        border-color: {c["hairline"]};
    }}
    QPushButton#primaryButton {{
        background-color: {c["accent"]};
        color: {c["accent_text"]};
        border: 1px solid {c["accent"]};
        font-weight: 500;
    }}
    QPushButton#primaryButton:hover {{
        background-color: {c["accent_hover"]};
        border-color: {c["accent_hover"]};
    }}
    QPushButton#primaryButton:pressed {{
        background-color: {c["accent"]};
    }}
    QPushButton#primaryButton:disabled {{
        background-color: {c["raised"]};
        color: {c["text_faint"]};
        border-color: {c["hairline"]};
    }}
    QPushButton#strongButton {{
        border-color: {c["hairline_strong"]};
    }}
    QPushButton#ghostButton {{
        background: transparent;
        border: none;
        color: {c["text_muted"]};
        padding: 4px 8px;
        min-height: 0;
        font-weight: 400;
    }}
    QPushButton#ghostButton:hover {{
        background-color: {c["hover"]};
        color: {c["text"]};
    }}
    QPushButton#ghostButton:pressed {{
        background-color: {c["hairline"]};
    }}
    QFrame#urlPanel {{
        background-color: {c["window"]};
        border-bottom: 1px solid {c["hairline"]};
    }}
    QFrame#card, QFrame#resultCard, QFrame#queuePanel {{
        background-color: {c["surface"]};
        border: 1px solid {c["hairline"]};
        border-radius: 8px;
    }}
    QFrame#setupBanner {{
        background-color: {c["surface"]};
        border: 1px solid {c["hairline"]};
        border-left: 2px solid {c["accent"]};
        border-radius: 6px;
    }}
    QFrame#queueRow {{
        background: transparent;
        border-bottom: 1px solid {c["hairline"]};
    }}
    QLabel#thumbnailLabel {{
        background-color: {c["raised"]};
        border: 1px solid {c["hairline"]};
        border-radius: 6px;
        color: {c["text_faint"]};
        font-size: 12px;
    }}
    QGroupBox {{
        border: none;
        border-top: 1px solid {c["hairline"]};
        margin-top: 18px;
        padding-top: 12px;
        font-weight: 500;
    }}
    QGroupBox::title {{
        subcontrol-origin: margin;
        left: 0;
        padding: 0 4px 0 0;
        color: {c["text"]};
    }}
    QProgressBar {{
        background-color: {c["progress_bg"]};
        border: none;
        border-radius: 2px;
        min-height: 4px;
        max-height: 4px;
    }}
    QProgressBar::chunk {{
        background-color: {c["accent"]};
        border-radius: 2px;
    }}
    QListWidget, QTreeWidget {{
        background-color: {c["surface"]};
        border: 1px solid {c["hairline"]};
        border-radius: 8px;
        outline: none;
        padding: 4px;
    }}
    QListWidget::item, QTreeWidget::item {{
        padding: 8px 10px;
        border-bottom: 1px solid {c["hairline"]};
    }}
    QListWidget::item:hover, QTreeWidget::item:hover {{
        background-color: {c["hover"]};
    }}
    QListWidget::item:selected, QTreeWidget::item:selected {{
        background-color: {c["raised"]};
        color: {c["text"]};
    }}
    QListWidget#plainList, QListWidget#queueList {{
        background: transparent;
        border: none;
        padding: 0;
    }}
    QListWidget#queueList::item {{
        padding: 0;
        border: none;
    }}
    QListWidget#queueList::item:selected, QListWidget#queueList::item:hover {{
        background: transparent;
    }}
    QTabWidget::pane {{
        border: none;
        background: transparent;
    }}
    QTabBar {{
        background: transparent;
    }}
    QTabBar::tab {{
        background: transparent;
        color: {c["text_muted"]};
        border: none;
        border-bottom: 2px solid transparent;
        padding: 7px 12px;
        margin-right: 4px;
    }}
    QTabBar::tab:hover {{
        color: {c["text"]};
    }}
    QTabBar::tab:selected {{
        color: {c["text"]};
        border-bottom: 2px solid {c["accent"]};
    }}
    QScrollBar:vertical {{
        background: transparent;
        width: 8px;
        border: none;
        margin: 0;
    }}
    QScrollBar::handle:vertical {{
        background-color: {c["hairline_strong"]};
        border-radius: 4px;
        min-height: 28px;
    }}
    QScrollBar::handle:vertical:hover {{
        background-color: {c["text_faint"]};
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0;
    }}
    QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
        background: transparent;
    }}
    QScrollBar:horizontal {{
        background: transparent;
        height: 8px;
        border: none;
        margin: 0;
    }}
    QScrollBar::handle:horizontal {{
        background-color: {c["hairline_strong"]};
        border-radius: 4px;
        min-width: 28px;
    }}
    QScrollBar::handle:horizontal:hover {{
        background-color: {c["text_faint"]};
    }}
    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
        width: 0;
    }}
    QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{
        background: transparent;
    }}
    QCheckBox, QRadioButton {{
        color: {c["text"]};
        background: transparent;
        spacing: 8px;
    }}
    QCheckBox::indicator, QRadioButton::indicator {{
        width: 16px;
        height: 16px;
        border: 1px solid {c["hairline_strong"]};
        border-radius: 4px;
        background-color: {c["raised"]};
    }}
    QRadioButton::indicator {{
        border-radius: 8px;
    }}
    QCheckBox::indicator:hover, QRadioButton::indicator:hover {{
        border-color: {c["text_faint"]};
    }}
    QCheckBox::indicator:checked, QRadioButton::indicator:checked {{
        background-color: {c["check_bg"]};
        border-color: {c["check_bg"]};
    }}
    QCheckBox::indicator:checked {{
        image: url("{check_icon}");
    }}
    QMenuBar {{
        background-color: {c["window"]};
        border-bottom: 1px solid {c["hairline"]};
        padding: 2px 4px;
    }}
    QMenuBar::item {{
        padding: 5px 10px;
        background: transparent;
        border-radius: 4px;
    }}
    QMenuBar::item:selected {{
        background-color: {c["hover"]};
    }}
    QMenu {{
        background-color: {c["surface"]};
        border: 1px solid {c["hairline_strong"]};
        padding: 4px;
    }}
    QMenu::item {{
        padding: 6px 24px 6px 12px;
        border-radius: 4px;
    }}
    QMenu::item:selected {{
        background-color: {c["hover"]};
        color: {c["text"]};
    }}
    QMenu::separator {{
        height: 1px;
        background-color: {c["hairline"]};
        margin: 4px 8px;
    }}
    QStatusBar {{
        background-color: {c["window"]};
        border-top: 1px solid {c["hairline"]};
        color: {c["text_faint"]};
        font-size: 12px;
    }}
    QStatusBar::item {{
        border: none;
    }}
    QSplitter::handle {{
        background-color: {c["hairline"]};
    }}
    QSplitter::handle:horizontal {{
        width: 1px;
    }}
    QSplitter::handle:vertical {{
        height: 1px;
    }}
    QSplitter::handle:hover {{
        background-color: {c["hairline_strong"]};
    }}
    QToolTip {{
        background-color: {c["raised"]};
        color: {c["text"]};
        border: 1px solid {c["hairline_strong"]};
        padding: 5px 8px;
    }}
    QScrollArea, QScrollArea#plainScroll {{
        border: none;
        background: transparent;
    }}
    QScrollArea#plainScroll > QWidget > QWidget {{
        background: transparent;
    }}
    """
