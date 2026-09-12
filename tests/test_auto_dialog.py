"""
Tests for the auto-generated dialog's parameter → widget → value round-trip.

These exist because of a defect class the rest of the suite cannot see: the
dialog is the only caller that invents argument values, and every test in this
project calls the geometry functions directly with good ones. A parameter that
the dialog mistranslates therefore passes 758 tests and fails the moment a user
clicks OK.

Two mistranslations have shipped so far, both the same shape — a value the
dialog could not express became 0.0:

    str parameters    open_face="TOP"  ->  0.0   (fixed 2026-09-12)
    None parameters   radius=None      ->  0.0   (fixed 2026-09-12)

The second was the worse of the two. Functions branch on `if x is not None`, so
0.0 does not approximate "unset", it selects the other branch: cone and rack
crashed, standoff raised "No ISO data for M0", and cylinder, sphere, torus,
disk, hemisphere and bearing_pocket returned invalid zero-volume solids with no
error anywhere.

Requires Qt, which imports fine under freecadcmd with an offscreen platform.
When it is unavailable these skip rather than fail — the geometry suite should
not go red on a headless box with no Qt.
"""
import inspect
import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _ROOT)

try:
    from PySide import QtWidgets
    _app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
    from partikus.gui import auto_dialog as ad
    _HAS_QT = ad.HAS_GUI
except Exception:                                # pragma: no cover
    _HAS_QT = False

import partikus


def _values_for(fn):
    """
    What the dialog would pass to *fn* with nothing touched.

    The QDialog must stay referenced until get_values() has run: it owns the
    Qt widgets, and letting it fall out of scope destroys the C++ objects the
    closure still reads ("Internal C++ object already deleted").
    """
    dlg = ad._build_dialog(fn)
    vals = dlg.get_values()
    del dlg
    return vals


# ── The None → 0.0 regression ────────────────────────────────────────────────

def test_none_defaults_round_trip_as_none():
    if not _HAS_QT:
        return
    # cone's base_radius/top_radius override base_diameter/top_diameter when
    # given. As 0.0 they override them with nothing and OCC refuses to build.
    vals = _values_for(partikus.cone)
    assert vals["base_radius"] is None, f"base_radius came back as {vals['base_radius']!r}"
    assert vals["top_radius"] is None, f"top_radius came back as {vals['top_radius']!r}"
    assert vals["base_diameter"] == 20.0


def test_every_none_default_in_the_api_round_trips_as_none():
    if not _HAS_QT:
        return
    offenders = []
    for name in sorted(getattr(partikus, "__all__", [])):
        fn = getattr(partikus, name, None)
        if not callable(fn) or inspect.isclass(fn):
            continue
        try:
            sig = inspect.signature(fn)
        except (TypeError, ValueError):
            continue
        optional = [p for p, v in sig.parameters.items() if v.default is None]
        if not optional:
            continue
        try:
            vals = _values_for(fn)
        except Exception:
            continue
        for p in optional:
            if p in vals and vals[p] is not None:
                offenders.append(f"{name}.{p} -> {vals[p]!r}")
    assert not offenders, "optional parameters not passed as None: " + ", ".join(offenders)


# ── The functions that actually broke ────────────────────────────────────────

def _builds(fn):
    shape = fn(**_values_for(fn))
    raw = getattr(shape, "shape", shape)
    return raw


def test_dialog_defaults_build_the_primitives():
    if not _HAS_QT:
        return
    # Every one of these returned an invalid zero-volume solid, or crashed,
    # when its optional parameter arrived as 0.0.
    for name in ("cone", "cylinder", "sphere", "torus", "disk", "hemisphere",
                 "boss", "rack", "bearing_pocket", "standoff", "flange",
                 "rounded_box", "chamfered_box"):
        fn = getattr(partikus, name, None)
        if fn is None:
            continue
        raw = _builds(fn)
        assert raw.isValid(), f"{name}: dialog defaults produce an invalid shape"
        assert raw.Volume > 1e-6, f"{name}: dialog defaults produce zero volume"


