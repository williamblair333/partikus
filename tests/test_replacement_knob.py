"""
Tests for examples/replacement_knob.py.

A replacement knob is only useful if it goes on the shaft, stays keyed to it,
and points where the old one did. These tests model the shaft as a solid and
check each of those against the built knob by interference, rather than by
reading dimensions back out of the parameters that produced them.

The default knob is built once and shared; variants are built only where a
test needs a different parameter.
"""
import sys, os, math, importlib.util

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _ROOT)

import FreeCAD


def _load_example():
    """Load the example under a name that suppresses its build-and-export."""
    path = os.path.join(_ROOT, "examples", "replacement_knob.py")
    spec = importlib.util.spec_from_file_location("replacement_knob_under_test", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


kn = _load_example()
_KNOB = kn.build_knob()


def _eq(a, b, tol=0.01):
    return abs(a - b) < tol


def _overlap(part, other):
    """Volume shared by two solids — zero means *other* fits inside the voids."""
    return part.shape.common(other.shape).Volume


def _shaft(height, grow=0.0, flats=kn.SHAFT_FLATS, spin_deg=0.0):
    """The appliance shaft, standing on z=0 — exactly nominal unless *grow*n."""
    from partikus import rotate
    s = kn.d_shaft(kn.SHAFT_DIA + 2 * grow, kn.SHAFT_FLAT + 2 * grow, flats,
                   height, z0=0.0)
    return rotate(s, axis=(0, 0, 1), angle_deg=spin_deg) if spin_deg else s


def _raises(fn, needle, **kw):
    try:
        fn(**kw)
    except ValueError as e:
        assert needle in str(e), f"message should mention {needle!r}: {e}"
        return
    raise AssertionError(f"{kw} should have been refused")


# ── The knob as a part ────────────────────────────────────────────────────

def test_default_knob_is_one_valid_solid():
    kn.verify(_KNOB, "default knob")

def test_knob_stands_on_z0_at_its_nominal_size():
    # optimalBoundingBox, not BoundBox: the fast box pads the filleted and
    # scalloped rim by over 3 mm, which would hide a real size error.
    bb = _KNOB.shape.optimalBoundingBox()
    assert _eq(bb.ZMin, 0.0) and _eq(bb.ZMax, kn.KNOB_HEIGHT)
    assert _eq(bb.XLength, kn.KNOB_DIA, tol=0.05)
    assert _eq(bb.YLength, kn.KNOB_DIA, tol=0.05)


# ── Does it go on the shaft? ──────────────────────────────────────────────

def test_nominal_shaft_slides_in_without_touching():
    # Measured shaft, full engagement depth: must not intersect the knob.
    assert _overlap(_KNOB, _shaft(kn.SHAFT_ENGAGE - 0.05)) < 1e-6

def test_fit_is_snug_not_sloppy():
    # A shaft just past the clearance must collide. If it does not, the bore
    # is oversize and the knob will wobble and let its pointer drift.
    fat = _shaft(kn.SHAFT_ENGAGE - 0.05, grow=kn.FIT_CLEARANCE + 0.05)
    assert _overlap(_KNOB, fat) > 0.01

def test_flat_keys_the_knob_so_it_cannot_spin():
    # The whole job of the D: turned 10 degrees, the shaft must hit the flat.
    assert _overlap(_KNOB, _shaft(kn.SHAFT_ENGAGE - 0.05, spin_deg=10)) > 0.01

def test_bore_stops_at_the_engagement_depth():
    # A blind bore, not a through-hole — the knob's top stays closed.
    assert _overlap(_KNOB, _shaft(kn.SHAFT_ENGAGE + 1.0)) > 0.01

def test_double_d_shaft_fits_and_is_keyed():
    k2 = kn.build_knob(flats=2)
    kn.verify(k2, "double-D knob")
    assert _overlap(k2, _shaft(kn.SHAFT_ENGAGE - 0.05, flats=2)) < 1e-6
    assert _overlap(k2, _shaft(kn.SHAFT_ENGAGE - 0.05, flats=2, spin_deg=10)) > 0.01


# ── Does it point the right way? ──────────────────────────────────────────

def _groove_probe(knob, angle_deg):
    """A point just under the top surface, part-way out, at *angle_deg*
    measured from the flat side (+Y) counter-clockwise."""
    r = kn.KNOB_DIA / 2 - kn.TOP_FILLET - 2.0
    a = math.radians(90 + angle_deg)
    return FreeCAD.Vector(r * math.cos(a), r * math.sin(a),
                          kn.KNOB_HEIGHT - kn.POINTER_DEPTH / 2)

def test_pointer_groove_faces_the_flat_by_default():
    assert not _KNOB.shape.isInside(_groove_probe(_KNOB, 0), 1e-6, True)
    assert _KNOB.shape.isInside(_groove_probe(_KNOB, 180), 1e-6, True)

def test_pointer_follows_pointer_deg():
    k = kn.build_knob(pointer_deg=90)
    assert not k.shape.isInside(_groove_probe(k, 90), 1e-6, True)
    assert k.shape.isInside(_groove_probe(k, 0), 1e-6, True)


# ── Grip and material ─────────────────────────────────────────────────────

def test_grip_flutes_are_cut_into_the_rim():
    step = 360.0 / kn.GRIP_FLUTES
    r = kn.KNOB_DIA / 2 - 0.3
    z = kn.KNOB_HEIGHT / 3
    def at(deg):
        a = math.radians(deg)
        return FreeCAD.Vector(r * math.cos(a), r * math.sin(a), z)
    # Flutes are offset half a step from +Y so none lands under the pointer.
    flute = 90 + step / 2
    assert not _KNOB.shape.isInside(at(flute), 1e-6, True)
    assert _KNOB.shape.isInside(at(flute + step / 2), 1e-6, True)

def test_underside_is_hollow_around_the_boss():
    r = (kn.BOSS_DIA / 2 + (kn.KNOB_DIA / 2 - kn.WALL)) / 2
    assert not _KNOB.shape.isInside(FreeCAD.Vector(r, 0, 1.0), 1e-6, True)
    # ...but the top plate above it is solid.
    assert _KNOB.shape.isInside(
        FreeCAD.Vector(r, 0, kn.KNOB_HEIGHT - kn.TOP_THICK / 2 - 0.5), 1e-6, True)


# ── Printing ──────────────────────────────────────────────────────────────

def test_print_orientation_puts_the_top_on_the_bed():
    p = kn.print_oriented(_KNOB)
    bb = p.shape.BoundBox
    assert _eq(bb.ZMin, 0.0) and _eq(bb.ZMax, kn.KNOB_HEIGHT)
    # Old top is now the solid bottom layer; the bore opens upward.
    assert p.shape.isInside(FreeCAD.Vector(0, -1, 0.5), 1e-6, True)
    assert not p.shape.isInside(FreeCAD.Vector(0, -1, kn.KNOB_HEIGHT - 0.5), 1e-6, True)
    assert _eq(p.shape.Volume, _KNOB.shape.Volume, tol=0.01)

def test_fit_coupon_takes_the_shaft_all_the_way_through():
    c = kn.verify(kn.build_fit_coupon(), "fit coupon")
    h = c.shape.BoundBox.ZLength
    assert h < kn.KNOB_HEIGHT / 2, "the coupon is meant to be a 5-minute print"
    assert _overlap(c, _shaft(h + 5.0)) < 1e-6
    assert _overlap(c, _shaft(h + 5.0, spin_deg=10)) > 0.01


# ── Refusals ──────────────────────────────────────────────────────────────

def test_flat_wider_than_the_shaft_is_refused():
    _raises(kn.build_knob, "SHAFT_FLAT", shaft_flat=kn.SHAFT_DIA + 0.1)

def test_flat_past_the_centre_is_refused():
    # Across-flat measured from the flat to the far side: below half the
    # diameter the "flat" has cut past the axis, which is a misreading.
    _raises(kn.build_knob, "SHAFT_FLAT", shaft_flat=kn.SHAFT_DIA / 2 - 0.1)

def test_double_d_needs_room_for_two_flats():
    _raises(kn.build_knob, "SHAFT_FLAT", flats=2, shaft_flat=0.5)

def test_deep_double_d_is_accepted():
    # Flat to flat on a double-D is symmetric about the axis, so the D rule
    # "the flat must not pass the centre" does not apply. 3 mm across the
    # flats of a 6.35 mm shaft is a real, if thin, shaft.
    k = kn.verify(kn.build_knob(flats=2, shaft_flat=3.0), "deep double-D knob")
    assert _overlap(k, _shaft(kn.SHAFT_ENGAGE - 0.05, flats=2)) > 0.01, \
        "sanity: the default-flat test shaft should not fit a 3 mm double-D bore"

def test_engagement_deeper_than_the_knob_allows_is_refused():
    _raises(kn.build_knob, "SHAFT_ENGAGE", engage=kn.KNOB_HEIGHT)

def test_flutes_deeper_than_the_wall_are_refused():
    _raises(kn.build_knob, "FLUTE_BITE", flute_bite=kn.WALL)

def test_boss_that_fills_the_skirt_is_refused():
    _raises(kn.build_knob, "BOSS_DIA", boss_dia=kn.KNOB_DIA - 2 * kn.WALL)

def test_boss_too_thin_around_the_bore_is_refused():
    _raises(kn.build_knob, "BOSS_DIA", boss_dia=kn.SHAFT_DIA + 0.5)


# ── Guards ────────────────────────────────────────────────────────────────

def test_verify_rejects_an_invalid_or_split_shape():
    from partikus import box, union, translate
    apart = union(box(5, 5, 5), translate(box(5, 5, 5), dx=50))
    try:
        kn.verify(apart, "two islands")
    except ValueError as e:
        assert "solid" in str(e)
        return
    raise AssertionError("verify should reject a multi-solid shape")

def test_importing_the_example_does_not_build_and_export():
    # main() is guarded on __name__ == "replacement_knob", which freecadcmd
    # sets when running the file directly; loading it under another name must
    # not rewrite examples/out/ on every test run.
    assert kn.__name__ == "replacement_knob_under_test"
    assert callable(kn.main)

def test_script_runs_under_its_own_file_name():
    # The README tells people to copy this file (examples/my_knob.py) before
    # editing it. The guard must match whatever the file is called, not the
    # literal "replacement_knob" — otherwise a copy silently does nothing.
    assert kn.SCRIPT_NAME == "replacement_knob"
    assert kn.__name__ != kn.SCRIPT_NAME
    names = kn.output_names()
    assert names == {"knob": "replacement_knob.stl",
                     "coupon": "replacement_knob_fit_coupon.stl",
                     "step": "replacement_knob.step"}
