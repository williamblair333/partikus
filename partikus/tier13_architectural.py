"""
Tier 13 — Architectural.

Parametric building elements: walls, stairs, roofs, columns, beams, slabs,
trusses. All shapes centred at origin. All dimensions in mm unless noted.
"""

import math
import FreeCAD
import Part

from .core.shape_wrapper import PartikusShape
from .core.anchors import CENTER, TOP, BOTTOM, FRONT, BACK, LEFT, RIGHT


def _V(x, y, z):
    return FreeCAD.Vector(x, y, z)


def _bb_result(fc_shape):
    bb = fc_shape.BoundBox
    cx = (bb.XMin + bb.XMax) / 2
    cy = (bb.YMin + bb.YMax) / 2
    cz = (bb.ZMin + bb.ZMax) / 2
    return PartikusShape(
        fc_shape,
        {
            CENTER: _V(cx, cy, cz),
            TOP:    _V(cx, cy, bb.ZMax),
            BOTTOM: _V(cx, cy, bb.ZMin),
            FRONT:  _V(cx, bb.YMax, cz),
            BACK:   _V(cx, bb.YMin, cz),
            RIGHT:  _V(bb.XMax, cy, cz),
            LEFT:   _V(bb.XMin, cy, cz),
        },
        {
            TOP:   _V(0, 0, 1),  BOTTOM: _V(0, 0, -1),
            FRONT: _V(0, 1, 0),  BACK:   _V(0, -1, 0),
            RIGHT: _V(1, 0, 0),  LEFT:   _V(-1, 0, 0),
        },
    )


def _center(fc_shape):
    bb = fc_shape.BoundBox
    cx = (bb.XMin + bb.XMax) / 2
    cy = (bb.YMin + bb.YMax) / 2
    cz = (bb.ZMin + bb.ZMax) / 2
    m = FreeCAD.Matrix()
    m.move(_V(-cx, -cy, -cz))
    s = fc_shape.copy()
    s.transformShape(m)
    return s


# ── Wall ──────────────────────────────────────────────────────────────────────

def wall(length=3000.0, height=2400.0, thickness=200.0, openings=None):
    """
    Solid wall with optional rectangular openings (doors/windows) cut through it.

    Args:
        length:    wall run length along X (mm)
        height:    wall height along Z (mm)
        thickness: wall thickness along Y (mm)
        openings:  list of dicts, each with keys:
                     x_offset  — opening left edge from wall left end (mm)
                     z_offset  — opening bottom edge from wall base (mm)
                     width     — opening width (mm)
                     height    — opening height (mm)

    Example:
        wall(3000, 2400, 200, openings=[
            {"x_offset": 500, "z_offset": 0,   "width": 900,  "height": 2100},
            {"x_offset": 1800, "z_offset": 900, "width": 1200, "height": 1200},
        ])
    """
    half_l = length / 2
    half_h = height / 2
    half_t = thickness / 2

    raw = Part.makeBox(length, thickness, height,
                       _V(-half_l, -half_t, -half_h))

    for op in (openings or []):
        ox = op.get("x_offset", 0)
        oz = op.get("z_offset", 0)
        ow = op.get("width", 900)
        oh = op.get("height", 2100)
        cut = Part.makeBox(ow, thickness * 1.02, oh,
                           _V(-half_l + ox, -half_t - 0.01, -half_h + oz))
        raw = raw.cut(cut)

    return _bb_result(raw)


# ── Door ──────────────────────────────────────────────────────────────────────

def door(width=900.0, height=2100.0, thickness=40.0):
    """
    Solid door panel. Combine with wall() openings for full assemblies.

    Args:
        width:     door leaf width (mm)
        height:    door leaf height (mm)
        thickness: door leaf thickness (mm)

    Example:
        door(width=900, height=2100, thickness=40)
    """
    raw = Part.makeBox(width, thickness, height,
                       _V(-width / 2, -thickness / 2, -height / 2))
    return _bb_result(raw)


# ── Window ────────────────────────────────────────────────────────────────────

