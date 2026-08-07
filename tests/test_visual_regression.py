"""
Visual regression tests for the Tier 15D surface-analysis renderers.

Renders deterministic reference surfaces through analyze_zebra / analyze_reflection
and compares the PNG output, pixel-for-pixel, against committed baseline images in
tests/baselines/. The renderer (core.render.write_png + tier15d _render_uv_stripes)
is fully deterministic, so any pixel drift signals a real change in geometry,
UV sampling, or the stripe-mapping maths — not rendering noise.

Comparison is done at the pixel level (both PNGs decoded, then diffed) so it is
robust to zlib-version differences in the compressed byte stream.

Regenerate baselines after an *intended* renderer change:

    PARTIKUS_UPDATE_BASELINES=1 squashfs-root/usr/bin/freecadcmd tests/run_tests.py
"""
import sys, os, math, zlib, struct

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from partikus import surface_from_points
from partikus.tier15d_analysis import analyze_zebra, analyze_reflection

_BASELINE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "baselines")
_UPDATE       = os.environ.get("PARTIKUS_UPDATE_BASELINES") == "1"
_RES          = 48   # baseline image size (RES x RES) — small keeps the PNGs tiny


# ── deterministic reference surfaces ───────────────────────────────────────────

def _flat_grid(n=5, size=20):
    return [[[i * size / (n - 1) - size / 2,
              j * size / (n - 1) - size / 2,
              0.0] for j in range(n)] for i in range(n)]


def _dome_grid(n=7, size=40, height=12):
    """Smooth radial bump (C-infinity) — produces clean, well-defined zebra stripes."""
    grid = []
    for i in range(n):
        row = []
        for j in range(n):
            x  = i * size / (n - 1) - size / 2
            y  = j * size / (n - 1) - size / 2
            r2 = (x / (size / 2)) ** 2 + (y / (size / 2)) ** 2
            z  = height * math.exp(-1.5 * r2)
            row.append([x, y, z])
        grid.append(row)
    return grid


def _flat_surf():
    return surface_from_points(_flat_grid())


def _dome_surf():
    return surface_from_points(_dome_grid())


# ── minimal PNG decoder (matches core.render.write_png output exactly) ──────────

def _decode_png(data):
    """Decode an 8-bit RGB, filter-0 PNG as written by core.render.write_png.

    Returns (width, height, [(r, g, b), ...]) row-major, top-left first.
    """
    assert data[:8] == b"\x89PNG\r\n\x1a\n", "not a PNG"
    pos    = 8
    width  = height = None
    idat   = bytearray()
    while pos < len(data):
        (length,) = struct.unpack(">I", data[pos:pos + 4])
        tag       = data[pos + 4:pos + 8]
        chunk     = data[pos + 8:pos + 8 + length]
        if tag == b"IHDR":
            width, height, bit_depth, color_type = struct.unpack(">IIBB", chunk[:10])
            assert bit_depth == 8 and color_type == 2, "expected 8-bit RGB PNG"
        elif tag == b"IDAT":
            idat += chunk
        elif tag == b"IEND":
            break
        pos += 12 + length  # 4 (len) + 4 (tag) + length (data) + 4 (crc)

    raw    = zlib.decompress(bytes(idat))
    stride = width * 3
    pixels = []
    for y in range(height):
        base = y * (stride + 1)
        assert raw[base] == 0, "only PNG filter 0 is supported"
        rowstart = base + 1
        for x in range(width):
            o = rowstart + x * 3
            pixels.append((raw[o], raw[o + 1], raw[o + 2]))
    return width, height, pixels


def _pixel_diff(a, b):
    """Return (differing_pixel_count, first_diff_coord_or_None) for two decoded images."""
    wa, ha, pa = a
    wb, hb, pb = b
    assert (wa, ha) == (wb, hb), f"dimension mismatch {wa}x{ha} vs {wb}x{hb}"
    count = 0
    first = None
    for idx, (pxa, pxb) in enumerate(zip(pa, pb)):
        if pxa != pxb:
            count += 1
            if first is None:
                first = (idx % wa, idx // wa)
    return count, first


def _check_against_baseline(name, png_bytes):
    """Compare rendered PNG against the committed baseline, capturing if requested."""
    assert png_bytes is not None, f"{name}: renderer returned no image_bytes"
    path = os.path.join(_BASELINE_DIR, name)

    if _UPDATE or not os.path.exists(path):
        os.makedirs(_BASELINE_DIR, exist_ok=True)
        with open(path, "wb") as f:
            f.write(png_bytes)
        if not _UPDATE:
            raise AssertionError(
                f"baseline '{name}' was missing — captured it now. Re-run to verify, "
                f"or set PARTIKUS_UPDATE_BASELINES=1 to (re)capture intentionally.")
        return

    with open(path, "rb") as f:
        baseline = f.read()
    count, first = _pixel_diff(_decode_png(baseline), _decode_png(png_bytes))
    assert count == 0, f"{name}: {count} pixel(s) differ from baseline (first at {first})"


# ── determinism + decoder self-checks (no baseline needed) ─────────────────────

def test_zebra_render_is_deterministic():
    a = analyze_zebra(_dome_surf(), stripe_count=10, resolution=_RES)["image_bytes"]
    b = analyze_zebra(_dome_surf(), stripe_count=10, resolution=_RES)["image_bytes"]
    assert a == b, "zebra renderer is not deterministic — visual regression is meaningless"


def test_reflection_render_is_deterministic():
    a = analyze_reflection(_dome_surf(), stripe_count=8, resolution=_RES)["image_bytes"]
    b = analyze_reflection(_dome_surf(), stripe_count=8, resolution=_RES)["image_bytes"]
    assert a == b, "reflection renderer is not deterministic"


def test_decoder_roundtrip_dimensions():
    r = analyze_zebra(_flat_surf(), resolution=_RES)
    w, h, px = _decode_png(r["image_bytes"])
    assert (w, h) == (_RES, _RES)
    assert len(px) == _RES * _RES


def test_dome_zebra_has_stripe_contrast():
    _, _, px = _decode_png(
        analyze_zebra(_dome_surf(), stripe_count=10, resolution=_RES)["image_bytes"])
    blacks = sum(1 for p in px if p == (0, 0, 0))
    whites = sum(1 for p in px if p == (255, 255, 255))
    assert blacks > 0 and whites > 0, "curved surface produced no zebra stripe contrast"


# ── baseline comparisons ───────────────────────────────────────────────────────

def test_zebra_flat_matches_baseline():
    r = analyze_zebra(_flat_surf(), stripe_count=8, resolution=_RES)
    _check_against_baseline("zebra_flat.png", r["image_bytes"])


def test_zebra_dome_matches_baseline():
    r = analyze_zebra(_dome_surf(), stripe_count=10, resolution=_RES)
    _check_against_baseline("zebra_dome.png", r["image_bytes"])


def test_reflection_dome_matches_baseline():
    r = analyze_reflection(_dome_surf(), stripe_count=8, resolution=_RES)
    _check_against_baseline("reflection_dome.png", r["image_bytes"])
