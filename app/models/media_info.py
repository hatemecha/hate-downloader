from typing import Optional

from pydantic import BaseModel


class MediaFormat(BaseModel):
    format_id: str
    ext: str
    resolution: Optional[str] = None
    filesize: Optional[int] = None
    filesize_approx: Optional[int] = None
    tbr: Optional[float] = None
    vcodec: Optional[str] = None
    acodec: Optional[str] = None
    fps: Optional[float] = None
    height: Optional[int] = None
    width: Optional[int] = None
    dynamic_range: Optional[str] = None
    format_note: Optional[str] = None
    has_audio: bool = False
    has_video: bool = False


class Subtitle(BaseModel):
    lang: str
    name: str
    auto_generated: bool = False


class MediaInfo(BaseModel):
    url: str
    webpage_url: str = ""
    title: str = ""
    description: str = ""
    duration: int = 0
    uploader: str = ""
    uploader_url: str = ""
    thumbnail: str = ""
    extractor: str = ""
    extractor_key: str = ""
    formats: list[MediaFormat] = []
    subtitles: list[Subtitle] = []
    is_playlist: bool = False
    playlist_count: int = 0
    entries: list["MediaInfo"] = []
    webpage_url_domain: str = ""
    view_count: int = 0
    like_count: int = 0
    average_rating: float = 0.0
    age_limit: int = 0
    is_live: bool = False
    protocol: str = ""
    fps: Optional[float] = None
    height: Optional[int] = None
    width: Optional[int] = None
    vcodec: str = ""
    acodec: str = ""
    ext: str = ""
    dynamic_range: str = ""
