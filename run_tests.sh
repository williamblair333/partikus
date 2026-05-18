#!/usr/bin/env bash
# Run the Partikus test suite via FreeCAD's headless Python interpreter.
set -e
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
FREECAD_CMD="$SCRIPT_DIR/squashfs-root/usr/bin/freecadcmd"

if [ ! -x "$FREECAD_CMD" ]; then
    echo "freecadcmd not found — run the AppImage with --appimage-extract first:"
    echo "  ./FreeCAD_1.1.1-Linux-x86_64-py311.AppImage --appimage-extract"
    exit 1
fi

exec "$FREECAD_CMD" "$SCRIPT_DIR/tests/run_tests.py" "$@"
