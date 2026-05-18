"""Tests for Tier 4 — Mechanical Features."""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import FreeCAD
from partikus.tier04_mechanical import (
    boss, counterbore_hole, countersink_hole, slot_hole, keyway,
    rib, gusset, flange, lip, l_bracket, t_bracket, u_bracket,
    tab, slot_cutout, dovetail_pin, dovetail_slot, tongue, groove,
    living_hinge, snap_clip,
)

def _approx(a, b, tol=1.0):
    return abs(a - b) < tol

def _V(x, y, z):
    return FreeCAD.Vector(x, y, z)


# ── boss ──────────────────────────────────────────────────────────────────────

def test_boss_volume():
    b = boss(diameter=10, height=5)
    expected = math.pi * 25 * 5
    assert _approx(b.shape.Volume, expected, tol=2.0)

def test_boss_valid():
    assert boss(10, 5).shape.isValid()

def test_boss_with_hole_less_volume():
    solid = boss(diameter=10, height=5)
    hollow = boss(diameter=10, height=5, hole_diameter=4)
    assert hollow.shape.Volume < solid.shape.Volume
    assert hollow.shape.Volume > 0

def test_boss_anchors():
    b = boss(diameter=10, height=8)
    assert _approx(b.anchors["TOP"].z, 4.0, tol=0.1)
    assert _approx(b.anchors["BOTTOM"].z, -4.0, tol=0.1)


# ── counterbore_hole ──────────────────────────────────────────────────────────

def test_counterbore_hole_volume():
    c = counterbore_hole(thru_diameter=5, bore_diameter=9, bore_depth=4, depth=12)
    bore_vol = math.pi * 4.5**2 * 4
    thru_vol = math.pi * 2.5**2 * 8
    assert _approx(c.shape.Volume, bore_vol + thru_vol, tol=5.0)

def test_counterbore_hole_valid():
    assert counterbore_hole(5, 9, 4, 12).shape.isValid()

def test_counterbore_hole_anchors():
    c = counterbore_hole(5, 9, 4, 12)
    assert _approx(c.anchors["TOP"].z, 6.0, tol=0.1)
    assert _approx(c.anchors["BOTTOM"].z, -6.0, tol=0.1)


# ── countersink_hole ──────────────────────────────────────────────────────────

def test_countersink_hole_valid():
    assert countersink_hole(3.5, 7, 82, 12).shape.isValid()

def test_countersink_hole_volume_positive():
    c = countersink_hole(3, 6, 90, 10)
    assert c.shape.Volume > 0

def test_countersink_hole_larger_than_thru():
    thru = math.pi * 1.5**2 * 10
    c = countersink_hole(3, 6, 90, 10)
    assert c.shape.Volume > thru


# ── slot_hole ─────────────────────────────────────────────────────────────────

def test_slot_hole_volume():
    s = slot_hole(length=20, width=6, depth=5)
    # full circle + rectangle
    expected = math.pi * 9 * 5 + (20 - 6) * 6 * 5
    assert _approx(s.shape.Volume, expected, tol=3.0)

def test_slot_hole_valid():
    assert slot_hole(20, 6, 5).shape.isValid()

def test_slot_hole_equal_length_width():
    # degenerate: length == width → just a cylinder
    s = slot_hole(length=6, width=6, depth=4)
    assert s.shape.isValid()
    assert s.shape.Volume > 0

def test_slot_hole_anchors():
    s = slot_hole(20, 6, 5)
    assert _approx(s.anchors["TOP"].z, 2.5, tol=0.1)


# ── keyway ────────────────────────────────────────────────────────────────────

def test_keyway_volume():
    k = keyway(width=4, depth=2, length=20)
    assert _approx(k.shape.Volume, 4 * 2 * 20, tol=0.1)

def test_keyway_valid():
    assert keyway(4, 2, 20).shape.isValid()

