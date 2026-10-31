from pathlib import Path

import pytest

from app.utils import paths as paths_module
from app.utils.paths import (
    find_bundled_tool,
    get_config_dir,
    get_data_dir,
    get_log_dir,
    get_tools_dir,
)
from app.utils.system import get_platform, sanitize_filename


class TestPaths:
    def test_data_dir(self) -> None:
        path = get_data_dir()
        assert isinstance(path, Path)
        assert "hate-downloader" in str(path).lower()

    def test_config_dir(self) -> None:
        path = get_config_dir()
        assert isinstance(path, Path)

    def test_log_dir(self) -> None:
        path = get_log_dir()
        assert isinstance(path, Path)

    def test_tools_dir(self) -> None:
        path = get_tools_dir()
        assert isinstance(path, Path)


class TestFindBundledTool:
    def test_missing_dir_returns_empty(self, tmp_path, monkeypatch) -> None:
        monkeypatch.setattr(paths_module, "get_tools_dir", lambda: tmp_path / "nope")
        assert find_bundled_tool("aria2c.exe", "aria2c") == ""

    def test_finds_nested_binary(self, tmp_path, monkeypatch) -> None:
        monkeypatch.setattr(paths_module, "get_tools_dir", lambda: tmp_path)
        nested = tmp_path / "aria2-1.37.0-win-64bit-build1"
        nested.mkdir()
        binary = nested / "aria2c.exe"
        binary.write_text("stub")
        assert find_bundled_tool("aria2c.exe", "aria2c") == str(binary)

    def test_case_insensitive_match(self, tmp_path, monkeypatch) -> None:
        monkeypatch.setattr(paths_module, "get_tools_dir", lambda: tmp_path)
        binary = tmp_path / "FFmpeg.exe"
        binary.write_text("stub")
        assert find_bundled_tool("ffmpeg.exe", "ffmpeg") == str(binary)


class TestSystem:
    @pytest.mark.parametrize(
        "input_name,expected",
        [
            ("normal_file.mp4", "normal_file.mp4"),
            ("file<with>bad:chars.mp4", "file_with_bad_chars.mp4"),
            ("file/with\\slashes|and?quotes*", "file_with_slashes_and_quotes_"),
            ("", "untitled"),
            ("  ", "untitled"),
        ],
    )
    def test_sanitize_filename(self, input_name: str, expected: str) -> None:
        result = sanitize_filename(input_name)
        assert result == expected

    def test_platform(self) -> None:
        platform = get_platform()
        assert platform in ("windows", "linux", "macos")
