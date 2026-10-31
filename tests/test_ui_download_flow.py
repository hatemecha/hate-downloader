import os
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest
from PySide6.QtCore import QPoint
from PySide6.QtWidgets import QApplication

from app.db.database import Database
from app.models.download_job import JobStatus
from app.ui.main_window import MainWindow


@pytest.fixture(scope="module")
def qapp():
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    return QApplication.instance() or QApplication([])


def wait_until(app, predicate, timeout=15):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        app.processEvents()
        if predicate():
            return True
        time.sleep(0.02)
    return False


def test_analyze_and_download_direct_media_through_window(qapp, monkeypatch, tmp_path):
    payload = b"test media payload" * 100

    class Handler(BaseHTTPRequestHandler):
        def do_HEAD(self):
            self.send_response(200)
            self.send_header("Content-Type", "video/mp4")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()

        def do_GET(self):
            self.do_HEAD()
            self.wfile.write(payload)

        def log_message(self, *_args):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()
    db = Database()
    db.close()
    monkeypatch.setattr("app.db.database.get_db_path", lambda: tmp_path / "test.db")
    monkeypatch.setattr(MainWindow, "_show_welcome_if_first_run", lambda self: None)
    monkeypatch.setattr(MainWindow, "_check_deps_async", lambda self: None)
    window = MainWindow()
    window.settings.addmetadata = False
    window.settings.writethumbnail = False
    window.settings.default_folder = str(tmp_path / "downloads")
    window.result_card.set_download_folder(window.settings.default_folder)
    window.show()
    try:
        url = f"http://127.0.0.1:{server.server_port}/fixture.mp4"
        window.url_panel.input.setText(url)
        window.url_panel.analyze_btn.click()
        assert wait_until(qapp, lambda: window.result_card.get_media_info() is not None)
        window.result_card.download_btn.click()
        assert wait_until(qapp, lambda: bool(window.download_manager.get_queue()))
        assert wait_until(
            qapp,
            lambda: window.download_manager.get_queue()[0].status
            in (JobStatus.COMPLETED, JobStatus.FAILED),
        )
        job = window.download_manager.get_queue()[0]
        assert job.status == JobStatus.COMPLETED, job.error_message
        assert next((tmp_path / "downloads").glob("*.mp4")).read_bytes() == payload
        window.resize(900, 600)
        window.url_panel.set_advanced(True)
        qapp.processEvents()
        assert window.tabs.indexOf(window.search_panel) >= 0
        assert window.tabs.currentWidget() is window.format_selector
        combo = window.result_card.format_combo
        assert combo.height() >= combo.sizeHint().height()
        combo_bottom = combo.mapTo(window, QPoint(0, combo.height())).y()
        folder_top = window.result_card.folder_input.mapTo(window, QPoint(0, 0)).y()
        assert folder_top >= combo_bottom
        button = window.result_card.download_btn
        button_bottom = button.mapTo(window.result_card, QPoint(0, button.height())).y()
        assert button_bottom <= window.result_card.height()
        button_in_window = button.mapTo(window, QPoint(0, button.height())).y()
        tabs_top = window.tabs.mapTo(window, QPoint(0, 0)).y()
        assert button_in_window <= tabs_top
        window.url_panel.input.setText(url + "?new=1")
        assert window.result_card.get_media_info() is None
    finally:
        wait_until(qapp, lambda: not window.download_manager._active_count)
        window.close()
        db.close()
        server.shutdown()
        server.server_close()
        server_thread.join(timeout=2)
