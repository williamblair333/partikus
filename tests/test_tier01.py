"""Tests for Tier 1 raw primitives."""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import FreeCAD
from partikus.tier01_primitives import (
    box, cylinder, sphere, cone, torus, wedge, pyramid, disk, polyhedron,
)
from partikus.core.anchors import CENTER, TOP, BOTTOM, LEFT, RIGHT, FRONT, BACK


def _V(x, y, z):
    return FreeCAD.Vector(x, y, z)

def _eq(a, b, tol=0.5):
    return abs(a - b) < tol

def _vec_eq(v1, v2, tol=1e-3):
    return abs(v1.x - v2.x) < tol and abs(v1.y - v2.y) < tol and abs(v1.z - v2.z) < tol


# ── box ───────────────────────────────────────────────────────────────────────

def test_box_volume():
    assert _eq(box(10, 20, 30).shape.Volume, 6000.0, tol=0.01)

def test_box_defaults():
    assert _eq(box().shape.Volume, 1000.0, tol=0.01)

def test_box_centered():
    b = box(10, 20, 30)
    assert _vec_eq(b.anchors[CENTER], _V(0, 0, 0))
    assert _vec_eq(b.anchors[TOP],    _V(0, 0, 15))
    assert _vec_eq(b.anchors[BOTTOM], _V(0, 0, -15))
    assert _vec_eq(b.anchors[FRONT],  _V(0, 10, 0))
    assert _vec_eq(b.anchors[BACK],   _V(0, -10, 0))
    assert _vec_eq(b.anchors[RIGHT],  _V(5, 0, 0))
    assert _vec_eq(b.anchors[LEFT],   _V(-5, 0, 0))

def test_box_orientations_present():
    b = box(10, 10, 10)
    for a in (TOP, BOTTOM, FRONT, BACK, LEFT, RIGHT):
        assert a in b.orientations

def test_box_corner_anchors():
    from partikus.core.anchors import TOP_FRONT_RIGHT, BOTTOM_BACK_LEFT
    b = box(10, 20, 30)
    assert _vec_eq(b.anchors[TOP_FRONT_RIGHT],  _V(5, 10, 15))
    assert _vec_eq(b.anchors[BOTTOM_BACK_LEFT], _V(-5, -10, -15))


# ── cylinder ──────────────────────────────────────────────────────────────────

def test_cylinder_volume():
    c = cylinder(diameter=10, height=20)
    assert _eq(c.shape.Volume, math.pi * 25 * 20, tol=1.0)

def test_cylinder_defaults():
    c = cylinder()
    assert c.shape.Volume > 0

def test_cylinder_centered():
    c = cylinder(diameter=10, height=20)
    assert _vec_eq(c.anchors[CENTER], _V(0, 0, 0))
    assert _vec_eq(c.anchors[TOP],    _V(0, 0, 10))
    assert _vec_eq(c.anchors[BOTTOM], _V(0, 0, -10))

def test_cylinder_radius_param():
    c1 = cylinder(diameter=10, height=20)
    c2 = cylinder(radius=5,   height=20)
    assert _eq(c1.shape.Volume, c2.shape.Volume, tol=0.01)


# ── sphere ────────────────────────────────────────────────────────────────────

def test_sphere_volume():
    s = sphere(diameter=10)
    assert _eq(s.shape.Volume, (4/3) * math.pi * 125, tol=1.0)

def test_sphere_centered():
    s = sphere(diameter=10)
    assert _vec_eq(s.anchors[CENTER], _V(0, 0, 0))
    assert _vec_eq(s.anchors[TOP],    _V(0, 0, 5))
    assert _vec_eq(s.anchors[BOTTOM], _V(0, 0, -5))

def test_sphere_radius_param():
    s = sphere(radius=5)
    assert _eq(s.shape.Volume, (4/3) * math.pi * 125, tol=1.0)


# ── cone ──────────────────────────────────────────────────────────────────────

def test_cone_volume_point():
    c = cone(base_diameter=10, top_diameter=0, height=20)
    assert _eq(c.shape.Volume, math.pi * 25 * 20 / 3, tol=1.0)

