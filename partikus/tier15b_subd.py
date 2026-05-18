"""
Tier 15B — Subdivision Surfaces.

Implemented via a pure-Python Catmull-Clark engine (partikus.subd_mesh)
since FreeCAD 1.1.1 has no native SubD kernel. All functions return
PartikusShape wrapping a tessellated Part.Shape; the underlying SubDMesh
is attached as .subd_mesh for further editing.
"""

from .subd_mesh import (
    SubDMesh,
    cube_mesh, sphere_mesh, cylinder_mesh, cone_mesh, torus_mesh,
)


def _wrap(subd_mesh):
    """Convert SubDMesh to PartikusShape, attaching .subd_mesh for re-editing."""
    ps = subd_mesh.to_partikus_shape()
    ps.subd_mesh = subd_mesh
    return ps


def _unwrap(shape_or_subd):
    """Extract SubDMesh from a PartikusShape or return the SubDMesh directly."""
    if isinstance(shape_or_subd, SubDMesh):
        return shape_or_subd
    if hasattr(shape_or_subd, "subd_mesh"):
        return shape_or_subd.subd_mesh
    raise TypeError(
        "Expected a SubDMesh or a PartikusShape created by a subd_* function; "
        f"got {type(shape_or_subd).__name__}"
    )


def subd_primitive(primitive_type, **kwargs):
    """
    Create a SubD primitive and return it as a PartikusShape.

    primitive_type: "cube" | "sphere" | "cylinder" | "cone" | "torus"

    Keyword args per type:
        cube:     size=10.0
        sphere:   diameter=10.0
        cylinder: diameter=10.0, height=20.0, segments=8
        cone:     base_diameter=10.0, height=20.0, segments=8
        torus:    major_diameter=20.0, minor_diameter=5.0

    Returns:
        PartikusShape (with .subd_mesh for further SubD operations)

    Example:
        body = subd_primitive("cube", size=40)
        body = subd_subdivide(body, iterations=2)
    """
    pt = primitive_type.lower()
    if pt == "cube":
        mesh = cube_mesh(size=kwargs.get("size", 10.0))
    elif pt == "sphere":
        mesh = sphere_mesh(diameter=kwargs.get("diameter", 10.0))
    elif pt == "cylinder":
        mesh = cylinder_mesh(
            diameter=kwargs.get("diameter", 10.0),
            height=kwargs.get("height", 20.0),
            segments=kwargs.get("segments", 8),
        )
    elif pt == "cone":
        mesh = cone_mesh(
            base_diameter=kwargs.get("base_diameter", 10.0),
            height=kwargs.get("height", 20.0),
            segments=kwargs.get("segments", 8),
        )
    elif pt == "torus":
        mesh = torus_mesh(
            major_diameter=kwargs.get("major_diameter", 20.0),
            minor_diameter=kwargs.get("minor_diameter", 5.0),
            major_seg=kwargs.get("major_seg", 16),
            minor_seg=kwargs.get("minor_seg", 8),
        )
    else:
        raise ValueError(
            f"Unknown primitive type {primitive_type!r}. "
            "Choose from: cube, sphere, cylinder, cone, torus"
        )
    return _wrap(mesh)


def subd_push_pull(subd, faces, distance):
    """
    Extrude selected faces of a SubD mesh along their average normal.

    Args:
        subd:     PartikusShape from subd_* or SubDMesh
        faces:    list of face indices to extrude
        distance: extrusion distance in mm (positive = outward)

    Returns:
        PartikusShape

    Example:
        body = subd_primitive("cube", size=30)
        top  = subd_push_pull(body, faces=[1], distance=15)  # extrude top face
    """
    mesh = _unwrap(subd).copy()
    mesh.push_pull(list(faces), distance)
    return _wrap(mesh)


def subd_insert_loop(subd, edge, position=0.5):
    """
    Insert an edge loop through the mesh at fractional *position* along *edge*.

    Args:
        subd:     PartikusShape or SubDMesh
        edge:     (vi, vj) vertex index pair identifying the seed edge
        position: fraction along the edge [0, 1], default 0.5

    Returns:
        PartikusShape

    Example:
        body = subd_primitive("cube", size=30)
        body = subd_insert_loop(body, edge=(0, 1))
    """
    mesh = _unwrap(subd).copy()
    mesh.insert_loop(edge[0], edge[1], position)
    return _wrap(mesh)


def subd_bevel_edge(subd, edges, size, segments=1):
    """
    Bevel selected edges.

    Args:
        subd:     PartikusShape or SubDMesh
        edges:    list of (vi, vj) edge pairs
        size:     bevel offset as fraction of edge length [0, 0.5]
        segments: number of bevel segments (1 = single chamfer loop)

    Returns:
        PartikusShape

    Example:
        body = subd_primitive("cube", size=30)
        body = subd_bevel_edge(body, edges=[(0,1),(1,2)], size=0.1)
    """
    mesh = _unwrap(subd).copy()
    mesh.bevel_edge(list(edges), size, segments)
    return _wrap(mesh)


