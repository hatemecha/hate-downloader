import math
import threading
from pathlib import Path
from typing import Any, Optional

import yt_dlp
from PySide6.QtCore import QObject, Signal

from app.core.aria2_service import Aria2Service
from app.core.error_mapper import classify_error
from app.core.ffmpeg_service import FFmpegService
from app.core.ytdlp_service import PRESETS, js_runtime_options
from app.db.downloads_repository import DownloadsRepository
from app.models.app_settings import AppSettings
from app.models.download_job import DownloadJob, JobStatus
from app.utils.logger import logger

try:
    from yt_dlp.utils import DownloadCancelled
except ImportError:  # pragma: no cover - very old yt-dlp

    class DownloadCancelled(Exception):
        pass


_ALLOWED_EXTRA_OPTS = {
    "format_sort",
    "merge_output_format",
    "writesubtitles",
    "writeautomaticsub",
    "subtitleslangs",
    "writethumbnail",
}


def _parse_ratelimit(value: str) -> Optional[float]:
    value = (value or "").strip().upper()
    if not value:
        return None
    multipliers = {"K": 1024, "M": 1024**2, "G": 1024**3}
    try:
        if value[-1] in multipliers:
            rate = float(value[:-1]) * multipliers[value[-1]]
        else:
            rate = float(value)
        return rate if math.isfinite(rate) and rate > 0 else None
    except (ValueError, IndexError):
        return None


