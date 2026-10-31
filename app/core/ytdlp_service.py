import subprocess
import sys
from typing import Any, Optional

import yt_dlp
from yt_dlp.utils import DownloadError

from app.models.media_info import MediaFormat, MediaInfo, Subtitle
from app.utils.logger import logger
from app.utils.paths import find_bundled_tool


def js_runtime_options() -> dict[str, dict]:
    """Enable yt-dlp's JavaScript runtimes, including a downloaded Deno build.

    yt-dlp only searches PATH on its own. Deno installed through the Setup
    window lives in the app tools folder, so it has to be passed explicitly.
    """
    runtimes: dict[str, dict] = {"deno": {}, "node": {}}
    deno = find_bundled_tool("deno.exe", "deno")
    if deno:
        runtimes["deno"] = {"path": deno}
    return runtimes

PRESETS: dict[str, dict[str, Any]] = {
    "best_mp4": {
        "name": "best_mp4",
        "label": "Best MP4 compatible",
        "format": "bv*[ext=mp4]+ba[ext=m4a]/b[ext=mp4]/best",
        "merge_output_format": "mp4",
        "category": "video",
    },
    "max_quality": {
        "name": "max_quality",
        "label": "Maximum quality",
        "format": "bv*+ba/b",
        "merge_output_format": "",
        "category": "video",
    },
    "1080p_mp4": {
        "name": "1080p_mp4",
        "label": "1080p MP4",
        "format": (
            "bv*[height<=1080][ext=mp4]+ba[ext=m4a]/b[height<=1080][ext=mp4]/best[height<=1080]"
        ),
        "merge_output_format": "mp4",
        "category": "video",
    },
    "720p_mp4": {
        "name": "720p_mp4",
        "label": "720p MP4",
        "format": "bv*[height<=720][ext=mp4]+ba[ext=m4a]/b[height<=720][ext=mp4]/best[height<=720]",
        "merge_output_format": "mp4",
        "category": "video",
    },
    "480p_mp4": {
        "name": "480p_mp4",
        "label": "480p MP4",
        "format": "bv*[height<=480][ext=mp4]+ba[ext=m4a]/b[height<=480][ext=mp4]/best[height<=480]",
        "merge_output_format": "mp4",
        "category": "video",
    },
    "video_original": {
        "name": "video_original",
        "label": "Original video (no convert)",
        "format": "bv*+ba/b",
        "merge_output_format": "",
        "category": "video",
    },
    "video_no_audio": {
        "name": "video_no_audio",
        "label": "Video only (no audio)",
        "format": "bv/b",
        "merge_output_format": "",
        "category": "video",
    },
    "video_light": {
        "name": "video_light",
        "label": "Light video (480p)",
        "format": "worst[height<=480]",
        "merge_output_format": "mp4",
        "category": "video",
    },
    "video_editing": {
        "name": "video_editing",
        "label": "Video for editing (best quality)",
        "format": "bv*+ba/b",
        "merge_output_format": "mkv",
        "category": "video",
    },
    "best_audio": {
        "name": "best_audio",
        "label": "Best audio original",
        "format": "bestaudio/best",
        "postprocessors": [],
        "category": "audio",
    },
    "m4a": {
        "name": "m4a",
        "label": "M4A",
        "format": "bestaudio/best",
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "m4a",
            }
        ],
        "category": "audio",
    },
    "opus": {
        "name": "opus",
        "label": "Opus",
        "format": "bestaudio/best",
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "opus",
            }
        ],
        "category": "audio",
    },
    "mp3_320": {
        "name": "mp3_320",
        "label": "MP3 320kbps",
        "format": "bestaudio/best",
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "320",
            }
        ],
        "category": "audio",
    },
    "mp3_192": {
        "name": "mp3_192",
        "label": "MP3 192kbps",
        "format": "bestaudio/best",
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }
        ],
        "category": "audio",
    },
    "wav": {
        "name": "wav",
        "label": "WAV",
        "format": "bestaudio/best",
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "wav",
            }
        ],
        "category": "audio",
    },
    "flac": {
        "name": "flac",
        "label": "FLAC",
        "format": "bestaudio/best",
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "flac",
            }
        ],
        "category": "audio",
    },
}


