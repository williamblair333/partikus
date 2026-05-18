"""
Tier 11 — Pattern / Array Operations.

Arrays return a single compound shape containing all copies.
Use with difference() to punch arrays of holes, or union() to fuse.
"""

import math
import FreeCAD
import Part

from .core.shape_wrapper import PartikusShape
from .core.anchors import CENTER, TOP, BOTTOM, FRONT, BACK, LEFT, RIGHT
from .tier14_assembly import translate, rotate


def _V(x, y, z):
    return FreeCAD.Vector(x, y, z)


def _vec(v):
    return v if isinstance(v, FreeCAD.Vector) else FreeCAD.Vector(*v)


def _unwrap(s):
    return s.shape if isinstance(s, PartikusShape) else s


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


def _compound(copies):
    comp = Part.makeCompound([_unwrap(c) for c in copies])
    return _bb_result(comp)


# ── Linear Array ──────────────────────────────────────────────────────────────

def linear_array(shape, count, spacing, axis=None):
    """
    Create *count* copies of *shape* spaced *spacing* mm apart along *axis*.
    The array is centered at the origin.

    Args:
        shape:   PartikusShape to repeat
        count:   number of copies (including the original position)
        spacing: distance between copy centres (mm)
        axis:    direction vector; default X

    Example:
        linear_array(screw_hole, count=4, spacing=20)
        linear_array(fin, count=8, spacing=5, axis=(0,1,0))
    """
    if count < 1:
        raise ValueError("count must be >= 1")
    if axis is None:
        axis = _V(1, 0, 0)
    ax = _vec(axis).normalize()
    half = (count - 1) * spacing / 2
    copies = [
        translate(shape, ax.x * (i * spacing - half),
                         ax.y * (i * spacing - half),
                         ax.z * (i * spacing - half))
        for i in range(count)
    ]
    return _compound(copies)


# ── Grid Array ────────────────────────────────────────────────────────────────

def grid_array(shape, count_x, count_y, spacing_x, spacing_y):
    """
    Create a 2D rectangular grid of copies in the XY plane, centered at origin.

    Args:
        shape:     PartikusShape to repeat
        count_x:   columns along X
        count_y:   rows along Y
        spacing_x: column spacing (mm)
        spacing_y: row spacing (mm)

    Example:
        grid_array(standoff, count_x=4, count_y=3, spacing_x=20, spacing_y=15)
    """
    ox = (count_x - 1) * spacing_x / 2
    oy = (count_y - 1) * spacing_y / 2
    copies = [
        translate(shape, i * spacing_x - ox, j * spacing_y - oy, 0)
        for i in range(count_x)
        for j in range(count_y)
    ]
    return _compound(copies)


# ── Polar Array ───────────────────────────────────────────────────────────────

def polar_array(shape, count, radius, center_axis=None, full_angle_deg=360):
    """
    Arrange *count* copies of *shape* in a circle of *radius* around *center_axis*.

    Each copy is placed at *radius* from the axis, rotated by equal angle steps.
    The first copy is along the X axis (or the axis perpendicular to *center_axis*).

    Args:
        shape:         PartikusShape to repeat
        count:         number of copies
        radius:        radial distance from center axis (mm)
        center_axis:   rotation axis vector; default Z
        full_angle_deg: total arc swept (default 360 = full circle)

    Example:
        polar_array(screw_hole, count=4, radius=20)
        polar_array(led_mount, count=6, radius=30, full_angle_deg=180)
    """
    if count < 1:
        raise ValueError("count must be >= 1")
    if center_axis is None:
        center_axis = _V(0, 0, 1)
    ax = _vec(center_axis).normalize()

    # Find a direction perpendicular to ax for the radial offset.
    perp = _V(1, 0, 0)
    if abs(ax.dot(perp)) > 0.9:
        perp = _V(0, 1, 0)
    radial = ax.cross(perp).normalize()
    # Normalize radial (cross product of unit vectors isn't necessarily unit)

    # Translate shape outward by radius along radial direction.
    placed = translate(shape,
                       radial.x * radius,
                       radial.y * radius,
                       radial.z * radius)

    step = full_angle_deg / count
    copies = [rotate(placed, axis=ax, angle_deg=i * step) for i in range(count)]
    return _compound(copies)


# ── Mirror ────────────────────────────────────────────────────────────────────

def mirror(shape, plane="XY"):
    """
    Reflect *shape* through *plane* and return both the original and mirrored copy.

    Args:
        shape: PartikusShape
        plane: "XY" (reflects Z), "XZ" (reflects Y), or "YZ" (reflects X)

    To get only the mirrored copy (replacing original), use
    mirror_position() from tier14_assembly.

    Example:
        both_halves = mirror(half_body, "YZ")
    """
    _NORMALS = {"XY": _V(0, 0, 1), "XZ": _V(0, 1, 0), "YZ": _V(1, 0, 0)}
    if plane not in _NORMALS:
        raise ValueError(f"plane must be 'XY', 'XZ', or 'YZ', got {plane!r}")
    fc = _unwrap(shape)
    mirrored = fc.mirror(_V(0, 0, 0), _NORMALS[plane])
    comp = Part.makeCompound([fc, mirrored])
    return _bb_result(comp)


# ── Helix Array / Honeycomb / Path Array (deferred) ──────────────────────────

def helix_array(shape, count, radius, pitch, turns):
    """Arrange copies along a helix. (Planned for a future milestone.)"""
    raise NotImplementedError("helix_array() planned for a future milestone.")


def honeycomb_fill(area_shape, cell_diameter, wall_thickness):
    """Fill an area with a honeycomb pattern. (Planned for a future milestone.)"""
    raise NotImplementedError("honeycomb_fill() planned for a future milestone.")


def path_array(shape, path_curve, count):
    """Distribute copies along an arbitrary curve. (Planned for a future milestone.)"""
    raise NotImplementedError("path_array() planned for a future milestone.")
