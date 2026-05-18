"""Tests for core shape wrapper and transform utilities."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import FreeCAD
import Part
from partikus.core.shape_wrapper import PartikusShape
from partikus.core.transforms import rotation_from_to
from partikus.core.anchors import CENTER, TOP, BOTTOM, LEFT, RIGHT, FRONT, BACK
from partikus.tier14_assembly import translate, rotate


def _V(x, y, z):
    return FreeCAD.Vector(x, y, z)

def _eq(a, b, tol=1e-4):
    return abs(a - b) < tol

def _vec_eq(v1, v2, tol=1e-4):
    return abs(v1.x - v2.x) < tol and abs(v1.y - v2.y) < tol and abs(v1.z - v2.z) < tol


def test_shape_wrapper_basic():
    shape = Part.makeBox(10, 10, 10)
    ps = PartikusShape(shape, {CENTER: _V(0, 0, 0)})
    assert ps.shape is shape
    assert CENTER in ps.anchors
    assert ps.orientations == {}


def test_translate_moves_center():
    from partikus.tier01_primitives import box
    b = box(10, 10, 10)
    moved = translate(b, 5, 3, -2)
    assert _vec_eq(moved.anchors[CENTER], _V(5, 3, -2))


def test_translate_moves_all_anchors():
    from partikus.tier01_primitives import box
    b = box(10, 10, 10)
    moved = translate(b, 0, 0, 10)
    assert _vec_eq(moved.anchors[TOP],    _V(0, 0, 15))
    assert _vec_eq(moved.anchors[BOTTOM], _V(0, 0,  5))


def test_translate_preserves_volume():
    from partikus.tier01_primitives import box
    b = box(10, 10, 10)
    moved = translate(b, 100, 200, 300)
    assert _eq(moved.shape.Volume, 1000.0, tol=1e-2)


def test_rotate_90_z_moves_right_to_front():
    from partikus.tier01_primitives import box
    b = box(10, 10, 10)
    r = rotate(b, axis=_V(0, 0, 1), angle_deg=90)
    # RIGHT anchor was at (5,0,0) → should be at (0,5,0)
    assert _vec_eq(r.anchors[RIGHT], _V(0, 5, 0), tol=1e-3)


def test_rotate_preserves_center():
    from partikus.tier01_primitives import box
    b = box(10, 10, 10)
    r = rotate(b, axis=_V(1, 1, 1), angle_deg=120)
    assert _vec_eq(r.anchors[CENTER], _V(0, 0, 0), tol=1e-3)


def test_rotate_top_stays_on_z_after_z_rotation():
    from partikus.tier01_primitives import cylinder
    c = cylinder(10, 20)
    r = rotate(c, axis=_V(0, 0, 1), angle_deg=45)
    assert _vec_eq(r.anchors[TOP], _V(0, 0, 10), tol=1e-3)


def test_rotation_from_to_basic():
    r = rotation_from_to(_V(0, 0, 1), _V(1, 0, 0))
    result = r.multVec(_V(0, 0, 1))
    assert _vec_eq(result, _V(1, 0, 0), tol=1e-4)


def test_rotation_from_to_identity():
    r = rotation_from_to(_V(0, 1, 0), _V(0, 1, 0))
    result = r.multVec(_V(3, 4, 5))
    assert _vec_eq(result, _V(3, 4, 5), tol=1e-4)


def test_rotation_from_to_antiparallel():
    r = rotation_from_to(_V(0, 0, 1), _V(0, 0, -1))
    result = r.multVec(_V(0, 0, 1))
    assert _vec_eq(result, _V(0, 0, -1), tol=1e-4)


def test_shape_repr():
    from partikus.tier01_primitives import box
    b = box(10, 10, 10)
    s = repr(b)
    assert "PartikusShape" in s
    assert "volume" in s.lower()
