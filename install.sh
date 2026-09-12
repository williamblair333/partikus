#!/usr/bin/env bash
# install.sh — set up Partikus with FreeCAD >= 1.1
# Accepts an existing system freecadcmd, an already-extracted AppImage,
# or a raw AppImage in this directory (extracts it automatically).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
MIN_MAJOR=1
MIN_MINOR=1

GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; BOLD='\033[1m'; NC='\033[0m'
ok()      { printf "${GREEN}✓${NC}  %s\n" "$*"; }
warn()    { printf "${YELLOW}!${NC}  %s\n" "$*"; }
die()     { printf "${RED}✗${NC}  %s\n" "$*" >&2; exit 1; }
heading() { printf "\n${BOLD}%s${NC}\n" "$*"; }

# Return version string (e.g. "1.1.1") for a freecadcmd binary, or empty string.
get_version() {
    local cmd="$1"
    local ver
    # --version flag is the fast path; some builds print to stderr
    ver=$("$cmd" --version 2>&1 | grep -oE '[0-9]+\.[0-9]+(\.[0-9]+)?' | head -1 || true)
    if [[ -z "$ver" ]]; then
        # Fallback: run a tiny inline script via a temp file
        local tmp
        tmp=$(mktemp /tmp/fc_ver_XXXXXX.py)
        printf 'import FreeCAD, sys\nv=FreeCAD.Version()\nsys.stderr.write(v[0]+"."+v[1]+"\\n")\n' > "$tmp"
        ver=$("$cmd" "$tmp" 2>&1 | grep -oE '[0-9]+\.[0-9]+' | head -1 || true)
        rm -f "$tmp"
    fi
    echo "$ver"
}

# Return 0 if version string meets the minimum.
version_ok() {
    local ver="$1"
    [[ -z "$ver" ]] && return 1
    local major minor
    major=$(echo "$ver" | cut -d. -f1)
    minor=$(echo "$ver" | cut -d. -f2)
    [[ "$major" -gt "$MIN_MAJOR" || ( "$major" -eq "$MIN_MAJOR" && "$minor" -ge "$MIN_MINOR" ) ]]
}

FREECADCMD=""

heading "Partikus — install"

# 1. System freecadcmd
if command -v freecadcmd &>/dev/null; then
    SYS_CMD="$(command -v freecadcmd)"
    VER=$(get_version "$SYS_CMD")
    if version_ok "$VER"; then
        FREECADCMD="$SYS_CMD"
        ok "System freecadcmd $VER — $SYS_CMD"
    else
        warn "System freecadcmd found but version '${VER:-unknown}' < ${MIN_MAJOR}.${MIN_MINOR} — skipping"
    fi
fi

# 2. Already-extracted AppImage (squashfs-root present)
if [[ -z "$FREECADCMD" ]]; then
    AI_CMD="$SCRIPT_DIR/squashfs-root/usr/bin/freecadcmd"
    if [[ -x "$AI_CMD" ]]; then
        VER=$(get_version "$AI_CMD")
        if version_ok "$VER"; then
            FREECADCMD="$AI_CMD"
            ok "AppImage (already extracted) freecadcmd $VER"
        else
            warn "Extracted AppImage freecadcmd version '${VER:-unknown}' < ${MIN_MAJOR}.${MIN_MINOR}"
        fi
    fi
fi

# 3. Raw AppImage in the project root — extract it
if [[ -z "$FREECADCMD" ]]; then
    APPIMAGE=$(find "$SCRIPT_DIR" -maxdepth 1 -name "FreeCAD*.AppImage" | sort -V | tail -1 || true)
    if [[ -n "$APPIMAGE" ]]; then
        printf "  Extracting %s ...\n" "$(basename "$APPIMAGE")"
        chmod +x "$APPIMAGE"
        (cd "$SCRIPT_DIR" && "$APPIMAGE" --appimage-extract >/dev/null)
        AI_CMD="$SCRIPT_DIR/squashfs-root/usr/bin/freecadcmd"
        if [[ ! -x "$AI_CMD" ]]; then
            die "Extraction finished but freecadcmd not found at squashfs-root/usr/bin/freecadcmd"
        fi
        VER=$(get_version "$AI_CMD")
        if version_ok "$VER"; then
            FREECADCMD="$AI_CMD"
            ok "AppImage extracted — freecadcmd $VER"
        else
            die "Extracted AppImage version '${VER:-unknown}' < ${MIN_MAJOR}.${MIN_MINOR} — need FreeCAD >= ${MIN_MAJOR}.${MIN_MINOR}"
        fi
    fi
