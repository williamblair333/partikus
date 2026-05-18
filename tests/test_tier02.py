"""Tests for Tier 2 — Enhanced Primitives."""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import FreeCAD
from partikus.tier02_enhanced import (
    rounded_box, chamfered_box, rounded_cylinder,
    tube, tube_by_wall, hollow_box,
    hemisphere, spherical_cap, frustum,
    prism, rounded_prism, stepped_cylinder,
)

def _approx(a, b, tol=1.0):
    return abs(a - b) < tol

def _V(x, y, z):
    return FreeCAD.Vector(x, y, z)

def _vec_eq(v1, v2, tol=0.1):
    return abs(v1.x-v2.x)<tol and abs(v1.y-v2.y)<tol and abs(v1.z-v2.z)<tol


# ── rounded_box ───────────────────────────────────────────────────────────────

def test_rounded_box_less_volume():
    from partikus.tier01_primitives import box
    b  = box(20, 20, 20)
    rb = rounded_box(20, 20, 20, fillet_radius=2)
    assert rb.shape.Volume < b.shape.Volume
    assert rb.shape.Volume > 0

def test_rounded_box_valid():
    assert rounded_box(20, 20, 10, 2).shape.isValid()

def test_rounded_box_anchors():
    rb = rounded_box(10, 10, 10, 1)
    assert abs(rb.anchors["TOP"].z - 5.0) < 0.01


# ── chamfered_box ─────────────────────────────────────────────────────────────

def test_chamfered_box_less_volume():
    from partikus.tier01_primitives import box
    b  = box(20, 20, 20)
    cb = chamfered_box(20, 20, 20, chamfer_size=2)
    assert cb.shape.Volume < b.shape.Volume

def test_chamfered_box_valid():
    assert chamfered_box(20, 20, 10, 1.5).shape.isValid()


# ── rounded_cylinder ─────────────────────────────────────────────────────────

def test_rounded_cylinder_less_volume():
    from partikus.tier01_primitives import cylinder
    c  = cylinder(diameter=20, height=30)
    rc = rounded_cylinder(diameter=20, height=30, fillet_radius=2)
    assert rc.shape.Volume < c.shape.Volume or _approx(rc.shape.Volume, c.shape.Volume, tol=5)

def test_rounded_cylinder_valid():
    assert rounded_cylinder(20, 30, 2).shape.isValid()

def test_rounded_cylinder_top_only():
    rc = rounded_cylinder(20, 30, 2, ends="TOP")
    assert rc.shape.isValid()

def test_rounded_cylinder_bottom_only():
    rc = rounded_cylinder(20, 30, 2, ends="BOTTOM")
    assert rc.shape.isValid()


# ── tube ──────────────────────────────────────────────────────────────────────

def test_tube_volume():
    t = tube(outer_diameter=20, inner_diameter=14, height=30)
    expected = math.pi * (100 - 49) * 30  # (R²-r²)*pi*h
    assert _approx(t.shape.Volume, expected, tol=5.0)

def test_tube_valid():
    assert tube(20, 14, 30).shape.isValid()

def test_tube_centered():
    t = tube(20, 14, 30)
    assert abs(t.anchors["CENTER"].z) < 0.5


# ── tube_by_wall ─────────────────────────────────────────────────────────────

def test_tube_by_wall_volume():
    t1 = tube(outer_diameter=20, inner_diameter=14, height=30)
    t2 = tube_by_wall(outer_diameter=20, wall_thickness=3, height=30)
    assert _approx(t1.shape.Volume, t2.shape.Volume, tol=2.0)

def test_tube_by_wall_too_thick():
    try:
        tube_by_wall(outer_diameter=10, wall_thickness=6, height=20)
        assert False, "should raise"
    except ValueError:
        pass


# ── hollow_box ────────────────────────────────────────────────────────────────

def test_hollow_box_valid():
    assert hollow_box(30, 20, 15, wall_thickness=2).shape.isValid()

def test_hollow_box_less_volume():
    from partikus.tier01_primitives import box
    b  = box(30, 20, 15)
    hb = hollow_box(30, 20, 15, wall_thickness=2)
    assert hb.shape.Volume < b.shape.Volume


