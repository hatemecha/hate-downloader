import platform
import shutil
import stat
import sys
import tarfile
import zipfile
from pathlib import Path
from typing import Callable, Optional

import httpx

from app import __version__
from app.core.aria2_service import Aria2Service
from app.core.ffmpeg_service import FFmpegService
from app.core.ytdlp_service import YtDlpService
from app.models.dependency_status import DependencyInfo, SystemStatus
from app.utils.logger import logger
from app.utils.paths import find_bundled_tool, get_default_download_dir, get_tools_dir
from app.utils.system import get_platform, run_command

ProgressCallback = Optional[Callable[[float], None]]

FFMPEG_DOWNLOAD_URLS = {
    "windows": "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip",
    "linux": "https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz",
}

ARIA2_DOWNLOAD_URLS = {
    "windows": "https://github.com/aria2/aria2/releases/download/release-1.37.0/aria2-1.37.0-win-64bit-build1.zip",
    "linux": "",
}

DENO_DOWNLOAD_URLS = {
    "windows": "https://github.com/denoland/deno/releases/latest/download/deno-x86_64-pc-windows-msvc.zip",
    "linux": "https://github.com/denoland/deno/releases/latest/download/deno-x86_64-unknown-linux-gnu.zip",
    "macos_arm": "https://github.com/denoland/deno/releases/latest/download/deno-aarch64-apple-darwin.zip",
    "macos_intel": "https://github.com/denoland/deno/releases/latest/download/deno-x86_64-apple-darwin.zip",
}


def deno_download_url() -> str:
    current = get_platform()
    if current == "macos":
        machine = platform.machine().lower()
        key = "macos_arm" if machine in ("arm64", "aarch64") else "macos_intel"
        return DENO_DOWNLOAD_URLS[key]
    return DENO_DOWNLOAD_URLS.get(current, "")

MAX_ARCHIVE_DOWNLOAD_BYTES = 1_000_000_000
MAX_ARCHIVE_EXTRACTED_BYTES = 2_000_000_000
MAX_ARCHIVE_MEMBERS = 50_000


