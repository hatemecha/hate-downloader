import threading
from unittest.mock import MagicMock

import pytest
from PySide6.QtCore import Qt

from app.core.download_manager import DownloadManager, _parse_ratelimit
from app.models.download_job import DownloadJob, JobStatus


@pytest.mark.parametrize("value", ["-2M", "nan", "inf", "0", "bad"])
def test_invalid_rate_limits_do_not_reach_downloader(value):
    assert _parse_ratelimit(value) is None


@pytest.mark.parametrize(
    "result,cancel,status",
    [
        (0, False, JobStatus.COMPLETED),
        (1, False, JobStatus.FAILED),
        (0, True, JobStatus.CANCELLED),
    ],
)
def test_download_result_is_not_false_success(monkeypatch, tmp_path, result, cancel, status):
    monkeypatch.setattr("app.core.download_manager.DownloadsRepository", MagicMock)
    manager = DownloadManager()
    monkeypatch.setattr(manager, "_build_opts", lambda *_: {})
    ydl = MagicMock()
    ydl.download.return_value = result
    monkeypatch.setattr("app.core.download_manager.yt_dlp.YoutubeDL", lambda _: ydl)
    job = DownloadJob(id=1, url="https://example.com", folder=str(tmp_path))
    if cancel:
        manager._cancelled.add(1)
    manager._do_download(job)
    assert job.status == status
    assert manager.repo.complete.called == (status == JobStatus.COMPLETED)
    ydl.close.assert_called_once()


def test_single_download_never_ignores_errors(monkeypatch, tmp_path):
    monkeypatch.setattr("app.core.download_manager.DownloadsRepository", MagicMock)
    manager = DownloadManager()
    monkeypatch.setattr(manager, "_bundled_ffmpeg_location", lambda: "")
    manager.settings.ignoreerrors = True
    opts = manager._build_opts(DownloadJob(url="https://example.com"), tmp_path)
    assert opts["ignoreerrors"] is False
    assert opts["noprogress"] is True


def test_retry_does_not_duplicate_active_download(monkeypatch):
    monkeypatch.setattr("app.core.download_manager.DownloadsRepository", MagicMock)
    manager = DownloadManager()
    manager._queue.append(DownloadJob(id=1, status=JobStatus.DOWNLOADING))
    manager.retry_job(1)
    manager.repo.get_by_id.assert_not_called()


def test_postprocessing_observes_cancellation(monkeypatch):
    from app.core.download_manager import DownloadCancelled

    monkeypatch.setattr("app.core.download_manager.DownloadsRepository", MagicMock)
    manager = DownloadManager()
    manager._cancelled.add(1)
    with pytest.raises(DownloadCancelled):
        manager._postprocessor_hook(DownloadJob(id=1))({"status": "started"})


def test_cancelling_pending_job_allows_status_listener_to_read_queue(monkeypatch):
    monkeypatch.setattr("app.core.download_manager.DownloadsRepository", MagicMock)
    manager = DownloadManager()
    job = DownloadJob(id=1, status=JobStatus.PENDING)
    manager._queue.append(job)
    observed = []
    manager.status_changed.connect(
        lambda _: observed.extend(manager.get_queue()), Qt.DirectConnection
    )
    thread = threading.Thread(target=manager.cancel_job, args=(1,), daemon=True)
    thread.start()
    thread.join(timeout=2)
    assert not thread.is_alive(), "status listener deadlocked while reading the queue"
    assert observed == [job]
    assert job.status == JobStatus.CANCELLED


def test_advanced_audio_codec_replaces_preset_conversion(monkeypatch, tmp_path):
    monkeypatch.setattr("app.core.download_manager.DownloadsRepository", MagicMock)
    manager = DownloadManager()
    monkeypatch.setattr(manager, "_bundled_ffmpeg_location", lambda: "")
    job = DownloadJob(
        selected_preset="mp3_320",
        extra_opts={"postprocessors": [{"key": "FFmpegExtractAudio", "preferredcodec": "opus"}]},
    )
    processors = manager._build_opts(job, tmp_path)["postprocessors"]
    audio = [item for item in processors if item["key"] == "FFmpegExtractAudio"]
    assert audio == [{"key": "FFmpegExtractAudio", "preferredcodec": "opus"}]


def test_transient_progress_error_does_not_mark_job_failed(monkeypatch):
    monkeypatch.setattr("app.core.download_manager.DownloadsRepository", MagicMock)
    manager = DownloadManager()
    job = DownloadJob(id=1, status=JobStatus.DOWNLOADING)
    manager._progress_hook(job)({"status": "error", "msg": "retrying"})
    assert job.status == JobStatus.DOWNLOADING
    manager.repo.update_status.assert_not_called()


def test_terminal_status_is_emitted_after_worker_releases_its_slot(monkeypatch):
    monkeypatch.setattr("app.core.download_manager.DownloadsRepository", MagicMock)
    manager = DownloadManager()
    job = DownloadJob(id=1, status=JobStatus.DOWNLOADING)
    manager._active_count = 1
    monkeypatch.setattr(
        manager, "_do_download", lambda item: setattr(item, "status", JobStatus.FAILED)
    )
    observed = []
    manager.status_changed.connect(lambda _: observed.append(manager._active_count))
    manager._download_worker(job)
    assert observed == [0]


def test_thumbnail_file_is_not_written_by_default(monkeypatch, tmp_path):
    monkeypatch.setattr("app.core.download_manager.DownloadsRepository", MagicMock)
    manager = DownloadManager()
    manager.settings.writethumbnail = False
    manager.settings.embedthumbnail = False
    opts = manager._build_opts(DownloadJob(url="https://example.com"), tmp_path)
    assert "writethumbnail" not in opts


def test_embedding_uses_and_removes_a_temporary_thumbnail(monkeypatch, tmp_path):
    monkeypatch.setattr("app.core.download_manager.DownloadsRepository", MagicMock)
    manager = DownloadManager()
    manager.settings.writethumbnail = False
    manager.settings.embedthumbnail = True
    opts = manager._build_opts(DownloadJob(url="https://example.com"), tmp_path)
    embed = [pp for pp in opts["postprocessors"] if pp["key"] == "EmbedThumbnail"]
    assert opts["writethumbnail"] is True
    assert embed == [{"key": "EmbedThumbnail", "already_have_thumbnail": False}]


def test_embedding_keeps_the_thumbnail_when_the_user_asked_for_it(monkeypatch, tmp_path):
    monkeypatch.setattr("app.core.download_manager.DownloadsRepository", MagicMock)
    manager = DownloadManager()
    manager.settings.writethumbnail = True
    manager.settings.embedthumbnail = True
    opts = manager._build_opts(DownloadJob(url="https://example.com"), tmp_path)
    embed = [pp for pp in opts["postprocessors"] if pp["key"] == "EmbedThumbnail"]
    assert embed == [{"key": "EmbedThumbnail", "already_have_thumbnail": True}]
