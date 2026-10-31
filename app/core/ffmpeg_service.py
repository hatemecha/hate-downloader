from pathlib import Path

from app.utils.paths import find_bundled_tool
from app.utils.system import is_windows, run_command


class FFmpegService:
    def __init__(self, ffmpeg_path: str = "", ffprobe_path: str = "") -> None:
        self._ffmpeg_path = ffmpeg_path
        self._ffprobe_path = ffprobe_path
        self._ffmpeg_version = ""
        self._ffprobe_version = ""
        self._detected = False

    def detect(self) -> tuple[bool, str, str]:
        ffmpeg_found = False
        ffprobe_found = False
        self._ffmpeg_version = ""
        self._ffprobe_version = ""

        ffmpeg = self._find_tool("ffmpeg", self._ffmpeg_path)
        ffprobe = self._find_tool("ffprobe", self._ffprobe_path)

        if ffmpeg:
            code, out, _ = run_command([ffmpeg, "-version"])
            if code == 0:
                self._ffmpeg_path = ffmpeg
                self._ffmpeg_version = out.split("\n")[0] if out else "found"
                ffmpeg_found = True

        if ffprobe:
            code, out, _ = run_command([ffprobe, "-version"])
            if code == 0:
                self._ffprobe_path = ffprobe
                self._ffprobe_version = out.split("\n")[0] if out else "found"
                ffprobe_found = True

        self._detected = ffmpeg_found and ffprobe_found
        return ffmpeg_found, self._ffmpeg_version, self._ffprobe_version

    def _find_tool(self, name: str, custom_path: str = "") -> str:
        if custom_path and Path(custom_path).exists():
            return custom_path

        candidates = [name]
        if is_windows():
            candidates = [f"{name}.exe", f"{name}.bat", name]

        for candidate in candidates:
            code, out, _ = run_command([candidate, "-version"])
            if code == 0:
                return candidate

        bundled = find_bundled_tool(f"{name}.exe", name)
        if bundled:
            return bundled

        if custom_path:
            return custom_path
        return ""

    @property
    def ffmpeg_path(self) -> str:
        return self._ffmpeg_path

    @property
    def ffprobe_path(self) -> str:
        return self._ffprobe_path

    @property
    def ffmpeg_version(self) -> str:
        return self._ffmpeg_version

    @property
    def ffprobe_version(self) -> str:
        return self._ffprobe_version

    @property
    def available(self) -> bool:
        return self._detected
