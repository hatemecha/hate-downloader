"""Render the main window (and a fake queue) to PNG files for visual checking."""

import sys
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QApplication, QTabWidget

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import __version__  # noqa: E402
from app.models.dependency_status import DependencyInfo, SystemStatus  # noqa: E402
from app.models.download_job import DownloadJob, JobStatus  # noqa: E402
from app.models.media_info import MediaFormat, MediaInfo  # noqa: E402
from app.ui.dependency_window import DependencyWindow  # noqa: E402
from app.ui.dialogs import ErrorDialog, WelcomeDialog  # noqa: E402
from app.ui.main_window import MainWindow  # noqa: E402
from app.ui.settings_window import SettingsWindow  # noqa: E402

OUT = Path(__file__).resolve().parents[1] / "_ui_snapshots"
OUT.mkdir(exist_ok=True)


def fake_jobs() -> list[DownloadJob]:
    now = datetime.now().isoformat()
    return [
        DownloadJob(
            id=1,
            url="https://example.com/1",
            title="A very long video title that should wrap onto multiple lines "
            "without being clipped in the queue panel",
            status=JobStatus.DOWNLOADING,
            progress=42.0,
            speed="3.2 MB/s",
            eta="00:41",
            created_at=now,
        ),
        DownloadJob(
            id=2,
            url="https://example.com/2",
            title="Failed item",
            status=JobStatus.FAILED,
            error_message="HTTP Error 403: Forbidden - the server refused the request",
            created_at=now,
        ),
        DownloadJob(
            id=3,
            url="https://example.com/3",
            title="Completed item",
            status=JobStatus.COMPLETED,
            output_path="C:/Downloads",
            created_at=now,
        ),
    ]


def main() -> None:
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    # Never read or modify the user's history/settings while rendering fixtures.
    sandbox = tempfile.TemporaryDirectory()
    from app.db.database import Database

    Database().close()
    db_patch = patch("app.db.database.get_db_path", return_value=Path(sandbox.name) / "ui.db")
    db_patch.start()
    with (
        patch.object(MainWindow, "_show_welcome_if_first_run"),
        patch.object(MainWindow, "_check_deps_async"),
    ):
        win = MainWindow()
    win.settings.first_run = False
    win.queue_panel.update_queue(fake_jobs())
    win.url_panel.set_advanced(False)
    win.show()

    def grab() -> None:
        win.resize(1100, 720)
        app.processEvents()
        win.grab().save(str(OUT / "main_default.png"))

        win.resize(900, 600)
        app.processEvents()
        win.grab().save(str(OUT / "main_min.png"))

        win.url_panel.set_advanced(True)
        app.processEvents()
        win.grab().save(str(OUT / "main_advanced.png"))

        win.url_panel.set_advanced(False)
        info = MediaInfo(
            url="https://example.com/watch?v=abc",
            title="Example video with a fairly long title to test wrapping in card",
            uploader="Example Channel",
            duration=754,
            extractor="youtube",
            formats=[
                MediaFormat(
                    format_id="137", ext="mp4", height=1080, has_video=True, filesize=210_000_000
                ),
                MediaFormat(format_id="140", ext="m4a", has_audio=True, filesize=12_000_000),
            ],
        )
        win.resize(1100, 720)
        win.result_card.display_info(info)
        app.processEvents()
        win.grab().save(str(OUT / "main_result.png"))

        dlg = SettingsWindow(win.settings, win)
        dlg.setStyleSheet(win.styleSheet())
        dlg.show()
        app.processEvents()
        tabs = dlg.findChild(QTabWidget)
        for index in range(tabs.count()):
            tabs.setCurrentIndex(index)
            app.processEvents()
            dlg.grab().save(str(OUT / f"settings_{tabs.tabText(index).lower()}.png"))
        dlg.close()

        with patch.object(DependencyWindow, "_check"):
            deps = DependencyWindow(win)
            deps.setStyleSheet(win.styleSheet())
            deps.show()
            deps._on_check_done(SystemStatus(
                dependencies=[
                    DependencyInfo(
                        name="Deno",
                        installed=False,
                        optional=False,
                        status_message="YouTube needs Deno 2.3+ or Node.js 22+. Install Deno here.",
                    ),
                    DependencyInfo(name="yt-dlp", installed=True, version="2026.08.19"),
                    DependencyInfo(
                        name="FFmpeg", installed=False, status_message="Needed for conversion"
                    ),
                ],
                app_version=__version__, python_version="3.13", platform="windows",
                download_folder="Downloads", download_folder_writable=True,
                can_download=True, can_convert=False, can_accelerate=False,
            ))
            app.processEvents()
            deps.grab().save(str(OUT / "dependencies.png"))
            deps.close()

        for theme in ("hate_dark", "light"):
            win.settings.theme = theme
            win._apply_theme()
            app.processEvents()
            win.grab().save(str(OUT / f"main_{theme}.png"))
        win.settings.theme = "hate_dark"
        win._apply_theme()

        win._on_deps_checked(SystemStatus(
            dependencies=[
                DependencyInfo(name="Deno", installed=False, optional=False),
                DependencyInfo(name="FFmpeg", installed=False, optional=False),
            ],
            app_version=__version__, platform="windows",
            download_folder="Downloads", download_folder_writable=True,
        ))
        app.processEvents()
        win.grab().save(str(OUT / "main_setup_banner.png"))
        win.setup_banner.hide()

        err = ErrorDialog(
            "Could not analyze the URL", "Traceback (most recent call last): ...", parent=win
        )
        err.setStyleSheet(win.styleSheet())
        err.show()
        app.processEvents()
        err.grab().save(str(OUT / "error_dialog.png"))
        err.close()

        wel = WelcomeDialog(win)
        wel.setStyleSheet(win.styleSheet())
        wel.show()
        app.processEvents()
        wel.grab().save(str(OUT / "welcome.png"))
        wel.close()

        app.quit()

    QTimer.singleShot(400, grab)
    app.exec()
    Database().close()
    db_patch.stop()
    sandbox.cleanup()


if __name__ == "__main__":
    main()
