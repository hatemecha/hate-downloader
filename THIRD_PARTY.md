# Third-party software

Hate Downloader's own source is MIT-licensed. It depends on other projects with their own terms.
This is an attribution list, not legal advice.

## Direct Python dependencies

| Project | License | Use |
| --- | --- | --- |
| [PySide6 / Qt for Python](https://doc.qt.io/qtforpython/) | LGPL | GUI. Packaged Windows/macOS/Linux builds bundle Qt libraries. |
| [yt-dlp](https://github.com/yt-dlp/yt-dlp) | Unlicense | URL analysis and downloads |
| [yt-dlp-ejs](https://github.com/yt-dlp/ejs) | Unlicense, MIT, ISC | YouTube JavaScript challenge scripts |
| [Mutagen](https://github.com/quodlibet/mutagen) | GPL-2.0-or-later | yt-dlp default dependency for audio tags |
| [Brotli](https://github.com/google/brotli) | MIT | HTTP decompression |
| [PyCryptodome](https://github.com/Legrandin/pycryptodome) | BSD / public domain | yt-dlp cryptography dependency |
| [websockets](https://github.com/python-websockets/websockets) | BSD-3-Clause | yt-dlp WebSocket support |
| [httpx](https://www.python-httpx.org/) | BSD-3-Clause | HTTP client |
| [beautifulsoup4](https://www.crummy.com/software/BeautifulSoup/) | MIT | HTML parsing for page scans |
| [lxml](https://lxml.de/) | BSD | HTML parser backend |
| [pydantic](https://docs.pydantic.dev/) | MIT | Data models |
| [platformdirs](https://github.com/tox-dev/platformdirs) | MIT | Per-user data/config/log paths |

Qt for Python is LGPL. The corresponding Qt source is available from the Qt project. This
application's preferred form of modification is the source in this repository.

For binary redistribution, this attribution list does not replace the full license texts or
the requirements to provide the corresponding Qt source and allow replacement of the LGPL
libraries. The current one-file package has not yet been verified against those requirements.
The bundled Mutagen distribution is GPL-2.0-or-later and also needs review for the combined
distribution. See [Qt's open-source obligations](https://www.qt.io/development/open-source-lgpl-obligations).

## Optional tools downloaded at runtime

These are **not** bundled in the repository. The Dependencies window can fetch them into the
per-user tools directory.

| Tool | Typical license | Source used by this app |
| --- | --- | --- |
| FFmpeg / FFprobe | LGPL / GPL, depending on the build | [gyan.dev](https://www.gyan.dev/ffmpeg/builds/) (Windows), [johnvansickle.com](https://johnvansickle.com/ffmpeg/) (Linux) |
| Deno | MIT | [Deno releases](https://github.com/denoland/deno/releases) |
| aria2 | GPL-2.0-or-later | [aria2 releases](https://github.com/aria2/aria2/releases) (Windows) |

If you distribute copies of those binaries yourself, you must follow their licenses.

## Network services

The app talks to sites the user asks it to (YouTube and other yt-dlp extractors, archive.org,
media CDNs) and to the configured SearXNG instance. Those services have their own terms.
