import os
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from PySide6.QtWidgets import QApplication

from app.models.media_info import MediaFormat, MediaInfo
from app.ui.format_selector import FormatSelector
from app.ui.main_window import MainWindow
from app.ui.result_card import ResultCard


@pytest.fixture(scope="module")
def qapp():
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    return QApplication.instance() or QApplication([])


def test_default_settings_do_not_override_globals(qapp) -> None:
    selector = FormatSelector()
    settings = selector.get_settings()
    assert "vcodec" not in settings
    assert "embedthumbnail" not in settings
    assert "addmetadata" not in settings
    assert "writesubtitles" not in settings
    assert "postprocessors" not in settings


def test_codec_and_resolution_use_format_sort(qapp) -> None:
    selector = FormatSelector()
    selector.vcodec_combo.setCurrentText("h264")
    selector.resolution_combo.setCurrentText("1080p")
    selector.container_combo.setCurrentText("mkv")
    settings = selector.get_settings()
    assert settings["format_sort"] == ["vcodec:h264", "res:1080"]
    assert settings["merge_output_format"] == "mkv"


def test_audio_and_embed_become_postprocessors(qapp) -> None:
    selector = FormatSelector()
    selector.acodec_combo.setCurrentText("mp3")
    selector.quality_combo.setCurrentText("192")
    selector.embed_thumb_check.setChecked(True)
    selector.metadata_check.setChecked(True)
    settings = selector.get_settings()
    keys = [pp["key"] for pp in settings["postprocessors"]]
    assert keys == ["FFmpegExtractAudio", "EmbedThumbnail", "FFmpegMetadata"]
    embed = settings["postprocessors"][1]
    assert embed["already_have_thumbnail"] is False
    assert settings["postprocessors"][0]["preferredquality"] == "192"
    # yt-dlp needs a temporary image on disk to embed, then deletes it.
    assert settings["writethumbnail"] is True


def test_keeping_the_thumbnail_is_explicit(qapp) -> None:
    selector = FormatSelector()
    selector.thumbnail_check.setChecked(True)
    selector.embed_thumb_check.setChecked(True)
    settings = selector.get_settings()
    embed = [pp for pp in settings["postprocessors"] if pp["key"] == "EmbedThumbnail"]
    assert embed == [{"key": "EmbedThumbnail", "already_have_thumbnail": True}]
    assert settings["writethumbnail"] is True


def test_simple_mode_clears_exact_format_and_filters_quality(qapp):
    card = ResultCard()
    card.display_info(
        MediaInfo(
            url="https://example.com",
            formats=[
                MediaFormat(format_id="v", ext="mp4", height=720, has_video=True, has_audio=True)
            ],
        )
    )
    assert card.preset_combo.findData("1080p_mp4") == -1
    assert card.preset_combo.findData("720p_mp4") >= 0
    card.set_advanced(True)
    card.format_combo.setCurrentIndex(1)
    assert card.get_selected_format()
    card.set_advanced(False)
    assert card.get_selected_format() == ""


def test_audio_media_does_not_offer_video_and_playlist_cannot_download(qapp):
    card = ResultCard()
    card.display_info(
        MediaInfo(
            url="https://example.com",
            formats=[MediaFormat(format_id="a", ext="m4a", has_audio=True)],
        )
    )
    assert card.preset_combo.findData("best_mp4") == -1
    assert card.preset_combo.findData("mp3_192") >= 0
    card.display_info(MediaInfo(url="https://example.com", is_playlist=True))
    assert not card.download_btn.isEnabled()


def test_direct_download_can_be_queued_without_ffmpeg(qapp, tmp_path):
    card = Mock()
    card.get_media_info.return_value = MediaInfo(url="https://example.com/video.mp4")
    card.get_selected_preset.return_value = "best_mp4"
    card.get_selected_format.return_value = ""
    card.get_download_folder.return_value = str(tmp_path)
    window = SimpleNamespace(
        result_card=card,
        settings=SimpleNamespace(default_folder=""),
        _advanced_opts=lambda: {},
        _start_download=Mock(),
    )
    MainWindow._on_download_result(window)
    assert window._start_download.call_args.args[0].url == "https://example.com/video.mp4"
