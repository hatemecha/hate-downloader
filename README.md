# Hate Downloader

Desktop app for searching, analyzing, and downloading **public** media with
[yt-dlp](https://github.com/yt-dlp/yt-dlp). It can look up YouTube results, Internet Archive
items, and direct file links on web pages.

This is a maintainer-led personal project. It is not a service, it has no telemetry, and it
cannot bypass DRM, paywalls, or private access.

## Download (Windows)

Tagged GitHub Releases include a Windows zip with `HateDownloader.exe`. Extract it and double-click
the executable. Python is not required for that build.

1. Open [Releases](https://github.com/hatemecha/hate-downloader/releases)
2. Download `HateDownloader-windows.zip`
3. Extract it and run `HateDownloader.exe`

Windows SmartScreen may warn because these builds are not code-signed. Only download from this
repository. FFmpeg is still needed to merge separate audio/video streams and to convert formats;
the app can install it from **Tools → Dependencies** on Windows and Linux.

YouTube also requires [Deno](https://deno.com/) (2.3+) or Node.js (22+). The app can install Deno
from **Tools → Dependencies**; it passes the bundled path to yt-dlp directly. If you install a
runtime yourself, restart the app so it can find it. The app also packages yt-dlp's EJS scripts.

Linux and macOS packages are built the same way when a version tag is pushed. PyInstaller does not
cross-compile: each OS produces its own binary.

## What it does

- Analyze a public URL and pick a quality preset (MP4, MP3, FLAC, and others)
- Queue multiple downloads with progress, speed, and ETA
- Search YouTube, Internet Archive, and the web (via a SearXNG instance)
- Scan a page for direct video/audio links
- Keep a local download history
- Check and install Deno, FFmpeg, and aria2c, and update yt-dlp in source installs
- Save the downloaded media only; thumbnail images are opt-in

## What it does not do

- Bypass DRM, paywalls, or site protection
- Download from Netflix, Disney+, Prime Video, Spotify, or similar protected services
- Download a full playlist or channel in one click (paste a single video URL)
- Access private or age-restricted videos unless you supply cookies you already have

## Run from source

Requires Python 3.10+ on Windows 10/11, Linux, or macOS.

Python 3.12 or 3.13 is recommended for development and builds; upstream yt-dlp has
deprecated Python 3.10. Use a clean virtual environment for release packaging.

```bash
git clone https://github.com/hatemecha/hate-downloader.git
cd hate-downloader
python -m venv .venv
# Windows: .venv\Scripts\activate
source .venv/bin/activate
pip install -r requirements.txt
python run.py
```

On Linux, install FFmpeg from your package manager if you want conversions. On macOS, install
Python and FFmpeg with Homebrew; automatic FFmpeg/aria2 downloads are not available there.

## Development

```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt
ruff check .
pytest -q
python run.py --self-test
```

To build a native package for the current OS:

```bash
pip install ".[build]"
python scripts/build_exe.py
```

The output is `dist/HateDownloader.exe` on Windows, `dist/HateDownloader` on Linux, and
`dist/HateDownloader.app` on macOS, plus `LICENSE`, `THIRD_PARTY.md`, and `README.md`.

Application icons are included in source installs and native packages. Edit
`app/assets/icons/icon.svg` and run `python scripts/build_icons.py` to regenerate
the PNG, Windows ICO (16–256 px), and macOS ICNS. The executable self-test verifies
that the application icon is present.

## Usage

1. Paste a URL and click **Analyze**, or type words and click **Search**
2. Choose a quality preset and a folder
3. Click **Download** and watch the queue
4. Use **Advanced options** for codec, container, subtitles, and extras
5. History, Settings, and Setup are in the tabs and menus

## Configuration

**SearXNG.** Web search uses the instance in Settings → Advanced. Default:
`https://search.sapti.me`. You can point it at any instance you trust.

**Thumbnails.** No thumbnail image is saved by default. The "keep the thumbnail image
file" and "embed the thumbnail in the file" options are in Advanced options and Settings.
Embedding uses a temporary image that yt-dlp deletes after it is attached.

**Cookies.** For age-restricted public videos, export a cookies.txt file or set
“cookies from browser” (for example `firefox` or `chrome`) in Settings.

## Data and privacy

Hate Downloader has no telemetry. It makes outbound requests only for searches, analysis,
thumbnails, downloads, optional tool installs, and source-mode yt-dlp updates.

Web search queries go to the configured SearXNG instance. YouTube, Internet Archive, media hosts,
and tool download hosts receive normal request metadata such as IP address and user agent.

Settings, history, logs, and downloaded helper tools stay in the per-user directories selected by
`platformdirs`. Cookie paths are stored locally; cookies are then read by yt-dlp and sent to the
site being accessed.

Set `HATE_DOWNLOADER_HOME` before launch to place app data, settings, logs, tools and the default
download folder under a chosen directory. This is useful for isolated testing or portable use.

Packaged builds ship a frozen copy of yt-dlp. Update it by installing a newer Hate Downloader
release.

## Limitations

- yt-dlp extractors break when sites change; keep the app (or the source install) updated
- FFmpeg is required for conversions and for merging separate audio/video streams
- YouTube needs Deno 2.3+ or Node.js 22+; install Deno from the Setup window if needed
- Web search needs a reachable SearXNG instance
- Community binaries are not code-signed
- The Windows `.exe` bundles Qt under LGPL; see [THIRD_PARTY.md](THIRD_PARTY.md)

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Use GitHub issues for reproducible, non-sensitive bugs.
The maintainer makes final scope and release decisions.

To publish a GitHub Release with binaries, push a version tag (`v0.1.0-alpha`). The release workflow
builds Windows, Linux, and macOS packages and attaches them to the tag.

## License

MIT for this project's own code — see [LICENSE](LICENSE). Bundled and downloaded third-party
software has its own terms, listed in [THIRD_PARTY.md](THIRD_PARTY.md).
