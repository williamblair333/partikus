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
    """
    Convert a SubD mesh to a NURBS surface by subdividing until the tessellated
    mesh approximates a smooth surface, then fitting a BSplineSurface.

    Args:
        subd:             SubDMesh or PartikusShape created by a subd_* function
        target_tolerance: max deviation from the subdivided mesh in mm

    Returns:
        PartikusShape wrapping a Part.Face (BSplineSurface)

    Example:
        body  = subd_primitive("cube", size=20)
        nurbs = subd_to_nurbs(subd_subdivide(body, 3))
    """
    from .subd_mesh import SubDMesh

    if isinstance(subd, SubDMesh):
        mesh = subd
    elif hasattr(subd, "subd_mesh"):
        mesh = subd.subd_mesh
    else:
        raise TypeError("subd must be a SubDMesh or a PartikusShape from a subd_* function")

    # Subdivide to a fine enough mesh, then fit via mesh_to_nurbs
    refined = mesh.copy().subdivide(2)
    fc_mesh_shape = refined.to_part_shape()
    return mesh_to_nurbs(fc_mesh_shape, patch_size="fine", degree=3, tolerance=target_tolerance)


def nurbs_to_subd(surface, density="medium"):
    """
    Sample a NURBS surface onto a regular quad grid to produce a SubDMesh.

    Args:
        surface: PartikusShape wrapping a Part.Face (BSplineSurface) or Part.Face
        density: "coarse" (4×4), "medium" (8×8), "fine" (16×16) sample grid

    Returns:
        SubDMesh

    Example:
        from partikus import surface_from_points, nurbs_to_subd
        surf = surface_from_points(my_grid)
        mesh = nurbs_to_subd(surf, density="medium")
    """
    from .subd_mesh import SubDMesh
    from .core.shape_wrapper import PartikusShape

    density_map = {"coarse": 4, "medium": 8, "fine": 16}
    if density not in density_map:
        raise ValueError(f"density must be 'coarse', 'medium', or 'fine', got {density!r}")
    n = density_map[density]

    if isinstance(surface, PartikusShape):
        face = surface.shape
    else:
        face = surface

    if not hasattr(face, "Surface"):
        raise TypeError("surface must wrap a Part.Face with an underlying BSplineSurface")

    bss = face.Surface
    u0, u1, v0, v1 = face.ParameterRange

    verts = []
    grid_idx = {}
    for i in range(n):
        u = u0 + (u1 - u0) * i / (n - 1)
        for j in range(n):
            v = v0 + (v1 - v0) * j / (n - 1)
            pt = bss.value(u, v)
            grid_idx[(i, j)] = len(verts)
            verts.append([pt.x, pt.y, pt.z])

    faces = []
    for i in range(n - 1):
        for j in range(n - 1):
            a = grid_idx[(i,     j    )]
            b = grid_idx[(i + 1, j    )]
            c = grid_idx[(i + 1, j + 1)]
            d = grid_idx[(i,     j + 1)]
            faces.append([a, b, c, d])

    return SubDMesh(verts, faces)


def mesh_to_subd(mesh, preserve_features=True):
    """
    Convert a Part.Shape mesh or PartikusShape to a SubDMesh by extracting
    vertex and face topology.

    Args:
        mesh:              PartikusShape or Part.Shape (Solid, Shell, or compound)
        preserve_features: if True, mark boundary edges as sharp creases

    Returns:
        SubDMesh

    Example:
        from partikus import box, mesh_to_subd
        box_subd = mesh_to_subd(box(30, 20, 10))
        smooth   = box_subd.subdivide(2).to_partikus_shape()
    """
    from .subd_mesh import SubDMesh
    from .core.shape_wrapper import PartikusShape

    if isinstance(mesh, PartikusShape):
        raw = mesh.shape
    else:
        raw = mesh

    vert_list  = []
    vert_index = {}

    def _key(pt, tol=1e-4):
        return (round(pt.x / tol), round(pt.y / tol), round(pt.z / tol))

    def _get_or_add(pt):
        k = _key(pt)
        if k not in vert_index:
            vert_index[k] = len(vert_list)
            vert_list.append([pt.x, pt.y, pt.z])
        return vert_index[k]

    face_list = []
    for face in raw.Faces:
        pts, tris = face.tessellate(0.5)
        for tri in tris:
            fi = [_get_or_add(pts[i]) for i in tri]
            if len(set(fi)) == 3:
                face_list.append(fi)

    if not face_list:
        raise ValueError("mesh has no faces to extract")

    subd = SubDMesh(vert_list, face_list)

    if preserve_features:
        # Mark edges where the dihedral angle between adjacent faces is sharp
        # (> 30 degrees) as creases. This preserves hard edges on closed solids
        # like boxes where no boundary edges exist.
        _CREASE_ANGLE_COS = math.cos(math.radians(30))
        efm = subd._efm()
        for e, fis in efm.items():
            if len(fis) == 1:
                # True boundary edge — always crease
                subd.creases[e] = 1.0
            elif len(fis) == 2:
                # Interior edge — crease if dihedral angle is sharp
                n0 = subd.face_normal(fis[0])
                n1 = subd.face_normal(fis[1])
                dot = sum(n0[c] * n1[c] for c in range(3))
                if dot < _CREASE_ANGLE_COS:
                    subd.creases[e] = 1.0

    return subd


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
