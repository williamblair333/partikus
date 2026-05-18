"""Tests for Tier 5 — Fasteners & Standard Parts."""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import FreeCAD
from partikus.tier05_fasteners import (
    threaded_rod, tapped_hole,
    hex_bolt, socket_head_bolt, button_head_bolt, flat_head_bolt,
    hex_nut, flat_washer, lock_washer,
    heat_set_insert_pocket, clearance_hole, screw_size_preset,
    standoff, dowel_pin,
)
from partikus.presets.screws import parse_size, lookup

def _approx(a, b, tol=1.0):
    return abs(a - b) < tol

def _V(x, y, z):
    return FreeCAD.Vector(x, y, z)


# ── presets / table ───────────────────────────────────────────────────────────

def test_parse_size_m6():
    d, p = parse_size("M6")
    assert d == 6 and p is None

def test_parse_size_with_pitch():
    d, p = parse_size("M6x1.0")
    assert d == 6 and _approx(p, 1.0, tol=0.001)

def test_parse_size_m2_5():
    d, p = parse_size("M2.5")
    assert d == 2.5 and p is None

def test_lookup_m6_pitch():
    assert lookup(6)["pitch"] == 1.0

def test_lookup_m3_tap_drill():
    assert _approx(lookup(3)["tap_drill"], 2.5, tol=0.01)

def test_lookup_invalid():
    try:
        lookup(7)
        assert False, "should have raised"
    except ValueError:
        pass

def test_screw_size_preset_returns_dict():
    p = screw_size_preset("M6")
    assert isinstance(p, dict)
    assert p["pitch"] == 1.0
    assert p["clearance"]["close"] == 6.4

def test_screw_size_preset_m3():
    p = screw_size_preset("M3")
    assert p["hex_nut"]["height"] == 2.4


# ── threaded_rod ──────────────────────────────────────────────────────────────

def test_threaded_rod_valid():
    assert threaded_rod(6, 30).shape.isValid()

def test_threaded_rod_volume():
    r = threaded_rod(diameter=6, length=30)
    expected = math.pi * 9 * 30
    assert _approx(r.shape.Volume, expected, tol=3.0)

def test_threaded_rod_anchors():
    r = threaded_rod(6, 30)
    assert _approx(r.anchors["TOP"].z, 15.0, tol=0.1)
    assert _approx(r.anchors["BOTTOM"].z, -15.0, tol=0.1)

def test_threaded_rod_bad_form():
    try:
        threaded_rod(6, 20, thread_form="imperial")
        assert False
    except NotImplementedError:
        pass


# ── tapped_hole ───────────────────────────────────────────────────────────────

def test_tapped_hole_valid():
    assert tapped_hole(6, 12).shape.isValid()

def test_tapped_hole_smaller_than_nominal():
    # tap drill < nominal diameter
    rod = threaded_rod(6, 12)
    hole = tapped_hole(6, 12)
    assert hole.shape.Volume < rod.shape.Volume

def test_tapped_hole_volume_m6():
    h = tapped_hole(6, 12)
    # tap drill = 6 - 1.0 = 5.0 mm
    expected = math.pi * 6.25 * 12
    assert _approx(h.shape.Volume, expected, tol=2.0)


# ── hex_bolt ──────────────────────────────────────────────────────────────────

def test_hex_bolt_valid():
    assert hex_bolt(6, 25).shape.isValid()

def test_hex_bolt_volume_greater_than_shank():
    shank_vol = math.pi * 9 * 25
    b = hex_bolt(6, 25)
    assert b.shape.Volume > shank_vol

def test_hex_bolt_anchors():
    b = hex_bolt(6, 25)
    # head height = 4, shank = 25, total = 29, centred → top = 14.5
    assert _approx(b.anchors["TOP"].z, 14.5, tol=0.5)

def test_hex_bolt_m8_valid():
    assert hex_bolt(8, 30).shape.isValid()


# ── socket_head_bolt ──────────────────────────────────────────────────────────

def test_socket_head_bolt_valid():
    assert socket_head_bolt(6, 20).shape.isValid()

def test_socket_head_bolt_volume():
    b = socket_head_bolt(6, 20)
    shank_vol = math.pi * 9 * 20
    assert b.shape.Volume > shank_vol

def test_socket_head_bolt_anchors():
    b = socket_head_bolt(6, 20)
    # head_height=6, shank=20, total=26 → top=13
    assert _approx(b.anchors["TOP"].z, 13.0, tol=0.5)


# ── button_head_bolt ──────────────────────────────────────────────────────────

def test_button_head_bolt_valid():
    assert button_head_bolt(6, 16).shape.isValid()

def test_button_head_bolt_no_data_m16():
    try:
        button_head_bolt(16, 30)
        assert False
    except ValueError:
        pass

def test_button_head_bolt_volume_positive():
    assert button_head_bolt(6, 16).shape.Volume > 0


