# Changelog

## 0.1.0 — first alpha

First public alpha.

- New graphite and paper themes, a quieter layout, and a single signal red for the
  Download action, the active section, setup notices, and queue progress
- Thumbnails are no longer saved next to downloads by default; embedding removes its
  temporary image, and existing installs are migrated once
- Install Deno from the Setup window; bundled Deno is passed to yt-dlp, and Node.js
  remains a supported fallback
- Safer retries, cancellation during processing, and accurate completed history
- Handle fractional media durations, missing metadata, and invalid saved settings
- Allow direct downloads without requiring FFmpeg when no processing is needed
- Search, analyze, and download public media through yt-dlp
- YouTube, Internet Archive, and SearXNG web search
- Download queue, history, and a dependency helper for Deno, FFmpeg, and aria2c
- Windows, Linux, and macOS packages from tagged GitHub Releases
