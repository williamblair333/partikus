"""
Tier 9 — Boolean Operations.

Functions operate on PartikusShape objects (or plain Part.Shape objects).
Results carry a CENTER anchor at the bounding-box centroid.
"""

import FreeCAD
import Part

from .core.shape_wrapper import PartikusShape
from .core.anchors import CENTER, TOP, BOTTOM


def _V(x, y, z):
    return FreeCAD.Vector(x, y, z)


def _unwrap(s):
    return s.shape if isinstance(s, PartikusShape) else s


def _bb_anchors(shape):
    bb = shape.BoundBox
    cx = bb.XMin + bb.XLength / 2
    cy = bb.YMin + bb.YLength / 2
    cz = bb.ZMin + bb.ZLength / 2
    return {
        CENTER: _V(cx, cy, cz),
        TOP:    _V(cx, cy, bb.ZMax),
        BOTTOM: _V(cx, cy, bb.ZMin),
    }


def _bb_orientations():
    return {TOP: _V(0, 0, 1), BOTTOM: _V(0, 0, -1)}


# ── Union ─────────────────────────────────────────────────────────────────────

def union(*shapes):
    """
    Fuse all shapes into one solid.  Alias: fuse().

    Args:
        *shapes: two or more PartikusShape or Part.Shape objects

    Example:
        union(box(10,10,10), cylinder(diameter=6, height=20))
    """
    if len(shapes) < 2:
        raise ValueError("union requires at least 2 shapes")
    result = _unwrap(shapes[0])
    for s in shapes[1:]:
        result = result.fuse(_unwrap(s))
    return PartikusShape(result, _bb_anchors(result), _bb_orientations())


fuse = union   # alias


# ── Difference ────────────────────────────────────────────────────────────────

def difference(base, *to_subtract):
    """
    Subtract one or more shapes from *base*.  Alias: cut().

    Args:
        base:         the PartikusShape to subtract from
        *to_subtract: shapes to remove

    Example:
        difference(box(20,20,10), cylinder(diameter=8, height=15))
    """
    result = _unwrap(base)
    for s in to_subtract:
        result = result.cut(_unwrap(s))
    return PartikusShape(result, _bb_anchors(result), _bb_orientations())


cut = difference   # alias


# ── Intersection ──────────────────────────────────────────────────────────────

def intersection(*shapes):
    """
    Keep only the volume common to all shapes.  Alias: intersect().

    Args:
        *shapes: two or more shapes

    Example:
        intersection(box(10,10,10), sphere(diameter=12))
    """
    if len(shapes) < 2:
        raise ValueError("intersection requires at least 2 shapes")
    result = _unwrap(shapes[0])
    for s in shapes[1:]:
        result = result.common(_unwrap(s))
    return PartikusShape(result, _bb_anchors(result), _bb_orientations())


intersect = intersection   # alias


# ── Hull / Minkowski (deferred) ───────────────────────────────────────────────

def hull(*shapes):
    """Convex hull of all inputs. (Not yet implemented — requires mesh kernel.)"""
    raise NotImplementedError(
        "hull() requires mesh-based convex hull; planned for a future milestone."
    )


def minkowski_sum(shape, kernel):
    """Minkowski sum. (Not yet implemented — OpenCASCADE lacks native support.)"""
    raise NotImplementedError(
        "minkowski_sum() is not natively supported by OpenCASCADE; "
        "planned for a future milestone."
    )