def test_dialog_defaults_match_calling_the_function_directly():
    if not _HAS_QT:
        return
    # The dialog with nothing touched must mean the same thing as fn().
    for name in ("cone", "cylinder", "sphere", "torus", "hemisphere", "boss",
                 "bearing_pocket", "rack"):
        fn = getattr(partikus, name, None)
        if fn is None:
            continue
        direct = getattr(fn(), "shape", None)
        via_dialog = _builds(fn)
        assert abs(direct.Volume - via_dialog.Volume) < 1e-6, (
            f"{name}: dialog defaults give volume {via_dialog.Volume:.3f}, "
            f"calling it directly gives {direct.Volume:.3f}")


# ── The sentinel itself ──────────────────────────────────────────────────────

def test_auto_sentinel_is_below_any_real_dimension():
    if not _HAS_QT:
        return
    # If this ever moves into the usable range, a value a user typed is read as
    # "unset" and silently replaced by the function's own default.
    assert ad._AUTO <= -1000.0, "the auto sentinel must not be a plausible dimension"


def test_a_typed_value_is_not_mistaken_for_auto():
    if not _HAS_QT:
        return
    dlg = ad._build_dialog(partikus.cone)
    # Simulate the user typing into the optional field.
    for row in range(dlg.layout().itemAt(0).layout().rowCount()):
        pass
    vals_before = dlg.get_values()
    assert vals_before["base_radius"] is None
    # Reach the widget the same way get_values does, and set a real number.
    widget = None
    for w in dlg.findChildren(QtWidgets.QDoubleSpinBox):
        if w.property("partikus_optional") and w.value() == w.minimum():
            widget = w
            break
    assert widget is not None, "no optional spin box found on the cone dialog"
    widget.setValue(7.5)
    assert 7.5 in dlg.get_values().values(), "a typed value was swallowed as auto"


# ── str parameters, the earlier regression of the same class ─────────────────

def test_string_defaults_are_not_floats():
    if not _HAS_QT:
        return
    vals = _values_for(partikus.hollow_box)
    assert vals["open_face"] == "TOP", f"open_face came back as {vals['open_face']!r}"


# ── Degenerate-shape warning ─────────────────────────────────────────────────

def test_degenerate_shape_is_reported_not_silent():
    # The whole point: an empty solid must not enter a document quietly.
    import FreeCAD
    from partikus.core.serialise import _warn_if_degenerate
    import Part

    seen = []
    original = FreeCAD.Console.PrintWarning
    try:
        FreeCAD.Console.PrintWarning = lambda m: seen.append(m)
        _warn_if_degenerate("probe", Part.Shape())          # empty compound
        _warn_if_degenerate("good", partikus.box(10, 10, 10).shape)
    finally:
        FreeCAD.Console.PrintWarning = original

    assert len(seen) == 1, f"expected exactly one warning, got {len(seen)}: {seen}"
    assert "probe" in seen[0]


# ── Literal annotations ──────────────────────────────────────────────────────
#
# A Literal[...] on a constrained string parameter is what turns a free-text box
# into a validated dropdown — the dialog already had that branch, the signatures
# just never used it. Several of these duplicate a preset table's keys, which is
# unavoidable (Literal needs literals) and drifts silently the moment the table
# gains an entry. These tests are the thing that stops that.

def _literal_values(fn, param):
    import typing
    hints = typing.get_type_hints(fn)
    ann = hints.get(param)
    assert typing.get_origin(ann) is typing.Literal, (
        f"{fn.__name__}.{param} is not annotated Literal[...] — the dialog will "
        f"give it a free-text box instead of a validated dropdown")
    return list(typing.get_args(ann))


def test_literal_choices_match_their_preset_tables():
    from partikus import tier07_enclosures as t07
    from partikus import tier08_electronics as t08
    from partikus.presets.bearings import BEARINGS

    cases = [
        (partikus.battery_compartment, "battery_type", list(t07._BATTERY_DIMS)),
        (partikus.raspberry_pi_mount,  "model",        list(t08._RPI_DIMS)),
        (partikus.arduino_mount,       "model",        list(t08._ARDUINO_DIMS)),
        (partikus.usb_cutout,          "connector_type", list(t08._USB_DIMS)),
        (partikus.hdmi_cutout,         "connector_type", list(t08._HDMI_DIMS)),
        (partikus.din_rail_clip,       "rail_type",    list(t08._DIN_DIMS)),
        (partikus.bearing_pocket,      "bearing_id",   list(BEARINGS)),
    ]
    for fn, param, table in cases:
        assert _literal_values(fn, param) == table, (
            f"{fn.__name__}.{param} choices have drifted from the preset table")


