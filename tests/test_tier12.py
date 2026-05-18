"""Tests for Tier 12 — Sweep / Loft Operations."""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import FreeCAD
import Part
from partikus.tier03_profiles_2d import (
    rectangle, circle, regular_polygon, polyline,
)
from partikus.tier12_sweep_loft import extrude, revolve, sweep, loft, pipe

def _approx(a, b, tol=2.0):
    return abs(a - b) < tol

def _V(x, y, z):
    return FreeCAD.Vector(x, y, z)


# ── extrude ───────────────────────────────────────────────────────────────────

def test_extrude_rectangle_volume():
    result = extrude(rectangle(10, 10), height=5)
    assert _approx(result.shape.Volume, 500.0, tol=1.0)

def test_extrude_circle_volume():
    result = extrude(circle(10), height=20)
    expected = math.pi * 25 * 20
    assert _approx(result.shape.Volume, expected, tol=2.0)

def test_extrude_polygon_volume():
    result = extrude(regular_polygon(6, diameter=10), height=15)
    # Hex area: 3*sqrt(3)/2 * R²; R=5
    area = 3 * math.sqrt(3) / 2 * 25
    assert _approx(result.shape.Volume, area * 15, tol=2.0)

def test_extrude_centered():
    result = extrude(rectangle(10, 10), height=10)
    c = result.anchors["CENTER"]
    assert abs(c.x) < 0.1 and abs(c.y) < 0.1 and abs(c.z) < 0.1

def test_extrude_valid():
    result = extrude(circle(15), height=30)
    assert result.shape.isValid()

def test_extrude_anchors():
    result = extrude(rectangle(20, 10), height=8)
    assert abs(result.anchors["TOP"].z - 4.0) < 0.1
    assert abs(result.anchors["BOTTOM"].z + 4.0) < 0.1

def test_extrude_taper_raises():
    try:
        extrude(circle(10), height=10, taper_angle_deg=5)
        assert False, "should raise NotImplementedError"
    except NotImplementedError:
        pass


# ── revolve ───────────────────────────────────────────────────────────────────

def test_revolve_annulus_volume():
    # XZ-plane rectangle (Y=0): x from 5 to 15, z from 0 to 10
    prof = polyline([(5,0,0),(15,0,0),(15,0,10),(5,0,10)], closed=True)
    result = revolve(prof, axis=(0,0,1), angle_deg=360)
    expected = math.pi * (15**2 - 5**2) * 10   # hollow cylinder
    assert _approx(result.shape.Volume, expected, tol=5.0)

def test_revolve_solid_cylinder():
    # Circle at x=0..5, z=0..10 → solid cylinder
    prof = polyline([(0,0,0),(5,0,0),(5,0,10),(0,0,10)], closed=True)
    result = revolve(prof, axis=(0,0,1), angle_deg=360)
    expected = math.pi * 25 * 10
    assert _approx(result.shape.Volume, expected, tol=3.0)

def test_revolve_partial():
    prof = polyline([(5,0,0),(15,0,0),(15,0,10),(5,0,10)], closed=True)
    result = revolve(prof, axis=(0,0,1), angle_deg=180)
    full = revolve(prof, axis=(0,0,1), angle_deg=360)
    assert _approx(result.shape.Volume, full.shape.Volume / 2, tol=5.0)

def test_revolve_valid():
    prof = polyline([(5,0,0),(15,0,0),(15,0,10),(5,0,10)], closed=True)
    result = revolve(prof, axis=(0,0,1))
    assert result.shape.isValid()

def test_revolve_centered():
    prof = polyline([(5,0,0),(15,0,0),(15,0,10),(5,0,10)], closed=True)
    result = revolve(prof, axis=(0,0,1))
    c = result.anchors["CENTER"]
    assert abs(c.x) < 0.5 and abs(c.y) < 0.5 and abs(c.z) < 0.5


# ── sweep ─────────────────────────────────────────────────────────────────────

def test_sweep_straight_pipe():
    path = Part.Wire([Part.LineSegment(_V(0,0,0), _V(0,0,20)).toShape()])
    result = sweep(circle(10), path)
    expected = math.pi * 25 * 20
    assert _approx(result.shape.Volume, expected, tol=3.0)

def test_sweep_rectangle_prism():
    path = Part.Wire([Part.LineSegment(_V(0,0,0), _V(0,0,10)).toShape()])
    result = sweep(rectangle(8, 6), path)
    assert _approx(result.shape.Volume, 480.0, tol=3.0)

def test_sweep_valid():
    path = Part.Wire([Part.LineSegment(_V(0,0,0), _V(0,0,15)).toShape()])
    result = sweep(circle(5), path)
    assert result.shape.isValid()

def test_sweep_centered():
    path = Part.Wire([Part.LineSegment(_V(0,0,0), _V(0,0,20)).toShape()])
    result = sweep(circle(6), path)
    c = result.anchors["CENTER"]
    assert abs(c.z) < 0.5


# ── loft ─────────────────────────────────────────────────────────────────────

def test_loft_two_circles():
    w1 = circle(20)   # at z=0
    m  = FreeCAD.Matrix()
    m.move(_V(0, 0, 30))
    w2 = circle(10).copy()
    w2.transformShape(m)
    result = loft([w1, w2])
    # Volume of cone frustum: pi*h/3*(R²+Rr+r²) with R=10, r=5, h=30
    expected = math.pi * 30 / 3 * (100 + 50 + 25)
    assert _approx(result.shape.Volume, expected, tol=10.0)

def test_loft_two_squares():
    w1 = rectangle(20, 20)
    m  = FreeCAD.Matrix()
    m.move(_V(0, 0, 20))
    w2 = rectangle(10, 10).copy()
    w2.transformShape(m)
    result = loft([w1, w2])
    assert result.shape.Volume > 0
    assert result.shape.isValid()

def test_loft_centered():
    w1 = circle(20)
    m  = FreeCAD.Matrix(); m.move(_V(0,0,20))
    w2 = circle(10).copy(); w2.transformShape(m)
    result = loft([w1, w2])
    c = result.anchors["CENTER"]
    assert abs(c.z) < 0.5


# ── pipe ─────────────────────────────────────────────────────────────────────

def test_pipe_solid():
    path = Part.Wire([Part.LineSegment(_V(0,0,-10), _V(0,0,10)).toShape()])
    result = pipe(path, diameter=10)
    expected = math.pi * 25 * 20
    assert _approx(result.shape.Volume, expected, tol=3.0)

def test_pipe_hollow():
    path = Part.Wire([Part.LineSegment(_V(0,0,-10), _V(0,0,10)).toShape()])
    result = pipe(path, diameter=10, wall_thickness=1)
    solid  = pipe(path, diameter=10, wall_thickness=0)
    assert result.shape.Volume < solid.shape.Volume
    assert result.shape.Volume > 0

def test_pipe_valid():
    path = Part.Wire([Part.LineSegment(_V(0,0,0), _V(0,0,20)).toShape()])
    assert pipe(path, diameter=8).shape.isValid()

def test_pipe_too_thick_raises():
    path = Part.Wire([Part.LineSegment(_V(0,0,0), _V(0,0,10)).toShape()])
    try:
        pipe(path, diameter=10, wall_thickness=6)
        assert False, "should raise"
    except ValueError:
        pass