def test_keyway_anchors():
    k = keyway(width=4, depth=2, length=20)
    assert _approx(k.anchors["TOP"].z, 1.0, tol=0.1)


# ── rib ───────────────────────────────────────────────────────────────────────

def test_rib_volume():
    r = rib(length=20, height=15, thickness=3)
    expected = 0.5 * 20 * 15 * 3
    assert _approx(r.shape.Volume, expected, tol=3.0)

def test_rib_valid():
    assert rib(20, 15, 3).shape.isValid()

def test_rib_draft_valid():
    assert rib(20, 15, 3, draft_angle_deg=5).shape.isValid()

def test_rib_anchors():
    r = rib(20, 15, 3)
    assert _approx(r.anchors["TOP"].z, 7.5, tol=0.5)


# ── gusset ────────────────────────────────────────────────────────────────────

def test_gusset_volume():
    g = gusset(length=20, height=20, thickness=4)
    expected = 0.5 * 20 * 20 * 4
    assert _approx(g.shape.Volume, expected, tol=3.0)

def test_gusset_valid():
    assert gusset(20, 20, 4).shape.isValid()


# ── flange ────────────────────────────────────────────────────────────────────

def test_flange_volume():
    f = flange(inner_diameter=20, outer_diameter=40, thickness=5)
    expected = math.pi * (20**2 - 10**2) * 5  # π(R²-r²)h
    assert _approx(f.shape.Volume, expected, tol=5.0)

def test_flange_valid():
    assert flange(20, 40, 5).shape.isValid()

def test_flange_with_holes_valid():
    f = flange(20, 60, 8, hole_pattern=[(6, 22, 4)])
    assert f.shape.isValid()
    assert f.shape.Volume > 0

def test_flange_holes_reduce_volume():
    plain = flange(20, 60, 8)
    holed = flange(20, 60, 8, hole_pattern=[(6, 22, 4)])
    assert holed.shape.Volume < plain.shape.Volume


# ── lip ───────────────────────────────────────────────────────────────────────

def test_lip_valid():
    assert lip(outer_diameter=50, height=20, lip_width=4, lip_height=6).shape.isValid()

def test_lip_more_volume_than_body():
    import math
    body_vol = math.pi * 25**2 * 20
    l = lip(outer_diameter=50, height=20, lip_width=4, lip_height=6)
    assert l.shape.Volume > body_vol

def test_lip_anchors():
    l = lip(outer_diameter=50, height=20, lip_width=4, lip_height=6)
    # total height = 20 + 6 = 26, so top = 13, bottom = -13
    assert _approx(l.anchors["TOP"].z, 13.0, tol=0.5)


# ── l_bracket ─────────────────────────────────────────────────────────────────

def test_l_bracket_valid():
    assert l_bracket(40, 40, 4, 25).shape.isValid()

def test_l_bracket_volume():
    b = l_bracket(length=40, height=40, thickness=4, width=25)
    # Horizontal: 40×25×4, Vertical: 4×25×40, Overlap: 4×25×4
    expected = 40*25*4 + 4*25*40 - 4*25*4
    assert _approx(b.shape.Volume, expected, tol=5.0)

def test_l_bracket_anchors():
    b = l_bracket(40, 40, 4, 25)
    assert b.anchors["TOP"] is not None


# ── t_bracket ─────────────────────────────────────────────────────────────────

def test_t_bracket_valid():
    assert t_bracket(60, 30, 25, 4).shape.isValid()

def test_t_bracket_volume_positive():
    assert t_bracket(60, 30, 25, 4).shape.Volume > 0

def test_t_bracket_anchors():
    b = t_bracket(60, 30, 25, 4)
    assert b.anchors["TOP"] is not None


# ── u_bracket ─────────────────────────────────────────────────────────────────

def test_u_bracket_valid():
    assert u_bracket(50, 20, 25, 3, 15).shape.isValid()

