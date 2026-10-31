from pathlib import Path

from app.utils.paths import find_bundled_tool
from app.utils.system import is_windows, run_command


class Aria2Service:
    def __init__(self, aria2c_path: str = "") -> None:
        self._aria2c_path = aria2c_path
        self._version = ""
        self._detected = False

    def detect(self) -> tuple[bool, str]:
        aria2c = self._find_aria2c()
        if not aria2c:
            return False, ""

        code, out, _ = run_command([aria2c, "--version"])
        if code == 0:
            self._aria2c_path = aria2c
            first_line = out.split("\n")[0] if out else ""
            self._version = first_line
            self._detected = True
            return True, first_line

        return False, ""

    def _find_aria2c(self) -> str:
        if self._aria2c_path and Path(self._aria2c_path).exists():
            return self._aria2c_path

        name = "aria2c.exe" if is_windows() else "aria2c"
        code, out, _ = run_command([name, "--version"])
        if code == 0:
            return name

        bundled = find_bundled_tool("aria2c.exe", "aria2c")
        if bundled:
            return bundled

        if self._aria2c_path:
            return self._aria2c_path
        return ""

    @property
    def available(self) -> bool:
        return self._detected

    @property
    def version(self) -> str:
        return self._version

    @property
    def path(self) -> str:
        return self._aria2c_path

    def get_ydl_opts(self) -> dict:
        if not self._detected:
            return {}
        return {
            "external_downloader": self._aria2c_path,
            "external_downloader_args": [
                "-x",
                "16",
                "-k",
                "1M",
                "--console-log-level=error",
            ],
        }
