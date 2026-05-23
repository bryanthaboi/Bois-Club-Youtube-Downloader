# Bois Club YouTube Downloader

[![Build and Release](https://github.com/bryanthaboi/Bois-Club-Youtube-Downloader/actions/workflows/build.yml/badge.svg)](https://github.com/bryanthaboi/Bois-Club-Youtube-Downloader/actions/workflows/build.yml)

Tiny tkinter GUI around `yt-dlp`. Paste a YouTube URL, pick **Audio (MP3)** or
**Video (highest quality MP4)**, hit Download.

## Install

Grab the latest build from [Releases](https://github.com/bryanthaboi/Bois-Club-Youtube-Downloader/releases/latest):

- **macOS** — unzip `Bois-Club-Youtube-Downloader-macOS.zip`, drag the `.app` to
  `/Applications`. First launch: right-click → **Open** (ad-hoc signed).
- **Windows** — unzip `Bois-Club-Youtube-Downloader-Windows.zip` anywhere and run
  `Bois Club YouTube Downloader.exe`.

`ffmpeg` is bundled in both builds — no separate install needed.

## Run from source

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python ytmp3.py
```

Requires `ffmpeg` on your PATH when running from source.

## Build locally

```bash
./Scripts/build_mac.sh           # -> dist/Bois Club YouTube Downloader.app
pwsh ./Scripts/build_windows.ps1 # -> dist/Bois Club YouTube Downloader/
```
