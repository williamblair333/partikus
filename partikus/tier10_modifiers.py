"""
Tier 10 — Edge & Surface Modifiers.

Applied to existing PartikusShape objects. Returns new PartikusShapes.
"""

import FreeCAD
import Part

from .core.shape_wrapper import PartikusShape
from .core.anchors import CENTER, TOP, BOTTOM, FRONT, BACK, LEFT, RIGHT


def _V(x, y, z):
    return FreeCAD.Vector(x, y, z)


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
            TOP:    _V(0, 0,  1), BOTTOM: _V(0, 0, -1),
            FRONT:  _V(0, 1,  0), BACK:   _V(0, -1, 0),
            RIGHT:  _V(1, 0,  0), LEFT:   _V(-1, 0, 0),
        },
    )


def _preserve(result_fc, src):
    """Return PartikusShape with anchors/orientations preserved from src."""
    if isinstance(src, PartikusShape):
        return PartikusShape(result_fc, dict(src.anchors), dict(src.orientations))
    return _bb_result(result_fc)


# ── Fillet ────────────────────────────────────────────────────────────────────

def fillet(shape, radius, edges=None):
    """
    Round edges of *shape* with the given *radius*.

    Args:
        shape:  PartikusShape to modify
        radius: fillet radius (mm)
        edges:  list of Part.Edge objects to round;
                None = round all edges

    Example:
        fillet(box(20, 20, 10), radius=2)
    """
    fc = _unwrap(shape)
    edge_list = fc.Edges if edges is None else list(edges)
    result = fc.makeFillet(radius, edge_list)
    return _preserve(result, shape)


# ── Chamfer ───────────────────────────────────────────────────────────────────

def chamfer(shape, size, edges=None):
    """
    Bevel edges of *shape* with the given *size*.

    Args:
        shape: PartikusShape to modify
        size:  chamfer distance (mm)
        edges: list of Part.Edge objects to bevel;
               None = bevel all edges

    Example:
        chamfer(box(20, 20, 10), size=1.5)
    """
    fc = _unwrap(shape)
    edge_list = fc.Edges if edges is None else list(edges)
    result = fc.makeChamfer(size, edge_list)
    return _preserve(result, shape)


# ── Shell ─────────────────────────────────────────────────────────────────────

def shell(shape, wall_thickness, open_faces=None):
    """
    Hollow out *shape*, leaving walls of *wall_thickness* mm.
    Specified faces are removed to create openings.

    Args:
        shape:          PartikusShape to hollow
        wall_thickness: wall thickness (mm)
        open_faces:     list of anchor name strings (e.g. ["TOP"]) or
                        Part.Face objects to remove.  Default: ["TOP"].

    Example:
        shell(box(30, 20, 15), wall_thickness=2)
        shell(box(30, 20, 15), wall_thickness=2, open_faces=["FRONT"])
    """
    if open_faces is None:
        open_faces = [TOP]

    fc = _unwrap(shape)
    fc_faces = []
    for spec in open_faces:
        if isinstance(spec, str):
            if not isinstance(shape, PartikusShape) or spec not in shape.anchors:
                raise ValueError(f"Anchor {spec!r} not found in shape")
            anchor_pos = shape.anchors[spec]
            fc_faces.append(
                min(fc.Faces, key=lambda f: (f.CenterOfMass - anchor_pos).Length)
            )
        else:
            fc_faces.append(spec)

    result = fc.makeThickness(fc_faces, -wall_thickness, 1e-3)
    return _preserve(result, shape)


# ── Offset ────────────────────────────────────────────────────────────────────

def offset(shape, distance):
    """
    Uniformly expand (positive *distance*) or shrink (negative) *shape*.

    Example:
        offset(sphere(20), 2)    # sphere with 2 mm added on all sides
        offset(box(10,10,10), -1)  # slightly smaller box
    """
    fc = _unwrap(shape)
    result = fc.makeOffsetShape(distance, 1e-3, False, False, 0, 0)
    return _bb_result(result)


# ── Deferred ──────────────────────────────────────────────────────────────────

def draft(shape, angle_deg, face, neutral_plane):
    """Apply mold draft angle. (Planned for a future milestone.)"""
    raise NotImplementedError("draft() planned for a future milestone.")


def emboss(shape, profile_2d, depth, face):
    """Raise a 2D profile on the surface. (Planned for a future milestone.)"""
    raise NotImplementedError("emboss() planned for a future milestone.")


def deboss(shape, profile_2d, depth, face):
    """Recess a 2D profile into the surface. (Planned for a future milestone.)"""
    raise NotImplementedError("deboss() planned for a future milestone.")


def knurl(shape, pattern="diamond", depth=0.3, pitch=1.0):
    """Add knurl texture. (Planned for a future milestone.)"""
    raise NotImplementedError("knurl() planned for a future milestone.")


def surface_texture(shape, texture, depth):
    """Add repeating surface pattern. (Planned for a future milestone.)"""
    raise NotImplementedError("surface_texture() planned for a future milestone.")