def window(width=1200.0, height=1200.0, frame_thickness=50.0, depth=80.0):
    """
    Window frame — hollow rectangle (frame only, no glazing geometry).

    Args:
        width:           outer frame width (mm)
        height:          outer frame height (mm)
        frame_thickness: frame member width (mm)
        depth:           frame depth / wall reveal (mm)

    Example:
        window(1200, 1200, frame_thickness=60, depth=80)
    """
    half_w = width / 2
    half_h = height / 2
    half_d = depth / 2

    outer = Part.makeBox(width, depth, height,
                         _V(-half_w, -half_d, -half_h))
    inner_w = width - 2 * frame_thickness
    inner_h = height - 2 * frame_thickness
    if inner_w > 0 and inner_h > 0:
        inner = Part.makeBox(inner_w, depth * 1.02, inner_h,
                             _V(-inner_w / 2, -half_d - 0.01, -inner_h / 2))
        raw = outer.cut(inner)
    else:
        raw = outer

    return _bb_result(raw)


# ── Stairs ────────────────────────────────────────────────────────────────────

def stairs(total_rise=2400.0, total_run=3600.0, tread_count=12, width=900.0):
    """
    Solid stringer staircase — each tread/riser pair is a rectangular step.

    Args:
        total_rise:  total vertical rise (mm)
        total_run:   total horizontal run (mm)
        tread_count: number of treads (= number of risers)
        width:       stair width (mm)

    Example:
        stairs(total_rise=2400, total_run=3600, tread_count=12, width=900)
    """
    if tread_count < 1:
        raise ValueError("tread_count must be >= 1")
    riser = total_rise / tread_count
    tread = total_run / tread_count
    half_w = width / 2
    half_run = total_run / 2
    half_rise = total_rise / 2

    steps = []
    for i in range(tread_count):
        # each step: full cumulative block (like stacked boxes)
        step_w = (i + 1) * tread
        step_h = (i + 1) * riser
        b = Part.makeBox(step_w, width, step_h,
                         _V(-half_run + total_run - step_w,
                            -half_w,
                            -half_rise))
        steps.append(b)

    raw = steps[0]
    for s in steps[1:]:
        raw = raw.fuse(s)

    raw = _center(raw)
    return _bb_result(raw)


# ── Roof — gable ──────────────────────────────────────────────────────────────

def roof_gable(length=6000.0, width=4000.0, peak_height=1500.0, overhang=300.0):
    """
    Gable (pitched) roof — triangular cross-section extruded along the ridge.

    Args:
        length:      ridge length (mm)
        width:       building width (eave to eave) (mm)
        peak_height: height of ridge above eave level (mm)
        overhang:    eave overhang beyond building width on each side (mm)

    Example:
        roof_gable(6000, 4000, 1500, overhang=300)
    """
    total_w = width + 2 * overhang
    total_l = length + 2 * overhang
    half_l = total_l / 2
    half_w = total_w / 2

    pts = [
        _V(-half_w, 0, 0),
        _V(0, 0, peak_height),
        _V(half_w, 0, 0),
        _V(-half_w, 0, 0),
    ]
    profile = Part.makePolygon(pts)
    if not profile.isClosed():
        profile.add(pts[0])

    wire = Part.Wire(profile.Edges)
    face = Part.Face(wire)
    raw = face.extrude(_V(0, total_l, 0))

    m = FreeCAD.Matrix()
    m.move(_V(0, -total_l / 2, 0))
    raw.transformShape(m)

    return _bb_result(raw)


# ── Roof — hip ────────────────────────────────────────────────────────────────