def test_u_bracket_volume():
    b = u_bracket(length=50, height=20, width=25, thickness=3, leg_height=15)
    base_t = 20 - 15  # = 5
    base_vol = 50 * 25 * base_t
    leg_vol = 3 * 25 * 15 * 2
    # Legs share no overlap with base (they sit on top), no internal overlap
    assert _approx(b.shape.Volume, base_vol + leg_vol, tol=5.0)

def test_u_bracket_anchors():
    b = u_bracket(50, 20, 25, 3, 15)
    assert _approx(b.anchors["TOP"].z, 10.0, tol=0.5)


# ── tab ───────────────────────────────────────────────────────────────────────

def test_tab_volume():
    t = tab(width=12, height=6, thickness=2)
    assert _approx(t.shape.Volume, 12 * 6 * 2, tol=0.1)

def test_tab_valid():
    assert tab(12, 6, 2).shape.isValid()


# ── slot_cutout ───────────────────────────────────────────────────────────────

def test_slot_cutout_volume():
    s = slot_cutout(width=15, height=8, depth=4)
    assert _approx(s.shape.Volume, 15 * 8 * 4, tol=0.1)

def test_slot_cutout_valid():
    assert slot_cutout(15, 8, 4).shape.isValid()


# ── dovetail_pin ──────────────────────────────────────────────────────────────

def test_dovetail_pin_valid():
    assert dovetail_pin(25, 6, 10, 5).shape.isValid()

def test_dovetail_pin_volume():
    d = dovetail_pin(length=25, narrow_width=6, wide_width=10, height=5)
    # Trapezoid area = (narrow + wide) / 2 * height
    expected = (6 + 10) / 2 * 5 * 25
    assert _approx(d.shape.Volume, expected, tol=3.0)

def test_dovetail_pin_anchors():
    d = dovetail_pin(25, 6, 10, 5)
    assert _approx(d.anchors["TOP"].z, 2.5, tol=0.1)


# ── dovetail_slot ─────────────────────────────────────────────────────────────

def test_dovetail_slot_same_as_pin():
    pin = dovetail_pin(25, 6, 10, 5)
    slot = dovetail_slot(25, 6, 10, 5)
    assert _approx(pin.shape.Volume, slot.shape.Volume, tol=0.1)

def test_dovetail_slot_valid():
    assert dovetail_slot(25, 6, 10, 5).shape.isValid()


# ── tongue ────────────────────────────────────────────────────────────────────

def test_tongue_volume():
    t = tongue(length=20, width=8, height=4)
    assert _approx(t.shape.Volume, 20 * 8 * 4, tol=0.1)

def test_tongue_valid():
    assert tongue(20, 8, 4).shape.isValid()


# ── groove ────────────────────────────────────────────────────────────────────

def test_groove_volume():
    g = groove(length=20, width=8, depth=4)
    assert _approx(g.shape.Volume, 20 * 8 * 4, tol=0.1)

def test_groove_valid():
    assert groove(20, 8, 4).shape.isValid()


# ── living_hinge ──────────────────────────────────────────────────────────────

def test_living_hinge_volume():
    h = living_hinge(length=30, thickness=0.6, hinge_width=15)
    assert _approx(h.shape.Volume, 30 * 0.6 * 15, tol=0.5)

def test_living_hinge_valid():
    assert living_hinge(30, 0.6, 15).shape.isValid()

def test_living_hinge_thin():
    h = living_hinge(40, 0.4, 10)
    assert h.shape.isValid()
    assert h.shape.Volume > 0


# ── snap_clip ─────────────────────────────────────────────────────────────────

def test_snap_clip_valid():
    assert snap_clip(20, 5, 2, 12).shape.isValid()

def test_snap_clip_volume_positive():
    assert snap_clip(20, 5, 2, 12).shape.Volume > 0

def test_snap_clip_anchors():
    s = snap_clip(20, 5, 2, 12)
    assert s.anchors["CENTER"] is not None
