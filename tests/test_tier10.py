"""Tests for Tier 10 — Edge & Surface Modifiers."""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import FreeCAD
from partikus.tier01_primitives import box, cylinder, sphere
from partikus.tier10_modifiers import fillet, chamfer, shell, offset

def _approx(a, b, tol=1.0):
    return abs(a - b) < tol


# ── fillet ────────────────────────────────────────────────────────────────────

def test_fillet_reduces_volume():
    b = box(10, 10, 10)
    f = fillet(b, 1)
    assert f.shape.Volume < 1000.0
    assert f.shape.Volume > 900.0

def test_fillet_valid_solid():
    b = box(20, 20, 10)
    f = fillet(b, 2)
    assert f.shape.isValid()

def test_fillet_preserves_center_anchor():
    import FreeCAD
    b = box(10, 10, 10)
    f = fillet(b, 1)
    c = f.anchors["CENTER"]
    assert abs(c.x) < 0.01 and abs(c.y) < 0.01 and abs(c.z) < 0.01

def test_fillet_preserves_top_anchor():
    b = box(10, 10, 10)
    f = fillet(b, 1)
    assert abs(f.anchors["TOP"].z - 5.0) < 0.01

def test_fillet_specific_edges():
    b = box(10, 10, 10)
    # Fillet only the top 4 edges (highest Z edges)
    top_edges = sorted(b.shape.Edges, key=lambda e: e.CenterOfMass.z, reverse=True)[:4]
    f = fillet(b, 1, edges=top_edges)
    assert f.shape.isValid()
    # Less material removed than filleting all 12 edges
    f_all = fillet(b, 1)
    assert f.shape.Volume > f_all.shape.Volume


# ── chamfer ───────────────────────────────────────────────────────────────────

def test_chamfer_reduces_volume():
    b = box(10, 10, 10)
    c = chamfer(b, 1)
    assert c.shape.Volume < 1000.0
    assert c.shape.Volume > 800.0

def test_chamfer_valid_solid():
    b = box(20, 20, 10)
    c = chamfer(b, 1.5)
    assert c.shape.isValid()

def test_chamfer_preserves_anchors():
    b = box(10, 10, 10)
    c = chamfer(b, 1)
    assert abs(c.anchors["TOP"].z - 5.0) < 0.01


# ── shell ─────────────────────────────────────────────────────────────────────

def test_shell_reduces_volume_significantly():
    b = box(20, 20, 20)
    s = shell(b, wall_thickness=2)
    assert s.shape.Volume < 8000.0 * 0.6   # hollow should be < 60% of solid
    assert s.shape.Volume > 0

def test_shell_valid_solid():
    b = box(30, 20, 15)
    s = shell(b, wall_thickness=2)
    assert s.shape.isValid()

def test_shell_default_opens_top():
    b = box(10, 10, 10)
    s = shell(b, wall_thickness=1)
    # The shell should be hollow — volume < original
    assert s.shape.Volume < b.shape.Volume

def test_shell_open_bottom():
    b = box(20, 20, 20)
    s = shell(b, wall_thickness=2, open_faces=["BOTTOM"])
    assert s.shape.isValid()
    assert s.shape.Volume < b.shape.Volume

def test_shell_bad_anchor_raises():
    b = box(10, 10, 10)
    try:
        shell(b, wall_thickness=2, open_faces=["NONEXISTENT"])
        assert False, "should have raised ValueError"
    except ValueError:
        pass


# ── offset ────────────────────────────────────────────────────────────────────

def test_offset_positive_increases_volume():
    b = box(10, 10, 10)
    o = offset(b, 2)
    assert o.shape.Volume > 1000.0

def test_offset_negative_decreases_volume():
    b = box(20, 20, 20)
    o = offset(b, -2)
    assert o.shape.Volume < 8000.0
    assert o.shape.Volume > 0

def test_offset_valid_solid():
    b = box(10, 10, 10)
    o = offset(b, 1)
    assert o.shape.isValid()
