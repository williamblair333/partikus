"""
Tier 15C — SubD ↔ NURBS Conversion Bridges.

mesh_to_nurbs is implemented via BSplineSurface.approximate on mesh vertices.
SubD-related conversions are stubbed pending Milestone 6 (SubD integration).
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


def subd_to_nurbs(subd, target_tolerance=0.01):
    """Convert SubD mesh to NURBS surface. (Milestone 6 — requires SubD support)"""
    raise NotImplementedError("subd_to_nurbs — planned for Milestone 6")


def nurbs_to_subd(surface, density="medium"):
    """Convert NURBS surface to SubD mesh. (Milestone 6 — requires SubD support)"""
    raise NotImplementedError("nurbs_to_subd — planned for Milestone 6")


def mesh_to_subd(mesh, preserve_features=True):
    """Convert polygon mesh to SubD. (Milestone 6 — requires SubD support)"""
    raise NotImplementedError("mesh_to_subd — planned for Milestone 6")


def mesh_to_nurbs(mesh, patch_size="auto", degree=3, tolerance=0.1):
    """
    Fit a NURBS surface to a Part.Shape mesh or PartikusShape via
    BSplineSurface.approximate on sampled vertex positions.

    The input is converted to a point cloud by sampling mesh vertices and
    re-gridding them into a regular U×V array via nearest-neighbour projection
    onto the dominant plane.

    Args:
        mesh:       PartikusShape or Part.Shape (Solid, Shell, or Face)
        patch_size: "auto" | "fine" | "coarse" — controls grid density;
                    "auto" targets ~8×8, "fine" 16×16, "coarse" 4×4
        degree:     output NURBS degree (1–5)
        tolerance:  approximation tolerance in mm

    Returns:
        PartikusShape wrapping a Part.Face (BSplineSurface)

    Example:
        box_shape = box(40, 30, 20)
        top_face  = box_shape.shape.Faces[0]   # Part.Face
        nurbs     = mesh_to_nurbs(top_face)
    """
    from .core.shape_wrapper import PartikusShape as _PS
    if isinstance(mesh, _PS):
        raw = mesh.shape
    else:
        raw = mesh

    density_map = {"coarse": 4, "auto": 8, "fine": 16}
    if patch_size not in density_map:
        raise ValueError(f"patch_size must be 'auto', 'fine', or 'coarse', got '{patch_size}'")
    n = density_map[patch_size]

    # Collect vertices from the shape
    if hasattr(raw, 'Vertexes'):
        verts = [v.Point for v in raw.Vertexes]
    elif hasattr(raw, 'Points'):
        verts = list(raw.Points)
    else:
        raise TypeError("mesh must have .Vertexes or .Points")

    if len(verts) < 4:
        raise ValueError("mesh must have at least 4 vertices")

    # Project vertices onto dominant plane (bounding box face with largest area)
    bb = raw.BoundBox
    dx, dy, dz = bb.XLength, bb.YLength, bb.ZLength
    # choose the two axes with the largest span
    spans = sorted([(dx, 0), (dy, 1), (dz, 2)], reverse=True)
    ua, va = spans[0][1], spans[1][1]  # primary U and V axis indices

    def _coord(v, axis):
        return (v.x, v.y, v.z)[axis]

    # Build a regular n×n grid by binning
    u_vals = [_coord(v, ua) for v in verts]
    v_vals = [_coord(v, va) for v in verts]
    u_min, u_max = min(u_vals), max(u_vals)
    v_min, v_max = min(v_vals), max(v_vals)

    if u_max == u_min or v_max == v_min:
        raise ValueError("mesh is degenerate in one or more directions")

    # For each grid cell, pick the vertex closest to the cell centre
    grid = []
    for i in range(n):
        u_target = u_min + (u_max - u_min) * i / (n - 1)
        row = []
        for j in range(n):
            v_target = v_min + (v_max - v_min) * j / (n - 1)
            best = min(verts, key=lambda v: (
                (_coord(v, ua) - u_target)**2 + (_coord(v, va) - v_target)**2
            ))
            row.append(best)
        grid.append(row)

    bss = Part.BSplineSurface()
    bss.approximate(grid, degree, degree, 1, tolerance)
    face = bss.toShape()
    return _bb_result(face)
