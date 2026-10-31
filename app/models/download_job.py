from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class JobStatus(str, Enum):
    PENDING = "pending"
    DOWNLOADING = "downloading"
    POSTPROCESSING = "postprocessing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class DownloadJob(BaseModel):
    id: int = 0
    url: str = ""
    webpage_url: str = ""
    title: str = ""
    extractor: str = ""
    uploader: str = ""
    duration: int = 0
    thumbnail: str = ""
    output_path: str = ""
    folder: str = ""
    selected_preset: str = ""
    selected_format: str = ""
    status: JobStatus = JobStatus.PENDING
    progress: float = 0.0
    speed: str = ""
    eta: str = ""
    error_message: str = ""
    created_at: str = ""
    started_at: str = ""
    completed_at: str = ""
    format_spec: str = ""
    extra_opts: dict[str, Any] = Field(default_factory=dict)
