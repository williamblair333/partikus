"""
Tier 7 — Container / Enclosure Features.

Functional enclosure shapes: lids, snap-fit boxes, hinged boxes, cable
channels, vents, cutouts. All shapes centred at origin. All dimensions in mm.
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


# ── Lid ───────────────────────────────────────────────────────────────────────

def lid(length=60.0, width=40.0, rim_height=5.0, rim_inset=1.0, wall_thickness=2.0):
    """
    Flat lid with a downward-facing rim that seats inside a matching container.

    Args:
        length:         outer X dimension (mm)
        width:          outer Y dimension (mm)
        rim_height:     height of the seating rim (mm)
        rim_inset:      how far the rim sits inside the container wall (mm)
        wall_thickness: lid panel thickness (mm)

    Custom anchors:
        TOP    — top face centre
        BOTTOM — underside of lid panel (rim attachment plane)

    Example:
        lid(length=80, width=50, rim_height=6, rim_inset=1.5, wall_thickness=2)
    """
    half_l = length / 2
    half_w = width / 2
    total_h = wall_thickness + rim_height

    panel = Part.makeBox(length, width, wall_thickness,
                         _V(-half_l, -half_w, rim_height))

    rim_outer_l = length - 2 * rim_inset
    rim_outer_w = width - 2 * rim_inset
    rim_inner_l = rim_outer_l - 2 * wall_thickness
    rim_inner_w = rim_outer_w - 2 * wall_thickness

    if rim_inner_l <= 0 or rim_inner_w <= 0:
        rim = Part.makeBox(rim_outer_l, rim_outer_w, rim_height,
                           _V(-rim_outer_l / 2, -rim_outer_w / 2, 0))
    else:
        outer = Part.makeBox(rim_outer_l, rim_outer_w, rim_height,
                             _V(-rim_outer_l / 2, -rim_outer_w / 2, 0))
        inner = Part.makeBox(rim_inner_l, rim_inner_w, rim_height * 1.01,
                             _V(-rim_inner_l / 2, -rim_inner_w / 2, -0.005))
        rim = outer.cut(inner)

    raw = panel.fuse(rim)
    raw = _center(raw)
    return _bb_result(raw)


# ── Snap-fit box ──────────────────────────────────────────────────────────────

def snap_fit_box(length=80.0, width=50.0, height=30.0,
                 wall_thickness=2.0, snap_count=4):
    """
    Open-top box with snap-clip tabs on the outer walls.

    Args:
        length:         outer X dimension (mm)
        width:          outer Y dimension (mm)
        height:         outer Z dimension (mm)
        wall_thickness: wall and floor thickness (mm)
        snap_count:     total number of snap tabs (distributed evenly, min 2)

    Example:
        snap_fit_box(80, 50, 30, wall_thickness=2, snap_count=4)
    """
    snap_count = max(2, snap_count)
    half_l = length / 2
    half_w = width / 2

    outer = Part.makeBox(length, width, height, _V(-half_l, -half_w, -height / 2))
    inner_l = length - 2 * wall_thickness
    inner_w = width - 2 * wall_thickness
    inner_h = height - wall_thickness
    inner = Part.makeBox(inner_l, inner_w, inner_h,
                         _V(-inner_l / 2, -inner_w / 2, -height / 2 + wall_thickness))
    box_raw = outer.cut(inner)

    # snap tabs: small protruding nubs on outer face, centred vertically
    tab_w = 4.0
    tab_h = 3.0
    tab_d = 1.2
    tabs = []
    per_side = max(1, snap_count // 4)
    remaining = snap_count

    def _make_tab(cx, cy, cz, dx, dy):
        t = Part.makeBox(tab_w if dx == 0 else tab_d,
                         tab_w if dy == 0 else tab_d,
                         tab_h,
                         _V(cx - (tab_w if dx == 0 else tab_d) / 2,
                            cy - (tab_w if dy == 0 else tab_d) / 2,
                            cz - tab_h / 2))
        return t

    mid_z = 0.0
    sides = [
        (0,  half_w,  mid_z, 0, 1),   # front
        (0, -half_w,  mid_z, 0, -1),  # back
        (half_l,  0,  mid_z, 1, 0),   # right
        (-half_l, 0,  mid_z, -1, 0),  # left
    ]
    for sx, sy, sz, dx, dy in sides:
        if remaining <= 0:
            break
        n = min(per_side, remaining)
        for _ in range(n):
            tabs.append(_make_tab(sx, sy, sz, dx, dy))
        remaining -= n

    for t in tabs:
        box_raw = box_raw.fuse(t)

    raw = _center(box_raw)
    return _bb_result(raw)


# ── Hinged box ────────────────────────────────────────────────────────────────

def hinged_box(length=80.0, width=50.0, height=30.0,
               wall_thickness=2.0, hinge_side="BACK"):
    """
    Two-piece box (base + lid) joined by a living-hinge strip on one side.
    Returns the combined open shape (base + lid flat, hinge connecting them).

    Args:
        length:         outer X dimension (mm)
        width:          outer Y dimension (mm)
        height:         total height when closed (mm); each half is height/2
        wall_thickness: wall and floor thickness (mm)
        hinge_side:     which side the hinge is on — "FRONT"|"BACK"|"LEFT"|"RIGHT"

    Example:
        hinged_box(80, 50, 40, wall_thickness=2, hinge_side="BACK")
    """
    half_h = height / 2
    half_l = length / 2
    half_w = width / 2

    def _half_box():
        outer = Part.makeBox(length, width, half_h, _V(-half_l, -half_w, 0))
        inner_l = length - 2 * wall_thickness
        inner_w = width - 2 * wall_thickness
        inner_h = half_h - wall_thickness
        inner = Part.makeBox(inner_l, inner_w, inner_h,
                             _V(-inner_l / 2, -inner_w / 2, wall_thickness))
        return outer.cut(inner)

    base = _half_box()

    # lid: same box flipped upside-down (open face down), offset above base
    lid_raw = _half_box()
    m = FreeCAD.Matrix()
    m.rotateX(math.pi)
    lid_raw.transformShape(m)
    # after flip, open face is up; shift so it sits above the base
    gap = 0.5
    m2 = FreeCAD.Matrix()
    m2.move(_V(0, 0, height + gap))
    lid_raw.transformShape(m2)

    # hinge strip connecting base top to lid bottom on the chosen side
    hinge_thickness = wall_thickness * 0.4
    hinge_length = min(length, width) * 0.6
    if hinge_side in ("BACK", "FRONT"):
        hx, hy = hinge_length, hinge_thickness
        y_base = -half_w if hinge_side == "BACK" else half_w
        hinge_raw = Part.makeBox(hx, hinge_thickness, gap + 0.1,
                                 _V(-hx / 2, y_base - hinge_thickness / 2, half_h - 0.05))
    else:  # LEFT / RIGHT
        hx, hy = hinge_thickness, hinge_length
        x_base = -half_l if hinge_side == "LEFT" else half_l
        hinge_raw = Part.makeBox(hinge_thickness, hy, gap + 0.1,
                                 _V(x_base - hinge_thickness / 2, -hy / 2, half_h - 0.05))

    combined = base.fuse(lid_raw).fuse(hinge_raw)
    raw = _center(combined)
    return _bb_result(raw)


# ── Magnetic recess ───────────────────────────────────────────────────────────

def magnetic_recess(magnet_diameter=6.0, magnet_thickness=2.0, count=1,
                    spacing=10.0):
    """
    Cylindrical pocket(s) for press-fit disc magnets, arranged in a row along X.

    Args:
        magnet_diameter:  pocket diameter (mm); add 0.1–0.2 mm clearance yourself
        magnet_thickness: pocket depth (mm)
        count:            number of pockets
        spacing:          centre-to-centre distance along X (mm)

    Example:
        magnetic_recess(magnet_diameter=6.2, magnet_thickness=2.1, count=2, spacing=12)
    """
    r = magnet_diameter / 2
    pockets = []
    total_span = spacing * (count - 1)
    for i in range(count):
        x = -total_span / 2 + i * spacing
        cyl = Part.makeCylinder(r, magnet_thickness, _V(x, 0, -magnet_thickness / 2),
                                _V(0, 0, 1))
        pockets.append(cyl)

    if len(pockets) == 1:
        raw = pockets[0]
    else:
        raw = pockets[0]
        for p in pockets[1:]:
            raw = raw.fuse(p)

    return _bb_result(raw)


# ── Battery compartment ───────────────────────────────────────────────────────

_BATTERY_DIMS = {
    "AA":    (14.5, 50.5),
    "AAA":   (10.5, 44.5),
    "C":     (26.2, 50.0),
    "D":     (34.2, 61.5),
    "9V":    (26.5, 48.5),
    "18650": (18.6, 65.2),
    "CR2032": (20.0, 3.2),
    "CR2025": (20.0, 2.5),
    "CR2016": (20.0, 1.6),
}

def battery_compartment(battery_type="AA", count=1, wall_thickness=1.5,
                        contact_clearance=2.0):
    """
    Open-ended tray sized for one or more standard batteries arranged in a row.

    Args:
        battery_type:       one of AA, AAA, C, D, 9V, 18650, CR2032, CR2025, CR2016
        count:              number of batteries side by side
        wall_thickness:     tray wall thickness (mm)
        contact_clearance:  extra length added to each end for contacts (mm)

    Example:
        battery_compartment("AA", count=2)
        battery_compartment("18650", count=1)
    """
    if battery_type not in _BATTERY_DIMS:
        raise ValueError(f"Unknown battery type '{battery_type}'. "
                         f"Choose from: {sorted(_BATTERY_DIMS)}")
    diam, bat_len = _BATTERY_DIMS[battery_type]
    r = diam / 2

    # cylindrical or box shape depending on circular vs rectangular battery
    is_cylindrical = battery_type not in ("9V",)

    cell_spacing = diam + 1.0  # 1 mm gap between cells
    total_width = count * cell_spacing - 1.0
    tray_len = bat_len + 2 * contact_clearance
    tray_h = diam + wall_thickness
    tray_w = total_width + 2 * wall_thickness

    outer = Part.makeBox(tray_len, tray_w, tray_h,
                         _V(-tray_len / 2, -tray_w / 2, -tray_h / 2))

    # carve cell slots
    cutters = []
    for i in range(count):
        cy = -total_width / 2 + i * cell_spacing + diam / 2
        if is_cylindrical:
            cyl = Part.makeCylinder(r, tray_len * 1.02,
                                    _V(-tray_len / 2 - 0.01, cy, 0),
                                    _V(1, 0, 0))
            cutters.append(cyl)
        else:
            b = Part.makeBox(tray_len * 1.02, diam, diam,
                             _V(-tray_len / 2 - 0.01, cy - diam / 2, -diam / 2))
            cutters.append(b)

    raw = outer
    for c in cutters:
        raw = raw.cut(c)

    raw = _center(raw)
    return _bb_result(raw)


# ── Cable channel ─────────────────────────────────────────────────────────────

def cable_channel(width=8.0, depth=5.0, length=50.0, wall_thickness=1.5):
    """
    U-shaped channel for routing cables along a surface.

    Args:
        width:          inner channel width (mm)
        depth:          inner channel depth (mm)
        length:         channel run length along X (mm)
        wall_thickness: wall thickness (mm)

    Example:
        cable_channel(width=8, depth=5, length=60)
    """
    outer_w = width + 2 * wall_thickness
    outer_h = depth + wall_thickness  # open top

    half_l = length / 2
    outer = Part.makeBox(length, outer_w, outer_h,
                         _V(-half_l, -outer_w / 2, -outer_h / 2))
    inner = Part.makeBox(length * 1.01, width, depth,
                         _V(-half_l - 0.005, -width / 2, -outer_h / 2 + wall_thickness))
    raw = outer.cut(inner)
    raw = _center(raw)
    return _bb_result(raw)


# ── Strain relief ─────────────────────────────────────────────────────────────

def strain_relief(cable_diameter=4.0, length=12.0, wall_thickness=2.0,
                  clamp_gap=1.0):
    """
    Two-piece cable clamp / strain-relief collar (returns combined shape).

    Args:
        cable_diameter: cable outer diameter (mm)
        length:         clamp body length along X (mm)
        wall_thickness: material thickness around cable (mm)
        clamp_gap:      gap between top and bottom halves (mm)

    Example:
        strain_relief(cable_diameter=4, length=12)
    """
    r = cable_diameter / 2
    outer_r = r + wall_thickness
    half_l = length / 2

    full_cyl = Part.makeCylinder(outer_r, length, _V(-half_l, 0, 0), _V(1, 0, 0))
    bore = Part.makeCylinder(r, length * 1.02, _V(-half_l - 0.01, 0, 0), _V(1, 0, 0))
    body = full_cyl.cut(bore)

    # split into two halves with a gap
    gap_box = Part.makeBox(length * 1.02, outer_r * 2 + 1, clamp_gap,
                           _V(-half_l - 0.01, -outer_r - 0.5, -clamp_gap / 2))
    body = body.cut(gap_box)

    raw = _center(body)
    return _bb_result(raw)


# ── Vent slots ────────────────────────────────────────────────────────────────

def vent_slots(length=60.0, width=30.0, slot_count=5, slot_width=2.0,
               depth=2.0, wall_thickness=1.0):
    """
    Panel with evenly-spaced rectangular through-slots for ventilation.

    Args:
        length:         panel X dimension (mm)
        width:          panel Y dimension (mm)
        slot_count:     number of slots
        slot_width:     width of each slot along Y (mm)
        depth:          panel thickness / slot depth (mm)
        wall_thickness: minimum material between slots (mm)

    Example:
        vent_slots(60, 30, slot_count=5, slot_width=2)
    """
    half_l = length / 2
    half_w = width / 2
    half_d = depth / 2

    panel = Part.makeBox(length, width, depth,
                         _V(-half_l, -half_w, -half_d))

    slot_length = length * 0.8
    total_slot_h = slot_count * slot_width
    spacing = (width - total_slot_h) / (slot_count + 1)
    if spacing < wall_thickness:
        spacing = wall_thickness

    raw = panel
    for i in range(slot_count):
        y = -half_w + spacing + i * (slot_width + spacing)
        cut = Part.makeBox(slot_length, slot_width, depth * 1.02,
                           _V(-slot_length / 2, y, -half_d - 0.01))
        raw = raw.cut(cut)

    raw = _center(raw)
    return _bb_result(raw)


# ── Display window ────────────────────────────────────────────────────────────

def display_window(length=40.0, width=25.0, recess_depth=0.0,
                   border_thickness=3.0, panel_thickness=2.0):
    """
    Rectangular panel with a centred viewing aperture, optionally recessed.

    Args:
        length:           outer panel X dimension (mm)
        width:            outer panel Y dimension (mm)
        recess_depth:     depth of a stepped recess around the aperture (mm); 0 = flush
        border_thickness: minimum border around the aperture (mm)
        panel_thickness:  total panel thickness (mm)

    Example:
        display_window(length=50, width=30, recess_depth=1.5, border_thickness=3)
    """
    half_l = length / 2
    half_w = width / 2
    half_t = panel_thickness / 2

    panel = Part.makeBox(length, width, panel_thickness,
                         _V(-half_l, -half_w, -half_t))

    apt_l = length - 2 * border_thickness
    apt_w = width - 2 * border_thickness
    if apt_l <= 0 or apt_w <= 0:
        raise ValueError("border_thickness too large for given length/width")

    aperture = Part.makeBox(apt_l, apt_w, panel_thickness * 1.02,
                            _V(-apt_l / 2, -apt_w / 2, -half_t - 0.01))
    raw = panel.cut(aperture)

    if recess_depth > 0:
        recess_l = apt_l + border_thickness
        recess_w = apt_w + border_thickness
        recess = Part.makeBox(recess_l, recess_w, recess_depth,
                              _V(-recess_l / 2, -recess_w / 2, half_t - recess_depth))
        raw = raw.cut(recess)

    raw = _center(raw)
    return _bb_result(raw)


# ── Button cutout ─────────────────────────────────────────────────────────────

def button_cutout(diameter=12.0, panel_thickness=2.0, shape="round"):
    """
    Through-hole cutout for a panel-mount button or switch.

    Args:
        diameter:        cutout diameter (round) or side length (square) (mm)
        panel_thickness: panel thickness — determines hole depth (mm)
        shape:           "round" or "square"

    Example:
        button_cutout(diameter=16, panel_thickness=3, shape="round")
        button_cutout(diameter=12, panel_thickness=2, shape="square")
    """
    half_t = panel_thickness / 2
    if shape == "round":
        raw = Part.makeCylinder(diameter / 2, panel_thickness,
                                _V(0, 0, -half_t))
    elif shape == "square":
        half_d = diameter / 2
        raw = Part.makeBox(diameter, diameter, panel_thickness,
                           _V(-half_d, -half_d, -half_t))
    else:
        raise ValueError(f"shape must be 'round' or 'square', got '{shape}'")

    return _bb_result(raw)
