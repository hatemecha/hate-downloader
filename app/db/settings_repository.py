import json
from typing import Any

from app.models.app_settings import AppSettings
from app.utils.logger import logger

from .database import Database

_THUMBNAIL_OPT_IN_KEY = "thumbnail_opt_in"


class SettingsRepository:
    def __init__(self) -> None:
        self.db = Database()

    def get(self, key: str, default: Any = "") -> Any:
        row = self.db.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
        if row is None:
            return default
        val = row["value"]
        try:
            return json.loads(val)
        except (json.JSONDecodeError, TypeError):
            return val

    def set(self, key: str, value: Any) -> None:
        val = json.dumps(value)
        self.db.execute(
            "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
            (key, val),
        )
        self.db.commit()

    def get_all_settings(self) -> dict[str, Any]:
        rows = self.db.execute("SELECT key, value FROM settings").fetchall()
        result = {}
        for row in rows:
            val = row["value"]
            try:
                result[row["key"]] = json.loads(val)
            except (json.JSONDecodeError, TypeError):
                result[row["key"]] = val
        return result

    def load_app_settings(self) -> AppSettings:
        settings = AppSettings()
        stored = self.get_all_settings()
        for key, value in stored.items():
            if key in AppSettings.model_fields:
                try:
                    validated = AppSettings.model_validate({key: value})
                    setattr(settings, key, getattr(validated, key))
                except (ValueError, TypeError) as e:
                    logger.warning("Invalid setting %s; using default (%s)", key, type(e).__name__)
        if not stored.get(_THUMBNAIL_OPT_IN_KEY):
            # Releases before 0.1.0 wrote a thumbnail file for every download.
            # Turn that off once; the user can opt in again in Settings.
            settings.writethumbnail = False
            self.set(_THUMBNAIL_OPT_IN_KEY, True)
        return settings

    def save_app_settings(self, settings: AppSettings) -> None:
        data = settings.model_dump()
        for key, value in data.items():
            self.set(key, value)
