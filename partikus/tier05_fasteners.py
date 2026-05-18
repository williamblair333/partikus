"""
Tier 5 — Fasteners & Standard Parts.

All bolt/nut/washer geometry is cosmetic (smooth cylinders / prisms).
Thread helices are not modelled — they add no fabrication value and make
boolean operations unreliable in OpenCASCADE.

Shapes are centred at origin. All dimensions in mm.
"""

import math
import FreeCAD
import Part

from .core.shape_wrapper import PartikusShape
from .core.anchors import CENTER, TOP, BOTTOM, FRONT, BACK, LEFT, RIGHT
from .presets.screws import lookup, parse_size


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


def _hex_prism(across_flats, height, z_bottom=0.0):
    """Regular hexagonal prism centred on the Z axis, starting at z_bottom."""
    R = (across_flats / 2) / math.cos(math.radians(30))
    pts = [
        _V(R * math.cos(math.radians(30 + 60 * i)),
           R * math.sin(math.radians(30 + 60 * i)),
           z_bottom)
        for i in range(6)
    ]
    pts.append(pts[0])
    wire = Part.makePolygon(pts)
    face = Part.Face(wire)
    return face.extrude(_V(0, 0, height))


def _get_pitch(diameter, pitch):
    if pitch is not None:
        return pitch
    return lookup(diameter)["pitch"]


# ── Threaded rod ──────────────────────────────────────────────────────────────

def threaded_rod(diameter=6.0, length=20.0, pitch=None, thread_form="metric"):
    """
    Cosmetic threaded rod: smooth cylinder at nominal diameter.

    Args:
        diameter:    nominal diameter (mm)
        length:      rod length (mm)
        pitch:       thread pitch (mm); looked up from ISO table if None
        thread_form: "metric" (only supported form)

    Example:
        threaded_rod(diameter=6, length=50)
    """
    if thread_form != "metric":
        raise NotImplementedError(f"thread_form={thread_form!r} not supported")
    _get_pitch(diameter, pitch)  # validate diameter is in table
    hh = length / 2
    raw = Part.makeCylinder(diameter / 2, length, _V(0, 0, -hh))
    return _bb_result(raw)


# ── Tapped hole ───────────────────────────────────────────────────────────────

def tapped_hole(diameter=6.0, depth=10.0, pitch=None):
    """
    Cosmetic tapped hole: cylinder at tap-drill diameter.

    Args:
        diameter: nominal thread diameter (mm)
        depth:    hole depth (mm)
        pitch:    thread pitch (mm); looked up from ISO table if None

    Example:
        tapped_hole(diameter=6, depth=12)
    """
    p = _get_pitch(diameter, pitch)
    tap_d = diameter - p
    hh = depth / 2
    raw = Part.makeCylinder(tap_d / 2, depth, _V(0, 0, -hh))
    return _bb_result(raw)


# ── Hex bolt ──────────────────────────────────────────────────────────────────

def hex_bolt(diameter=6.0, length=20.0, pitch=None):
    """
    ISO hex-head bolt (ISO 4014). Head at top, shank below.

    Args:
        diameter: nominal diameter (mm)
        length:   shank length under head (mm)
        pitch:    thread pitch (mm); looked up if None

    Example:
        hex_bolt(diameter=6, length=25)
    """
    dims = lookup(diameter)["hex_bolt"]
    s = dims["across_flats"]
    k = dims["head_height"]
    shank = Part.makeCylinder(diameter / 2, length, _V(0, 0, 0))
    head = _hex_prism(s, k, z_bottom=length)
    raw = shank.fuse(head)
    return _bb_result(_center(raw))


# ── Socket head bolt ──────────────────────────────────────────────────────────

def socket_head_bolt(diameter=6.0, length=20.0, pitch=None):
    """
    ISO socket-head cap screw (ISO 4762). Cylindrical head with hex socket.

    Args:
        diameter: nominal diameter (mm)
        length:   shank length under head (mm)
        pitch:    thread pitch (mm); looked up if None

    Example:
        socket_head_bolt(diameter=6, length=20)
    """
    dims = lookup(diameter)["socket_head"]
    dk = dims["head_diameter"]
    k = dims["head_height"]
    shank = Part.makeCylinder(diameter / 2, length, _V(0, 0, 0))
    head = Part.makeCylinder(dk / 2, k, _V(0, 0, length))
    raw = shank.fuse(head)
    return _bb_result(_center(raw))


