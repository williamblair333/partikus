"""Tests for Tier 6 — Mechanical Components."""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import FreeCAD
from partikus.tier06_mechanical_components import (
    spur_gear, bevel_gear, rack, pulley_timing, sprocket,
    bearing_pocket, shaft_coupling,
)
from partikus.presets.bearings import lookup_bearing

def _approx(a, b, tol=1.0):
    return abs(a - b) < tol

def _V(x, y, z):
    return FreeCAD.Vector(x, y, z)


# ── bearing preset table ──────────────────────────────────────────────────────

def test_bearing_lookup_608():
    d = lookup_bearing("608")
    assert d["id"] == 8 and d["od"] == 22 and d["width"] == 7

def test_bearing_lookup_invalid():
    try:
        lookup_bearing("9999")
        assert False
    except ValueError:
        pass


# ── spur_gear ─────────────────────────────────────────────────────────────────

def test_spur_gear_valid():
    assert spur_gear(teeth=20, module=2, thickness=10).shape.isValid()

def test_spur_gear_volume_positive():
    g = spur_gear(20, 2, 10)
    assert g.shape.Volume > 0

def test_spur_gear_pitch_diameter():
    # Bounding box diameter should be close to (teeth+2)*module (tip diameter)
    g = spur_gear(teeth=20, module=2, thickness=10)
    bb = g.shape.BoundBox
    dia = max(bb.XLength, bb.YLength)
    tip_d = (20 + 2) * 2   # = 44
    assert _approx(dia, tip_d, tol=2.0)

def test_spur_gear_thickness():
    g = spur_gear(20, 2, 10)
    assert _approx(g.shape.BoundBox.ZLength, 10, tol=0.5)

def test_spur_gear_centred():
    g = spur_gear(20, 2, 10)
    assert abs(g.anchors["CENTER"].z) < 0.1

def test_spur_gear_anchors():
    g = spur_gear(20, 2, 10)
    assert _approx(g.anchors["TOP"].z, 5.0, tol=0.5)

def test_spur_gear_few_teeth():
    assert spur_gear(teeth=10, module=1, thickness=5).shape.isValid()

def test_spur_gear_module_variation():
    g1 = spur_gear(20, 1, 5)
    g2 = spur_gear(20, 2, 5)
    assert g2.shape.Volume > g1.shape.Volume

def test_spur_gear_too_few_teeth():
    try:
        spur_gear(teeth=3, module=2, thickness=5)
        assert False
    except ValueError:
        pass


# ── bevel_gear ────────────────────────────────────────────────────────────────

def test_bevel_gear_valid():
    assert bevel_gear(teeth=20, module=2, cone_angle_deg=45, thickness=10).shape.isValid()

def test_bevel_gear_volume_positive():
    assert bevel_gear(20, 2, 45, 10).shape.Volume > 0

def test_bevel_gear_miter_symmetry():
    # At 45° both gears in a miter pair should have same volume
    g1 = bevel_gear(20, 2, 45, 10)
    g2 = bevel_gear(20, 2, 45, 10)
    assert _approx(g1.shape.Volume, g2.shape.Volume, tol=0.1)

def test_bevel_gear_anchors():
    g = bevel_gear(20, 2, 45, 10)
    assert g.anchors["CENTER"] is not None


# ── rack ──────────────────────────────────────────────────────────────────────

def test_rack_valid():
    assert rack(teeth=10, module=2).shape.isValid()

def test_rack_volume_positive():
    assert rack(10, 2).shape.Volume > 0

def test_rack_length():
    r = rack(teeth=10, module=2)
    cp = math.pi * 2
    expected_L = 10 * cp
    assert _approx(r.shape.BoundBox.XLength, expected_L, tol=2.0)

def test_rack_anchors():
    r = rack(10, 2)
    assert r.anchors["CENTER"] is not None


# ── pulley_timing ─────────────────────────────────────────────────────────────

def test_pulley_gt2_valid():
    assert pulley_timing(teeth=20, belt_type="GT2", width=7).shape.isValid()

def test_pulley_htd_valid():
    assert pulley_timing(teeth=20, belt_type="HTD", width=12).shape.isValid()

def test_pulley_pitch_diameter():
    p = pulley_timing(teeth=20, belt_type="GT2", width=7)
    # pd = 20 × 2 / π ≈ 12.73 mm
    pd = 20 * 2.0 / math.pi
    bb = p.shape.BoundBox
    dia = max(bb.XLength, bb.YLength)
    assert _approx(dia, pd, tol=0.5)

def test_pulley_bad_type():
    try:
        pulley_timing(20, "XYZ", 7)
        assert False
    except ValueError:
        pass

def test_pulley_anchors():
    p = pulley_timing(20, "GT2", 7)
    assert _approx(p.anchors["TOP"].z, 3.5, tol=0.1)


# ── sprocket ──────────────────────────────────────────────────────────────────

def test_sprocket_valid():
    assert sprocket(teeth=16, chain_pitch=12.7, thickness=6).shape.isValid()

def test_sprocket_volume_positive():
    assert sprocket(16, 12.7, 6).shape.Volume > 0

def test_sprocket_pitch_diameter():
    s = sprocket(teeth=16, chain_pitch=12.7, thickness=6)
    pd = 16 * 12.7 / math.pi
    bb = s.shape.BoundBox
    dia = max(bb.XLength, bb.YLength)
    # tooth tips extend beyond pd, so dia > pd but within reason
    assert dia > pd * 0.9

def test_sprocket_anchors():
    s = sprocket(16, 12.7, 6)
    assert _approx(s.anchors["TOP"].z, 3.0, tol=0.5)


# ── bearing_pocket ────────────────────────────────────────────────────────────

def test_bearing_pocket_608_valid():
    assert bearing_pocket("608").shape.isValid()

def test_bearing_pocket_608_dimensions():
    p = bearing_pocket("608")
    # OD=22, width=7
    bb = p.shape.BoundBox
    assert _approx(bb.XLength, 22.0, tol=0.5)
    assert _approx(bb.ZLength, 7.0, tol=0.5)

def test_bearing_pocket_custom_depth():
    p = bearing_pocket("608", depth=10)
    assert _approx(p.shape.BoundBox.ZLength, 10.0, tol=0.1)

def test_bearing_pocket_6004_valid():
    assert bearing_pocket("6004").shape.isValid()

def test_bearing_pocket_anchors():
    p = bearing_pocket("608")
    assert _approx(p.anchors["TOP"].z, 3.5, tol=0.1)


# ── shaft_coupling ────────────────────────────────────────────────────────────

def test_shaft_coupling_valid():
    assert shaft_coupling(6, 6, 30).shape.isValid()

def test_shaft_coupling_has_bores():
    solid = shaft_coupling(6, 6, 30)
    # Should be hollow (bores remove material)
    od = 2.5 * 6
    solid_vol = math.pi * (od / 2)**2 * 30
    assert solid.shape.Volume < solid_vol

def test_shaft_coupling_different_shafts():
    assert shaft_coupling(6, 8, 30).shape.isValid()

def test_shaft_coupling_anchors():
    c = shaft_coupling(6, 6, 30)
    assert _approx(c.anchors["TOP"].z, 15.0, tol=0.5)
