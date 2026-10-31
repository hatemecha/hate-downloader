from app.models.app_settings import AppSettings
from app.models.dependency_status import DependencyInfo, SystemStatus
from app.models.download_job import DownloadJob, JobStatus
from app.models.media_info import MediaFormat, MediaInfo, Subtitle
from app.models.search_result import SearchResult


class TestDownloadJob:
    def test_default_status(self) -> None:
        job = DownloadJob(url="https://example.com/video")
        assert job.status == JobStatus.PENDING
        assert job.progress == 0.0

    def test_status_values(self) -> None:
        assert JobStatus.PENDING.value == "pending"
        assert JobStatus.COMPLETED.value == "completed"
        assert JobStatus.FAILED.value == "failed"


class TestMediaInfo:
    def test_create_media_info(self) -> None:
        info = MediaInfo(url="https://youtube.com/watch?v=test")
        assert info.url == "https://youtube.com/watch?v=test"
        assert info.formats == []
        assert info.subtitles == []

    def test_format_resolution(self) -> None:
        f = MediaFormat(format_id="test", ext="mp4", height=1080, width=1920)
        assert f.height == 1080
        assert f.width == 1920

    def test_subtitle(self) -> None:
        s = Subtitle(lang="en", name="English", auto_generated=True)
        assert s.lang == "en"
        assert s.auto_generated is True


class TestSearchResult:
    def test_create(self) -> None:
        r = SearchResult(title="Test", url="https://example.com", source="YouTube")
        assert r.title == "Test"
        assert r.source == "YouTube"


class TestAppSettings:
    def test_defaults(self) -> None:
        s = AppSettings()
        assert s.theme == "hate_dark"
        assert s.max_concurrent == 3
        assert s.first_run is True
        assert s.writethumbnail is False
        assert not hasattr(s, "noplaylist")


class TestDependencies:
    def test_dependency_info(self) -> None:
        d = DependencyInfo(name="FFmpeg", installed=True, version="6.0")
        assert d.installed is True
        assert d.version == "6.0"

    def test_system_status(self) -> None:
        status = SystemStatus()
        assert status.all_ok is False
        assert status.dependencies == []