def roof_hip(length=6000.0, width=4000.0, peak_height=1500.0, overhang=300.0):
    """
    Hip roof — pyramid-like with four sloped faces meeting at a ridge line.

    Args:
        length:      building length (mm)
        width:       building width (mm)
        peak_height: height of ridge above eave level (mm)
        overhang:    eave overhang on all four sides (mm)

    Example:
        roof_hip(6000, 4000, 1500, overhang=300)
    """
    total_l = length + 2 * overhang
    total_w = width + 2 * overhang
    half_l = total_l / 2
    half_w = total_w / 2

    # Ridge runs along X; hip ends are triangular
    ridge_half = (total_l - total_w) / 2
    if ridge_half < 0:
        ridge_half = 0.0

    base_pts = [
        _V(-half_l, -half_w, 0),
        _V( half_l, -half_w, 0),
        _V( half_l,  half_w, 0),
        _V(-half_l,  half_w, 0),
        _V(-half_l, -half_w, 0),
    ]
    top_pts = [
        _V(-ridge_half, 0, peak_height),
        _V( ridge_half, 0, peak_height),
    ]

    # Build as loft between base rectangle and ridge line
    base_wire = Part.Wire(Part.makePolygon(base_pts).Edges)
    # Approximate ridge as a degenerate narrow rectangle
    eps = 1.0
    ridge_pts = [
        _V(-ridge_half, -eps, peak_height),
        _V( ridge_half, -eps, peak_height),
        _V( ridge_half,  eps, peak_height),
        _V(-ridge_half,  eps, peak_height),
        _V(-ridge_half, -eps, peak_height),
    ]
    ridge_wire = Part.Wire(Part.makePolygon(ridge_pts).Edges)

    raw = Part.makeLoft([base_wire, ridge_wire], True, False, False)
    return _bb_result(raw)


# ── Roof — shed ───────────────────────────────────────────────────────────────

def roof_shed(length=4000.0, width=3000.0, low_height=2000.0, high_height=2800.0):
    """
    Monopitch / shed roof — single slope from low eave to high eave.

    Args:
        length:      roof length along the ridge (mm)
        width:       roof depth (low eave to high eave) (mm)
        low_height:  height at the low eave (mm)
        high_height: height at the high eave (mm)

    Example:
        roof_shed(4000, 3000, low_height=2000, high_height=2800)
    """
    half_l = length / 2
    half_w = width / 2

    pts = [
        _V(-half_l, -half_w, 0),
        _V(-half_l,  half_w, high_height - low_height),
        _V( half_l,  half_w, high_height - low_height),
        _V( half_l, -half_w, 0),
        _V(-half_l, -half_w, 0),
    ]
    profile_wire = Part.Wire(Part.makePolygon(pts).Edges)
    face = Part.Face(profile_wire)
    # Extrude upward by low_height to get solid wedge + base
    raw = face.extrude(_V(0, 0, low_height))
    raw = _center(raw)
    return _bb_result(raw)


# ── Column ────────────────────────────────────────────────────────────────────

def column(diameter=300.0, height=3000.0, base_size=None, capital_size=None):
    """
    Round column with optional square base plinth and capital (top block).

    Args:
        diameter:     shaft diameter (mm)
        height:       total column height (mm)
        base_size:    side length of square base plinth; None = no plinth
        capital_size: side length of square capital block; None = no capital

    Example:
        column(diameter=300, height=3000, base_size=500, capital_size=450)
    """
    plinth_h = diameter * 0.4 if base_size else 0
    capital_h = diameter * 0.3 if capital_size else 0
    shaft_h = height - plinth_h - capital_h
    if shaft_h <= 0:
        raise ValueError("column height too short for base/capital sizes")

    shaft = Part.makeCylinder(diameter / 2, shaft_h, _V(0, 0, 0))

    parts = [shaft]
    if base_size:
        hs = base_size / 2
        plinth = Part.makeBox(base_size, base_size, plinth_h,
                              _V(-hs, -hs, -plinth_h))
        parts.append(plinth)
    if capital_size:
        hs = capital_size / 2
        cap = Part.makeBox(capital_size, capital_size, capital_h,
                           _V(-hs, -hs, shaft_h))
        parts.append(cap)

    raw = parts[0]
    for p in parts[1:]:
        raw = raw.fuse(p)

    raw = _center(raw)
    return _bb_result(raw)


# ── Beam ──────────────────────────────────────────────────────────────────────

