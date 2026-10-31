import tempfile
from pathlib import Path

import pytest

from app.db.database import Database
from app.db.downloads_repository import DownloadsRepository
from app.db.migrations import run_migrations
from app.db.settings_repository import SettingsRepository
from app.models.download_job import DownloadJob, JobStatus


@pytest.fixture(autouse=True)
def setup_db(monkeypatch):
    with tempfile.TemporaryDirectory() as tmp:
        monkeypatch.setattr("app.db.database.get_db_path", lambda: Path(tmp) / "test.db")
        db = Database()
        db.close()
        run_migrations()
        yield
        db.close()


class TestDownloadsRepo:
    def test_add_and_get(self) -> None:
        repo = DownloadsRepository()
        job = DownloadJob(url="https://test.com", title="Test")
        job_id = repo.add(job)
        assert job_id > 0

        loaded = repo.get_by_id(job_id)
        assert loaded is not None
        assert loaded.url == "https://test.com"

    def test_update_status(self) -> None:
        repo = DownloadsRepository()
        job = DownloadJob(url="https://test.com", title="Test")
        job_id = repo.add(job)
        repo.update_status(job_id, JobStatus.COMPLETED)

        loaded = repo.get_by_id(job_id)
        assert loaded is not None
        assert loaded.status == JobStatus.COMPLETED

    def test_complete(self) -> None:
        repo = DownloadsRepository()
        job = DownloadJob(url="https://test.com", title="Test")
        job_id = repo.add(job)
        repo.complete(job_id, "/downloads/test.mp4")

        loaded = repo.get_by_id(job_id)
        assert loaded is not None
        assert loaded.status == JobStatus.COMPLETED
        assert loaded.output_path == "/downloads/test.mp4"
        assert loaded.progress == 100

    def test_delete_removes_one_row(self) -> None:
        repo = DownloadsRepository()
        keep_id = repo.add(DownloadJob(url="https://keep.com", title="Keep"))
        drop_id = repo.add(DownloadJob(url="https://drop.com", title="Drop"))

        repo.delete(drop_id)

        assert repo.get_by_id(drop_id) is None
        assert repo.get_by_id(keep_id) is not None

    def test_clear_history_removes_all_rows(self) -> None:
        repo = DownloadsRepository()
        repo.add(DownloadJob(url="https://a.com", title="A"))
        repo.add(DownloadJob(url="https://b.com", title="B"))

        repo.clear_history()

        assert repo.get_all() == []


class TestSettingsRepo:
    def test_legacy_thumbnail_setting_is_turned_off_once(self):
        repo = SettingsRepository()
        repo.set("writethumbnail", True)

        assert repo.load_app_settings().writethumbnail is False
        assert repo.get("thumbnail_opt_in") is True

        # A deliberate opt-in after the migration must be preserved.
        repo.set("writethumbnail", True)
        assert repo.load_app_settings().writethumbnail is True

    def test_invalid_saved_values_fall_back_without_crashing(self):
        repo = SettingsRepository()
        repo.set("max_concurrent", 0)
        repo.set("default_folder", None)
        repo.set("continuedl", "false")
        loaded = repo.load_app_settings()
        assert loaded.max_concurrent == 3
        assert loaded.default_folder == ""
        assert loaded.continuedl is False

    def test_set_and_get(self) -> None:
        repo = SettingsRepository()
        repo.set("theme", "dark")
        assert repo.get("theme") == "dark"

    @pytest.mark.parametrize("value", ["123", "true", "null", '"quoted"'])
    def test_string_settings_round_trip_without_json_coercion(self, value):
        repo = SettingsRepository()
        repo.set("default_folder", value)
        assert repo.get("default_folder") == value
        assert repo.load_app_settings().default_folder == value

    def test_get_default(self) -> None:
        repo = SettingsRepository()
        assert repo.get("nonexistent", "default") == "default"

    def test_overwrite(self) -> None:
        repo = SettingsRepository()
        repo.set("key", "value1")
        repo.set("key", "value2")
        assert repo.get("key") == "value2"
