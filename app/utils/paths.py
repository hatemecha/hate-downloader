import os
from pathlib import Path

from platformdirs import user_config_dir, user_data_dir, user_log_dir

APP_NAME = "hate-downloader"
APP_AUTHOR = "hate-downloader"


def _custom_home() -> Path | None:
    path = os.environ.get("HATE_DOWNLOADER_HOME", "").strip()
    return Path(path).expanduser() if path else None


def get_data_dir() -> Path:
    if home := _custom_home():
        return home / "data"
    return Path(user_data_dir(APP_NAME, APP_AUTHOR))


def get_config_dir() -> Path:
    if home := _custom_home():
        return home / "config"
    return Path(user_config_dir(APP_NAME, APP_AUTHOR))


def get_log_dir() -> Path:
    if home := _custom_home():
        return home / "logs"
    return Path(user_log_dir(APP_NAME, APP_AUTHOR))


def get_tools_dir() -> Path:
    return get_data_dir() / "tools"


def find_bundled_tool(*names: str) -> str:
    """Search the app-managed tools directory for a downloaded binary.

    Tools downloaded through the Dependencies window are extracted (often into
    a nested folder) under ``get_tools_dir()``. Detection needs to look here,
    not just on PATH, otherwise a freshly downloaded tool stays invisible.
    """
    tools = get_tools_dir()
    if not tools.exists():
        return ""
    wanted = {n.lower() for n in names}
    for f in tools.rglob("*"):
        if f.is_file() and f.name.lower() in wanted:
            return str(f)
    return ""


def get_db_path() -> Path:
    return get_data_dir() / "hate-downloader.db"


def get_default_download_dir() -> Path:
    if home := _custom_home():
        return home / "downloads"
    return Path.home() / "Downloads" / "HateDownloader"


def ensure_dirs() -> None:
    for d in [get_data_dir(), get_config_dir(), get_log_dir(), get_tools_dir()]:
        d.mkdir(parents=True, exist_ok=True)
