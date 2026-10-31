from pathlib import Path

from PySide6.QtGui import QIcon


def application_icon() -> QIcon:
    return QIcon(str(Path(__file__).resolve().parents[1] / "assets" / "icons" / "icon.png"))
