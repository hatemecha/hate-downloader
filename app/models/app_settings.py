from pydantic import BaseModel, Field


class AppSettings(BaseModel):
    theme: str = "hate_dark"
    default_folder: str = ""
    default_preset: str = "best_mp4"
    max_concurrent: int = Field(default=3, ge=1, le=20)
    concurrent_fragments: int = Field(default=5, ge=1, le=32)
    use_aria2c: bool = False
    aria2c_path: str = ""
    ffmpeg_path: str = ""
    ffprobe_path: str = ""
    cookiefile: str = ""
    cookies_from_browser: str = ""
    download_archive: str = ""
    searxng_instance: str = "https://search.sapti.me"
    filename_template: str = "%(title)s.%(ext)s"
    retries: int = Field(default=10, ge=0)
    fragment_retries: int = Field(default=10, ge=0)
    socket_timeout: int = Field(default=30, ge=1)
    ratelimit: str = ""
    continuedl: bool = True
    ignoreerrors: bool = True
    writesubtitles: bool = False
    writeautomaticsub: bool = False
    subtitleslangs: str = "en"
    writethumbnail: bool = False
    embedthumbnail: bool = False
    addmetadata: bool = True
    embedsubtitles: bool = False
    window_width: int = 1100
    window_height: int = 720
    first_run: bool = True
