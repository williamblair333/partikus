"""
Tier 4 — Mechanical Features.

Cutout and feature shapes for mechanical assemblies. All shapes centred at
origin. All dimensions in mm.
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
            TOP:   _V(0, 0, 1), BOTTOM: _V(0, 0, -1),
            FRONT: _V(0, 1, 0), BACK:   _V(0, -1, 0),
            RIGHT: _V(1, 0, 0), LEFT:   _V(-1, 0, 0),
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


# ── Boss ──────────────────────────────────────────────────────────────────────

def boss(diameter=10.0, height=5.0, hole_diameter=None):
    """
    Raised cylindrical boss, optionally with a through bore.

    Args:
        diameter:      outer diameter (mm)
        height:        boss height (mm)
        hole_diameter: through-bore diameter; None = solid boss

    Example:
        boss(diameter=12, height=6, hole_diameter=4)
    """
    hh = height / 2
    raw = Part.makeCylinder(diameter / 2, height, _V(0, 0, -hh))
    if hole_diameter is not None:
        bore = Part.makeCylinder(hole_diameter / 2, height * 1.01, _V(0, 0, -hh * 1.005))
        raw = raw.cut(bore)
    return _bb_result(raw)


# ── Counterbore hole ──────────────────────────────────────────────────────────

def counterbore_hole(thru_diameter=5.0, bore_diameter=9.0, bore_depth=4.0, depth=10.0):
    """
    Stepped hole: wide counterbore at top, narrower through section below.

    Args:
        thru_diameter: through-hole diameter (mm)
        bore_diameter: counterbore diameter (mm)
        bore_depth:    depth of the wide bore section (mm)
        depth:         total depth (mm)

    Example:
        counterbore_hole(thru_diameter=5, bore_diameter=9, bore_depth=4, depth=12)
    """
    hh = depth / 2
    bore = Part.makeCylinder(bore_diameter / 2, bore_depth,
                             _V(0, 0, hh - bore_depth))
    thru_h = depth - bore_depth
    thru = Part.makeCylinder(thru_diameter / 2, thru_h, _V(0, 0, -hh))
    raw = bore.fuse(thru)
    return _bb_result(raw)


# ── Countersink hole ──────────────────────────────────────────────────────────

def countersink_hole(thru_diameter=3.0, head_diameter=6.0,
                     head_angle_deg=82, depth=10.0):
    """
    Conical countersink at top, cylindrical bore below.

    Args:
        thru_diameter:  through-hole diameter (mm)
        head_diameter:  countersink diameter at the surface (mm)
        head_angle_deg: included angle of the countersink cone (degrees)
        depth:          total depth of the feature (mm)

    Example:
        countersink_hole(thru_diameter=3.5, head_diameter=7, head_angle_deg=90, depth=10)
    """
    half_angle = math.radians(head_angle_deg / 2)
    cone_h = (head_diameter / 2 - thru_diameter / 2) / math.tan(half_angle)
    hh = depth / 2
    cone_shape = Part.makeCone(head_diameter / 2, thru_diameter / 2,
                               cone_h, _V(0, 0, hh - cone_h))
    cyl_h = max(depth - cone_h, 1e-3)
    cyl_shape = Part.makeCylinder(thru_diameter / 2, cyl_h, _V(0, 0, -hh))
    raw = cone_shape.fuse(cyl_shape)
    return _bb_result(raw)


# ── Slot hole ─────────────────────────────────────────────────────────────────

def slot_hole(length=20.0, width=6.0, depth=5.0):
    """
    Oblong slot: two semicircular ends joined by a rectangular middle.

    Args:
        length: total end-to-end length (mm); must be >= width
        width:  slot width / end-circle diameter (mm)
        depth:  depth of the slot (mm)

    Example:
        slot_hole(length=25, width=6, depth=8)
    """
    if length < width:
        raise ValueError("length must be >= width")
    hh = depth / 2
    half_straight = (length - width) / 2
    cyl1 = Part.makeCylinder(width / 2, depth, _V(-half_straight, 0, -hh))
    cyl2 = Part.makeCylinder(width / 2, depth, _V(half_straight, 0, -hh))
    if half_straight > 1e-6:
        mid = Part.makeBox(length - width, width, depth,
                           _V(-half_straight, -width / 2, -hh))
        raw = cyl1.fuse(cyl2).fuse(mid)
    else:
        raw = cyl1.fuse(cyl2)
    return _bb_result(raw)


# ── Keyway ────────────────────────────────────────────────────────────────────

def keyway(width=4.0, depth=2.0, length=20.0):
    """
    Rectangular key channel for shaft–hub connections.

    Args:
        width:  channel width (X, mm)
        depth:  channel depth (Z, mm)
        length: channel length (Y, mm)

    Example:
        keyway(width=5, depth=3, length=25)
    """
    raw = Part.makeBox(length, width, depth,
                       _V(-length / 2, -width / 2, -depth / 2))
    return _bb_result(raw)


# ── Rib ───────────────────────────────────────────────────────────────────────

def rib(length=20.0, height=15.0, thickness=3.0, draft_angle_deg=0.0):
    """
    Triangular support rib (right-triangle prism).

    The base runs along X (length), the fin stands up in Z (height), and the
    rib is extruded in Y (thickness). draft_angle_deg tilts the vertical face.

    Args:
        length:          base length (mm)
        height:          rib height (mm)
        thickness:       rib thickness / extrusion depth (mm)
        draft_angle_deg: inward tilt of the vertical face (degrees)

    Example:
        rib(length=30, height=20, thickness=4)
    """
    offset = height * math.tan(math.radians(draft_angle_deg))
    pts = [
        _V(0,      0, 0),
        _V(length, 0, 0),
        _V(offset, 0, height),
        _V(0,      0, 0),
    ]
    wire = Part.makePolygon(pts)
    face = Part.Face(wire)
    raw = face.extrude(_V(0, thickness, 0))
    return _bb_result(_center(raw))


# ── Gusset ────────────────────────────────────────────────────────────────────

def gusset(length=20.0, height=20.0, thickness=3.0):
    """
    Triangular corner gusset (right-triangle plate).

    The right-angle corner is at the origin before centering. Hypotenuse runs
    from (length, 0) to (0, height) in XZ.

    Args:
        length:    base length (X, mm)
        height:    vertical height (Z, mm)
        thickness: plate thickness (Y, mm)

    Example:
        gusset(length=25, height=25, thickness=4)
    """
    pts = [
        _V(0,      0, 0),
        _V(length, 0, 0),
        _V(0,      0, height),
        _V(0,      0, 0),
    ]
    wire = Part.makePolygon(pts)
    face = Part.Face(wire)
    raw = face.extrude(_V(0, thickness, 0))
    return _bb_result(_center(raw))


# ── Flange ────────────────────────────────────────────────────────────────────

def flange(inner_diameter=20.0, outer_diameter=40.0, thickness=5.0,
           hole_pattern=None):
    """
    Flat ring / flange plate with optional bolt-circle holes.

    Args:
        inner_diameter: bore diameter (mm)
        outer_diameter: flange outer diameter (mm)
        thickness:      flange thickness (mm)
        hole_pattern:   list of (hole_diameter, pcd_radius, count) tuples,
                        or None for no bolt holes

    Example:
        flange(inner_diameter=20, outer_diameter=60, thickness=8,
               hole_pattern=[(6, 22, 4)])
    """
    hh = thickness / 2
    outer = Part.makeCylinder(outer_diameter / 2, thickness, _V(0, 0, -hh))
    inner = Part.makeCylinder(inner_diameter / 2, thickness * 1.01,
                              _V(0, 0, -hh * 1.005))
    raw = outer.cut(inner)
    if hole_pattern is not None:
        for (hd, pcd_r, count) in hole_pattern:
            for i in range(count):
                angle = 2 * math.pi * i / count
                hx = pcd_r * math.cos(angle)
                hy = pcd_r * math.sin(angle)
                h = Part.makeCylinder(hd / 2, thickness * 1.1,
                                      _V(hx, hy, -hh * 1.05))
                raw = raw.cut(h)
    return _bb_result(raw)


# ── Lip ───────────────────────────────────────────────────────────────────────

def lip(outer_diameter=40.0, height=20.0, lip_width=3.0, lip_height=5.0):
    """
    Cylindrical body with a smaller-diameter plug extension (lip) on top.

    Args:
        outer_diameter: body outer diameter (mm)
        height:         body height (mm)
        lip_width:      how far the lip is inset from the body edge (mm)
        lip_height:     height of the lip extension (mm)

    Example:
        lip(outer_diameter=50, height=20, lip_width=4, lip_height=6)
    """
    hh = height / 2
    body = Part.makeCylinder(outer_diameter / 2, height, _V(0, 0, -hh))
    lip_r = (outer_diameter / 2) - lip_width
    lip_raw = Part.makeCylinder(lip_r, lip_height, _V(0, 0, hh))
    raw = body.fuse(lip_raw)
    return _bb_result(_center(raw))


# ── L-bracket ─────────────────────────────────────────────────────────────────

def l_bracket(length=30.0, height=30.0, thickness=3.0, width=20.0):
    """
    L-shaped bracket: horizontal leg (X) + vertical leg (Z), sharing a corner.

    Args:
        length:    horizontal leg length (mm)
        height:    vertical leg height (mm)
        thickness: wall thickness of both legs (mm)
        width:     depth of the bracket (Y, mm)

    Example:
        l_bracket(length=40, height=40, thickness=4, width=25)
    """
    horiz = Part.makeBox(length, width, thickness,
                         _V(0, -width / 2, 0))
    vert = Part.makeBox(thickness, width, height,
                        _V(0, -width / 2, 0))
    raw = horiz.fuse(vert)
    return _bb_result(_center(raw))


# ── T-bracket ─────────────────────────────────────────────────────────────────

def t_bracket(arm_length=40.0, stem_length=20.0, width=20.0, thickness=3.0):
    """
    T-shaped bracket: horizontal cross-arm on top, vertical stem below.

    Args:
        arm_length:   total length of the horizontal arm (mm)
        stem_length:  length of the vertical stem (mm)
        width:        depth of the bracket (Y, mm)
        thickness:    wall thickness (mm)

    Example:
        t_bracket(arm_length=60, stem_length=30, width=25, thickness=4)
    """
    arm = Part.makeBox(arm_length, width, thickness,
                       _V(-arm_length / 2, -width / 2, 0))
    stem = Part.makeBox(thickness, width, stem_length,
                        _V(-thickness / 2, -width / 2, -stem_length))
    raw = arm.fuse(stem)
    return _bb_result(_center(raw))


# ── U-bracket ─────────────────────────────────────────────────────────────────

def u_bracket(length=40.0, height=20.0, width=20.0, thickness=3.0,
              leg_height=15.0):
    """
    U-channel bracket: flat base + two upright side legs.

    Args:
        length:     base length (X, mm)
        height:     total outer height (Z, mm); base_thickness = height - leg_height
        width:      depth of the bracket (Y, mm)
        thickness:  side-leg wall thickness (X, mm)
        leg_height: inner channel height (mm); must be < height

    Example:
        u_bracket(length=50, height=20, width=25, thickness=3, leg_height=15)
    """
    base_t = height - leg_height
    hh = height / 2
    base = Part.makeBox(length, width, base_t,
                        _V(-length / 2, -width / 2, -hh))
    left_leg = Part.makeBox(thickness, width, leg_height,
                            _V(-length / 2, -width / 2, -hh + base_t))
    right_leg = Part.makeBox(thickness, width, leg_height,
                             _V(length / 2 - thickness, -width / 2, -hh + base_t))
    raw = base.fuse(left_leg).fuse(right_leg)
    return _bb_result(raw)


# ── Tab ───────────────────────────────────────────────────────────────────────

def tab(width=10.0, height=5.0, thickness=2.0):
    """
    Simple rectangular tab protrusion.

    Args:
        width:     X extent (mm)
        height:    Z extent (mm)
        thickness: Y extent (mm)

    Example:
        tab(width=12, height=6, thickness=2)
    """
    raw = Part.makeBox(width, thickness, height,
                       _V(-width / 2, -thickness / 2, -height / 2))
    return _bb_result(raw)


# ── Slot cutout ───────────────────────────────────────────────────────────────

def slot_cutout(width=10.0, height=5.0, depth=3.0):
    """
    Rectangular slot cutout (flat-ended, unlike slot_hole which has rounded ends).

    Args:
        width: X extent (mm)
        height: Z extent (mm)
        depth:  Y extent (mm)

    Example:
        slot_cutout(width=15, height=8, depth=4)
    """
    raw = Part.makeBox(width, depth, height,
                       _V(-width / 2, -depth / 2, -height / 2))
    return _bb_result(raw)


# ── Dovetail pin ──────────────────────────────────────────────────────────────

def dovetail_pin(length=20.0, narrow_width=6.0, wide_width=10.0, height=5.0):
    """
    Trapezoidal dovetail pin (wide at base, narrow at top).

    The pin slides along the Y axis. Cross-section is in the XZ plane.

    Args:
        length:      pin length (Y, mm)
        narrow_width: width at the top (mm)
        wide_width:  width at the base (mm)
        height:      cross-section height (Z, mm)

    Example:
        dovetail_pin(length=25, narrow_width=6, wide_width=10, height=5)
    """
    hh = height / 2
    hw_w = wide_width / 2
    hw_n = narrow_width / 2
    pts = [
        _V(-hw_w, 0, -hh),
        _V(hw_w,  0, -hh),
        _V(hw_n,  0,  hh),
        _V(-hw_n, 0,  hh),
        _V(-hw_w, 0, -hh),
    ]
    wire = Part.makePolygon(pts)
    face = Part.Face(wire)
    raw = face.extrude(_V(0, length, 0))
    return _bb_result(_center(raw))


# ── Dovetail slot ─────────────────────────────────────────────────────────────

def dovetail_slot(length=20.0, narrow_width=6.0, wide_width=10.0, height=5.0):
    """
    Trapezoidal dovetail slot — same shape as dovetail_pin, used as a cutout.

    Args:
        length:       slot length (Y, mm)
        narrow_width: width at the top (mm)
        wide_width:   width at the base (mm)
        height:       cross-section height (Z, mm)

    Example:
        dovetail_slot(length=25, narrow_width=6, wide_width=10, height=5)
    """
    return dovetail_pin(length, narrow_width, wide_width, height)


# ── Tongue ────────────────────────────────────────────────────────────────────

def tongue(length=15.0, width=6.0, height=3.0):
    """
    Rectangular tongue protrusion (slides into a matching groove).

    Args:
        length: X extent (mm)
        width:  Y extent (mm)
        height: Z extent (mm)

    Example:
        tongue(length=20, width=8, height=4)
    """
    raw = Part.makeBox(length, width, height,
                       _V(-length / 2, -width / 2, -height / 2))
    return _bb_result(raw)


# ── Groove ────────────────────────────────────────────────────────────────────

def groove(length=15.0, width=6.0, depth=3.0):
    """
    Rectangular groove / channel (receives a tongue or key).

    Args:
        length: X extent (mm)
        width:  Y extent (mm)
        depth:  Z extent (mm)

    Example:
        groove(length=20, width=8, depth=4)
    """
    raw = Part.makeBox(length, width, depth,
                       _V(-length / 2, -width / 2, -depth / 2))
    return _bb_result(raw)


# ── Living hinge ──────────────────────────────────────────────────────────────

def living_hinge(length=40.0, thickness=0.5, hinge_width=10.0):
    """
    Thin flexible hinge section (for 3D-printed living hinges).

    Args:
        length:      span of the hinge (X, mm)
        thickness:   thinned section thickness (Z, mm)
        hinge_width: hinge width (Y, mm)

    Example:
        living_hinge(length=30, thickness=0.6, hinge_width=15)
    """
    raw = Part.makeBox(length, hinge_width, thickness,
                       _V(-length / 2, -hinge_width / 2, -thickness / 2))
    return _bb_result(raw)


# ── Snap clip ─────────────────────────────────────────────────────────────────

def snap_clip(length=20.0, width=5.0, hook_height=2.0, flex_arm_length=12.0):
    """
    Cantilever snap-fit clip: thick body + thin flexible arm + hook tip.

    Args:
        length:          total clip length (X, mm)
        width:           clip width (Y, mm)
        hook_height:     hook protrusion height (Z, mm)
        flex_arm_length: length of the thin flexible arm section (mm)

    Example:
        snap_clip(length=20, width=5, hook_height=2, flex_arm_length=12)
    """
    body_length = length - flex_arm_length
    arm_thick = max(hook_height / 3, 0.3)
    hook_len = hook_height * 0.5

    # Build in local coords [0..length] in X, then centre
    body = Part.makeBox(body_length, width, hook_height,
                        _V(0, -width / 2, 0))
    arm = Part.makeBox(flex_arm_length, width, arm_thick,
                       _V(body_length, -width / 2, 0))
    hook = Part.makeBox(hook_len, width, hook_height - arm_thick,
                        _V(length - hook_len, -width / 2, arm_thick))
    raw = body.fuse(arm).fuse(hook)
    return _bb_result(_center(raw))