def beam(length=3000.0, cross_section_profile=None, width=100.0, height=200.0):
    """
    Structural beam — extrudes a cross-section profile along its length (X axis).

    Args:
        length:               beam length (mm)
        cross_section_profile: a Part.Wire in the YZ plane; if None, a
                               rectangular section of width × height is used
        width:                rectangular section Y dimension (mm) — used when
                               cross_section_profile is None
        height:               rectangular section Z dimension (mm)

    Example:
        beam(3000, width=100, height=200)
    """
    if cross_section_profile is None:
        half_w = width / 2
        half_h = height / 2
        pts = [
            _V(0, -half_w, -half_h),
            _V(0,  half_w, -half_h),
            _V(0,  half_w,  half_h),
            _V(0, -half_w,  half_h),
            _V(0, -half_w, -half_h),
        ]
        profile_wire = Part.Wire(Part.makePolygon(pts).Edges)
    else:
        profile_wire = cross_section_profile

    face = Part.Face(profile_wire)
    raw = face.extrude(_V(length, 0, 0))

    m = FreeCAD.Matrix()
    m.move(_V(-length / 2, 0, 0))
    raw.transformShape(m)

    return _bb_result(raw)


# ── Slab ──────────────────────────────────────────────────────────────────────

def slab(length=6000.0, width=4000.0, thickness=200.0):
    """
    Flat concrete/structural slab.

    Args:
        length:    X dimension (mm)
        width:     Y dimension (mm)
        thickness: Z dimension (mm)

    Example:
        slab(6000, 4000, 200)
    """
    raw = Part.makeBox(length, width, thickness,
                       _V(-length / 2, -width / 2, -thickness / 2))
    return _bb_result(raw)


# ── Truss — simple ────────────────────────────────────────────────────────────

def truss_simple(length=6000.0, height=800.0, panel_count=6,
                 member_width=50.0, member_height=100.0):
    """
    Planar Pratt truss — top chord, bottom chord, verticals, and diagonals.

    Args:
        length:       truss span (mm)
        height:       truss depth (mm)
        panel_count:  number of bays (must be even for symmetric diagonals)
        member_width: cross-section Y dimension of each member (mm)
        member_height: cross-section Z dimension of each member (mm)

    Example:
        truss_simple(6000, 800, panel_count=6)
    """
    if panel_count < 2:
        raise ValueError("panel_count must be >= 2")

    panel_l = length / panel_count
    half_l = length / 2
    half_h = height / 2
    mw = member_width
    mh = member_height

    def _box_member(x0, z0, x1, z1):
        dx = x1 - x0
        dz = z1 - z0
        member_len = math.sqrt(dx**2 + dz**2)
        if member_len < 1e-6:
            return None
        angle = math.atan2(dz, dx)
        b = Part.makeBox(member_len, mw, mh,
                         _V(0, -mw / 2, -mh / 2))
        m = FreeCAD.Matrix()
        m.rotateY(-angle)
        b.transformShape(m)
        m2 = FreeCAD.Matrix()
        m2.move(_V(x0, 0, z0))
        b.transformShape(m2)
        return b

    members = []

    # Top chord
    members.append(Part.makeBox(length, mw, mh,
                                _V(-half_l, -mw / 2, half_h - mh)))

    # Bottom chord
    members.append(Part.makeBox(length, mw, mh,
                                _V(-half_l, -mw / 2, -half_h)))

    # Verticals and diagonals
    for i in range(panel_count + 1):
        x = -half_l + i * panel_l
        # vertical
        v = Part.makeBox(mw, mw, height - mh,
                         _V(x - mw / 2, -mw / 2, -half_h + mh / 2))
        members.append(v)

    for i in range(panel_count):
        x0 = -half_l + i * panel_l
        x1 = x0 + panel_l
        # diagonals alternate direction
        if i % 2 == 0:
            d = _box_member(x0, -half_h + mh, x1, half_h - mh)
        else:
            d = _box_member(x0, half_h - mh, x1, -half_h + mh)
        if d is not None:
            members.append(d)

    raw = members[0]
    for m in members[1:]:
        raw = raw.fuse(m)

    raw = _center(raw)
    return _bb_result(raw)
