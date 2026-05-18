"""
Tier 15B — Subdivision Surfaces.

FreeCAD 1.1.1 has no native SubD support. All functions raise
NotImplementedError. Integration options (OpenSubDiv, Blender exchange)
are deferred to Milestone 5.
"""


def subd_primitive(primitive_type, **kwargs):
    """SubD primitive (cube/sphere/cylinder/cone/torus). (Milestone 5)"""
    raise NotImplementedError("subd_primitive — no native SubD in FreeCAD 1.1.1; planned for Milestone 5")

def subd_push_pull(subd, faces, distance):
    raise NotImplementedError("subd_push_pull — planned for Milestone 5")

def subd_insert_loop(subd, edge, position=0.5):
    raise NotImplementedError("subd_insert_loop — planned for Milestone 5")

def subd_bevel_edge(subd, edges, size, segments=1):
    raise NotImplementedError("subd_bevel_edge — planned for Milestone 5")

def subd_bevel_vertex(subd, vertices, size):
    raise NotImplementedError("subd_bevel_vertex — planned for Milestone 5")

def subd_bridge(subd, faces_a, faces_b):
    raise NotImplementedError("subd_bridge — planned for Milestone 5")

def subd_subdivide(subd, iterations=1):
    raise NotImplementedError("subd_subdivide — planned for Milestone 5")

def subd_crease(subd, edges, sharpness=1.0):
    raise NotImplementedError("subd_crease — planned for Milestone 5")

def subd_symmetry(subd, plane, mode="mirror"):
    raise NotImplementedError("subd_symmetry — planned for Milestone 5")

def subd_soft_select(subd, vertices, falloff_radius):
    raise NotImplementedError("subd_soft_select — planned for Milestone 5")

def subd_sculpt_brush(subd, point, brush_type, strength, radius):
    raise NotImplementedError("subd_sculpt_brush — planned for Milestone 5")