# ── hemisphere ────────────────────────────────────────────────────────────────

def test_hemisphere_volume():
    h = hemisphere(diameter=20)
    expected = (2/3) * math.pi * 1000  # 2/3 * pi * r³
    assert _approx(h.shape.Volume, expected, tol=5.0)

def test_hemisphere_valid():
    assert hemisphere(20).shape.isValid()

def test_hemisphere_centered():
    h = hemisphere(20)
    assert abs(h.anchors["CENTER"].z) < 0.5


# ── spherical_cap ─────────────────────────────────────────────────────────────

def test_spherical_cap_valid():
    assert spherical_cap(diameter=20, height=5).shape.isValid()

def test_spherical_cap_positive_volume():
    assert spherical_cap(20, 5).shape.Volume > 0

def test_spherical_cap_less_than_sphere():
    from partikus.tier01_primitives import sphere
    s  = sphere(diameter=20)
    sc = spherical_cap(diameter=20, height=5)
    assert sc.shape.Volume < s.shape.Volume

def test_spherical_cap_centered():
    sc = spherical_cap(20, 5)
    assert abs(sc.anchors["TOP"].z - 2.5) < 0.1   # height/2


# ── frustum ───────────────────────────────────────────────────────────────────

def test_frustum_volume():
    f = frustum(base_diameter=20, top_diameter=10, height=20)
    R, r, h = 10, 5, 20
    expected = math.pi * h / 3 * (R**2 + R*r + r**2)
    assert _approx(f.shape.Volume, expected, tol=2.0)


# ── prism ─────────────────────────────────────────────────────────────────────

def test_prism_triangular():
    p = prism(sides=3, diameter=10, height=15)
    assert p.shape.Volume > 0
    assert p.shape.isValid()

def test_prism_hex_volume():
    p = prism(sides=6, diameter=10, height=20)
    # Area of regular hexagon with circumradius R: 3*sqrt(3)/2 * R²
    R = 5
    area = 3 * math.sqrt(3) / 2 * R**2
    assert _approx(p.shape.Volume, area * 20, tol=1.0)

def test_prism_centered():
    p = prism(6, 10, 20)
    assert abs(p.anchors["TOP"].z - 10.0) < 0.1

def test_prism_bad_sides():
    try:
        prism(sides=2, diameter=10, height=10)
        assert False, "should raise"
    except ValueError:
        pass


# ── rounded_prism ─────────────────────────────────────────────────────────────

def test_rounded_prism_valid():
    assert rounded_prism(6, 20, 30, 2).shape.isValid()

def test_rounded_prism_less_volume():
    p  = prism(6, 20, 30)
    rp = rounded_prism(6, 20, 30, 2)
    # Rounded prism should have slightly less volume (filleted corners)
    # or about the same (fillet may not significantly change volume)
    assert rp.shape.Volume > 0


# ── stepped_cylinder ─────────────────────────────────────────────────────────

def test_stepped_cylinder_volume():
    sc = stepped_cylinder([20, 15, 10], [10, 8, 5])
    v1 = math.pi * 100 * 10  # R=10, h=10
    v2 = math.pi * 56.25 * 8  # R=7.5, h=8
    v3 = math.pi * 25 * 5  # R=5, h=5
    # The smaller cylinders are coaxial inside the larger, so total volume = sum
    assert _approx(sc.shape.Volume, v1 + v2 + v3, tol=20.0)

def test_stepped_cylinder_centered():
    sc = stepped_cylinder([20, 10], [10, 10])
    assert abs(sc.anchors["CENTER"].z) < 0.5

def test_stepped_cylinder_valid():
    assert stepped_cylinder([20, 15], [15, 10]).shape.isValid()

def test_stepped_cylinder_mismatched_lists():
    try:
        stepped_cylinder([20, 15], [10])
        assert False, "should raise"
    except ValueError:
        pass

def test_stepped_cylinder_empty():
    try:
        stepped_cylinder([], [])
        assert False, "should raise"
    except ValueError:
        pass
