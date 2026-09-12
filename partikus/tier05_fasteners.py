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


def _override(value, preset, label):
    """
    Take the caller's *value* for a dimension, or the ISO table's *preset*.

    Every fastener here was sized entirely from its nominal thread size, which
    is right for a standard part and useless for anything else — an oversize
    fender washer, a thin jam nut, a low-head cap screw, or a part from a
    supplier whose head is 0.3 mm off the standard. Each dimension now takes an
    optional override; None keeps the ISO figure, so existing calls are
    unchanged.

    Rejects non-positive values rather than building a degenerate solid: a
    zero-thickness washer is invalid geometry that renders as nothing, which is
    the silent-failure shape this project has spent a session removing.
    """
    if value is None:
        return preset
    if value <= 0:
        raise ValueError(f"{label} must be positive, got {value}")
    return value


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

def hex_bolt(diameter=6.0, length=20.0, pitch=None, across_flats=None,
             head_height=None):
    """
    ISO hex-head bolt (ISO 4014). Head at top, shank below.

    Args:
        diameter:     nominal diameter (mm)
        length:       shank length under head (mm)
        pitch:        thread pitch (mm); looked up if None
        across_flats: spanner size; None = ISO for this thread
        head_height:  head thickness; None = ISO

    Example:
        hex_bolt(diameter=6, length=25)
        hex_bolt(6, 25, across_flats=11)     # older 11 mm A/F M6
    """
    dims = lookup(diameter)["hex_bolt"]
    s = _override(across_flats, dims["across_flats"], "across_flats")
    k = _override(head_height, dims["head_height"], "head_height")
    shank = Part.makeCylinder(diameter / 2, length, _V(0, 0, 0))
    head = _hex_prism(s, k, z_bottom=length)
    raw = shank.fuse(head)
    return _bb_result(_center(raw))


# ── Socket head bolt ──────────────────────────────────────────────────────────

def socket_head_bolt(diameter=6.0, length=20.0, pitch=None,
                     head_diameter=None, head_height=None):
    """
    ISO socket-head cap screw (ISO 4762). Cylindrical head with hex socket.

    The socket itself is not modelled — the head is a plain cylinder.

    Args:
        diameter:      nominal diameter (mm)
        length:        shank length under head (mm)
        pitch:         thread pitch (mm); looked up if None
        head_diameter: head outside diameter; None = ISO
        head_height:   head height; None = ISO. A low-head cap screw is
                       roughly 0.6x the standard.

    Example:
        socket_head_bolt(diameter=6, length=20)
        socket_head_bolt(6, 20, head_diameter=8.5, head_height=3.5)  # low head
    """
    dims = lookup(diameter)["socket_head"]
    dk = _override(head_diameter, dims["head_diameter"], "head_diameter")
    k = _override(head_height, dims["head_height"], "head_height")
    shank = Part.makeCylinder(diameter / 2, length, _V(0, 0, 0))
    head = Part.makeCylinder(dk / 2, k, _V(0, 0, length))
    raw = shank.fuse(head)
    return _bb_result(_center(raw))


# ── Button head bolt ──────────────────────────────────────────────────────────

def button_head_bolt(diameter=6.0, length=20.0, pitch=None,
                     head_diameter=None, head_height=None):
    """
    ISO button-head socket screw (ISO 7380). Low-profile head.

    The dome is modelled as a plain cylinder — this is the envelope, not the
    profile.

    Args:
        diameter:      nominal diameter (mm)
        length:        shank length under head (mm)
        pitch:         thread pitch (mm); looked up if None
        head_diameter: head outside diameter; None = ISO
        head_height:   head height; None = ISO

    Example:
        button_head_bolt(diameter=6, length=16)
        button_head_bolt(6, 16, head_diameter=12)
    """
    dims = lookup(diameter)["button_head"]
    if dims is None:
        raise ValueError(
            f"No button-head data for M{diameter}. "
            "Available: M3–M12. Pass head_diameter and head_height to model "
            "one outside that range."
        )
    dk = _override(head_diameter, dims["head_diameter"], "head_diameter")
    k = _override(head_height, dims["head_height"], "head_height")
    shank = Part.makeCylinder(diameter / 2, length, _V(0, 0, 0))
    head = Part.makeCylinder(dk / 2, k, _V(0, 0, length))
    raw = shank.fuse(head)
    return _bb_result(_center(raw))


