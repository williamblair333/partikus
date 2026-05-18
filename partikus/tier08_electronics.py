"""
Tier 8 — Electronics Mounting.

Mounting features and cutouts for common electronics hardware: SBCs, Arduino
boards, LEDs, connectors. All shapes centred at origin. All dimensions in mm.
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


# ── PCB standoff ──────────────────────────────────────────────────────────────

def pcb_standoff(height=8.0, hole_diameter=3.2, base_diameter=6.0):
    """
    Cylindrical standoff with a through bore for a PCB mounting screw.

    Args:
        height:         standoff height (mm)
        hole_diameter:  centre bore diameter (mm)
        base_diameter:  outer diameter of the standoff body (mm)

    Custom anchors:
        TOP    — top face (where PCB rests)
        BOTTOM — base face (mounts to enclosure floor)

    Example:
        pcb_standoff(height=8, hole_diameter=3.2, base_diameter=6)
    """
    if hole_diameter >= base_diameter:
        raise ValueError("hole_diameter must be less than base_diameter")
    outer = Part.makeCylinder(base_diameter / 2, height, _V(0, 0, -height / 2))
    bore = Part.makeCylinder(hole_diameter / 2, height * 1.02,
                             _V(0, 0, -height / 2 - 0.01))
    raw = outer.cut(bore)
    return _bb_result(raw)


# ── SBC / SoC mount tables ────────────────────────────────────────────────────

# Hole positions relative to board corner (x, y) in mm; origin = board corner
# Format: (board_length, board_width, thickness, [(hole_x, hole_y), ...])
_RPI_DIMS = {
    "3B":   (85.0, 56.0, 1.6, [(3.5, 3.5), (61.5, 3.5), (3.5, 52.5), (61.5, 52.5)]),
    "3B+":  (85.0, 56.0, 1.6, [(3.5, 3.5), (61.5, 3.5), (3.5, 52.5), (61.5, 52.5)]),
    "4B":   (85.0, 56.0, 1.6, [(3.5, 3.5), (61.5, 3.5), (3.5, 52.5), (61.5, 52.5)]),
    "5":    (85.0, 56.0, 1.6, [(3.5, 3.5), (61.5, 3.5), (3.5, 52.5), (61.5, 52.5)]),
    "Zero": (65.0, 30.0, 1.6, [(3.5, 3.5), (61.5, 3.5), (3.5, 26.5), (61.5, 26.5)]),
    "Zero2":(65.0, 30.0, 1.6, [(3.5, 3.5), (61.5, 3.5), (3.5, 26.5), (61.5, 26.5)]),
}

def raspberry_pi_mount(model="4B", standoff_height=8.0, hole_diameter=2.9):
    """
    Mounting plate with four standoffs matching Raspberry Pi hole pattern.

    Args:
        model:           board variant — 3B, 3B+, 4B, 5, Zero, Zero2
        standoff_height: standoff column height (mm)
        hole_diameter:   M2.5 = 2.9 close-fit, 3.0 normal fit

    Custom anchors:
        TOP    — top of standoffs (PCB seating plane)
        BOTTOM — underside of base plate

    Example:
        raspberry_pi_mount("4B", standoff_height=8)
    """
    if model not in _RPI_DIMS:
        raise ValueError(f"Unknown RPi model '{model}'. Choose from: {sorted(_RPI_DIMS)}")
    bl, bw, _, holes = _RPI_DIMS[model]
    plate_t = 3.0
    margin = 2.0

    plate = Part.makeBox(bl + 2 * margin, bw + 2 * margin, plate_t,
                         _V(-(bl / 2 + margin), -(bw / 2 + margin), -plate_t))

    standoffs = []
    for hx, hy in holes:
        x = hx - bl / 2
        y = hy - bw / 2
        outer = Part.makeCylinder(3.0, standoff_height, _V(x, y, -plate_t))
        bore = Part.makeCylinder(hole_diameter / 2, standoff_height * 1.02,
                                 _V(x, y, -plate_t - 0.01))
        standoffs.append(outer.cut(bore))

    raw = plate
    for s in standoffs:
        raw = raw.fuse(s)

    raw = _center(raw)
    return _bb_result(raw)


_ARDUINO_DIMS = {
    "uno":       (68.6, 53.3, 1.6, [(13.97, 2.54), (15.24, 50.8), (66.04, 35.56), (66.04, 5.08)]),
    "mega":      (101.6, 53.3, 1.6, [(13.97, 2.54), (15.24, 50.8), (99.06, 2.54), (99.06, 50.8)]),
    "nano":      (43.2, 18.0, 1.6, [(1.5, 1.5), (41.5, 1.5), (1.5, 16.5), (41.5, 16.5)]),
    "leonardo":  (68.6, 53.3, 1.6, [(13.97, 2.54), (15.24, 50.8), (66.04, 35.56), (66.04, 5.08)]),
    "micro":     (43.2, 18.0, 1.6, [(1.5, 1.5), (41.5, 1.5), (1.5, 16.5), (41.5, 16.5)]),
}

def arduino_mount(model="uno", standoff_height=8.0, hole_diameter=3.2):
    """
    Mounting plate with standoffs matching Arduino hole pattern.

    Args:
        model:           uno, mega, nano, leonardo, micro
        standoff_height: standoff height (mm)
        hole_diameter:   M3 = 3.2 close-fit

    Example:
        arduino_mount("uno", standoff_height=10)
    """
    if model not in _ARDUINO_DIMS:
        raise ValueError(f"Unknown Arduino model '{model}'. Choose from: {sorted(_ARDUINO_DIMS)}")
    bl, bw, _, holes = _ARDUINO_DIMS[model]
    plate_t = 3.0
    margin = 2.0

    plate = Part.makeBox(bl + 2 * margin, bw + 2 * margin, plate_t,
                         _V(-(bl / 2 + margin), -(bw / 2 + margin), -plate_t))

    standoffs = []
    for hx, hy in holes:
        x = hx - bl / 2
        y = hy - bw / 2
        outer = Part.makeCylinder(3.5, standoff_height, _V(x, y, -plate_t))
        bore = Part.makeCylinder(hole_diameter / 2, standoff_height * 1.02,
                                 _V(x, y, -plate_t - 0.01))
        standoffs.append(outer.cut(bore))

    raw = plate
    for s in standoffs:
        raw = raw.fuse(s)

    raw = _center(raw)
    return _bb_result(raw)


# ── LED holder ────────────────────────────────────────────────────────────────

def led_holder(led_diameter=5.0, panel_thickness=2.0, retention_lip=0.5):
    """
    Panel-mount press-fit holder for a round LED.

    Args:
        led_diameter:    LED body diameter — 3 mm, 5 mm, or 10 mm common (mm)
        panel_thickness: thickness of the panel this mounts through (mm)
        retention_lip:   inward lip depth to retain LED from behind (mm)

    Example:
        led_holder(led_diameter=5, panel_thickness=3)
    """
    outer_r = led_diameter / 2 + 1.5
    led_r = led_diameter / 2
    half_t = panel_thickness / 2

    outer = Part.makeCylinder(outer_r, panel_thickness, _V(0, 0, -half_t))
    bore = Part.makeCylinder(led_r, panel_thickness * 1.02, _V(0, 0, -half_t - 0.01))
    body = outer.cut(bore)

    if retention_lip > 0:
        lip_r = led_r - retention_lip
        if lip_r > 0:
            lip = Part.makeCylinder(lip_r, retention_lip,
                                    _V(0, 0, half_t - retention_lip))
            body = body.fuse(lip)

    return _bb_result(body)


# ── USB cutout ────────────────────────────────────────────────────────────────

_USB_DIMS = {
    "USB-A":     (12.5, 4.7),
    "USB-B":     (12.2, 11.2),
    "USB-C":     (9.0,  3.4),
    "Micro-USB": (8.1,  2.7),
    "Mini-USB":  (7.4,  3.8),
}

def usb_cutout(connector_type="USB-C", panel_thickness=2.0, clearance=0.3):
    """
    Rectangular panel cutout for a USB connector.

    Args:
        connector_type: USB-A, USB-B, USB-C, Micro-USB, Mini-USB
        panel_thickness: panel depth (mm)
        clearance:      added to each dimension for fit (mm)

    Example:
        usb_cutout("USB-C", panel_thickness=3)
    """
    if connector_type not in _USB_DIMS:
        raise ValueError(f"Unknown connector '{connector_type}'. "
                         f"Choose from: {sorted(_USB_DIMS)}")
    w, h = _USB_DIMS[connector_type]
    w += 2 * clearance
    h += 2 * clearance
    raw = Part.makeBox(panel_thickness * 1.02, w, h,
                       _V(-panel_thickness / 2 - 0.01, -w / 2, -h / 2))
    return _bb_result(raw)


# ── HDMI cutout ───────────────────────────────────────────────────────────────

_HDMI_DIMS = {
    "full":  (14.0, 6.2),
    "mini":  (11.2, 3.8),
    "micro": (6.4,  2.8),
}

def hdmi_cutout(connector_type="full", panel_thickness=2.0, clearance=0.3):
    """
    Panel cutout for an HDMI connector.

    Args:
        connector_type: full, mini, micro
        panel_thickness: panel depth (mm)
        clearance:      added to each dimension for fit (mm)

    Example:
        hdmi_cutout("micro", panel_thickness=2)
    """
    if connector_type not in _HDMI_DIMS:
        raise ValueError(f"Unknown HDMI type '{connector_type}'. "
                         f"Choose from: {sorted(_HDMI_DIMS)}")
    w, h = _HDMI_DIMS[connector_type]
    w += 2 * clearance
    h += 2 * clearance
    raw = Part.makeBox(panel_thickness * 1.02, w, h,
                       _V(-panel_thickness / 2 - 0.01, -w / 2, -h / 2))
    return _bb_result(raw)


# ── Barrel jack cutout ────────────────────────────────────────────────────────

def barrel_jack_cutout(outer_diameter=8.0, panel_thickness=2.0, clearance=0.2):
    """
    Circular panel cutout for a barrel power jack.

    Args:
        outer_diameter:  connector barrel OD — common sizes: 5.5, 6.3, 8.0 mm
        panel_thickness: panel depth (mm)
        clearance:       diametric clearance (mm)

    Example:
        barrel_jack_cutout(outer_diameter=8.0, panel_thickness=3)
    """
    r = (outer_diameter + clearance) / 2
    raw = Part.makeCylinder(r, panel_thickness * 1.02,
                            _V(0, 0, -panel_thickness / 2 - 0.01))
    return _bb_result(raw)


# ── DIN rail clip ─────────────────────────────────────────────────────────────

_DIN_DIMS = {
    "35mm": (35.0, 7.5, 1.0),   # width, height, rail thickness
    "15mm": (15.0, 5.5, 1.0),
}

def din_rail_clip(rail_type="35mm", clip_length=40.0, wall_thickness=2.5):
    """
    Snap-on clip body that mounts to a standard DIN rail.

    Args:
        rail_type:      "35mm" (EN 60715 TS 35) or "15mm"
        clip_length:    clip body length along rail axis (mm)
        wall_thickness: clip material thickness (mm)

    Example:
        din_rail_clip("35mm", clip_length=50)
    """
    if rail_type not in _DIN_DIMS:
        raise ValueError(f"Unknown DIN rail type '{rail_type}'. "
                         f"Choose from: {sorted(_DIN_DIMS)}")
    rail_w, rail_h, rail_t = _DIN_DIMS[rail_type]

    # Back plate
    bp_w = rail_w + 2 * wall_thickness
    bp_h = rail_h + 2 * wall_thickness
    half_l = clip_length / 2

    back = Part.makeBox(clip_length, bp_w, wall_thickness,
                        _V(-half_l, -bp_w / 2, 0))

    # Top hook
    top_hook = Part.makeBox(clip_length, wall_thickness, bp_h,
                            _V(-half_l, bp_w / 2 - wall_thickness, 0))

    # Bottom retainer lip
    bot_leg = Part.makeBox(clip_length, wall_thickness, bp_h - wall_thickness,
                           _V(-half_l, -bp_w / 2, 0))
    lip = Part.makeBox(clip_length, wall_thickness * 1.5, wall_thickness,
                       _V(-half_l, -bp_w / 2, bp_h - 2 * wall_thickness))

    raw = back.fuse(top_hook).fuse(bot_leg).fuse(lip)
    raw = _center(raw)
    return _bb_result(raw)


# ── Heatsink fin array ────────────────────────────────────────────────────────

def heatsink_fin_array(base_length=40.0, base_width=40.0, fin_count=8,
                       fin_height=15.0, fin_thickness=1.5, base_thickness=3.0):
    """
    Extruded heatsink with rectangular fins on a flat base.

    Args:
        base_length:     base plate X dimension (mm)
        base_width:      base plate Y dimension (mm)
        fin_count:       number of fins
        fin_height:      fin height above base plate (mm)
        fin_thickness:   individual fin thickness (mm)
        base_thickness:  base plate thickness (mm)

    Example:
        heatsink_fin_array(40, 40, fin_count=8, fin_height=15, fin_thickness=1.5)
    """
    if fin_count < 1:
        raise ValueError("fin_count must be >= 1")
    half_l = base_length / 2
    half_w = base_width / 2

    base = Part.makeBox(base_length, base_width, base_thickness,
                        _V(-half_l, -half_w, 0))

    total_fin_thickness = fin_count * fin_thickness
    gap_total = base_length - total_fin_thickness
    if gap_total < 0:
        raise ValueError("fins too thick for base_length — reduce fin_count or fin_thickness")
    spacing = gap_total / (fin_count + 1)

    fins = []
    for i in range(fin_count):
        x = -half_l + spacing + i * (fin_thickness + spacing)
        fin = Part.makeBox(fin_thickness, base_width, fin_height,
                           _V(x, -half_w, base_thickness))
        fins.append(fin)

    raw = base
    for f in fins:
        raw = raw.fuse(f)

    raw = _center(raw)
    return _bb_result(raw)