def test_every_literal_choice_actually_builds():
    # A choice offered in the dropdown that the function rejects is worse than
    # no dropdown at all.
    for fn, param in [(partikus.hdmi_cutout, "connector_type"),
                      (partikus.usb_cutout, "connector_type"),
                      (partikus.din_rail_clip, "rail_type"),
                      (partikus.button_cutout, "shape"),
                      (partikus.pulley_timing, "belt_type"),
                      (partikus.rounded_cylinder, "ends"),
                      (partikus.hollow_box, "open_face"),
                      (partikus.hinged_box, "hinge_side"),
                      (partikus.battery_compartment, "battery_type"),
                      (partikus.raspberry_pi_mount, "model"),
                      (partikus.arduino_mount, "model"),
                      (partikus.bearing_pocket, "bearing_id")]:
        for choice in _literal_values(fn, param):
            shape = fn(**{param: choice})
            raw = getattr(shape, "shape", shape)
            assert raw.isValid(), f"{fn.__name__}({param}={choice!r}) is invalid"


def test_literal_params_become_a_combo_box():
    if not _HAS_QT:
        return
    dlg = ad._build_dialog(partikus.usb_cutout)
    combos = [w for w in dlg.findChildren(QtWidgets.QComboBox)]
    assert combos, "a Literal parameter should produce a QComboBox"
    items = [combos[0].itemText(i) for i in range(combos[0].count())]
    assert "USB-C" in items and "USB-A" in items
    assert _values_for(partikus.usb_cutout)["connector_type"] == "USB-C"


# ── Cutter marking ───────────────────────────────────────────────────────────
#
# workbench.py cannot be imported under freecadcmd — FreeCADGui exists there but
# is a stub without addCommand, so registration raises. The cutter list is read
# out of the source instead. That is weaker than importing it, but it does catch
# the failure that matters: a name in the list that is not a real function, so
# the marking silently applies to nothing.

def _cutter_names_from_source():
    import ast
    path = os.path.join(_ROOT, "partikus", "gui", "workbench.py")
    with open(path) as fh:
        tree = ast.parse(fh.read(), path)
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign):
            continue
        if not any(getattr(t, "id", None) == "_CUTTER_NAMES" for t in node.targets):
            continue
        call = node.value
        if isinstance(call, ast.Call) and call.args:
            return {e.value for e in call.args[0].elts}
    raise AssertionError("_CUTTER_NAMES not found in workbench.py")


def test_every_cutter_name_is_a_real_function():
    for name in _cutter_names_from_source():
        fn = getattr(partikus, name, None)
        assert callable(fn), f"_CUTTER_NAMES lists {name!r}, which partikus does not export"


def test_known_cutters_are_marked_and_parts_are_not():
    names = _cutter_names_from_source()
    # A negative volume you subtract...
    for name in ("clearance_hole", "tapped_hole", "counterbore_hole",
                 "heat_set_insert_pocket", "bearing_pocket", "usb_cutout"):
        assert name in names, f"{name} is a cutter but is not marked as one"
    # ...versus a part that merely sounds like one.
    for name in ("vent_slots", "display_window", "cable_channel", "led_holder",
                 "dovetail_pin", "tongue", "tab", "boss"):
        assert name not in names, f"{name} is a real part and must not be marked a cutter"


def test_valid_profile_wire_is_not_warned_about():
    # Tier 3 profiles are wires with zero volume and that is correct.
    import FreeCAD
    from partikus.core.serialise import _warn_if_degenerate

    seen = []
    original = FreeCAD.Console.PrintWarning
    try:
        FreeCAD.Console.PrintWarning = lambda m: seen.append(m)
        # Tier 3 returns a raw Part.Wire, not a PartikusShape.
        profile = partikus.rectangle(20, 10)
        _warn_if_degenerate("profile", getattr(profile, "shape", profile))
    finally:
        FreeCAD.Console.PrintWarning = original

    assert not seen, f"a 2D profile should not be flagged: {seen}"