# ── Flat head bolt ────────────────────────────────────────────────────────────

def flat_head_bolt(diameter=6.0, length=20.0, pitch=None,
                   head_diameter=None, head_angle_deg=None):
    """
    ISO flat-head (countersunk) screw (ISO 10642). 90° head angle.

    length = distance from the flush surface to the tip of the screw.

    Args:
        diameter:       nominal diameter (mm)
        length:         shank length below the flush surface (mm)
        pitch:          thread pitch (mm); looked up if None
        head_diameter:  head outside diameter; None = ISO
        head_angle_deg: included angle of the countersink; None = ISO (90°).
                        Use 82 to match an imperial countersink.

    Example:
        flat_head_bolt(diameter=6, length=20)
        flat_head_bolt(6, 20, head_angle_deg=82)   # imperial countersink
    """
    dims = lookup(diameter)["flat_head"]
    if dims is None:
        raise ValueError(
            f"No flat-head data for M{diameter}. "
            "Available: M2–M12. Pass head_diameter and head_angle_deg to model "
            "one outside that range."
        )
    dk = _override(head_diameter, dims["head_diameter"], "head_diameter")
    head_angle = _override(head_angle_deg, dims["head_angle"], "head_angle_deg")
    if not 0 < head_angle < 180:
        raise ValueError(f"head_angle_deg must be between 0 and 180, got {head_angle}")
    if dk <= diameter:
        raise ValueError(
            f"head_diameter ({dk}) must be larger than the shank ({diameter})")
    half_angle = math.radians(head_angle / 2)
    head_h = (dk / 2 - diameter / 2) / math.tan(half_angle)
    shank = Part.makeCylinder(diameter / 2, length, _V(0, 0, 0))
    # Cone: narrow at z=length (shank top), wide at z=length+head_h (surface)
    head = Part.makeCone(diameter / 2, dk / 2, head_h, _V(0, 0, length))
    raw = shank.fuse(head)
    return _bb_result(_center(raw))


# ── Hex nut ───────────────────────────────────────────────────────────────────

def hex_nut(diameter=6.0, pitch=None, across_flats=None, height=None):
    """
    ISO hex nut (ISO 4032).

    Args:
        diameter:     nominal thread diameter (mm)
        pitch:        thread pitch (mm); looked up if None
        across_flats: spanner size; None = ISO for this thread
        height:       nut height; None = ISO. A jam nut is roughly half.

    Example:
        hex_nut(diameter=6)                 # ISO 4032 M6, 10 mm A/F, 5.2 high
        hex_nut(6, height=3.0)              # jam nut
    """
    dims = lookup(diameter)["hex_nut"]
    s = _override(across_flats, dims["across_flats"], "across_flats")
    h = _override(height, dims["height"], "height")
    if s <= diameter:
        raise ValueError(
            f"across_flats ({s}) must be larger than the thread diameter ({diameter})")
    hh = h / 2
    prism = _hex_prism(s, h, z_bottom=-hh)
    bore = Part.makeCylinder(diameter / 2, h * 1.01, _V(0, 0, -hh * 1.005))
    raw = prism.cut(bore)
    return _bb_result(raw)


# ── Flat washer ───────────────────────────────────────────────────────────────

def flat_washer(bolt_diameter=6.0, inner_diameter=None, outer_diameter=None,
                thickness=None):
    """
    ISO flat washer — normal series (ISO 7089).

    Args:
        bolt_diameter:  nominal bolt diameter the washer fits (mm)
        inner_diameter: bore; None = ISO normal series for this bolt
        outer_diameter: outside diameter; None = ISO
        thickness:      washer thickness; None = ISO

    Example:
        flat_washer(bolt_diameter=6)                      # ISO 7089 M6
        flat_washer(6, outer_diameter=25, thickness=2)    # fender washer
    """
    dims = lookup(bolt_diameter)["flat_washer"]
    di = _override(inner_diameter, dims["inner_diameter"], "inner_diameter")
    do = _override(outer_diameter, dims["outer_diameter"], "outer_diameter")
    t = _override(thickness, dims["thickness"], "thickness")
    if di >= do:
        raise ValueError(
            f"inner_diameter ({di}) must be smaller than outer_diameter ({do})")
    hh = t / 2
    outer = Part.makeCylinder(do / 2, t, _V(0, 0, -hh))
    inner = Part.makeCylinder(di / 2, t * 1.01, _V(0, 0, -hh * 1.005))
    raw = outer.cut(inner)
    return _bb_result(raw)