# ── Button head bolt ──────────────────────────────────────────────────────────

def button_head_bolt(diameter=6.0, length=20.0, pitch=None):
    """
    ISO button-head socket screw (ISO 7380). Low-profile domed head.

    Args:
        diameter: nominal diameter (mm)
        length:   shank length under head (mm)
        pitch:    thread pitch (mm); looked up if None

    Example:
        button_head_bolt(diameter=6, length=16)
    """
    dims = lookup(diameter)["button_head"]
    if dims is None:
        raise ValueError(
            f"No button-head data for M{diameter}. "
            "Available: M3–M12."
        )
    dk = dims["head_diameter"]
    k = dims["head_height"]
    shank = Part.makeCylinder(diameter / 2, length, _V(0, 0, 0))
    head = Part.makeCylinder(dk / 2, k, _V(0, 0, length))
    raw = shank.fuse(head)
    return _bb_result(_center(raw))


# ── Flat head bolt ────────────────────────────────────────────────────────────

def flat_head_bolt(diameter=6.0, length=20.0, pitch=None):
    """
    ISO flat-head (countersunk) screw (ISO 10642). 90° head angle.

    length = distance from the flush surface to the tip of the screw.

    Args:
        diameter: nominal diameter (mm)
        length:   shank length below the flush surface (mm)
        pitch:    thread pitch (mm); looked up if None

    Example:
        flat_head_bolt(diameter=6, length=20)
    """
    dims = lookup(diameter)["flat_head"]
    if dims is None:
        raise ValueError(
            f"No flat-head data for M{diameter}. "
            "Available: M2–M12."
        )
    dk = dims["head_diameter"]
    head_angle = dims["head_angle"]
    half_angle = math.radians(head_angle / 2)
    head_h = (dk / 2 - diameter / 2) / math.tan(half_angle)
    shank = Part.makeCylinder(diameter / 2, length, _V(0, 0, 0))
    # Cone: narrow at z=length (shank top), wide at z=length+head_h (surface)
    head = Part.makeCone(diameter / 2, dk / 2, head_h, _V(0, 0, length))
    raw = shank.fuse(head)
    return _bb_result(_center(raw))


# ── Hex nut ───────────────────────────────────────────────────────────────────

def hex_nut(diameter=6.0, pitch=None):
    """
    ISO hex nut (ISO 4032).

    Args:
        diameter: nominal thread diameter (mm)
        pitch:    thread pitch (mm); looked up if None

    Example:
        hex_nut(diameter=6)
    """
    dims = lookup(diameter)["hex_nut"]
    s = dims["across_flats"]
    h = dims["height"]
    hh = h / 2
    prism = _hex_prism(s, h, z_bottom=-hh)
    bore = Part.makeCylinder(diameter / 2, h * 1.01, _V(0, 0, -hh * 1.005))
    raw = prism.cut(bore)
    return _bb_result(raw)


# ── Flat washer ───────────────────────────────────────────────────────────────

def flat_washer(bolt_diameter=6.0):
    """
    ISO flat washer — normal series (ISO 7089).

    Args:
        bolt_diameter: nominal bolt diameter the washer fits (mm)

    Example:
        flat_washer(bolt_diameter=6)
    """
    dims = lookup(bolt_diameter)["flat_washer"]
    di = dims["inner_diameter"]
    do = dims["outer_diameter"]
    t = dims["thickness"]
    hh = t / 2
    outer = Part.makeCylinder(do / 2, t, _V(0, 0, -hh))
    inner = Part.makeCylinder(di / 2, t * 1.01, _V(0, 0, -hh * 1.005))
    raw = outer.cut(inner)
    return _bb_result(raw)


# ── Lock washer ───────────────────────────────────────────────────────────────

