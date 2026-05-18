"""Tests for Tier 3 — 2D Profiles."""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import FreeCAD
import Part
from partikus.tier03_profiles_2d import (
    rectangle, rounded_rectangle, chamfered_rectangle,
    circle, ellipse, regular_polygon, star,
    slot, teardrop, arc, polyline,
)
from partikus.tier12_sweep_loft import extrude

def _approx(a, b, tol=0.5):
    return abs(a - b) < tol

def _is_wire(w):
    return isinstance(w, Part.Wire)

def _extruded_volume(wire, h=1.0):
    """Extrude a profile by h mm and return the volume."""
    try:
        face = Part.Face(wire)
        return face.extrude(FreeCAD.Vector(0, 0, h)).Volume
    except Exception:
        return None


# ── rectangle ─────────────────────────────────────────────────────────────────

def test_rectangle_is_wire():
    assert _is_wire(rectangle(10, 10))

def test_rectangle_area():
    vol = _extruded_volume(rectangle(10, 20), h=1)
    assert _approx(vol, 200.0, tol=0.1)

def test_rectangle_defaults():
    vol = _extruded_volume(rectangle(), h=1)
    assert _approx(vol, 100.0, tol=0.1)


# ── rounded_rectangle ─────────────────────────────────────────────────────────

def test_rounded_rectangle_is_wire():
    assert _is_wire(rounded_rectangle(20, 10, 2))

def test_rounded_rectangle_less_area_than_rect():
    rr = rounded_rectangle(20, 10, 2)
    r  = rectangle(20, 10)
    vol_rr = _extruded_volume(rr, h=1)
    vol_r  = _extruded_volume(r,  h=1)
    assert vol_rr < vol_r  # corners removed

def test_rounded_rectangle_positive_volume():
    vol = _extruded_volume(rounded_rectangle(30, 20, 3), h=1)
    assert vol > 0

def test_rounded_rectangle_too_large_radius():
    try:
        rounded_rectangle(10, 10, 6)
        assert False, "should raise"
    except ValueError:
        pass


# ── chamfered_rectangle ───────────────────────────────────────────────────────

def test_chamfered_rectangle_is_wire():
    assert _is_wire(chamfered_rectangle(20, 10, 2))

def test_chamfered_rectangle_less_area_than_rect():
    cr = chamfered_rectangle(20, 10, 2)
    r  = rectangle(20, 10)
    vol_cr = _extruded_volume(cr, h=1)
    vol_r  = _extruded_volume(r,  h=1)
    assert vol_cr < vol_r


# ── circle ────────────────────────────────────────────────────────────────────

def test_circle_is_wire():
    assert _is_wire(circle(10))

def test_circle_area():
    vol = _extruded_volume(circle(10), h=1)
    assert _approx(vol, math.pi * 25, tol=0.1)

def test_circle_radius_param():
    w1 = circle(diameter=10)
    w2 = circle(radius=5)
    v1 = _extruded_volume(w1, h=1)
    v2 = _extruded_volume(w2, h=1)
    assert _approx(v1, v2, tol=0.01)


# ── ellipse ───────────────────────────────────────────────────────────────────

def test_ellipse_is_wire():
    assert _is_wire(ellipse(20, 10))

def test_ellipse_area():
    vol = _extruded_volume(ellipse(20, 10), h=1)
    expected = math.pi * 10 * 5  # pi * a * b
    assert _approx(vol, expected, tol=0.5)


# ── regular_polygon ───────────────────────────────────────────────────────────

def test_regular_polygon_is_wire():
    assert _is_wire(regular_polygon(6, 10))

def test_regular_polygon_triangle():
    vol = _extruded_volume(regular_polygon(3, diameter=10), h=1)
    # Area of equilateral triangle inscribed in circle r=5: 3*sqrt(3)/4 * side²
    # side = 5*sqrt(3); area = 3*sqrt(3)/4 * 75 = 75*sqrt(3)/4 ≈ 32.5
    assert _approx(vol, 32.5, tol=1.0)

def test_regular_polygon_too_few_sides():
    try:
        regular_polygon(2, 10)
        assert False, "should raise"
    except ValueError:
        pass

def test_regular_polygon_hex_volume():
    # Hexagon inscribed in circle r=5: area = 3*sqrt(3)/2 * r²
    vol = _extruded_volume(regular_polygon(6, diameter=10), h=1)
    expected = 3 * math.sqrt(3) / 2 * 25
    assert _approx(vol, expected, tol=0.5)


# ── star ──────────────────────────────────────────────────────────────────────

def test_star_is_wire():
    assert _is_wire(star(5, 20, 8))

def test_star_positive_area():
    vol = _extruded_volume(star(5, 20, 8), h=1)
    assert vol > 0


# ── slot ──────────────────────────────────────────────────────────────────────

def test_slot_is_wire():
    assert _is_wire(slot(20, 8))

def test_slot_area_larger_than_circle():
    # slot of length=20, width=8 should have area > circle of width=8
    vol_slot = _extruded_volume(slot(20, 8), h=1)
    vol_circ = _extruded_volume(circle(8), h=1)
    assert vol_slot > vol_circ

def test_slot_equal_lengths_is_circle():
    # When length == width, slot degenerates to a circle
    w = slot(length=10, width=10)
    assert _is_wire(w)
    vol = _extruded_volume(w, h=1)
    expected = math.pi * 25
    assert _approx(vol, expected, tol=0.5)

def test_slot_bad_dims():
    try:
        slot(5, 10)   # length < width
        assert False, "should raise"
    except ValueError:
        pass


# ── teardrop ─────────────────────────────────────────────────────────────────

def test_teardrop_is_wire():
    assert _is_wire(teardrop(10, 45))

def test_teardrop_positive_area():
    vol = _extruded_volume(teardrop(10, 45), h=1)
    assert vol > 0


# ── arc ───────────────────────────────────────────────────────────────────────

def test_arc_is_wire():
    assert _is_wire(arc(5, 0, 180))

def test_arc_length():
    a = arc(10, 0, 90)
    # Quarter-circle arc: length = 2*pi*10 / 4 = 15.7...
    assert _approx(a.Length, math.pi * 10 / 2, tol=0.1)


# ── polyline ──────────────────────────────────────────────────────────────────

def test_polyline_is_wire():
    assert _is_wire(polyline([(0,0),(10,0),(10,10),(0,10)], closed=True))

def test_polyline_open():
    w = polyline([(0,0),(5,0),(5,5)])
    assert _is_wire(w)

def test_polyline_closed_area():
    w = polyline([(0,0),(10,0),(10,10),(0,10)], closed=True)
    vol = _extruded_volume(w, h=1)
    assert _approx(vol, 100.0, tol=0.1)

def test_polyline_3d_points():
    # XZ-plane rectangle (for revolve use case)
    w = polyline([(5,0,0),(15,0,0),(15,0,10),(5,0,10)], closed=True)
    assert _is_wire(w)