def subd_bevel_vertex(subd, vertices, size):
    """
    Bevel selected vertices by inserting edge loops on all incident edges.

    Args:
        subd:     PartikusShape or SubDMesh
        vertices: list of vertex indices
        size:     bevel offset as fraction [0, 0.5]

    Returns:
        PartikusShape
    """
    mesh = _unwrap(subd).copy()
    efm  = mesh._efm()
    vert_set = set(vertices)
    edges = [e for e in efm if e[0] in vert_set or e[1] in vert_set]
    mesh.bevel_edge(edges, size, segments=1)
    return _wrap(mesh)


def subd_bridge(subd, faces_a, faces_b):
    """
    Bridge two face loops with new quad faces.

    Args:
        subd:    PartikusShape or SubDMesh
        faces_a: list of face indices for the first loop
        faces_b: list of face indices for the second loop

    Returns:
        PartikusShape

    Example:
        body   = subd_primitive("cylinder", diameter=20, height=40)
        bottom = [fi for fi, f in enumerate(body.subd_mesh.faces) if fi < 8]
        top    = [fi for fi, f in enumerate(body.subd_mesh.faces) if 8 <= fi < 16]
        linked = subd_bridge(body, bottom, top)
    """
    mesh = _unwrap(subd).copy()
    mesh.bridge(list(faces_a), list(faces_b))
    return _wrap(mesh)


def subd_subdivide(subd, iterations=1):
    """
    Apply *iterations* rounds of Catmull-Clark subdivision.

    Args:
        subd:       PartikusShape or SubDMesh
        iterations: number of subdivision steps (each step ~quadruples face count)

    Returns:
        PartikusShape

    Example:
        body = subd_primitive("cube", size=30)
        smooth = subd_subdivide(body, iterations=3)
    """
    mesh = _unwrap(subd).copy()
    mesh.subdivide(iterations)
    return _wrap(mesh)


def subd_crease(subd, edges, sharpness=1.0):
    """
    Mark edges as sharp creases.

    Args:
        subd:      PartikusShape or SubDMesh
        edges:     list of (vi, vj) edge pairs
        sharpness: crease sharpness [0, ∞). 1.0 = fully sharp; decays by 1
                   per subdivision iteration (semi-sharp creases use values > 1)

    Returns:
        PartikusShape

    Example:
        body  = subd_primitive("cube", size=30)
        body  = subd_crease(body, edges=[(0,1),(1,2),(2,3),(3,0)], sharpness=2.0)
        sharp = subd_subdivide(body, iterations=2)
    """
    mesh = _unwrap(subd).copy()
    mesh.crease(list(edges), sharpness)
    return _wrap(mesh)


def subd_symmetry(subd, plane="YZ", mode="mirror"):
    """
    Apply symmetry to a SubD mesh.

    Args:
        subd:  PartikusShape or SubDMesh
        plane: "YZ" (mirror in X), "XZ" (mirror in Y), "XY" (mirror in Z)
        mode:  "mirror" (keep both halves) or "replace" (keep only mirror)

    Returns:
        PartikusShape

    Example:
        half = subd_primitive("cube", size=20)
        full = subd_symmetry(half, plane="YZ")
    """
    mesh = _unwrap(subd).copy()
    mesh.symmetry(plane, mode)
    return _wrap(mesh)


def subd_soft_select(subd, vertices, falloff_radius):
    """
    Compute a soft-selection weight dict for vertices near *vertices*.

    This does not modify the mesh — it returns a weight dict that can be
    passed to sculpt operations.

    Args:
        subd:          PartikusShape or SubDMesh
        vertices:      list of center vertex indices
        falloff_radius: influence radius in mm

    Returns:
        dict {vertex_idx: weight} with values in [0, 1]

    Example:
        weights = subd_soft_select(body, vertices=[0], falloff_radius=10)
    """
    mesh    = _unwrap(subd)
    combined = {}
    for vi in vertices:
        for idx, w in mesh.soft_select(vi, falloff_radius).items():
            combined[idx] = max(combined.get(idx, 0.0), w)
    return combined


def subd_sculpt_brush(subd, point, brush_type, strength, radius):
    """
    Apply a sculpt brush at *point*.

    Args:
        subd:       PartikusShape or SubDMesh
        point:      (x, y, z) brush center in mm
        brush_type: "push" | "pull" | "smooth" | "pinch" | "inflate" | "flatten"
        strength:   displacement magnitude in mm
        radius:     brush influence radius in mm

    Returns:
        PartikusShape

    Example:
        body = subd_primitive("sphere", diameter=30)
        body = subd_subdivide(body, iterations=2)
        body = subd_sculpt_brush(body, point=(0,0,15), brush_type="pull",
                                 strength=3, radius=8)
    """
    mesh = _unwrap(subd).copy()
    mesh.sculpt(point, brush_type, strength, radius)
    return _wrap(mesh)
