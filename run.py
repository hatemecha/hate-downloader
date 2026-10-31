#!/usr/bin/env python3
import os
import sys
import traceback
from pathlib import Path


def _print(message: str) -> None:
    stream = sys.stdout or sys.stderr
    if stream is None:
        return
    try:
        stream.write(message + "\n")
        stream.flush()
    except OSError:
        pass


def _write_error_log(text: str) -> None:
    _print(text)
    try:
        if getattr(sys, "frozen", False):
            path = Path(sys.executable).resolve().parent / "hate-downloader-error.txt"
        else:
            path = Path.cwd() / "hate-downloader-error.txt"
        path.write_text(text, encoding="utf-8")
    except OSError:
        pass


def _configure_qt_platform() -> None:
    if os.environ.get("QT_QPA_PLATFORM"):
        return
    frozen = bool(getattr(sys, "frozen", False))
    if not frozen:
        os.environ["QT_QPA_PLATFORM"] = "offscreen"
        return
    if sys.platform.startswith("linux") and not os.environ.get("DISPLAY"):
        os.environ["QT_QPA_PLATFORM"] = "offscreen"


def self_test() -> None:
    """Import runtime dependencies without opening the GUI."""
    _configure_qt_platform()

    import httpx  # noqa: F401
    import pydantic  # noqa: F401
    import yt_dlp  # noqa: F401
    from PySide6.QtGui import QPixmap
    from PySide6.QtWidgets import QApplication
    from yt_dlp.extractor import gen_extractor_classes

    from app import __version__

    if len(gen_extractor_classes()) < 100:
        raise RuntimeError("yt-dlp extractors were not packaged")

    app = QApplication.instance() or QApplication([])
    from app.ui.icons import application_icon

    if application_icon().isNull():
        raise RuntimeError("Application icon was not packaged")
    icons = Path(__file__).resolve().parent / "app" / "assets" / "icons"
    for name in ("check.svg", "chevron-up.svg", "chevron-down.svg"):
        if QPixmap(str(icons / name)).isNull():
            raise RuntimeError(f"Interface icon was not packaged or cannot be rendered: {name}")
    app.quit()
    _print(f"Hate Downloader {__version__}: self-test passed")


def main() -> None:
    src = Path(__file__).resolve().parent
    if str(src) not in sys.path:
        sys.path.insert(0, str(src))

    try:
        if "--self-test" in sys.argv:
            self_test()
            return
        from app.main import run

        run()
    except ImportError as e:
        _write_error_log(
            f"Error: {e}\n"
            "Install Python dependencies with:\n"
            "  pip install -r requirements.txt\n"
            "On Linux, Qt also needs system libraries such as libegl1 and libxcb-cursor0.\n"
        )
        sys.exit(1)
    except Exception:
        _write_error_log(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    main()
