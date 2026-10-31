from app.utils import paths


def test_custom_home_isolates_user_data_and_downloads(monkeypatch, tmp_path):
    monkeypatch.setenv("HATE_DOWNLOADER_HOME", str(tmp_path))
    assert paths.get_data_dir() == tmp_path / "data"
    assert paths.get_config_dir() == tmp_path / "config"
    assert paths.get_log_dir() == tmp_path / "logs"
    assert paths.get_default_download_dir() == tmp_path / "downloads"
    assert paths.get_tools_dir() == tmp_path / "data" / "tools"