def lock_washer(bolt_diameter=6.0):
    """
    ISO split lock washer (ISO 7980). Modelled as a flat ring (cosmetic).

    Args:
        bolt_diameter: nominal bolt diameter the washer fits (mm)

    Example:
        lock_washer(bolt_diameter=6)
    """
    dims = lookup(bolt_diameter)["lock_washer"]
    di = dims["inner_diameter"]
    do = dims["outer_diameter"]
    t = dims["thickness"]
    hh = t / 2
    outer = Part.makeCylinder(do / 2, t, _V(0, 0, -hh))
    inner = Part.makeCylinder(di / 2, t * 1.01, _V(0, 0, -hh * 1.005))
    raw = outer.cut(inner)
    return _bb_result(raw)


# ── Heat-set insert pocket ────────────────────────────────────────────────────

def heat_set_insert_pocket(insert_size="M3"):
    """
    Pocket (hole) to receive a heat-set threaded insert for 3D printing.

    Dimensions approximate Ruthex/CJT standard. Add your own tolerance if needed.

    Args:
        insert_size: nominal thread size, e.g. "M3" or "M4"

    Example:
        heat_set_insert_pocket("M3")
    """
    d, _ = parse_size(insert_size)
    dims = lookup(d)["heat_set"]
    if dims is None:
        raise ValueError(f"No heat-set data for {insert_size}")
    od = dims["outer_diameter"]
    L = dims["length"]
    hh = L / 2
    raw = Part.makeCylinder(od / 2, L, _V(0, 0, -hh))
    return _bb_result(raw)


# ── Clearance hole ────────────────────────────────────────────────────────────

def clearance_hole(bolt_size="M6", depth=10.0, fit="close"):
    """
    Through-hole sized for bolt clearance (ISO 273).

    Args:
        bolt_size: nominal bolt size, e.g. "M6" or "M6x1.0"
        depth:     hole depth (mm)
        fit:       "close", "normal", or "loose"

    Example:
        clearance_hole("M6", depth=15, fit="normal")
    """
    d, _ = parse_size(bolt_size)
    dims = lookup(d)["clearance"]
    if fit not in dims:
        raise ValueError(f"fit must be 'close', 'normal', or 'loose'; got {fit!r}")
    hole_d = dims[fit]
    hh = depth / 2
    raw = Part.makeCylinder(hole_d / 2, depth, _V(0, 0, -hh))
    return _bb_result(raw)


# ── Screw size preset ─────────────────────────────────────────────────────────

def screw_size_preset(name="M6"):
    """
    Return the full ISO dimension dict for a named screw size.

    Args:
        name: size string, e.g. "M6" or "M3x0.5"

    Returns:
        dict with keys: pitch, tap_drill, hex_bolt, socket_head, button_head,
        flat_head, hex_nut, flat_washer, lock_washer, clearance, heat_set

    Example:
        p = screw_size_preset("M6")
        p["pitch"]            # → 1.0
        p["clearance"]["close"]  # → 6.4
    """
    d, _ = parse_size(name)
    return lookup(d)


# ── Standoff ──────────────────────────────────────────────────────────────────

def standoff(diameter=8.0, length=10.0, thread_size=None):
    """
    Cylindrical standoff / spacer.

    Args:
        diameter:    outer diameter (mm)
        length:      standoff height (mm)
        thread_size: if given (e.g. "M3"), drills a cosmetic through bore at
                     tap-drill diameter to represent threaded ends

    Example:
        standoff(diameter=8, length=10, thread_size="M3")
    """
    hh = length / 2
    raw = Part.makeCylinder(diameter / 2, length, _V(0, 0, -hh))
    if thread_size is not None:
        d, _ = parse_size(thread_size)
        tap_d = lookup(d)["tap_drill"]
        bore = Part.makeCylinder(tap_d / 2, length * 1.01, _V(0, 0, -hh * 1.005))
        raw = raw.cut(bore)
    return _bb_result(raw)


# ── Dowel pin ─────────────────────────────────────────────────────────────────

def dowel_pin(diameter=4.0, length=20.0):
    """
    Precision dowel / alignment pin (smooth cylinder).

    Args:
        diameter: pin diameter (mm)
        length:   pin length (mm)

    Example:
        dowel_pin(diameter=6, length=30)
    """
    hh = length / 2
    raw = Part.makeCylinder(diameter / 2, length, _V(0, 0, -hh))
    return _bb_result(raw)