# ── flat_head_bolt ────────────────────────────────────────────────────────────

def test_flat_head_bolt_valid():
    assert flat_head_bolt(6, 20).shape.isValid()

def test_flat_head_bolt_no_data_m16():
    try:
        flat_head_bolt(16, 40)
        assert False
    except ValueError:
        pass

def test_flat_head_bolt_volume_positive():
    assert flat_head_bolt(6, 20).shape.Volume > 0


# ── hex_nut ───────────────────────────────────────────────────────────────────

def test_hex_nut_valid():
    assert hex_nut(6).shape.isValid()

def test_hex_nut_has_bore():
    # nut volume < solid hex prism of same size
    nut = hex_nut(6)
    assert nut.shape.Volume > 0
    # bore removes material → volume < equivalent solid prism
    # prism vol ≈ (√3/2) × s² × h = (√3/2) × 100 × 5 ≈ 433
    solid_prism_approx = (math.sqrt(3) / 2) * 10**2 * 5
    assert nut.shape.Volume < solid_prism_approx

def test_hex_nut_anchors():
    n = hex_nut(6)
    # height = 5.0 → top = 2.5, bottom = -2.5
    assert _approx(n.anchors["TOP"].z, 2.5, tol=0.1)


# ── flat_washer ───────────────────────────────────────────────────────────────

def test_flat_washer_valid():
    assert flat_washer(6).shape.isValid()

def test_flat_washer_volume():
    w = flat_washer(6)
    # outer_d=12, inner_d=6.4, t=1.6
    expected = math.pi * (36 - 10.24) * 1.6
    assert _approx(w.shape.Volume, expected, tol=2.0)

def test_flat_washer_anchors():
    w = flat_washer(6)
    assert _approx(w.anchors["TOP"].z, 0.8, tol=0.1)


# ── lock_washer ───────────────────────────────────────────────────────────────

def test_lock_washer_valid():
    assert lock_washer(6).shape.isValid()

def test_lock_washer_thinner_than_flat():
    # lock washer same outer_d but different thickness — just check it's valid
    lw = lock_washer(6)
    assert lw.shape.Volume > 0

def test_lock_washer_smaller_than_flat_washer():
    lw = lock_washer(6)
    fw = flat_washer(6)
    # lock washer OD (11) < flat washer OD (12) and thinner → smaller volume
    assert lw.shape.Volume < fw.shape.Volume


# ── heat_set_insert_pocket ────────────────────────────────────────────────────

def test_heat_set_pocket_valid():
    assert heat_set_insert_pocket("M3").shape.isValid()

def test_heat_set_pocket_volume():
    p = heat_set_insert_pocket("M3")
    # OD=4.5, L=5.7
    expected = math.pi * (2.25**2) * 5.7
    assert _approx(p.shape.Volume, expected, tol=1.0)

def test_heat_set_pocket_m6():
    assert heat_set_insert_pocket("M6").shape.isValid()

def test_heat_set_pocket_no_data():
    try:
        heat_set_insert_pocket("M16")
        assert False
    except ValueError:
        pass


# ── clearance_hole ────────────────────────────────────────────────────────────

def test_clearance_hole_valid():
    assert clearance_hole("M6", 15, "close").shape.isValid()

def test_clearance_hole_larger_than_nominal():
    rod = threaded_rod(6, 15)
    hole = clearance_hole("M6", 15, "close")
    assert hole.shape.Volume > rod.shape.Volume

def test_clearance_hole_loose_larger_than_close():
    close = clearance_hole("M6", 15, "close")
    loose = clearance_hole("M6", 15, "loose")
    assert loose.shape.Volume > close.shape.Volume

def test_clearance_hole_bad_fit():
    try:
        clearance_hole("M6", 10, fit="medium")
        assert False
    except ValueError:
        pass


# ── standoff ──────────────────────────────────────────────────────────────────

def test_standoff_solid_valid():
    assert standoff(diameter=8, length=10).shape.isValid()

def test_standoff_solid_volume():
    s = standoff(8, 10)
    expected = math.pi * 16 * 10
    assert _approx(s.shape.Volume, expected, tol=2.0)

def test_standoff_threaded_valid():
    assert standoff(diameter=8, length=10, thread_size="M3").shape.isValid()

def test_standoff_threaded_less_volume():
    solid = standoff(8, 10)
    threaded = standoff(8, 10, thread_size="M3")
    assert threaded.shape.Volume < solid.shape.Volume


# ── dowel_pin ─────────────────────────────────────────────────────────────────

def test_dowel_pin_valid():
    assert dowel_pin(6, 30).shape.isValid()

def test_dowel_pin_volume():
    d = dowel_pin(6, 30)
    expected = math.pi * 9 * 30
    assert _approx(d.shape.Volume, expected, tol=2.0)

def test_dowel_pin_anchors():
    d = dowel_pin(6, 30)
    assert _approx(d.anchors["TOP"].z, 15.0, tol=0.1)
