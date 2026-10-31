from typing import Optional

from app.models.download_job import DownloadJob, JobStatus

from .database import Database


class DownloadsRepository:
    def __init__(self) -> None:
        self.db = Database()

    def add(self, job: DownloadJob) -> int:
        cur = self.db.execute(
            """INSERT INTO downloads
            (url, webpage_url, title, extractor, uploader, duration,
             thumbnail, output_path, folder, selected_preset, selected_format,
             status, progress, speed, eta, error_message, format_spec,
             created_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                job.url,
                job.webpage_url,
                job.title,
                job.extractor,
                job.uploader,
                job.duration,
                job.thumbnail,
                job.output_path,
                job.folder,
                job.selected_preset,
                job.selected_format,
                job.status.value,
                job.progress,
                job.speed,
                job.eta,
                job.error_message,
                job.format_spec,
                job.created_at,
            ),
        )
        self.db.commit()
        return cur.lastrowid or 0

    def update_status(
        self,
        job_id: int,
        status: JobStatus,
        progress: float = 0.0,
        speed: str = "",
        eta: str = "",
        error_message: str = "",
    ) -> None:
        self.db.execute(
            """UPDATE downloads SET status=?, progress=?, speed=?, eta=?,
               error_message=?
               WHERE id=?""",
            (status.value, progress, speed, eta, error_message, job_id),
        )
        self.db.commit()

    def update_progress(self, job_id: int, progress: float, speed: str = "", eta: str = "") -> None:
        self.db.execute(
            "UPDATE downloads SET progress=?, speed=?, eta=? WHERE id=?",
            (progress, speed, eta, job_id),
        )
        self.db.commit()

    def complete(self, job_id: int, output_path: str = "") -> None:
        self.db.execute(
            """UPDATE downloads SET status=?, output_path=?, progress=100, speed='', eta='',
               error_message='',
               completed_at=datetime('now','localtime')
               WHERE id=?""",
            (JobStatus.COMPLETED.value, output_path, job_id),
        )
        self.db.commit()

    def fail(self, job_id: int, error_message: str) -> None:
        self.db.execute(
            "UPDATE downloads SET status=?, error_message=? WHERE id=?",
            (JobStatus.FAILED.value, error_message, job_id),
        )
        self.db.commit()

    def get_by_id(self, job_id: int) -> Optional[DownloadJob]:
        row = self.db.execute("SELECT * FROM downloads WHERE id=?", (job_id,)).fetchone()
        if row is None:
            return None
        return self._row_to_job(row)

    def get_all(self, limit: int = 100, offset: int = 0) -> list[DownloadJob]:
        rows = self.db.execute(
            "SELECT * FROM downloads ORDER BY id DESC LIMIT ? OFFSET ?",
            (limit, offset),
        ).fetchall()
        return [self._row_to_job(r) for r in rows]

    def get_by_status(self, status: JobStatus) -> list[DownloadJob]:
        rows = self.db.execute(
            "SELECT * FROM downloads WHERE status=? ORDER BY id DESC",
            (status.value,),
        ).fetchall()
        return [self._row_to_job(r) for r in rows]

    def delete(self, job_id: int) -> None:
        self.db.execute("DELETE FROM downloads WHERE id=?", (job_id,))
        self.db.commit()

    def clear_history(self) -> None:
        self.db.execute("DELETE FROM downloads")
        self.db.commit()

    def _row_to_job(self, row) -> DownloadJob:
        return DownloadJob(
            id=row["id"],
            url=row["url"],
            webpage_url=row["webpage_url"],
            title=row["title"],
            extractor=row["extractor"],
            uploader=row["uploader"],
            duration=row["duration"],
            thumbnail=row["thumbnail"],
            output_path=row["output_path"],
            folder=row["folder"],
            selected_preset=row["selected_preset"],
            selected_format=row["selected_format"],
            status=JobStatus(row["status"]),
            progress=row["progress"],
            speed=row["speed"],
            eta=row["eta"],
            error_message=row["error_message"],
            format_spec=row["format_spec"],
            created_at=row["created_at"],
            started_at=row["started_at"],
            completed_at=row["completed_at"],
        )
