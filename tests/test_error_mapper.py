from app.core.error_mapper import classify_error


def test_private_video() -> None:
    err = classify_error(Exception("This video is private"))
    assert err.message == "This video is private."
    assert "cookies" in err.action.lower()


def test_ffmpeg_missing() -> None:
    err = classify_error(Exception("ffmpeg not found"))
    assert "FFmpeg" in err.message


def test_unsupported_url() -> None:
    err = classify_error(Exception("Unsupported URL"))
    assert err.message == "Unsupported URL."


def test_unexpected_keeps_detail() -> None:
    err = classify_error(RuntimeError("weird boom"))
    assert err.message == "An unexpected error occurred."
    assert err.detail == "weird boom"


def test_http_error_keeps_server_response():
    err = classify_error(Exception("HTTP Error 403: Forbidden"))
    assert "server" in err.message
    assert "403" in err.detail
    assert err.action
