import platform
import subprocess
from pathlib import Path


def get_platform() -> str:
    system = platform.system().lower()
    if system == "windows":
        return "windows"
    if system == "linux":
        return "linux"
    if system == "darwin":
        return "macos"
    return system


def is_windows() -> bool:
    return get_platform() == "windows"


def is_linux() -> bool:
    return get_platform() == "linux"


def run_command(cmd: list[str], timeout: int = 30) -> tuple[int, str, str]:
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            creationflags=subprocess.CREATE_NO_WINDOW if is_windows() else 0,
        )
        return result.returncode, result.stdout.strip(), result.stderr.strip()
    except FileNotFoundError:
        return -1, "", "command not found"
    except subprocess.TimeoutExpired:
        return -2, "", "timeout"
    except Exception as e:
        return -3, "", str(e)


def sanitize_filename(name: str) -> str:
    invalid_chars = '<>:"/\\|?*'
    for c in invalid_chars:
        name = name.replace(c, "_")
    name = name.strip(". ")
    if not name:
        name = "untitled"
    return name[:200]


def open_folder_in_explorer(path: str | Path) -> bool:
    path = Path(path)
    if not path.exists():
        return False
    try:
        if is_windows():
            subprocess.run(["explorer", str(path)], check=False)
        elif is_linux():
            subprocess.run(["xdg-open", str(path)], check=False)
        else:
            subprocess.run(["open", str(path)], check=False)
        return True
    except Exception:
        return False
