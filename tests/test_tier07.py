"""Tests for Tier 7 — Container / Enclosure Features."""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import FreeCAD
from partikus.tier07_enclosures import (
    lid, snap_fit_box, hinged_box, magnetic_recess, battery_compartment,
    cable_channel, strain_relief, vent_slots, display_window, button_cutout,
)

def _approx(a, b, tol=1.0):
    return abs(a - b) < tol


# ── lid ───────────────────────────────────────────────────────────────────────

def test_lid_valid():
    assert lid(60, 40, 5, 1, 2).shape.isValid()

def test_lid_volume_positive():
    assert lid(60, 40, 5, 1, 2).shape.Volume > 0

def test_lid_anchors():
    s = lid(60, 40, 5, 1, 2)
    assert s.anchors["TOP"].z > s.anchors["BOTTOM"].z

def test_lid_dimensions():
    s = lid(length=80, width=50, rim_height=6, rim_inset=1.5, wall_thickness=2)
    bb = s.shape.BoundBox
    assert _approx(bb.XLength, 80, tol=1.0)
    assert _approx(bb.YLength, 50, tol=1.0)


# ── snap_fit_box ──────────────────────────────────────────────────────────────

def test_snap_fit_box_valid():
    assert snap_fit_box(80, 50, 30, 2, 4).shape.isValid()

def test_snap_fit_box_volume_positive():
    assert snap_fit_box(80, 50, 30, 2, 4).shape.Volume > 0

def test_snap_fit_box_anchors():
    s = snap_fit_box(80, 50, 30, 2, 4)
    assert s.anchors["TOP"].z > s.anchors["BOTTOM"].z

def test_snap_fit_box_min_snaps():
    s = snap_fit_box(60, 40, 25, 2, snap_count=1)
    assert s.shape.isValid()


# ── hinged_box ────────────────────────────────────────────────────────────────

def test_hinged_box_valid():
    assert hinged_box(80, 50, 40, 2, "BACK").shape.isValid()

def test_hinged_box_volume_positive():
    assert hinged_box(80, 50, 40, 2).shape.Volume > 0

def test_hinged_box_sides():
    for side in ("FRONT", "BACK", "LEFT", "RIGHT"):
        assert hinged_box(60, 40, 30, 2, hinge_side=side).shape.isValid()

def test_hinged_box_anchors():
    s = hinged_box(80, 50, 40, 2)
    assert s.anchors["TOP"].z > s.anchors["BOTTOM"].z


# ── magnetic_recess ───────────────────────────────────────────────────────────

def test_magnetic_recess_single_valid():
    assert magnetic_recess(6, 2, 1).shape.isValid()

def test_magnetic_recess_volume():
    s = magnetic_recess(magnet_diameter=6, magnet_thickness=2, count=1)
    expected = math.pi * 3**2 * 2
    assert _approx(s.shape.Volume, expected, tol=1.0)

def test_magnetic_recess_multi_valid():
    assert magnetic_recess(6, 2, count=3, spacing=10).shape.isValid()

def test_magnetic_recess_multi_volume():
    single = magnetic_recess(6, 2, count=1)
    triple = magnetic_recess(6, 2, count=3, spacing=10)
    assert _approx(triple.shape.Volume, single.shape.Volume * 3, tol=2.0)


# ── battery_compartment ───────────────────────────────────────────────────────

def test_battery_aa_valid():
    assert battery_compartment("AA", count=1).shape.isValid()

def test_battery_aa_volume_positive():
    assert battery_compartment("AA", count=1).shape.Volume > 0

def test_battery_multi_valid():
    assert battery_compartment("AA", count=2).shape.isValid()

def test_battery_18650_valid():
    assert battery_compartment("18650", count=1).shape.isValid()

def test_battery_cr2032_valid():
    assert battery_compartment("CR2032", count=1).shape.isValid()

def test_battery_bad_type():
    try:
        battery_compartment("D-cell-XL")
        assert False, "expected ValueError"
    except ValueError:
        pass


# ── cable_channel ─────────────────────────────────────────────────────────────

def test_cable_channel_valid():
    assert cable_channel(8, 5, 60, 1.5).shape.isValid()

def test_cable_channel_volume_positive():
    assert cable_channel(8, 5, 60, 1.5).shape.Volume > 0

def test_cable_channel_anchors():
    s = cable_channel(8, 5, 60)
    assert s.anchors["TOP"].z > s.anchors["BOTTOM"].z


# ── strain_relief ─────────────────────────────────────────────────────────────

def test_strain_relief_valid():
    assert strain_relief(4, 12, 2).shape.isValid()

def test_strain_relief_volume_positive():
    assert strain_relief(4, 12, 2).shape.Volume > 0

def test_strain_relief_bore_removes_material():
    solid = strain_relief(4, 12, 2, clamp_gap=0.001)
    outer_vol = math.pi * (2 + 2)**2 * 12
    assert solid.shape.Volume < outer_vol


# ── vent_slots ────────────────────────────────────────────────────────────────

def test_vent_slots_valid():
    assert vent_slots(60, 30, 5, 2, 2).shape.isValid()

def test_vent_slots_less_volume_than_panel():
    import Part, FreeCAD
    panel_vol = 60 * 30 * 2
    s = vent_slots(60, 30, 5, 2, 2)
    assert s.shape.Volume < panel_vol

def test_vent_slots_volume_positive():
    assert vent_slots(60, 30, 5, 2, 2).shape.Volume > 0

def test_vent_slots_anchors():
    s = vent_slots(60, 30, 5, 2, 2)
    assert s.anchors["TOP"].z > s.anchors["BOTTOM"].z


# ── display_window ────────────────────────────────────────────────────────────

def test_display_window_valid():
    assert display_window(50, 30, 0, 3, 2).shape.isValid()

def test_display_window_volume_positive():
    assert display_window(50, 30, 0, 3, 2).shape.Volume > 0

def test_display_window_has_aperture():
    full_vol = 50 * 30 * 2
    s = display_window(50, 30, 0, 3, 2)
    assert s.shape.Volume < full_vol

def test_display_window_recess_valid():
    assert display_window(50, 30, recess_depth=1.0, border_thickness=3, panel_thickness=2).shape.isValid()

def test_display_window_bad_border():
    try:
        display_window(20, 15, border_thickness=15)
        assert False, "expected ValueError"
    except ValueError:
        pass


# ── button_cutout ─────────────────────────────────────────────────────────────

def test_button_cutout_round_valid():
    assert button_cutout(12, 2, "round").shape.isValid()

def test_button_cutout_square_valid():
    assert button_cutout(12, 2, "square").shape.isValid()

def test_button_cutout_round_volume():
    s = button_cutout(diameter=12, panel_thickness=2, shape="round")
    expected = math.pi * 6**2 * 2
    assert _approx(s.shape.Volume, expected, tol=1.0)

def test_button_cutout_square_volume():
    s = button_cutout(diameter=10, panel_thickness=3, shape="square")
    assert _approx(s.shape.Volume, 10 * 10 * 3, tol=1.0)

def test_button_cutout_bad_shape():
    try:
        button_cutout(12, 2, "triangle")
        assert False, "expected ValueError"
    except ValueError:
        pass
