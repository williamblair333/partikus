"""Tests for Tier 14 assembly operations."""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import FreeCAD
from partikus.tier01_primitives import box, cylinder, sphere
from partikus.tier14_assembly import (
    translate, rotate, scale, mirror_position,
    attach, stack_on, place_beside, align, coaxial,
)
from partikus.core.anchors import CENTER, TOP, BOTTOM, LEFT, RIGHT, FRONT, BACK


def _V(x, y, z):
    return FreeCAD.Vector(x, y, z)

def _eq(a, b, tol=1e-3):
    return abs(a - b) < tol

def _vec_eq(v1, v2, tol=0.05):
    return abs(v1.x-v2.x) < tol and abs(v1.y-v2.y) < tol and abs(v1.z-v2.z) < tol


# ── translate ─────────────────────────────────────────────────────────────────

def test_translate_center():
    b = box(10, 10, 10)
    m = translate(b, 5, 3, -2)
    assert _vec_eq(m.anchors[CENTER], _V(5, 3, -2))

def test_translate_preserves_volume():
    b = box(10, 10, 10)
    assert _eq(translate(b, 100, 200, 300).shape.Volume, 1000.0, tol=0.01)

def test_translate_all_anchors_shift():
    b = box(10, 10, 10)
    m = translate(b, 0, 0, 5)
    assert _vec_eq(m.anchors[TOP],    _V(0, 0, 10))
    assert _vec_eq(m.anchors[BOTTOM], _V(0, 0,  0))


# ── rotate ────────────────────────────────────────────────────────────────────

def test_rotate_90_z():
    b = box(10, 20, 10)
    r = rotate(b, axis=_V(0, 0, 1), angle_deg=90)
    # RIGHT (5,0,0) → (0,5,0)
    assert _vec_eq(r.anchors[RIGHT], _V(0, 5, 0))
    # FRONT (0,10,0) → (-10,0,0)
    assert _vec_eq(r.anchors[FRONT], _V(-10, 0, 0))

def test_rotate_preserves_volume():
    b = box(10, 20, 30)
    assert _eq(rotate(b, axis=_V(1, 1, 0), angle_deg=45).shape.Volume, 6000.0, tol=1.0)

def test_rotate_about_non_origin_center():
    b = box(10, 10, 10)
    # Rotate 90° around Z with center at (10,0,0)
    r = rotate(b, axis=_V(0, 0, 1), angle_deg=90, center=_V(10, 0, 0))
    # CENTER was at (0,0,0), after rotation about (10,0,0):
    # new = (10,0,0) + R*((-10,0,0)) = (10,0,0) + (0,-10,0) = (10,-10,0)
    assert _vec_eq(r.anchors[CENTER], _V(10, -10, 0), tol=0.1)

def test_rotate_orientation_updates():
    b = box(10, 10, 10)
    r = rotate(b, axis=_V(0, 0, 1), angle_deg=90)
    # TOP orientation should still be (0,0,1) — rotation around Z doesn't change it
    assert _vec_eq(r.orientations[TOP], _V(0, 0, 1))
    # FRONT orientation (0,1,0) → (-1,0,0) after 90° CW rotation around Z
    assert _vec_eq(r.orientations[FRONT], _V(-1, 0, 0), tol=1e-3)


# ── scale ─────────────────────────────────────────────────────────────────────

def test_scale_uniform():
    b = box(10, 10, 10)
    s = scale(b, 2.0)
    assert _eq(s.shape.Volume, 8000.0, tol=1.0)

def test_scale_non_uniform():
    b = box(10, 10, 10)
    s = scale(b, fx=2, fy=1, fz=1)
    assert _eq(s.shape.Volume, 2000.0, tol=1.0)

def test_scale_anchors():
    b = box(10, 10, 10)
    s = scale(b, 3.0)
    assert _vec_eq(s.anchors[TOP], _V(0, 0, 15))


# ── mirror_position ───────────────────────────────────────────────────────────

def test_mirror_position_xz():
    b = translate(box(10, 10, 10), dy=20)
    m = mirror_position(b, "XZ")
    assert _vec_eq(m.anchors[CENTER], _V(0, -20, 0))


# ── attach ────────────────────────────────────────────────────────────────────

def test_attach_bottom_to_top():
    base    = box(20, 20, 10)   # TOP at z=5
    top_box = box(10, 10,  5)   # BOTTOM at z=-2.5
    result  = attach(top_box, base, child_anchor=BOTTOM, parent_anchor=TOP)
    # top_box BOTTOM should land at base TOP = (0,0,5)
    assert _vec_eq(result.anchors[BOTTOM], _V(0, 0, 5))
    # top_box TOP should be at z=5+5=10
    assert _vec_eq(result.anchors[TOP],    _V(0, 0, 10))

def test_attach_with_offset():
    base    = box(20, 20, 10)
    top_box = box(10, 10,  5)
    result  = attach(top_box, base, child_anchor=BOTTOM, parent_anchor=TOP, offset=2)
    assert _vec_eq(result.anchors[BOTTOM], _V(0, 0, 7))

def test_attach_preserves_volume():
    base    = box(20, 20, 10)
    top_box = box(10, 10,  5)
    result  = attach(top_box, base)
    assert _eq(result.shape.Volume, 500.0, tol=1.0)


# ── stack_on ──────────────────────────────────────────────────────────────────

def test_stack_on():
    base    = box(20, 20, 10)
    top_box = box(10, 10,  5)
    result  = stack_on(top_box, base)
    assert _vec_eq(result.anchors[BOTTOM], _V(0, 0, 5))


# ── place_beside ──────────────────────────────────────────────────────────────

def test_place_beside_right():
    base  = box(10, 10, 10)
    buddy = box(10, 10, 10)
    result = place_beside(buddy, base, side=RIGHT)
    # buddy's LEFT should meet base's RIGHT (at x=5)
    assert _vec_eq(result.anchors[LEFT], _V(5, 0, 0), tol=0.1)

def test_place_beside_right_with_gap():
    base  = box(10, 10, 10)
    buddy = box(10, 10, 10)
    result = place_beside(buddy, base, side=RIGHT, gap=5)
    # buddy LEFT should be at x = 5 + 5 = 10
    assert _vec_eq(result.anchors[LEFT], _V(10, 0, 0), tol=0.1)


# ── align / coaxial ───────────────────────────────────────────────────────────

def test_align_z():
    a = translate(box(10, 10, 10), dz=20)
    b = box(10, 10, 10)
    result = align(a, b, "Z")
    assert _vec_eq(result.anchors[CENTER], _V(0, 0, 0), tol=0.1)

def test_coaxial():
    a = translate(box(10, 10, 10), dx=15, dy=8)
    b = box(10, 10, 10)
    result = coaxial(a, b)
    assert _vec_eq(result.anchors[CENTER], _V(0, 0, 0), tol=0.1)