class DownloadManager(QObject):
    progress_updated = Signal(object)
    status_changed = Signal(object)
    queue_changed = Signal(object)

    def __init__(self, settings: Optional[AppSettings] = None) -> None:
        super().__init__()
        self.repo = DownloadsRepository()
        self.aria2 = Aria2Service()
        self.settings = settings or AppSettings()
        self._active: dict[int, yt_dlp.YoutubeDL] = {}
        self._cancelled: set[int] = set()
        self._queue: list[DownloadJob] = []
        self._max_concurrent = self.settings.max_concurrent
        self._lock = threading.Lock()
        self._active_count = 0

    def set_settings(self, settings: AppSettings) -> None:
        self.settings = settings
        self.set_max_concurrent(settings.max_concurrent)

    def set_max_concurrent(self, n: int) -> None:
        with self._lock:
            self._max_concurrent = max(1, n)
        self._process_queue()

    def _emit_queue(self) -> None:
        self.queue_changed.emit(self.get_queue())

    def add_to_queue(self, job: DownloadJob) -> int:
        job_id = self.repo.add(job)
        job.id = job_id
        with self._lock:
            self._queue.append(job)
        self._emit_queue()
        self._process_queue()
        return job_id

    def _process_queue(self) -> None:
        with self._lock:
            if self._active_count >= self._max_concurrent:
                return
            pending = [j for j in self._queue if j.status == JobStatus.PENDING and j.id > 0]
            if not pending:
                return

            for job in pending[: self._max_concurrent - self._active_count]:
                job.status = JobStatus.DOWNLOADING
                self._active_count += 1
                thread = threading.Thread(
                    target=self._download_worker,
                    args=(job,),
                    daemon=True,
                )
                thread.start()

    def _download_worker(self, job: DownloadJob) -> None:
        try:
            self._do_download(job)
        except Exception as e:
            logger.error(f"Download worker error: {e}")
            job.status = JobStatus.FAILED
            mapped = classify_error(e)
            job.error_message = " ".join(
                filter(None, (mapped.message, mapped.action, mapped.detail))
            )
            self.repo.fail(job.id, job.error_message)
        finally:
            with self._lock:
                self._active_count -= 1
            self.status_changed.emit(job)
            self._process_queue()

    def _progress_hook(self, job: DownloadJob) -> Any:
        def hook(d: dict[str, Any]) -> None:
            if job.id in self._cancelled:
                raise DownloadCancelled(f"Cancelled job {job.id}")

            status = d.get("status", "")
            if status == "downloading":
                if job.status != JobStatus.DOWNLOADING:
                    job.status = JobStatus.DOWNLOADING
                    self.status_changed.emit(job)
                total = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
                downloaded = d.get("downloaded_bytes", 0)
                if total > 0:
                    job.progress = round(downloaded / total * 100, 1)
                speed = d.get("speed", 0)
                job.speed = self._format_speed(speed) if speed else ""
                eta_val = d.get("eta", 0)
                job.eta = self._format_eta(eta_val) if eta_val else ""
                self.repo.update_progress(job.id, job.progress, job.speed, job.eta)
                self.progress_updated.emit(job)

            elif status == "finished":
                job.progress = 100.0
                job.speed = ""
                job.eta = ""
                self.repo.update_progress(job.id, job.progress)
                self.progress_updated.emit(job)

        return hook

    def _postprocessor_hook(self, job: DownloadJob) -> Any:
        def hook(d: dict[str, Any]) -> None:
            if job.id in self._cancelled:
                raise DownloadCancelled(f"Cancelled job {job.id}")
            if d.get("status") == "started" and job.status != JobStatus.POSTPROCESSING:
                job.status = JobStatus.POSTPROCESSING
                self.repo.update_status(job.id, JobStatus.POSTPROCESSING, job.progress)
                self.status_changed.emit(job)

        return hook

    def _build_opts(self, job: DownloadJob, output_dir: Path) -> dict[str, Any]:
        preset = PRESETS.get(job.selected_preset) or PRESETS["best_mp4"]
        s = self.settings

        template = s.filename_template or "%(title)s.%(ext)s"
        opts: dict[str, Any] = {
            "outtmpl": str(output_dir / template),
            "format": job.format_spec or job.selected_format or preset["format"],
            "progress_hooks": [self._progress_hook(job)],
            "postprocessor_hooks": [self._postprocessor_hook(job)],
            "quiet": True,
            "noprogress": True,
            "js_runtimes": js_runtime_options(),
            "no_warnings": True,
            "continuedl": s.continuedl,
            "ignoreerrors": False,
            # Single-item download is the supported flow; never expand a
            # video's mix/radio/playlist (e.g. ?list=RD...) into many jobs.
            "noplaylist": True,
            "retries": s.retries,
            "fragment_retries": s.fragment_retries,
            "socket_timeout": s.socket_timeout,
            "concurrent_fragment_downloads": max(1, s.concurrent_fragments),
        }

        if preset.get("merge_output_format"):
            opts["merge_output_format"] = preset["merge_output_format"]
        if job.selected_preset.endswith("_mp4"):
            opts["format_sort"] = ["vcodec:h264", "acodec:aac"]

        postprocessors: list[dict[str, Any]] = []
        if preset.get("postprocessors"):
            postprocessors.extend(preset["postprocessors"])

        rate = _parse_ratelimit(s.ratelimit)
        if rate:
            opts["ratelimit"] = rate

        if s.cookiefile:
            opts["cookiefile"] = s.cookiefile
        if s.cookies_from_browser:
            opts["cookiesfrombrowser"] = (s.cookies_from_browser,)

        if s.writesubtitles:
            opts["writesubtitles"] = True
        if s.writeautomaticsub:
            opts["writeautomaticsub"] = True
        if (s.writesubtitles or s.writeautomaticsub) and s.subtitleslangs:
            opts["subtitleslangs"] = [
                lang.strip() for lang in s.subtitleslangs.split(",") if lang.strip()
            ]
        if s.embedsubtitles:
            postprocessors.append({"key": "FFmpegEmbedSubtitle"})

        # Keep the thumbnail file only when the user asked for one. Embedding
        # still needs the image on disk, so yt-dlp gets a temporary one and the
        # postprocessor deletes it right after embedding.
        if s.writethumbnail:
            opts["writethumbnail"] = True
        if s.embedthumbnail:
            postprocessors.append(
                {
                    "key": "EmbedThumbnail",
                    "already_have_thumbnail": bool(s.writethumbnail),
                }
            )
            if not s.writethumbnail:
                opts["writethumbnail"] = True

        if s.addmetadata:
            postprocessors.append({"key": "FFmpegMetadata"})

        if s.download_archive:
            opts["download_archive"] = s.download_archive

        if postprocessors:
            opts["postprocessors"] = postprocessors

        if s.use_aria2c:
            if s.aria2c_path:
                self.aria2 = Aria2Service(s.aria2c_path)
            available, _ = self.aria2.detect()
            if available:
                opts.update(self.aria2.get_ydl_opts())
            else:
                logger.warning("aria2c requested but not found; using default downloader")

        ffmpeg_location = s.ffmpeg_path or self._bundled_ffmpeg_location()
        if ffmpeg_location:
            opts["ffmpeg_location"] = ffmpeg_location

        if job.extra_opts:
            extra = dict(job.extra_opts)
            extra_pp = extra.pop("postprocessors", None)
            for key in list(extra):
                if key not in _ALLOWED_EXTRA_OPTS:
                    extra.pop(key)
            opts.update(extra)
            if extra_pp:
                extra_keys = {pp.get("key") for pp in extra_pp}
                opts["postprocessors"] = [
                    pp for pp in postprocessors if pp.get("key") not in extra_keys
                ] + list(extra_pp)

        return opts

    @staticmethod
    def _bundled_ffmpeg_location() -> str:
        """Return an absolute ffmpeg path only when it lives in our tools dir.

        yt-dlp already finds ffmpeg on PATH, so we only need to hand it a
        location for a binary downloaded through the Dependencies window.
        """
        ffmpeg = FFmpegService()
        ffmpeg.detect()
        path = ffmpeg.ffmpeg_path
        if path and Path(path).is_absolute() and Path(path).exists():
            return path
        return ""

    def _do_download(self, job: DownloadJob) -> None:
        output_dir = (
            Path(job.folder) if job.folder else Path.home() / "Downloads" / "HateDownloader"
        )
        output_dir.mkdir(parents=True, exist_ok=True)

        opts = self._build_opts(job, output_dir)

        ydl = yt_dlp.YoutubeDL(opts)
        self._active[job.id] = ydl

        try:
            self.repo.update_status(job.id, JobStatus.DOWNLOADING)
            self.status_changed.emit(job)
            result = ydl.download([job.url])
            if result:
                raise RuntimeError("Download failed. Retry or analyze the link again.")
            if job.id in self._cancelled:
                raise DownloadCancelled(f"Cancelled job {job.id}")
            job.status = JobStatus.COMPLETED
            job.progress = 100.0
            job.output_path = str(output_dir)
            self.repo.complete(job.id, job.output_path)
        except DownloadCancelled:
            job.status = JobStatus.CANCELLED
            self.repo.update_status(job.id, JobStatus.CANCELLED)
        except Exception as e:
            logger.exception("Download failed for job %s", job.id)
            mapped = classify_error(e)
            job.status = JobStatus.FAILED
            job.error_message = " ".join(
                filter(None, (mapped.message, mapped.action, mapped.detail))
            )
            self.repo.fail(job.id, job.error_message)
        finally:
            ydl.close()
            self._active.pop(job.id, None)
            self._cancelled.discard(job.id)

    def cancel_job(self, job_id: int) -> None:
        cancelled_pending = None
        with self._lock:
            target = None
            for job in self._queue:
                if job.id == job_id:
                    target = job
                    break
            if target is None:
                return

            if target.status == JobStatus.PENDING:
                target.status = JobStatus.CANCELLED
                self.repo.update_status(job_id, JobStatus.CANCELLED)
                cancelled_pending = target
            elif target.status in (JobStatus.DOWNLOADING, JobStatus.POSTPROCESSING):
                self._cancelled.add(job_id)
        if cancelled_pending is not None:
            self.status_changed.emit(cancelled_pending)
        self._emit_queue()
        self._process_queue()

    def cancel_all(self) -> None:
        cancelled: list[DownloadJob] = []
        with self._lock:
            for job in self._queue:
                if job.status == JobStatus.PENDING:
                    job.status = JobStatus.CANCELLED
                    self.repo.update_status(job.id, JobStatus.CANCELLED)
                    cancelled.append(job)
                elif job.status in (JobStatus.DOWNLOADING, JobStatus.POSTPROCESSING):
                    self._cancelled.add(job.id)
        for job in cancelled:
            self.status_changed.emit(job)
        self._emit_queue()

    def retry_job(self, job_id: int) -> None:
        with self._lock:
            existing = next((j for j in self._queue if j.id == job_id), None)
            if existing and existing.status not in (JobStatus.FAILED, JobStatus.CANCELLED):
                return
        job = self.repo.get_by_id(job_id)
        if not job or job.status not in (JobStatus.FAILED, JobStatus.CANCELLED):
            return
        job.status = JobStatus.PENDING
        job.progress = 0.0
        job.speed = ""
        job.eta = ""
        job.error_message = ""
        self.repo.update_status(job_id, JobStatus.PENDING)
        with self._lock:
            existing = next((j for j in self._queue if j.id == job_id), None)
            if existing is not None:
                existing.status = JobStatus.PENDING
                existing.progress = 0.0
                existing.speed = ""
                existing.eta = ""
                existing.error_message = ""
            else:
                self._queue.append(job)
        self.status_changed.emit(job)
        self._emit_queue()
        self._process_queue()

    def get_queue(self) -> list[DownloadJob]:
        with self._lock:
            return self._queue.copy()

    def _format_speed(self, speed: float) -> str:
        if speed >= 1_000_000:
            return f"{speed / 1_000_000:.1f} MB/s"
        elif speed >= 1_000:
            return f"{speed / 1_000:.1f} KB/s"
        return f"{speed:.0f} B/s"

    def _format_eta(self, seconds: float) -> str:
        if seconds >= 3600:
            return f"{seconds / 3600:.0f}h {seconds % 3600 / 60:.0f}m"
        elif seconds >= 60:
            return f"{seconds / 60:.0f}m {seconds % 60:.0f}s"
        return f"{seconds:.0f}s"