# ── Lock washer ───────────────────────────────────────────────────────────────

def lock_washer(bolt_diameter=6.0, inner_diameter=None, outer_diameter=None,
                thickness=None):
    """
    ISO split lock washer (ISO 7980). Modelled as a flat ring (cosmetic).

    The split and the helical rise are not modelled — this is the envelope.

    Args:
        bolt_diameter:  nominal bolt diameter the washer fits (mm)
        inner_diameter: bore; None = ISO for this bolt
        outer_diameter: outside diameter; None = ISO
        thickness:      washer thickness; None = ISO

    Example:
        lock_washer(bolt_diameter=6)
        lock_washer(6, thickness=1.8)
    """
    dims = lookup(bolt_diameter)["lock_washer"]
    di = _override(inner_diameter, dims["inner_diameter"], "inner_diameter")
    do = _override(outer_diameter, dims["outer_diameter"], "outer_diameter")
    t = _override(thickness, dims["thickness"], "thickness")
    if di >= do:
        raise ValueError(
            f"inner_diameter ({di}) must be smaller than outer_diameter ({do})")
    hh = t / 2
    outer = Part.makeCylinder(do / 2, t, _V(0, 0, -hh))
    inner = Part.makeCylinder(di / 2, t * 1.01, _V(0, 0, -hh * 1.005))
    raw = outer.cut(inner)
    return _bb_result(raw)


# ── Heat-set insert pocket ────────────────────────────────────────────────────

def heat_set_insert_pocket(insert_size="M3", outer_diameter=None, length=None):
    """
    Pocket (hole) to receive a heat-set threaded insert for 3D printing.

    CUTTER — this is the negative volume. Subtract it from your part.

    Dimensions approximate the Ruthex/CJT standard. Insert dimensions vary
    noticeably between suppliers, so measure yours: the pocket wants to be a
    few hundredths under the insert's knurl diameter so the plastic melts and
    grips rather than the insert dropping straight through.

    Args:
        insert_size:    nominal thread size, e.g. "M3" or "M4"
        outer_diameter: pocket diameter; None = the standard for this size
        length:         pocket depth; None = the standard

    Example:
        heat_set_insert_pocket("M3")
        heat_set_insert_pocket("M3", outer_diameter=4.0, length=5.7)
    """
    d, _ = parse_size(insert_size)
    dims = lookup(d)["heat_set"]
    if dims is None and (outer_diameter is None or length is None):
        raise ValueError(
            f"No heat-set data for {insert_size} — pass outer_diameter and "
            f"length to model it anyway")
    dims = dims or {}
    od = _override(outer_diameter, dims.get("outer_diameter"), "outer_diameter")
    L = _override(length, dims.get("length"), "length")
    hh = L / 2
    raw = Part.makeCylinder(od / 2, L, _V(0, 0, -hh))
    return _bb_result(raw)


# ── Clearance hole ────────────────────────────────────────────────────────────

def clearance_hole(bolt_size="M6", depth=10.0, fit="close", hole_diameter=None):
    """
    Through-hole sized for bolt clearance (ISO 273).

    CUTTER — this is the negative volume. Subtract it from your part.

    Args:
        bolt_size:     nominal bolt size, e.g. "M6" or "M6x1.0"
        depth:         hole depth (mm)
        fit:           "close", "normal", or "loose"
        hole_diameter: exact diameter, overriding the ISO fit class. Useful for
                       3D printing, where a printed hole comes out undersize
                       and the ISO figure is optimistic.

    Example:
        clearance_hole("M6", depth=15, fit="normal")
        clearance_hole("M6", depth=15, hole_diameter=6.6)   # printed, oversized
    """
    d, _ = parse_size(bolt_size)
    dims = lookup(d)["clearance"]
    if hole_diameter is None and fit not in dims:
        raise ValueError(f"fit must be 'close', 'normal', or 'loose'; got {fit!r}")
    hole_d = _override(hole_diameter, dims.get(fit), "hole_diameter")
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
