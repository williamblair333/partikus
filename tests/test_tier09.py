"""Tests for Tier 9 boolean operations."""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from partikus.tier01_primitives import box, cylinder, sphere
from partikus.tier09_boolean import union, fuse, difference, cut, intersection, intersect
from partikus.tier14_assembly import translate


def _eq(a, b, tol=0.5):
    return abs(a - b) < tol


# ── union ─────────────────────────────────────────────────────────────────────

def test_union_non_overlapping():
    b1 = box(10, 10, 10)
    b2 = translate(box(10, 10, 10), dx=20)
    u = union(b1, b2)
    assert _eq(u.shape.Volume, 2000.0, tol=1.0)

def test_fuse_is_alias():
    b1 = box(10, 10, 10)
    b2 = box(10, 10, 10)
    assert _eq(fuse(b1, b2).shape.Volume, union(b1, b2).shape.Volume, tol=0.01)

def test_union_three_shapes():
    parts = [translate(box(5, 5, 5), dx=i*10) for i in range(3)]
    u = union(*parts)
    assert _eq(u.shape.Volume, 375.0, tol=1.0)

def test_union_overlapping():
    # Two 10³ boxes sharing half their volume
    b1 = box(10, 10, 10)
    b2 = translate(box(10, 10, 10), dx=5)
    u = union(b1, b2)
    assert u.shape.Volume < 2000.0
    assert u.shape.Volume > 1000.0

def test_union_requires_two():
    try:
        union(box(5, 5, 5))
        assert False, "should have raised"
    except ValueError:
        pass


# ── difference ────────────────────────────────────────────────────────────────

def test_difference_reduces_volume():
    b = box(10, 10, 10)
    c = cylinder(diameter=6, height=20)
    d = difference(b, c)
    assert d.shape.Volume < 1000.0
    assert d.shape.Volume > 0

def test_cut_is_alias():
    b = box(10, 10, 10)
    c = cylinder(diameter=6, height=20)
    assert _eq(cut(b, c).shape.Volume, difference(b, c).shape.Volume, tol=0.01)

def test_difference_multi():
    b = box(20, 20, 20)
    c1 = cylinder(diameter=4, height=25)
    c2 = translate(cylinder(diameter=4, height=25), dx=5)
    d = difference(b, c1, c2)
    assert d.shape.Volume < box(20, 20, 20).shape.Volume
    assert d.shape.Volume > 0


# ── intersection ──────────────────────────────────────────────────────────────

def test_intersection_two_boxes():
    b1 = box(10, 10, 10)
    b2 = translate(box(10, 10, 10), dx=5)
    i = intersection(b1, b2)
    # Overlap is a 5×10×10 box
    assert _eq(i.shape.Volume, 500.0, tol=1.0)

def test_intersect_is_alias():
    b1 = box(10, 10, 10)
    b2 = box(10, 10, 10)
    assert _eq(intersect(b1, b2).shape.Volume, intersection(b1, b2).shape.Volume, tol=0.01)

def test_intersection_box_sphere():
    b = box(10, 10, 10)
    s = sphere(diameter=12)
    i = intersection(b, s)
    # Result is the part of the sphere inside the box
    assert i.shape.Volume < s.shape.Volume
    assert i.shape.Volume > 0

def test_intersection_requires_two():
    try:
        intersection(box(5, 5, 5))
        assert False, "should have raised"
    except ValueError:
        pass


# ── hull / minkowski (deferred) ───────────────────────────────────────────────

def test_hull_not_implemented():
    from partikus.tier09_boolean import hull
    try:
        hull(box(5, 5, 5), box(5, 5, 5))
        assert False, "should raise NotImplementedError"
    except NotImplementedError:
        pass

def test_minkowski_not_implemented():
    from partikus.tier09_boolean import minkowski_sum
    try:
        minkowski_sum(box(5, 5, 5), sphere(diameter=2))
        assert False, "should raise NotImplementedError"
    except NotImplementedError:
        pass