class DependencyManager:
    def __init__(self) -> None:
        self.ffmpeg = FFmpegService()
        self.aria2 = Aria2Service()
        self.ytdlp = YtDlpService()
        self._tools_dir = get_tools_dir()

    def check_all(self) -> SystemStatus:
        ffmpeg_found, ffmpeg_ver, ffprobe_ver = self.ffmpeg.detect()
        aria2_found, aria2_ver = self.aria2.detect()

        yt_dlp_ver = self.ytdlp.version
        yt_dlp_installed = yt_dlp_ver != ""

        deno_path = shutil.which("deno") or find_bundled_tool("deno.exe", "deno")
        node_path = shutil.which("node") or find_bundled_tool("node.exe", "node")
        js_path = deno_path or node_path
        js_version = ""
        if deno_path:
            code, out, _ = run_command([deno_path, "--version"])
            if code == 0 and out:
                js_version = out.splitlines()[0]
        if not js_version and node_path:
            code, out, _ = run_command([node_path, "--version"])
            if code == 0 and out:
                js_version = f"Node.js {out.strip()}"

        download_dir = get_default_download_dir()
        try:
            download_dir.mkdir(parents=True, exist_ok=True)
            writable = True
        except OSError:
            writable = False

        if deno_path:
            js_message = "Runs YouTube's JavaScript challenges."
        elif node_path:
            js_message = "Using Node.js as the JavaScript runtime."
        else:
            js_message = "YouTube needs Deno 2.3+ or Node.js 22+. Install Deno here."

        deps = [
            DependencyInfo(
                name="Deno",
                installed=bool(js_path),
                version=js_version,
                optional=False,
                status_message=js_message,
                path=js_path or "",
                download_url=deno_download_url(),
                actionable=not bool(js_path),
            ),
            DependencyInfo(
                name="yt-dlp",
                installed=yt_dlp_installed,
                version=yt_dlp_ver,
                optional=False,
                status_message=(
                    "Download engine bundled with the app."
                    if yt_dlp_installed
                    else "Missing from this build. Reinstall Hate Downloader."
                ),
                actionable=not yt_dlp_installed,
            ),
            DependencyInfo(
                name="FFmpeg",
                installed=ffmpeg_found,
                version=ffmpeg_ver,
                optional=False,
                status_message=(
                    "Merges audio and video, and converts formats."
                    if ffmpeg_found
                    else "Not installed. Merging audio and video needs FFmpeg."
                ),
                path=self.ffmpeg.ffmpeg_path,
                download_url=FFMPEG_DOWNLOAD_URLS.get(get_platform(), ""),
                actionable=not ffmpeg_found,
            ),
            DependencyInfo(
                name="FFprobe",
                installed=bool(ffprobe_ver),
                version=ffprobe_ver,
                optional=False,
                status_message=(
                    "Reads media metadata."
                    if ffprobe_ver
                    else "Not installed. It ships with FFmpeg."
                ),
                path=self.ffmpeg.ffprobe_path,
                actionable=not bool(ffprobe_ver),
            ),
            DependencyInfo(
                name="aria2c",
                installed=aria2_found,
                version=aria2_ver,
                optional=True,
                status_message=(
                    "Optional download accelerator."
                    if aria2_found
                    else "Optional. Downloads work without it."
                ),
                path=self.aria2.path,
                download_url=ARIA2_DOWNLOAD_URLS.get(get_platform(), ""),
                actionable=False,
            ),
        ]

        return SystemStatus(
            dependencies=deps,
            app_version=__version__,
            python_version=sys.version,
            platform=get_platform(),
            download_folder_writable=writable,
            download_folder=str(download_dir),
            all_ok=all(d.installed for d in deps if not d.optional),
            can_download=yt_dlp_installed,
            can_convert=ffmpeg_found and bool(ffprobe_ver),
            can_accelerate=aria2_found,
        )

    def download_ffmpeg(self, progress_callback: ProgressCallback = None) -> tuple[bool, str]:
        platform = get_platform()
        url = FFMPEG_DOWNLOAD_URLS.get(platform, "")
        if not url:
            return False, f"No download URL for {platform}"

        return self._download_tool("ffmpeg", url, progress_callback)

    def download_deno(self, progress_callback: ProgressCallback = None) -> tuple[bool, str]:
        url = deno_download_url()
        if not url:
            return False, f"No Deno download for {get_platform()}"

        return self._download_tool("deno", url, progress_callback)

    def download_aria2(self, progress_callback: ProgressCallback = None) -> tuple[bool, str]:
        platform = get_platform()
        url = ARIA2_DOWNLOAD_URLS.get(platform, "")
        if not url:
            return False, f"No download URL for {platform}"

        return self._download_tool("aria2c", url, progress_callback)

    def _download_tool(
        self, name: str, url: str, progress_callback: ProgressCallback = None
    ) -> tuple[bool, str]:
        archive_path: Optional[Path] = None
        try:
            self._tools_dir.mkdir(parents=True, exist_ok=True)
            suffix = self._archive_suffix(url)
            archive_path = self._tools_dir / f"{name}{suffix}"

            with httpx.stream("GET", url, follow_redirects=True, timeout=300) as resp:
                resp.raise_for_status()
                total = int(resp.headers.get("content-length", 0))
                if total > MAX_ARCHIVE_DOWNLOAD_BYTES:
                    raise ValueError(f"Archive is too large: {total} bytes")
                downloaded = 0
                with open(archive_path, "wb") as f:
                    for chunk in resp.iter_bytes(8192):
                        downloaded += len(chunk)
                        if downloaded > MAX_ARCHIVE_DOWNLOAD_BYTES:
                            raise ValueError("Archive exceeded the download size limit")
                        f.write(chunk)
                        if progress_callback and total:
                            progress_callback(downloaded / total * 100)

            self._extract_archive(archive_path)
            self._make_tools_executable()
            return True, f"Downloaded to {self._tools_dir}"
        except Exception as e:
            logger.error(f"Failed to download {name}: {e}")
            return False, str(e)
        finally:
            if archive_path is not None:
                archive_path.unlink(missing_ok=True)

    @staticmethod
    def _archive_suffix(url: str) -> str:
        lowered = url.lower()
        for suffix in (".tar.xz", ".tar.gz", ".tgz", ".zip"):
            if lowered.endswith(suffix):
                return suffix
        return ".zip"

    def _extract_archive(self, archive_path: Path) -> None:
        name = archive_path.name.lower()
        if name.endswith(".zip"):
            with zipfile.ZipFile(archive_path, "r") as zf:
                self._safe_extract_zip(zf, self._tools_dir)
        elif name.endswith((".tar.xz", ".tar.gz", ".tgz")):
            with tarfile.open(archive_path, "r:*") as tf:
                self._safe_extract_tar(tf, self._tools_dir)
        else:
            raise ValueError(f"Unsupported archive format: {archive_path.name}")

    @staticmethod
    def _safe_extract_zip(zf: zipfile.ZipFile, dest: Path) -> None:
        dest = dest.resolve()
        members = zf.infolist()
        if len(members) > MAX_ARCHIVE_MEMBERS:
            raise ValueError("Archive contains too many files")
        if sum(info.file_size for info in members) > MAX_ARCHIVE_EXTRACTED_BYTES:
            raise ValueError("Archive expands beyond the size limit")
        for info in members:
            mode = info.external_attr >> 16
            if stat.S_ISLNK(mode):
                raise ValueError(f"Archive link blocked: {info.filename}")
            target = (dest / info.filename).resolve()
            try:
                target.relative_to(dest)
            except ValueError as exc:
                raise ValueError(f"Unsafe zip path blocked: {info.filename}") from exc
            zf.extract(info, dest)

    @staticmethod
    def _safe_extract_tar(tf: tarfile.TarFile, dest: Path) -> None:
        dest = dest.resolve()
        members = tf.getmembers()
        if len(members) > MAX_ARCHIVE_MEMBERS:
            raise ValueError("Archive contains too many files")
        if sum(member.size for member in members) > MAX_ARCHIVE_EXTRACTED_BYTES:
            raise ValueError("Archive expands beyond the size limit")
        for member in members:
            if not (member.isfile() or member.isdir()):
                raise ValueError(f"Archive link or special file blocked: {member.name}")
            target = (dest / member.name).resolve()
            try:
                target.relative_to(dest)
            except ValueError as exc:
                raise ValueError(f"Unsafe tar path blocked: {member.name}") from exc
            tf.extract(member, dest)

    def _make_tools_executable(self) -> None:
        """Archives lose the executable bit on Unix; restore it for our tools."""
        names = {"deno", "ffmpeg", "ffprobe", "aria2c"}
        for path in self._tools_dir.rglob("*"):
            if path.is_file() and path.stem.lower() in names:
                try:
                    path.chmod(path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP)
                except OSError as exc:
                    logger.debug("Could not mark %s executable: %s", path, exc)

    def find_existing_tools(self) -> tuple[str, str, str]:
        ffmpeg = shutil.which("ffmpeg") or find_bundled_tool("ffmpeg.exe", "ffmpeg")
        ffprobe = shutil.which("ffprobe") or find_bundled_tool("ffprobe.exe", "ffprobe")
        aria2c = shutil.which("aria2c") or find_bundled_tool("aria2c.exe", "aria2c")
        return ffmpeg, ffprobe, aria2c
    def update_ytdlp(self) -> tuple[bool, str]:
        return self.ytdlp.update_ytdlp()
