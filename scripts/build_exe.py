#!/usr/bin/env python3
"""Build Hate Downloader as a standalone executable with PyInstaller."""

import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LICENSE_FILES = ("LICENSE", "THIRD_PARTY.md", "README.md")


def built_executable(dist_dir: Path) -> Path:
    if sys.platform.startswith("win"):
        return dist_dir / "HateDownloader.exe"
    if sys.platform == "darwin":
        app_binary = dist_dir / "HateDownloader.app" / "Contents" / "MacOS" / "HateDownloader"
        if app_binary.is_file():
            return app_binary
    return dist_dir / "HateDownloader"


def copy_release_files(dist_dir: Path) -> None:
    for name in LICENSE_FILES:
        src = ROOT / name
        if src.is_file():
            shutil.copy2(src, dist_dir / name)


def main() -> None:
    try:
        import PyInstaller  # noqa: F401
        import yt_dlp
    except ImportError:
        print('PyInstaller is missing. Install it with: pip install ".[build]"')
        sys.exit(2)

    dist_dir = ROOT / "dist"
    build_dir = ROOT / "build"
    assets_dir = ROOT / "app" / "assets"
    icon_name = "icon.icns" if sys.platform == "darwin" else "icon.ico"
    icon_path = assets_dir / "icons" / icon_name
    if not icon_path.is_file():
        raise RuntimeError("Missing application icon. Run scripts/build_icons.py first.")
    ytdlp_hooks = Path(yt_dlp.__file__).resolve().parent / "__pyinstaller"

    sep = ";" if sys.platform.startswith("win") else ":"

    args = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--name",
        "HateDownloader",
        "--onefile",
        "--windowed",
        "--distpath",
        str(dist_dir),
        "--workpath",
        str(build_dir),
        "--clean",
        "--noconfirm",
        "--noupx",
        "--additional-hooks-dir",
        str(ytdlp_hooks),
        "--copy-metadata",
        "yt-dlp",
        "--collect-all",
        "yt_dlp_ejs",
        "--hidden-import",
        "pydantic_core",
        "--hidden-import",
        "pydantic_core._pydantic_core",
        "--exclude-module",
        "rich",
        "--exclude-module",
        "pygments",
        "--exclude-module",
        "tkinter",
    ]

    if assets_dir.is_dir():
        args += ["--add-data", f"{assets_dir}{sep}app/assets"]
    if icon_path.is_file():
        args += ["--icon", str(icon_path)]

    if sys.platform.startswith("win"):
        sys.path.insert(0, str(ROOT))
        from app import __version__

        version = tuple(int(part) for part in __version__.split("."))
        version = (version + (0, 0, 0, 0))[:4]
        build_dir.mkdir(exist_ok=True)
        version_file = build_dir / "windows-version.txt"
        fields = {
            "CompanyName": "hatemecha",
            "FileDescription": "Hate Downloader",
            "FileVersion": __version__,
            "InternalName": "HateDownloader",
            "OriginalFilename": "HateDownloader.exe",
            "ProductName": "Hate Downloader",
            "ProductVersion": __version__,
        }
        strings = ",".join(f"StringStruct({key!r}, {value!r})" for key, value in fields.items())
        version_file.write_text(
            f"VSVersionInfo(ffi=FixedFileInfo(filevers={version!r}, prodvers={version!r}, "
            "mask=0x3f, flags=0, OS=0x40004, fileType=1, subtype=0, date=(0,0)), "
            f"kids=[StringFileInfo([StringTable('040904B0', [{strings}])]), "
            "VarFileInfo([VarStruct('Translation', [1033, 1200])])])",
            encoding="utf-8",
        )
        args += ["--version-file", str(version_file)]

    args.append(str(ROOT / "run.py"))

    print("Building Hate Downloader...")
    build_env = os.environ.copy()
    if sys.platform.startswith("win"):
        # Avoid collecting unrelated DLLs (e.g. Poppler's ICU) from the host PATH.
        # Qt uses the Windows ICU API; a same-named third-party DLL breaks startup.
        windows = Path(os.environ.get("SystemRoot", r"C:\Windows"))
        build_env["PATH"] = os.pathsep.join(
            str(path)
            for path in (
                Path(sys.executable).parent,
                Path(sys.base_prefix),
                windows / "System32",
                windows,
            )
        )
    result = subprocess.run(args, cwd=ROOT, env=build_env)
    if result.returncode != 0:
        print("Build failed.")
        sys.exit(1)

    executable = built_executable(dist_dir)
    if not executable.is_file():
        print(f"Build finished but the executable was not found: {executable}")
        sys.exit(1)

    copy_release_files(dist_dir)

    print(f"Running packaged self-test: {executable}")
    smoke = subprocess.run([str(executable), "--self-test"], cwd=ROOT, timeout=180)
    if smoke.returncode != 0:
        print(f"Packaged self-test failed with exit code {smoke.returncode}.")
        sys.exit(smoke.returncode)

    print(f"Build and packaged self-test successful: {executable}")


if __name__ == "__main__":
    main()
