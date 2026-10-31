from app.core.ffmpeg_service import FFmpegService


def test_detection_does_not_keep_stale_success(monkeypatch):
    service = FFmpegService("ffmpeg", "ffprobe")
    monkeypatch.setattr(service, "_find_tool", lambda name, path: name)
    monkeypatch.setattr("app.core.ffmpeg_service.run_command", lambda cmd: (0, "version", ""))
    assert service.detect() == (True, "version", "version")
    assert service.available
    monkeypatch.setattr("app.core.ffmpeg_service.run_command", lambda cmd: (1, "", "error"))
    assert service.detect() == (False, "", "")
    assert not service.available
