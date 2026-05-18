"""Tests for Tier 8 — Electronics Mounting."""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import FreeCAD
from partikus.tier08_electronics import (
    pcb_standoff, raspberry_pi_mount, arduino_mount, led_holder,
    usb_cutout, hdmi_cutout, barrel_jack_cutout, din_rail_clip,
    heatsink_fin_array,
)

def _approx(a, b, tol=1.0):
    return abs(a - b) < tol


# ── pcb_standoff ──────────────────────────────────────────────────────────────

def test_pcb_standoff_valid():
    assert pcb_standoff(8, 3.2, 6).shape.isValid()

def test_pcb_standoff_volume():
    s = pcb_standoff(height=10, hole_diameter=3.2, base_diameter=6)
    outer_vol = math.pi * 3**2 * 10
    assert s.shape.Volume < outer_vol
    assert s.shape.Volume > 0

def test_pcb_standoff_anchors():
    s = pcb_standoff(8, 3.2, 6)
    assert _approx(s.anchors["TOP"].z, 4.0, tol=0.2)
    assert _approx(s.anchors["BOTTOM"].z, -4.0, tol=0.2)

def test_pcb_standoff_bad_dims():
    try:
        pcb_standoff(hole_diameter=10, base_diameter=8)
        assert False, "expected ValueError"
    except ValueError:
        pass


# ── raspberry_pi_mount ────────────────────────────────────────────────────────

def test_rpi_4b_valid():
    assert raspberry_pi_mount("4B").shape.isValid()

def test_rpi_zero_valid():
    assert raspberry_pi_mount("Zero").shape.isValid()

def test_rpi_volume_positive():
    assert raspberry_pi_mount("4B").shape.Volume > 0

def test_rpi_bad_model():
    try:
        raspberry_pi_mount("99B")
        assert False, "expected ValueError"
    except ValueError:
        pass

def test_rpi_anchors():
    s = raspberry_pi_mount("4B", standoff_height=8)
    assert s.anchors["TOP"].z > s.anchors["BOTTOM"].z


# ── arduino_mount ─────────────────────────────────────────────────────────────

def test_arduino_uno_valid():
    assert arduino_mount("uno").shape.isValid()

def test_arduino_mega_valid():
    assert arduino_mount("mega").shape.isValid()

def test_arduino_nano_valid():
    assert arduino_mount("nano").shape.isValid()

def test_arduino_volume_positive():
    assert arduino_mount("uno").shape.Volume > 0

def test_arduino_bad_model():
    try:
        arduino_mount("pico")
        assert False, "expected ValueError"
    except ValueError:
        pass


# ── led_holder ────────────────────────────────────────────────────────────────

def test_led_holder_5mm_valid():
    assert led_holder(5.0, 3.0).shape.isValid()

def test_led_holder_3mm_valid():
    assert led_holder(3.0, 2.0).shape.isValid()

def test_led_holder_10mm_valid():
    assert led_holder(10.0, 3.0).shape.isValid()

def test_led_holder_volume_positive():
    assert led_holder(5.0, 3.0).shape.Volume > 0

def test_led_holder_bore_reduces_volume():
    import Part
    outer_vol = math.pi * (5.0 / 2 + 1.5)**2 * 3.0
    s = led_holder(5.0, 3.0, retention_lip=0)
    assert s.shape.Volume < outer_vol


# ── usb_cutout ────────────────────────────────────────────────────────────────

def test_usb_c_valid():
    assert usb_cutout("USB-C", 2).shape.isValid()

def test_usb_a_valid():
    assert usb_cutout("USB-A", 3).shape.isValid()

def test_usb_micro_valid():
    assert usb_cutout("Micro-USB", 2).shape.isValid()

def test_usb_volume_positive():
    assert usb_cutout("USB-C", 2).shape.Volume > 0

def test_usb_bad_type():
    try:
        usb_cutout("USB-D")
        assert False, "expected ValueError"
    except ValueError:
        pass


# ── hdmi_cutout ───────────────────────────────────────────────────────────────

def test_hdmi_full_valid():
    assert hdmi_cutout("full", 2).shape.isValid()

def test_hdmi_micro_valid():
    assert hdmi_cutout("micro", 2).shape.isValid()

def test_hdmi_volume_positive():
    assert hdmi_cutout("full", 2).shape.Volume > 0

def test_hdmi_bad_type():
    try:
        hdmi_cutout("nano")
        assert False, "expected ValueError"
    except ValueError:
        pass


# ── barrel_jack_cutout ────────────────────────────────────────────────────────

def test_barrel_jack_valid():
    assert barrel_jack_cutout(8.0, 3.0).shape.isValid()

def test_barrel_jack_volume():
    s = barrel_jack_cutout(outer_diameter=8.0, panel_thickness=3.0, clearance=0)
    expected = math.pi * 4.0**2 * 3.0 * 1.02
    assert _approx(s.shape.Volume, expected, tol=2.0)

def test_barrel_jack_anchors():
    s = barrel_jack_cutout(8.0, 3.0)
    assert s.anchors["TOP"].z > s.anchors["BOTTOM"].z


# ── din_rail_clip ─────────────────────────────────────────────────────────────

def test_din_35mm_valid():
    assert din_rail_clip("35mm", 40).shape.isValid()

def test_din_15mm_valid():
    assert din_rail_clip("15mm", 40).shape.isValid()

def test_din_volume_positive():
    assert din_rail_clip("35mm", 40).shape.Volume > 0

def test_din_bad_type():
    try:
        din_rail_clip("50mm")
        assert False, "expected ValueError"
    except ValueError:
        pass

def test_din_anchors():
    s = din_rail_clip("35mm", 40)
    assert s.anchors["TOP"].z > s.anchors["BOTTOM"].z


# ── heatsink_fin_array ────────────────────────────────────────────────────────

def test_heatsink_valid():
    assert heatsink_fin_array(40, 40, 8, 15, 1.5, 3).shape.isValid()

def test_heatsink_volume_positive():
    assert heatsink_fin_array(40, 40, 8, 15, 1.5, 3).shape.Volume > 0

def test_heatsink_more_fins_more_volume():
    s4 = heatsink_fin_array(60, 40, 4, 15, 1.5, 3)
    s8 = heatsink_fin_array(60, 40, 8, 15, 1.5, 3)
    assert s8.shape.Volume > s4.shape.Volume

def test_heatsink_bad_fin_count():
    try:
        heatsink_fin_array(40, 40, 0, 15, 1.5, 3)
        assert False, "expected ValueError"
    except ValueError:
        pass

def test_heatsink_anchors():
    s = heatsink_fin_array(40, 40, 8, 15, 1.5, 3)
    assert s.anchors["TOP"].z > s.anchors["BOTTOM"].z
