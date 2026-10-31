# Release verification

## 0.1.0-alpha — Windows build, 2026-10-31

### Automated checks

- Ruff passes on the release checkout.
- 84 tests pass on Windows with Python 3.13.
- `run.py --self-test` passes and reports `Hate Downloader 0.1.0`.
- `dist/HateDownloader.exe` reports file and product version `0.1.0`, and its
  packaged `--self-test` passes.

### Real media checks

- Source mode, YouTube `jNQXAC9IVRw` with the default 480p MP4 preset:
  completed with only `Me at the zoo.mp4`. FFprobe reports video and audio
  streams. No `.webp` or other image file is written.
- Source mode, same video with thumbnail embedding enabled and "keep the
  thumbnail image" off: completed with only the MP4. The temporary image is
  deleted after embedding, and FFprobe shows an attached cover stream.
- A test fixture serves a local page and media through HTTP, then drives
  analyze and download through the Qt window and verifies the result. Its
  database and download folder are temporary.

### Packaged application check

The extracted executable was driven through its real widgets with Windows UI
Automation, using an isolated `HATE_DOWNLOADER_HOME`:

1. Welcome dialog appears; **Start** dismisses it.
2. The YouTube URL is entered and **Analyze** returns `Me at the zoo`.
3. **Download** enqueues the job, which reaches `completed` at 100%.
4. The downloads folder contains only `Me at the zoo.mp4` (745,938 bytes).
   FFprobe reports video and audio streams, and no image file exists.
5. The queue reports `Completed: Me at the zoo`.

This was a single Windows account and session, not a clean machine. It does not
validate every format, third-party service availability, or SmartScreen
behavior. The build is unsigned.

### Interface review

Fresh screenshots were rendered and reviewed for the main window, minimum size,
advanced mode, setup banner, both themes (Graphite and Paper), every settings
tab, dependencies, welcome, and error dialog.

### Known limitations and obligations

- Windows builds are unsigned. SmartScreen may warn; reputation is not
  established by these checks.
- FFmpeg is still required to merge separate audio/video streams and convert
  formats. YouTube needs Deno 2.3+ or Node.js 22+; the Setup window can install
  Deno, and Node remains a fallback.
- Public redistribution requires further review of the packaged third-party
  licenses, including PySide6/Qt and Mutagen, and the ability to replace Qt
  components in the one-file distribution. `THIRD_PARTY.md` is an attribution
  list, not evidence that every distribution obligation has been met.
- Linux and macOS artifacts require their native CI builds; they were not run
  here.
- Site changes, account restrictions, network failures, and uncommon formats
  cannot be covered by these smoke tests.
- Before broad distribution, run paste → analyze → download from the extracted
  ZIP on a clean Windows account, including the dependency setup flow.

### History and data isolation

An earlier test setup could touch the real local database because it patched
the wrong module path. That defect is fixed: tests and screenshot rendering use
temporary databases. `tests/test_paths_isolation.py` covers
`HATE_DOWNLOADER_HOME`, which isolates data, configuration, logs, tools, and the
default download folder. Whether real history was affected before the fix was
recorded is unknown.

### Distribution

Publish only the release ZIP and its SHA-256 checksum, not the raw development
`dist` directory. Keep the previous known-good release available. To roll back,
remove the new package from the featured release and restore the previous one;
do not delete user data.
