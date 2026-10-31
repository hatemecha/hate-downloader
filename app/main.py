import sys

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication

from app import __version__
from app.ui.icons import application_icon
from app.ui.main_window import MainWindow
from app.utils.logger import logger


def run() -> None:
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    app = QApplication(sys.argv)
    app.setApplicationName("Hate Downloader")
    app.setOrganizationName("hate-downloader")
    app.setApplicationVersion(__version__)
    app.setWindowIcon(application_icon())
    if sys.platform == "win32":
        import ctypes

        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("hatemecha.HateDownloader")
    app.setStyle("Fusion")
    app.setFont(QFont("Segoe UI", 10))

    window = MainWindow()
    window.show()
    QTimer.singleShot(0, window._show_welcome_if_first_run)

    try:
        exit_code = app.exec()
    except Exception:
        logger.exception("Fatal error")
        exit_code = 1

    sys.exit(exit_code)


if __name__ == "__main__":
    run()