class YtDlpService:
    def __init__(self) -> None:
        self._version: str = ""

    @property
    def version(self) -> str:
        if not self._version:
            try:
                self._version = yt_dlp.version.__version__
            except Exception:
                self._version = "unknown"
        return self._version

    def _build_opts(
        self,
        download: bool = False,
        progress_hooks: Optional[list] = None,
        settings: Optional[dict] = None,
    ) -> dict[str, Any]:
        opts: dict[str, Any] = {
            "quiet": True,
            "no_warnings": True,
            "socket_timeout": 30,
            "noplaylist": True,
            "extract_flat": False,
            "js_runtimes": js_runtime_options(),
        }
        if not download:
            opts.update(
                {
                    "skip_download": True,
                    "no_color": True,
                }
            )
        else:
            opts.update(
                {
                    "progress_hooks": progress_hooks or [],
                    "quiet": False,
                    "verbose": False,
                }
            )
        if settings:
            for key, val in settings.items():
                if val is not None and val != "":
                    opts[key] = val
        return opts

    def extract_info(self, url: str, settings: Optional[dict] = None) -> dict[str, Any]:
        opts = self._build_opts(download=False, settings=settings)
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=False)
            if not info:
                raise DownloadError("No media information could be extracted from this URL.")
            return info
        except Exception as e:
            logger.error(f"yt-dlp extract_info error: {e}")
            raise

    def parse_media_info(self, raw: dict[str, Any]) -> MediaInfo:
        formats = []
        for f in raw.get("formats") or []:
            formats.append(
                MediaFormat(
                    format_id=f.get("format_id", ""),
                    ext=f.get("ext", ""),
                    resolution=f.get("resolution", ""),
                    filesize=f.get("filesize"),
                    filesize_approx=f.get("filesize_approx"),
                    tbr=f.get("tbr"),
                    vcodec=f.get("vcodec", ""),
                    acodec=f.get("acodec", ""),
                    fps=f.get("fps"),
                    height=f.get("height"),
                    width=f.get("width"),
                    dynamic_range=f.get("dynamic_range", ""),
                    format_note=f.get("format_note", ""),
                    has_audio=f.get("acodec") not in (None, "none"),
                    has_video=f.get("vcodec") not in (None, "none"),
                )
            )

        subs = []
        for lang, sub_data in (raw.get("subtitles") or {}).items():
            subs.append(
                Subtitle(
                    lang=lang,
                    name=(sub_data[0].get("name") or lang) if sub_data else lang,
                    auto_generated=False,
                )
            )
        for lang, sub_data in (raw.get("automatic_captions") or {}).items():
            subs.append(
                Subtitle(
                    lang=lang,
                    name=(sub_data[0].get("name") or lang) if sub_data else lang,
                    auto_generated=True,
                )
            )

        entries = []
        for entry in raw.get("entries") or []:
            if isinstance(entry, dict):
                entries.append(self.parse_media_info(entry))

        return MediaInfo(
            url=raw.get("original_url") or raw.get("webpage_url") or "",
            webpage_url=(raw.get("webpage_url") or ""),
            title=(raw.get("title") or ""),
            description=raw.get("description", "") or "",
            duration=int(raw.get("duration") or 0),
            uploader=raw.get("uploader") or raw.get("channel") or "",
            uploader_url=raw.get("uploader_url") or "",
            thumbnail=(raw.get("thumbnail") or ""),
            extractor=(raw.get("extractor") or ""),
            extractor_key=(raw.get("extractor_key") or ""),
            formats=formats,
            subtitles=subs,
            is_playlist=raw.get("_type") == "playlist" or bool(raw.get("entries")),
            playlist_count=raw.get("playlist_count") or 0,
            entries=entries,
            webpage_url_domain=(raw.get("webpage_url_domain") or ""),
            view_count=raw.get("view_count") or 0,
            like_count=raw.get("like_count") or 0,
            average_rating=raw.get("average_rating") or 0.0,
            age_limit=raw.get("age_limit") or 0,
            is_live=raw.get("is_live") or False,
            protocol=(raw.get("protocol") or ""),
            fps=raw.get("fps"),
            height=raw.get("height"),
            width=raw.get("width"),
            vcodec=(raw.get("vcodec") or ""),
            acodec=(raw.get("acodec") or ""),
            ext=(raw.get("ext") or ""),
            dynamic_range=(raw.get("dynamic_range") or ""),
        )

    def search(self, query: str, limit: int = 20) -> list[dict[str, Any]]:
        search_url = f"ytsearch{limit}:{query}"
        opts = self._build_opts(download=False)
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(search_url, download=False)
            return info.get("entries") or []
        except Exception as e:
            logger.error(f"yt-dlp search error: {e}")
            return []

    def update_ytdlp(self) -> tuple[bool, str]:
        if getattr(sys, "frozen", False):
            return (
                False,
                "The packaged app includes yt-dlp. Install a newer Hate Downloader release "
                "to update it.",
            )
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", "--upgrade", "yt-dlp[default]"],
                capture_output=True,
                text=True,
                timeout=120,
            )
            if result.returncode == 0:
                self._version = ""
                return True, "yt-dlp updated successfully"
            return False, result.stderr
        except Exception as e:
            return False, str(e)