def test_cone_volume_frustum():
    c = cone(base_diameter=10, top_diameter=6, height=20)
    R, r, h = 5, 3, 20
    expected = math.pi * h / 3 * (R**2 + R*r + r**2)
    assert _eq(c.shape.Volume, expected, tol=1.0)

def test_cone_centered():
    c = cone(base_diameter=10, top_diameter=0, height=20)
    assert _vec_eq(c.anchors[TOP],    _V(0, 0, 10))
    assert _vec_eq(c.anchors[BOTTOM], _V(0, 0, -10))


# ── torus ─────────────────────────────────────────────────────────────────────

def test_torus_volume():
    t = torus(major_diameter=20, minor_diameter=4)
    R, r = 10, 2
    expected = 2 * math.pi**2 * R * r**2
    assert _eq(t.shape.Volume, expected, tol=5.0)

def test_torus_centered():
    t = torus(major_diameter=20, minor_diameter=4)
    assert _vec_eq(t.anchors[CENTER], _V(0, 0, 0))


# ── wedge ─────────────────────────────────────────────────────────────────────

def test_wedge_volume():
    w = wedge(10, 10, 10)
    # Right-triangular prism: V = ½ × l × h × width
    assert _eq(w.shape.Volume, 0.5 * 10 * 10 * 10, tol=1.0)

def test_wedge_centered():
    w = wedge(10, 10, 10)
    # Bounding-box centre should be at origin
    bb = w.shape.BoundBox
    assert abs(bb.XMin + bb.XLength / 2) < 1e-3
    assert abs(bb.ZMin + bb.ZLength / 2) < 1e-3


# ── pyramid ───────────────────────────────────────────────────────────────────

def test_pyramid_volume():
    p = pyramid(10, 10, 10)
    expected = (1/3) * 100 * 10
    assert _eq(p.shape.Volume, expected, tol=1.0)

def test_pyramid_centered():
    p = pyramid(10, 10, 10)
    assert _vec_eq(p.anchors[TOP],    _V(0, 0, 5))
    assert _vec_eq(p.anchors[BOTTOM], _V(0, 0, -5))

def test_pyramid_is_solid():
    p = pyramid(20, 15, 25)
    assert p.shape.Volume > 0
    assert p.shape.isValid()


# ── disk ──────────────────────────────────────────────────────────────────────

def test_disk_volume():
    d = disk(diameter=10, thickness=2)
    assert _eq(d.shape.Volume, math.pi * 25 * 2, tol=0.5)

def test_disk_centered():
    d = disk(diameter=10, thickness=4)
    assert _vec_eq(d.anchors[TOP],    _V(0, 0, 2))
    assert _vec_eq(d.anchors[BOTTOM], _V(0, 0, -2))


# ── polyhedron ────────────────────────────────────────────────────────────────

def test_polyhedron_tetrahedron():
    s3 = math.sqrt(3)
    s6 = math.sqrt(6)
    verts = [
        (0, 0, 0),
        (1, 0, 0),
        (0.5, s3/2, 0),
        (0.5, s3/6, s6/3),
    ]
    # Each face wound so outward normal points away from interior
    faces = [[0, 2, 1], [0, 1, 3], [1, 2, 3], [0, 3, 2]]
    p = polyhedron(verts, faces)
    assert p.shape.Volume > 0
    assert p.shape.isValid()

def test_polyhedron_centered():
    verts = [(0,0,0),(2,0,0),(2,2,0),(0,2,0),
             (0,0,2),(2,0,2),(2,2,2),(0,2,2)]
    faces = [
        [0,3,2,1],[4,5,6,7],
        [0,1,5,4],[1,2,6,5],
        [2,3,7,6],[3,0,4,7],
    ]
    p = polyhedron(verts, faces)
    bb = p.shape.BoundBox
    assert abs(bb.XMin + bb.XLength / 2) < 1e-3
    assert abs(bb.YMin + bb.YLength / 2) < 1e-3
    assert abs(bb.ZMin + bb.ZLength / 2) < 1e-3
