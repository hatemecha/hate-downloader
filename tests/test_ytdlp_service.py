import sys

import pytest

from app.core.ytdlp_service import YtDlpService, js_runtime_options


def test_bundled_deno_is_passed_to_ytdlp(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.core.ytdlp_service.find_bundled_tool",
        lambda *names: "/tools/deno" if "deno" in names else "",
    )
    assert js_runtime_options()["deno"] == {"path": "/tools/deno"}


def test_js_runtimes_fall_back_to_path_lookup(monkeypatch) -> None:
    monkeypatch.setattr("app.core.ytdlp_service.find_bundled_tool", lambda *names: "")
    assert js_runtime_options() == {"deno": {}, "node": {}}


def test_frozen_app_does_not_try_to_run_pip(monkeypatch) -> None:
    monkeypatch.setattr(sys, "frozen", True, raising=False)

    ok, message = YtDlpService().update_ytdlp()

    assert not ok
    assert "newer Hate Downloader release" in message


def test_parse_media_info_maps_formats_and_subs() -> None:
    raw = {
        "title": "Hello",
        "webpage_url": "https://example.com/v",
        "original_url": "https://example.com/v",
        "duration": 12,
        "uploader": "Chan",
        "formats": [
            {
                "format_id": "137",
                "ext": "mp4",
                "height": 1080,
                "vcodec": "avc1",
                "acodec": "none",
            },
            {
                "format_id": "140",
                "ext": "m4a",
                "vcodec": "none",
                "acodec": "mp4a",
            },
        ],
        "subtitles": {"en": [{"name": "English"}]},
    }
    info = YtDlpService().parse_media_info(raw)
    assert info.title == "Hello"
    assert info.formats[0].has_video is True
    assert info.formats[0].has_audio is False
    assert info.formats[1].has_audio is True
    assert info.subtitles[0].lang == "en"
    assert info.is_playlist is False


@pytest.mark.parametrize("duration", [12.75, None, 0])
def test_media_accepts_fractional_duration_and_null_metadata(duration):
    info = YtDlpService().parse_media_info(
        {
            "webpage_url": "https://example.com/video",
            "duration": duration,
            "thumbnail": None,
            "vcodec": None,
            "acodec": None,
            "dynamic_range": None,
            "title": None,
            "protocol": None,
        }
    )
    assert info.duration == int(duration or 0)
    assert info.thumbnail == ""
