#!/usr/bin/env bash
# Build Bois Club YouTube Downloader as a macOS .app bundle.
# Bundles a static ffmpeg binary so users don't need to install it.
#
# Usage:
#   ./Scripts/build_mac.sh            # build -> dist/Bois Club YouTube Downloader.app
#   ./Scripts/build_mac.sh run        # build + launch

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

APP_NAME="Bois Club YouTube Downloader"
DIST="$ROOT/dist"
BUILD="$ROOT/build"
VENV="$ROOT/.venv-build"
FFMPEG_BIN="$ROOT/.ffmpeg/ffmpeg"

echo "==> verifying python has tkinter (PyInstaller bundles tk statically and silently produces a broken .app if _tkinter is missing)"
PY_VER="$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
if ! python3 -c "import tkinter" >/dev/null 2>&1; then
    if command -v brew >/dev/null 2>&1; then
        echo "    installing python-tk@${PY_VER} via brew"
        brew install "python-tk@${PY_VER}"
    else
        echo "ERROR: python3 ($PY_VER) is missing the tkinter (_tkinter) module." >&2
        echo "       Install a python build that includes Tk, e.g. 'brew install python-tk@${PY_VER}'." >&2
        exit 1
    fi
    python3 -c "import tkinter" >/dev/null 2>&1 || {
        echo "ERROR: tkinter still missing after brew install python-tk@${PY_VER}." >&2
        exit 1
    }
fi

echo "==> python venv ($VENV)"
python3 -m venv "$VENV"
"$VENV/bin/pip" install --upgrade pip wheel >/dev/null
"$VENV/bin/pip" install -r requirements.txt pyinstaller >/dev/null

if [[ ! -x "$FFMPEG_BIN" ]]; then
    echo "==> fetching ffmpeg (static, evermeet.cx)"
    mkdir -p "$ROOT/.ffmpeg"
    curl -fsSL -o "$ROOT/.ffmpeg/ffmpeg.zip" \
        https://evermeet.cx/ffmpeg/getrelease/zip
    unzip -o "$ROOT/.ffmpeg/ffmpeg.zip" -d "$ROOT/.ffmpeg" >/dev/null
    rm "$ROOT/.ffmpeg/ffmpeg.zip"
    chmod +x "$FFMPEG_BIN"
fi

echo "==> pyinstaller"
rm -rf "$DIST" "$BUILD"
"$VENV/bin/pyinstaller" \
    --noconfirm \
    --windowed \
    --name "$APP_NAME" \
    --osx-bundle-identifier com.boisclub.ytdownloader \
    --add-binary "$FFMPEG_BIN:." \
    ytmp3.py

# PyInstaller's macOS bundle puts the executable at Contents/MacOS/<name>,
# and bundled binaries land in Contents/Frameworks/. yt-dlp finds ffmpeg by
# walking PATH, so wrap the real binary in a tiny launcher that prepends the
# bundle's Frameworks dir.
APP_BUNDLE="$DIST/$APP_NAME.app"
EXEC_DIR="$APP_BUNDLE/Contents/MacOS"
REAL_EXEC="$EXEC_DIR/$APP_NAME"
WRAPPED="$EXEC_DIR/$APP_NAME-bin"

if [[ -x "$REAL_EXEC" && ! -x "$WRAPPED" ]]; then
    mv "$REAL_EXEC" "$WRAPPED"
    cat > "$REAL_EXEC" <<'LAUNCH'
#!/bin/bash
DIR="$(cd "$(dirname "$0")" && pwd)"
export PATH="$DIR/../Frameworks:$PATH"
exec "$DIR/$(basename "$0")-bin" "$@"
LAUNCH
    chmod +x "$REAL_EXEC"
fi

echo "==> codesign (ad-hoc)"
codesign --force --deep --sign - "$APP_BUNDLE" >/dev/null 2>&1 || true

echo ""
echo "Built: $APP_BUNDLE"

if [[ "${1:-}" == "run" ]]; then
    open "$APP_BUNDLE"
fi