fi

if [[ -z "$FREECADCMD" ]]; then
    printf '\n'
    die "FreeCAD ${MIN_MAJOR}.${MIN_MINOR}+ not found. Options:
    1. Install FreeCAD >= ${MIN_MAJOR}.${MIN_MINOR} from https://www.freecad.org/downloads.php
       (freecadcmd must be on your PATH)
    2. Place a FreeCAD AppImage (>= ${MIN_MAJOR}.${MIN_MINOR}) in this directory and re-run install.sh"
fi

# Resolve AppRun path for GUI mode (AppImage only)
APPRUN="$SCRIPT_DIR/squashfs-root/AppRun"

# ── Install the workbench into FreeCAD's user Mod directory ───────────────────
#
# FreeCAD only ever runs partikus/gui/workbench.py by executing InitGui.py from
# the root of a directory on its Mod path. Until this step existed the workbench
# could not appear in the dropdown no matter what the registration code did.

heading "FreeCAD workbench"

# The two loader files are tracked in the repo — this script does not generate
# them, so there is one copy and it cannot drift from what git has.
for loader in Init.py InitGui.py; do
    [[ -f "$SCRIPT_DIR/$loader" ]] \
        || die "$loader is missing from $SCRIPT_DIR — FreeCAD loads the add-on by
    that exact filename and skips the directory silently without it.
    Restore it with: git checkout -- $loader"
done

# Ask FreeCAD where its user Mod directory is. Never guess: the path is stamped
# with the minor version (v1-1, v1-2, ...) and a wrong one installs into a
# directory FreeCAD does not read, with no error at any point.
#
# freecadcmd captures stdout, so the probe writes to stderr.
MOD_PARENT=""
PROBE=$(mktemp /tmp/partikus_moddir_XXXXXX.py)
printf 'import FreeCAD, sys\nsys.stderr.write("USERAPPDATA=" + FreeCAD.getUserAppDataDir() + "\\n")\n' > "$PROBE"
MOD_PARENT=$("$FREECADCMD" "$PROBE" 2>&1 | sed -n 's/^USERAPPDATA=//p' | head -1 || true)
rm -f "$PROBE"
MOD_PARENT="${MOD_PARENT%/}"

if [[ -z "$MOD_PARENT" || ! -d "$MOD_PARENT" ]]; then
    warn "Could not determine FreeCAD's user app data directory — workbench NOT installed."
    warn "The headless API still works. To install it by hand, run FreeCAD's Python console:"
    warn "    import FreeCAD; FreeCAD.getUserAppDataDir()"
    warn "then: ln -sfn '$SCRIPT_DIR' <that path>/Mod/partikus"
else
    MOD_DIR="$MOD_PARENT/Mod"
    LINK="$MOD_DIR/partikus"
    mkdir -p "$MOD_DIR"

    if [[ -d "$LINK" && ! -L "$LINK" ]]; then
        # A real directory here is someone else's install (Addon Manager, a
        # manual copy). Linking into it would nest partikus/partikus and load
        # neither cleanly, so leave it alone and say so.
        warn "$LINK is a real directory, not a link — leaving it untouched."
        warn "Remove or rename it and re-run install.sh to link this checkout instead."
    else
        ln -sfn "$SCRIPT_DIR" "$LINK"
        ok "Workbench installed: $LINK -> $SCRIPT_DIR"
        printf '     Restart FreeCAD, then pick "Partikus" from the workbench dropdown.\n'
        printf '     Re-run this script after a FreeCAD upgrade — the Mod path is\n'
        printf '     version-stamped, and an upgrade leaves the workbench behind.\n'
        printf '     To uninstall: rm %s\n' "$LINK"
    fi
fi

heading "Setup complete"
printf '\n'
printf '  Run examples (headless):\n'
printf '    %s examples/capped_cylinder.py\n' "$FREECADCMD"
printf '    %s examples/rpi4_enclosure.py\n'  "$FREECADCMD"
printf '\n'
if [[ -x "$APPRUN" ]]; then
    printf '  Run examples (live GUI — watch it build):\n'
    printf '    PARTIKUS_GUI=1 %s freecad examples/rpi4_enclosure.py\n' "$APPRUN"
    printf '\n'
    printf '  Open a result file in FreeCAD:\n'
    printf '    %s examples/out/rpi4_enclosure.FCStd\n' "$APPRUN"
    printf '\n'
fi
printf '  Run tests:\n'
printf '    ./run_tests.sh\n'
printf '    (or: %s tests/run_tests.py)\n' "$FREECADCMD"
printf '\n'
