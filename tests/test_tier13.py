"""Tests for Tier 13 — Architectural."""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import FreeCAD
from partikus.tier13_architectural import (
    wall, door, window, stairs, roof_gable, roof_hip, roof_shed,
    column, beam, slab, truss_simple,
)

def _approx(a, b, tol=1.0):
    return abs(a - b) < tol


# ── wall ──────────────────────────────────────────────────────────────────────

def test_wall_valid():
    assert wall(3000, 2400, 200).shape.isValid()

def test_wall_volume():
    s = wall(3000, 2400, 200)
    assert _approx(s.shape.Volume, 3000 * 2400 * 200, tol=10000)

def test_wall_with_door_opening():
    s = wall(3000, 2400, 200, openings=[
        {"x_offset": 500, "z_offset": 0, "width": 900, "height": 2100}
    ])
    assert s.shape.isValid()
    full_vol = 3000 * 2400 * 200
    assert s.shape.Volume < full_vol

def test_wall_with_window_opening():
    s = wall(3000, 2400, 200, openings=[
        {"x_offset": 1200, "z_offset": 900, "width": 1200, "height": 1200}
    ])
    assert s.shape.isValid()

def test_wall_anchors():
    s = wall(3000, 2400, 200)
    assert s.anchors["TOP"].z > s.anchors["BOTTOM"].z


# ── door ──────────────────────────────────────────────────────────────────────

def test_door_valid():
    assert door(900, 2100, 40).shape.isValid()

def test_door_volume():
    s = door(900, 2100, 40)
    assert _approx(s.shape.Volume, 900 * 2100 * 40, tol=1000)

def test_door_anchors():
    s = door(900, 2100, 40)
    assert s.anchors["TOP"].z > s.anchors["BOTTOM"].z


# ── window ────────────────────────────────────────────────────────────────────

def test_window_valid():
    assert window(1200, 1200, 60, 80).shape.isValid()

def test_window_has_aperture():
    full_vol = 1200 * 80 * 1200
    s = window(1200, 1200, 60, 80)
    assert s.shape.Volume < full_vol

def test_window_volume_positive():
    assert window(1200, 1200, 60, 80).shape.Volume > 0

def test_window_anchors():
    s = window(1200, 1200, 60, 80)
    assert s.anchors["TOP"].z > s.anchors["BOTTOM"].z


# ── stairs ────────────────────────────────────────────────────────────────────

def test_stairs_valid():
    assert stairs(2400, 3600, 12, 900).shape.isValid()

def test_stairs_volume_positive():
    assert stairs(2400, 3600, 12, 900).shape.Volume > 0

def test_stairs_anchors():
    s = stairs(2400, 3600, 12, 900)
    assert s.anchors["TOP"].z > s.anchors["BOTTOM"].z

def test_stairs_bad_count():
    try:
        stairs(2400, 3600, 0, 900)
        assert False, "expected ValueError"
    except ValueError:
        pass

def test_stairs_single_step():
    assert stairs(200, 300, 1, 900).shape.isValid()


# ── roof_gable ────────────────────────────────────────────────────────────────

def test_roof_gable_valid():
    assert roof_gable(6000, 4000, 1500, 300).shape.isValid()

def test_roof_gable_volume_positive():
    assert roof_gable(6000, 4000, 1500, 300).shape.Volume > 0

def test_roof_gable_anchors():
    s = roof_gable(6000, 4000, 1500, 300)
    assert s.anchors["TOP"].z > s.anchors["BOTTOM"].z


# ── roof_hip ──────────────────────────────────────────────────────────────────

def test_roof_hip_valid():
    assert roof_hip(6000, 4000, 1500, 300).shape.isValid()

def test_roof_hip_volume_positive():
    assert roof_hip(6000, 4000, 1500, 300).shape.Volume > 0

def test_roof_hip_anchors():
    s = roof_hip(6000, 4000, 1500, 300)
    assert s.anchors["TOP"].z > s.anchors["BOTTOM"].z


# ── roof_shed ─────────────────────────────────────────────────────────────────

def test_roof_shed_valid():
    assert roof_shed(4000, 3000, 2000, 2800).shape.isValid()

def test_roof_shed_volume_positive():
    assert roof_shed(4000, 3000, 2000, 2800).shape.Volume > 0

def test_roof_shed_anchors():
    s = roof_shed(4000, 3000, 2000, 2800)
    assert s.anchors["TOP"].z > s.anchors["BOTTOM"].z


# ── column ────────────────────────────────────────────────────────────────────

def test_column_valid():
    assert column(300, 3000).shape.isValid()

def test_column_with_base_and_capital():
    assert column(300, 3000, base_size=500, capital_size=450).shape.isValid()

def test_column_volume_positive():
    assert column(300, 3000).shape.Volume > 0

def test_column_with_plinth_has_more_volume():
    plain = column(300, 3000)
    fancy = column(300, 3000, base_size=500, capital_size=450)
    assert fancy.shape.Volume > plain.shape.Volume

def test_column_anchors():
    s = column(300, 3000)
    assert s.anchors["TOP"].z > s.anchors["BOTTOM"].z


# ── beam ──────────────────────────────────────────────────────────────────────

def test_beam_valid():
    assert beam(3000, width=100, height=200).shape.isValid()

def test_beam_volume():
    s = beam(3000, width=100, height=200)
    assert _approx(s.shape.Volume, 3000 * 100 * 200, tol=5000)

def test_beam_anchors():
    s = beam(3000, width=100, height=200)
    assert s.anchors["TOP"].z > s.anchors["BOTTOM"].z


# ── slab ──────────────────────────────────────────────────────────────────────

def test_slab_valid():
    assert slab(6000, 4000, 200).shape.isValid()

def test_slab_volume():
    s = slab(6000, 4000, 200)
    assert _approx(s.shape.Volume, 6000 * 4000 * 200, tol=10000)

def test_slab_anchors():
    s = slab(6000, 4000, 200)
    assert _approx(s.anchors["TOP"].z, 100.0, tol=1.0)
    assert _approx(s.anchors["BOTTOM"].z, -100.0, tol=1.0)


# ── truss_simple ──────────────────────────────────────────────────────────────

def test_truss_valid():
    assert truss_simple(6000, 800, 6, 50, 100).shape.isValid()

def test_truss_volume_positive():
    assert truss_simple(6000, 800, 6, 50, 100).shape.Volume > 0

def test_truss_anchors():
    s = truss_simple(6000, 800, 6, 50, 100)
    assert s.anchors["TOP"].z > s.anchors["BOTTOM"].z

def test_truss_bad_panel_count():
    try:
        truss_simple(6000, 800, 1)
        assert False, "expected ValueError"
    except ValueError:
        pass
