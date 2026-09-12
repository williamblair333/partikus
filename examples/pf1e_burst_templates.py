"""
examples/pf1e_burst_templates.py — Pathfinder 1E area-of-effect ring templates

Snap-together rings you lay over a 1-inch battlemat to show the reach of a
10 / 20 / 30 ft area effect.

Two outline styles, switched by OUTLINE:

    "circle"  (default) — a true circle at literal scale: 10 ft = 2 inches, so
              the rings are 4, 8 and 12 inches across. Clean to look at, and
              the size players expect. The circle passes through the centre of
              each square exactly N away, so it cuts through the outermost
              squares rather than enclosing them.

    "grid"    — the exact set of affected squares under Pathfinder's 1-2-1
              diagonal rule, as a stepped outline whose every edge lies on a
              grid line. Blockier, but nothing is left to judgement and it
              self-aligns to the mat.

The two disagree on the diagonals, and the circle is the smaller of them: at
20 ft the square 3 across and 3 up is affected by the rules (3 + 3//2 = 4
squares, exactly 20 ft) but its centre lies 4.24 squares out, outside the
circle. Read the circle as the reach of the effect, not as a square-by-square
adjudication — the build log prints how many squares each circle misses.

Two centring modes, switched by CENTER_ON:
    "square"        emanation/spread centred on a creature — the miniature
                    stands in the empty middle square.
    "intersection"  burst centred on a grid corner (fireball &c).

Finding the centre: each ring carries four radial PADS at north/south/east/west
whose tips point inward at the centre. On segmented rings the split runs down
the middle of each pad, so the four seams cross exactly on the miniature.

Parts produced (per radius):
    <n> holes punched in each pad = radius in squares (2 / 4 / 6). Holes rather
    than recessed text because partikus deboss() is not implemented yet
    (tier10_modifiers.py) — and on a 2 mm flat print, through-holes read better
    anyway.

    Rings wider than BED_MM are quartered on the cardinal axes. The four
    quarters are congruent under 90-degree rotation, so only one segment is
    exported — print it four times.

Shared parts (printed once):
    joint key     — bowtie spline, press-fits two segment ends together.
                    Print one per seam: 4 for each segmented ring.
                    KEY_CLEAR is the press-fit allowance — print ONE key and
                    check the fit before committing to four large segments.
    centre collar — 1-inch square frame the miniature's base drops into.

Run headless (no display required):
    cd /opt/proj/partikus
    squashfs-root/usr/bin/freecadcmd examples/pf1e_burst_templates.py

Run with live GUI (watch it build step-by-step):
    PARTIKUS_GUI=1 squashfs-root/AppRun freecad examples/pf1e_burst_templates.py

Output files land in  examples/out/ :
    pf1e_10ft_whole.stl / .step         one piece
    pf1e_20ft_segment.stl / .step       print 4x
    pf1e_30ft_segment.stl / .step       print 4x
    pf1e_joint_key.stl / .step          print 4x per segmented ring
    pf1e_centre_collar.stl / .step      print 1x
    pf1e_burst_templates.FCStd          every ring assembled, for inspection
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ─── Imports ──────────────────────────────────────────────────────────────────
from partikus import (
    # Tier 1  — primitives
    box, cylinder,
    # Tier 3  — 2D profiles
    polyline,
    # Tier 9  — boolean operations
    union, difference, intersection,
    # Tier 12 — sweep / loft
    extrude,
    # Tier 14 — assembly
    translate, rotate,
)
from partikus.io import to_step, to_stl, save_fcstd


# ─── GUI mode ─────────────────────────────────────────────────────────────────
GUI_MODE = os.environ.get("PARTIKUS_GUI") == "1"
_fgui = None
_fdoc = None


def _log(msg):
    if GUI_MODE:
        try:
            import FreeCAD as _FC2
            _FC2.Console.PrintMessage(msg + "\n")
            return
        except Exception:
            pass
    sys.stderr.write(msg + "\n")


if GUI_MODE:
    try:
        import FreeCADGui as _fgui
        import FreeCAD as _FC
        _fdoc = _FC.newDocument("pf1e_burst_templates")
        _log("[gui] GUI mode active — shapes appear in FreeCAD as each step runs")
    except Exception as _e:
        _log(f"[gui] FreeCADGui unavailable ({_e})")
        _log("[gui] Tip: PARTIKUS_GUI=1 squashfs-root/AppRun freecad "
             "examples/pf1e_burst_templates.py")
        GUI_MODE = False
        _fgui = None


def _gui_show(shape, label):
    """Add shape to the live FreeCAD document and refresh the 3-D view."""
    if not GUI_MODE or _fgui is None or _fdoc is None:
        return
    raw = shape.shape if hasattr(shape, "shape") else shape
    obj = _fdoc.addObject("Part::Feature", label.replace(" ", "_"))
    obj.Shape = raw
    _fdoc.recompute()
    _fgui.updateGui()
    try:
        _fgui.ActiveDocument.ActiveView.fitAll()
    except Exception:
        pass
    try:
        from PySide2.QtWidgets import QApplication
        QApplication.processEvents()
    except Exception:
        pass


# ─── Parameters  (edit these to retune the set) ───────────────────────────────

GRID_MM     = 25.4    # one battlemat square — 1 inch
FT_PER_SQ   = 5       # feet represented by one square
RADII_FT    = (10, 20, 30)
OUTLINE     = "circle"   # "circle" (true circle) | "grid" (stepped squares)
CENTER_ON   = "square"   # "square" (emanation) | "intersection" (burst)

BAND_W      = 5.0     # radial width of the outline band (mm)
THICK       = 2.0     # part thickness (mm)

BED_MM      = 180.0   # usable print bed square — Bambu A1 mini is 180 x 180
SEGMENTS    = 4       # pieces a too-large ring is cut into (cardinal cuts)

PAD_W       = 14.0    # radial width of the band where a joint lives (mm)
PAD_HALF_L  = 12.0    # pad reach along the band, each side of the cut (mm)

KEY_LEN     = 16.0    # bowtie key length, across the seam (mm)
KEY_END_W   = 8.0     # bowtie width at each end (mm)
KEY_WAIST_W = 5.0     # bowtie width at the waist (mm)
KEY_CLEAR   = 0.10    # per-face socket clearance — raise if the key won't seat

DOT_D       = 3.0     # radius-label hole diameter (mm)
DOT_PITCH   = 5.0     # centre spacing of label holes (mm)
DOT_GROUP_Y = 6.0     # label-group offset from the cut line, along the band (mm)

COLLAR_OPEN = 25.8    # centre collar inner opening — 1 inch + 0.4 mm clearance
COLLAR_BAND = 2.0     # centre collar wall width (mm)

OUT_DIR     = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out")

_BIG   = 4000.0       # oversize stock for half-space intersections
_CUT_D = THICK * 4    # punch depth that safely clears the part in Z
_EPS   = 0.01         # corner-patch overlap — see corner_patches()


# ─── Grid geometry ────────────────────────────────────────────────────────────

def pf1e_distance(dx, dy):
    """
    Pathfinder 1E movement distance in squares, using the 1-2-1 diagonal rule:
    every second diagonal step costs double.

    Args:
        dx, dy: non-negative square counts along each axis

    Example:
        pf1e_distance(3, 3)  ->  4    (three diagonals = 3, plus 1 extra)
    """
    if dx < 0 or dy < 0:
        raise ValueError("pf1e_distance takes non-negative square counts")
    return max(dx, dy) + min(dx, dy) // 2


def cell_set(n, mode):
    """
    Every grid cell inside a radius-*n*-square effect, as a set of (i, j) keys.

    This is the rules-exact answer. OUTLINE="grid" traces it; OUTLINE="circle"
    approximates it and is measured against it in the build log.

    Args:
        n:    radius in squares
        mode: "square"       — centred on a creature's square, spans 2n+1
              "intersection" — centred on a grid corner, spans 2n

    Example:
        cell_set(2, "square")   ->  21 cells (a 5x5 block, four corners clipped)
    """
    if mode == "square":
        span = range(-n, n + 1)
        return {(i, j) for i in span for j in span
                if pf1e_distance(abs(i), abs(j)) <= n}
    if mode == "intersection":
        span = range(-n, n)
        return {(i, j) for i in span for j in span
                if pf1e_distance(i + 1 if i >= 0 else -i,
                                 j + 1 if j >= 0 else -j) <= n}
    raise ValueError(f"CENTER_ON must be 'square' or 'intersection', got {mode!r}")


def cell_center(i, j, mode):
    """XY centre of grid cell (i, j) in mm, for the given centring mode."""
    if mode == "square":
        return i * GRID_MM, j * GRID_MM
    return (i + 0.5) * GRID_MM, (j + 0.5) * GRID_MM


def outer_extent(n, mode, outline):
    """Distance in mm from the centre to the outermost face of the template."""
    if outline == "circle":
        # Literal scale: 10 ft = 2 inches, measured from the centre.
        return n * GRID_MM
    if outline != "grid":
        raise ValueError(f"OUTLINE must be 'circle' or 'grid', got {outline!r}")
    return (n + 0.5) * GRID_MM if mode == "square" else n * GRID_MM


def cells_missed_by_circle(n, mode):
    """
    Affected squares whose centres fall outside the literal-scale circle.

    These are the diagonal squares the circle under-covers. Reported in the
    build log so the compromise is measured rather than assumed — the circle
    shows the reach of an effect, not a square-by-square adjudication.
    """
    r = n * GRID_MM
    return {(i, j) for (i, j) in cell_set(n, mode)
            if math.hypot(*cell_center(i, j, mode)) > r}


def _runs(values):
    """Collapse a sorted list of ints into maximal consecutive (start, end) runs."""
    out = []
    start = prev = values[0]
    for v in values[1:]:
        if v == prev + 1:
            prev = v
        else:
            out.append((start, prev))
            start = prev = v
    out.append((start, prev))
    return out


def boundary_bars(cells, mode):
    """
    The stepped outline, as a list of (cx, cy, lx, ly) axis-aligned footprints.

    A bar is emitted just *inside* every cell face that has no neighbouring cell,
    so the union hugs the grid lines exactly. Collinear faces are merged into
    single runs first, which keeps the boolean fuse fast and the result clean.
    """
    bars = []
    inset = GRID_MM / 2 - BAND_W / 2

    # North / south faces — bars run along X.
    for dj, sign in ((1, 1), (-1, -1)):
        rows = {}
        for (i, j) in cells:
            if (i, j + dj) not in cells:
                rows.setdefault(j, []).append(i)
        for j, ilist in rows.items():
            for i0, i1 in _runs(sorted(ilist)):
                x0, yc = cell_center(i0, j, mode)
                x1, _ = cell_center(i1, j, mode)
                bars.append(((x0 + x1) / 2, yc + sign * inset,
                             (x1 - x0) + GRID_MM, BAND_W))

    # East / west faces — bars run along Y.
    for di, sign in ((1, 1), (-1, -1)):
        cols = {}
        for (i, j) in cells:
            if (i + di, j) not in cells:
                cols.setdefault(i, []).append(j)
        for i, jlist in cols.items():
            for j0, j1 in _runs(sorted(jlist)):
                xc, y0 = cell_center(i, j0, mode)
                _, y1 = cell_center(i, j1, mode)
                bars.append((xc + sign * inset, (y0 + y1) / 2,
                             BAND_W, (y1 - y0) + GRID_MM))

    return bars


def corner_patches(cells, mode):
    """
    Square fillers for the inward corners of the staircase, as a list of
    (cx, cy) centres.

    At a *convex* corner one cell owns both boundary faces, so its two bars
    overlap and fuse on their own. At a *concave* corner the two bars belong to
    different cells and, once inset, meet along a single edge — zero shared
    volume, which OCC will not fuse. The outline then exports as several
    disjoint solids that look right on screen and fall apart in the slicer.

    So: inspect the four cells around every grid vertex. Three present and one
    absent is a concave corner — fill it, on the diagonal away from the missing
    cell. Two present on a diagonal is a pinch point and gets both fills. The
    patch is grown by _EPS so it shares volume with the bars rather than merely
    touching them.
    """
    half = GRID_MM / 2
    reach = BAND_W / 2
    patches = []

    lo = min(min(i, j) for i, j in cells)
    hi = max(max(i, j) for i, j in cells)

    # Quadrant offsets keyed by which of the four cells around the vertex it is.
    quad = {"sw": (-1, -1), "se": (1, -1), "nw": (-1, 1), "ne": (1, 1)}

    for i in range(lo, hi + 2):
        for j in range(lo, hi + 2):
            here = {
                "sw": (i - 1, j - 1) in cells,
                "se": (i, j - 1) in cells,
                "nw": (i - 1, j) in cells,
                "ne": (i, j) in cells,
            }
            present = sum(here.values())
            cx, cy = cell_center(i, j, mode)
            vx, vy = cx - half, cy - half   # the shared grid vertex

            if present == 3:
                # Concave: fill the diagonal opposite the one missing cell.
                missing = next(k for k, v in here.items() if not v)
                sx, sy = quad[missing]
                patches.append((vx - sx * reach, vy - sy * reach))
            elif present == 2 and here["sw"] == here["ne"]:
                # Pinch point: two cells meeting corner-to-corner. Fill both.
                for k in ("sw", "ne") if here["sw"] else ("se", "nw"):
                    sx, sy = quad[k]
                    patches.append((vx + sx * reach, vy + sy * reach))

    return patches


# ─── Part construction ────────────────────────────────────────────────────────

def build_circle_band(n):
    """A plain annulus at literal scale — one boolean, nothing to come apart."""
    r = n * GRID_MM
    if r <= BAND_W:
        raise ValueError(f"radius {r:.1f} mm is not wider than BAND_W={BAND_W}")
    return difference(
        translate(cylinder(radius=r, height=THICK), dz=THICK / 2),
        translate(cylinder(radius=r - BAND_W, height=_CUT_D), dz=THICK / 2),
    )


def build_grid_band(n, mode):
    """The stepped outline of the rules-exact affected-square set."""
    cells = cell_set(n, mode)
    solids = [translate(box(lx, ly, THICK), dx=cx, dy=cy, dz=THICK / 2)
              for cx, cy, lx, ly in boundary_bars(cells, mode)]
    patch = BAND_W + 2 * _EPS
    solids += [translate(box(patch, patch, THICK), dx=cx, dy=cy, dz=THICK / 2)
               for cx, cy in corner_patches(cells, mode)]
    return union(*solids)


def build_band(n, mode, outline):
    """The bare outline for a radius-*n*-square effect, in the chosen style."""
    if outline == "circle":
        return build_circle_band(n)
    if outline == "grid":
        return build_grid_band(n, mode)
    raise ValueError(f"OUTLINE must be 'circle' or 'grid', got {outline!r}")


def pad_center(n, mode, outline):
    """
    Radial distance to the centre of a joint pad. The pad grows inward only, so
    it never pushes the part past the ring's own bounding box — which is what
    keeps the largest quarter on the bed.
    """
    return outer_extent(n, mode, outline) - PAD_W / 2


def pad_solids(n, mode, outline):
    """
    Four radial pads at N/S/E/W. These carry the joints and the labels, and
    their inward-pointing tips are what you line the miniature up against.

    On a circle the pad's outer corners would stand proud of the arc, so each
    pad is clipped back to the outer disk. On the grid outline every cardinal
    face spans at least three squares of straight run, so a pad centred on the
    axis always lands mid-run and needs no clipping.
    """
    c = pad_center(n, mode, outline)
    ew = box(PAD_W, 2 * PAD_HALF_L, THICK)
    ns = box(2 * PAD_HALF_L, PAD_W, THICK)
    pads = [
        translate(ew, dx=c, dz=THICK / 2),
        translate(ew, dx=-c, dz=THICK / 2),
        translate(ns, dy=c, dz=THICK / 2),
        translate(ns, dy=-c, dz=THICK / 2),
    ]
    if outline == "circle":
        disk = translate(
            cylinder(radius=outer_extent(n, mode, outline), height=_CUT_D),
            dz=THICK / 2)
        pads = [intersection(p, disk) for p in pads]
    return pads


def bowtie_profile(grow=0.0):
    """
    Closed bowtie (double-dovetail) wire, long axis along Y, centred at origin.

    Args:
        grow: outward offset in mm — 0 for the key itself, KEY_CLEAR for a socket
    """
    half_len = KEY_LEN / 2 + grow
    half_end = KEY_END_W / 2 + grow
    half_waist = KEY_WAIST_W / 2 + grow
    return polyline([
        (-half_end, -half_len), (half_end, -half_len), (half_waist, 0.0),
        (half_end, half_len), (-half_end, half_len), (-half_waist, 0.0),
    ], closed=True)


def joint_key():
    """The bowtie spline that bridges two segment ends."""
    return translate(extrude(bowtie_profile(), height=THICK), dz=THICK / 2)


def socket_solids(n, mode, outline):
    """Four bowtie pockets, one straddling each cardinal cut line."""
    r = pad_center(n, mode, outline)
    blank = extrude(bowtie_profile(KEY_CLEAR), height=_CUT_D)
    turned = rotate(blank, angle_deg=90.0)
    return [
        translate(blank, dx=r),
        translate(blank, dx=-r),
        translate(turned, dy=r),
        translate(turned, dy=-r),
    ]


def _dot_group(count, cx, cy):
    """A compact 2-column grid of *count* through-holes centred on (cx, cy)."""
    cols = 2
    rows = math.ceil(count / cols)
    holes = []
    for k in range(count):
        r, c = divmod(k, cols)
        holes.append(translate(
            cylinder(diameter=DOT_D, height=_CUT_D),
            dx=cx + (c - (cols - 1) / 2) * DOT_PITCH,
            dy=cy + (r - (rows - 1) / 2) * DOT_PITCH,
        ))
    return holes


def label_solids(n, mode, outline):
    """
    Punch *n* holes into every pad, on both sides of every cut line, so each
    finished segment reads its own radius in squares (2 / 4 / 6).
    """
    r = pad_center(n, mode, outline)
    holes = []
    for s in (1, -1):
        holes += _dot_group(n, r, s * DOT_GROUP_Y)
        holes += _dot_group(n, -r, s * DOT_GROUP_Y)
        holes += _dot_group(n, s * DOT_GROUP_Y, r)
        holes += _dot_group(n, s * DOT_GROUP_Y, -r)
    return holes


def quadrant_stock(sx, sy):
    """Oversize half-space block covering one quadrant, for cardinal cuts."""
    return translate(box(_BIG, _BIG, _BIG), dx=sx * _BIG / 2, dy=sy * _BIG / 2)


def centre_collar():
    """
    1-inch square frame the miniature's base drops into. Place it first, stand
    the mini in it, then bring each ring's four pad tips to meet its edges.
    """
    outer = COLLAR_OPEN + 2 * COLLAR_BAND
    return difference(
        translate(box(outer, outer, THICK), dz=THICK / 2),
        translate(box(COLLAR_OPEN, COLLAR_OPEN, _CUT_D), dz=THICK / 2),
    )


def verify(shape, name):
    """
    Fail loudly on a boolean that produced a degenerate result.

    partikus to_stl() tessellates whatever it is handed, so an invalid fuse
    would export as a normal-looking STL and only surface in the slicer — or
    worse, on the bed after a multi-hour print. Gate every export on this.
    """
    raw = shape.shape
    if not raw.isValid():
        raise ValueError(f"{name}: boolean produced an invalid shape — do not print it")
    if len(raw.Solids) != 1:
        raise ValueError(
            f"{name}: expected 1 solid, got {len(raw.Solids)} — the outline "
            f"came apart; check BAND_W against GRID_MM"
        )
    return shape


def build_ring(n, mode, bed_mm, outline):
    """
    Build one radius-*n* template.

    Returns (kind, part, whole) where *kind* is "whole" or "segment", *part* is
    the piece you actually print, and *whole* is the assembled ring for preview.
    Segments are congruent under 90-degree rotation, so one covers all four.
    """
    ring = union(build_band(n, mode, outline), *pad_solids(n, mode, outline))
    span = 2 * outer_extent(n, mode, outline)

    if span <= bed_mm:
        whole = difference(ring, *label_solids(n, mode, outline))
        return "whole", whole, whole

    whole = difference(ring, *label_solids(n, mode, outline),
                       *socket_solids(n, mode, outline))
    segment = intersection(whole, quadrant_stock(1, 1))

    bb = segment.shape.BoundBox
    if max(bb.XLength, bb.YLength) > bed_mm:
        raise ValueError(
            f"{n * FT_PER_SQ} ft segment is {max(bb.XLength, bb.YLength):.1f} mm "
            f"across a {bed_mm:.0f} mm bed even cut into {SEGMENTS} pieces. "
            f"Lower GRID_MM, or add diagonal cuts for an 8-way split."
        )
    return "segment", segment, whole


# ─── Build ────────────────────────────────────────────────────────────────────

def main():
    if SEGMENTS != 4:
        raise NotImplementedError(
            "only SEGMENTS=4 (cardinal cuts) is implemented — those cuts always "
            "land mid-way along a straight run of the outline, which is what "
            "makes the pads, the seams and the centre line up."
        )

    exports = []
    assembly = []
    any_segmented = False

    _log(f"[style] {OUTLINE} outline, centred on a {CENTER_ON}")

    for ft in RADII_FT:
        if ft % FT_PER_SQ:
            raise ValueError(f"{ft} ft is not a whole number of {FT_PER_SQ} ft squares")
        n = ft // FT_PER_SQ

        kind, part, whole = build_ring(n, CENTER_ON, BED_MM, OUTLINE)
        verify(part, f"{ft} ft {kind}")
        bb = part.shape.BoundBox
        copies = 1 if kind == "whole" else SEGMENTS
        any_segmented = any_segmented or kind == "segment"

        _log(f"[{ft:>2} ft] spans {2 * outer_extent(n, CENTER_ON, OUTLINE):.1f} mm"
             f" | {kind} {bb.XLength:.1f} x {bb.YLength:.1f} mm | print {copies}x")

        if OUTLINE == "circle":
            affected = len(cell_set(n, CENTER_ON))
            missed = len(cells_missed_by_circle(n, CENTER_ON))
            _log(f"        {affected} squares affected by the rules; {missed} of "
                 f"them lie outside this circle (diagonals — judge those by 1-2-1)")

        exports.append((f"pf1e_{ft}ft_{kind}", part))
        assembly.append((whole, f"{ft}ft"))
        _gui_show(part, f"pf1e_{ft}ft_{kind}")

    collar = verify(centre_collar(), "centre collar")
    exports.append(("pf1e_centre_collar", collar))
    assembly.append((collar, "centre_collar"))
    _gui_show(collar, "pf1e_centre_collar")

    if any_segmented:
        key = verify(joint_key(), "joint key")
        exports.append(("pf1e_joint_key", key))
        assembly.append((key, "joint_key"))
        _gui_show(key, "pf1e_joint_key")
        _log(f"[joint] KEY_CLEAR={KEY_CLEAR} mm per face — print one key and "
             f"test the fit before running off four large segments")

    for name, shape in exports:
        to_stl(shape, os.path.join(OUT_DIR, name + ".stl"))
        to_step(shape, os.path.join(OUT_DIR, name + ".step"))
        _log(f"[export] {name}.stl + .step")

    fcstd = os.path.join(OUT_DIR, "pf1e_burst_templates.FCStd")
    save_fcstd(assembly, fcstd)
    _log(f"[export] {os.path.basename(fcstd)}")
    _log(f"[done] {len(exports)} parts in {OUT_DIR}")


# freecadcmd execs a script with __name__ set to its basename, not "__main__",
# so the usual __main__ guard would never fire here. Matching on the basename
# instead lets tests/test_pf1e_templates.py load this module under a different
# name to exercise the geometry without building and exporting every part.
if __name__ == "pf1e_burst_templates":
    main()
