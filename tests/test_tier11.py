"""Tests for Tier 11 — Pattern / Array Operations."""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import FreeCAD
from partikus.tier01_primitives import box, cylinder
from partikus.tier11_patterns import linear_array, grid_array, polar_array, mirror

def _approx(a, b, tol=1.0):
    return abs(a - b) < tol

def _V(x, y, z):
    return FreeCAD.Vector(x, y, z)

def _vec_eq(v1, v2, tol=0.1):
    return abs(v1.x-v2.x) < tol and abs(v1.y-v2.y) < tol and abs(v1.z-v2.z) < tol


# ── linear_array ──────────────────────────────────────────────────────────────

def test_linear_array_volume():
    b = box(5, 5, 5)
    arr = linear_array(b, count=3, spacing=10)
    assert _approx(arr.shape.Volume, 375.0, tol=2.0)

def test_linear_array_centered():
    b = box(5, 5, 5)
    arr = linear_array(b, count=3, spacing=10)
    # Bounding box should be centred near origin in X
    bb = arr.shape.BoundBox
    cx = (bb.XMin + bb.XMax) / 2
    assert abs(cx) < 0.5

def test_linear_array_count_1():
    b = box(5, 5, 5)
    arr = linear_array(b, count=1, spacing=10)
    assert _approx(arr.shape.Volume, 125.0, tol=1.0)

def test_linear_array_y_axis():
    b = box(5, 5, 5)
    arr = linear_array(b, count=4, spacing=8, axis=(0, 1, 0))
    assert _approx(arr.shape.Volume, 500.0, tol=2.0)
    bb = arr.shape.BoundBox
    cy = (bb.YMin + bb.YMax) / 2
    assert abs(cy) < 0.5

def test_linear_array_valid():
    b = box(5, 5, 5)
    arr = linear_array(b, count=5, spacing=6)
    assert arr.shape.isValid()

def test_linear_array_bad_count():
    b = box(5, 5, 5)
    try:
        linear_array(b, count=0, spacing=10)
        assert False, "should raise"
    except ValueError:
        pass


# ── grid_array ────────────────────────────────────────────────────────────────

def test_grid_array_volume():
    b = box(5, 5, 5)
    arr = grid_array(b, count_x=3, count_y=2, spacing_x=10, spacing_y=10)
    assert _approx(arr.shape.Volume, 6 * 125.0, tol=5.0)

def test_grid_array_centered():
    b = box(5, 5, 5)
    arr = grid_array(b, count_x=3, count_y=3, spacing_x=10, spacing_y=10)
    bb = arr.shape.BoundBox
    cx = (bb.XMin + bb.XMax) / 2
    cy = (bb.YMin + bb.YMax) / 2
    assert abs(cx) < 0.5 and abs(cy) < 0.5

def test_grid_array_1x1():
    b = box(5, 5, 5)
    arr = grid_array(b, 1, 1, 10, 10)
    assert _approx(arr.shape.Volume, 125.0, tol=1.0)


# ── polar_array ───────────────────────────────────────────────────────────────

def test_polar_array_volume():
    c = cylinder(diameter=4, height=10)
    arr = polar_array(c, count=4, radius=15)
    cyl_vol = math.pi * 4 * 10   # r=2, h=10
    assert _approx(arr.shape.Volume, 4 * cyl_vol, tol=5.0)

def test_polar_array_count_1():
    c = cylinder(diameter=4, height=10)
    arr = polar_array(c, count=1, radius=10)
    cyl_vol = math.pi * 4 * 10
    assert _approx(arr.shape.Volume, cyl_vol, tol=2.0)

def test_polar_array_symmetric():
    b = box(3, 3, 3)
    arr = polar_array(b, count=4, radius=20)
    bb = arr.shape.BoundBox
    cx = (bb.XMin + bb.XMax) / 2
    cy = (bb.YMin + bb.YMax) / 2
    assert abs(cx) < 1.0 and abs(cy) < 1.0

def test_polar_array_valid():
    c = cylinder(diameter=4, height=10)
    arr = polar_array(c, count=6, radius=20)
    assert arr.shape.isValid()


# ── mirror ────────────────────────────────────────────────────────────────────

def test_mirror_xy_doubles_volume():
    b = box(10, 10, 10)
    from partikus.tier14_assembly import translate
    b_up = translate(b, dz=15)
    m = mirror(b_up, "XY")
    assert _approx(m.shape.Volume, 2 * 1000.0, tol=5.0)

def test_mirror_yz_symmetric():
    b = box(10, 10, 10)
    from partikus.tier14_assembly import translate
    b_right = translate(b, dx=15)
    m = mirror(b_right, "YZ")
    bb = m.shape.BoundBox
    cx = (bb.XMin + bb.XMax) / 2
    assert abs(cx) < 0.5

def test_mirror_xz_symmetric():
    b = box(10, 10, 10)
    from partikus.tier14_assembly import translate
    b_front = translate(b, dy=15)
    m = mirror(b_front, "XZ")
    bb = m.shape.BoundBox
    cy = (bb.YMin + bb.YMax) / 2
    assert abs(cy) < 0.5

def test_mirror_bad_plane():
    b = box(5, 5, 5)
    try:
        mirror(b, "ZX")
        assert False, "should raise"
    except ValueError:
        pass
