"""
Tests for the GUI Attach command's document logic (partikus.gui.attach).

The dialog is a thin shell; everything it does to the document goes through
attach_objects(), which runs headless under freecadcmd and is tested here.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import FreeCAD
from partikus import box, cylinder
from partikus.core.serialise import save_to_doc, load_from_doc
from partikus.gui.attach import attach_objects, anchor_names, is_partikus_object


def _approx(a, b, tol=1e-3):
    return abs(a - b) <= tol


def _doc(name):
    doc = FreeCAD.newDocument(name)
    doc.UndoMode = 1
    return doc


def _base_and_pin(doc):
    # Base spans z -5..5, pin (cylinder) z -5..5: they start overlapping.
    base = save_to_doc(box(20, 20, 10), "Base", doc)
    pin = save_to_doc(cylinder(diameter=10, height=10), "Pin", doc)
    return base, pin


# ── Placement ────────────────────────────────────────────────────────────────

def test_child_anchor_lands_on_parent_anchor():
    doc = _doc("TestAtt1")
    try:
        base, pin = _base_and_pin(doc)
        attach_objects(pin, base, "BOTTOM", "TOP")
        bb = pin.Shape.BoundBox
        assert _approx(bb.ZMin, 5) and _approx(bb.ZMax, 15), bb
        # Stored anchors move with it, so a second operation starts from truth.
        assert _approx(load_from_doc(pin).anchors["BOTTOM"].z, 5)
    finally:
        FreeCAD.closeDocument(doc.Name)


def test_parent_moved_by_hand_is_respected():
    doc = _doc("TestAtt2")
    try:
        base, pin = _base_and_pin(doc)
        p = base.Placement
        p.Base = FreeCAD.Vector(100, 0, 0)
        base.Placement = p
        doc.recompute()
        attach_objects(pin, base, "BOTTOM", "TOP")
        bb = pin.Shape.BoundBox
        assert _approx(bb.Center.x, 100) and _approx(bb.ZMin, 5), bb
    finally:
        FreeCAD.closeDocument(doc.Name)


def test_gap_and_rotation():
    doc = _doc("TestAtt3")
    try:
        base, pin = _base_and_pin(doc)
        attach_objects(pin, base, "BOTTOM", "TOP", offset=2.0, rotation_deg=45.0)
        assert _approx(pin.Shape.BoundBox.ZMin, 7), pin.Shape.BoundBox
    finally:
        FreeCAD.closeDocument(doc.Name)


def test_attaching_twice_is_stable():
    doc = _doc("TestAtt4")
    try:
        base, pin = _base_and_pin(doc)
        attach_objects(pin, base, "BOTTOM", "TOP")
        first = pin.Shape.BoundBox
        attach_objects(pin, base, "BOTTOM", "TOP")
        second = pin.Shape.BoundBox
        assert _approx(first.ZMin, second.ZMin) and _approx(first.Center.x, second.Center.x)
    finally:
        FreeCAD.closeDocument(doc.Name)


# ── Weld ─────────────────────────────────────────────────────────────────────

def test_weld_makes_one_solid_and_hides_the_inputs():
    doc = _doc("TestAtt5")
    try:
        base, pin = _base_and_pin(doc)
        expected = base.Shape.Volume + pin.Shape.Volume   # touching, not overlapping
        weld = attach_objects(pin, base, "BOTTOM", "TOP", weld=True)
        assert weld is not pin and weld is not base
        assert weld.Shape.isValid()
        assert len(weld.Shape.Solids) == 1, "welded parts should be one solid"
        assert _approx(weld.Shape.Volume, expected, tol=1.0)
        assert not base.Visibility and not pin.Visibility
        assert is_partikus_object(weld), "the weld should carry anchors like any part"
    finally:
        FreeCAD.closeDocument(doc.Name)


# ── Undo ─────────────────────────────────────────────────────────────────────

def test_attach_is_one_undo_step():
    doc = _doc("TestAtt6")
    try:
        base, pin = _base_and_pin(doc)
        before = pin.Shape.BoundBox.ZMin
        attach_objects(pin, base, "BOTTOM", "TOP")
        doc.undo()
        doc.recompute()
        assert _approx(pin.Shape.BoundBox.ZMin, before), pin.Shape.BoundBox
    finally:
        FreeCAD.closeDocument(doc.Name)


def test_weld_undo_removes_the_weld_and_restores_the_inputs():
    doc = _doc("TestAtt7")
    try:
        base, pin = _base_and_pin(doc)
        n_before = len(doc.Objects)
        attach_objects(pin, base, "BOTTOM", "TOP", weld=True)
        doc.undo()
        doc.recompute()
        assert len(doc.Objects) == n_before
        assert base.Visibility and pin.Visibility
    finally:
        FreeCAD.closeDocument(doc.Name)


# ── Rejections ───────────────────────────────────────────────────────────────

def _raises(fn, *words):
    try:
        fn()
    except ValueError as e:
        msg = str(e)
        for w in words:
            assert w in msg, f"message should mention {w!r}: {msg}"
        return
    raise AssertionError("expected ValueError")


def test_rejects_a_non_partikus_object():
    doc = _doc("TestAtt8")
    try:
        base, _ = _base_and_pin(doc)
        plain = doc.addObject("Part::Box", "PlainBox")
        doc.recompute()
        _raises(lambda: attach_objects(plain, base), "PlainBox")
    finally:
        FreeCAD.closeDocument(doc.Name)


def test_rejects_attaching_a_part_to_itself():
    doc = _doc("TestAtt9")
    try:
        base, _ = _base_and_pin(doc)
        _raises(lambda: attach_objects(base, base), "itself")
    finally:
        FreeCAD.closeDocument(doc.Name)


def test_rejects_an_unknown_anchor_and_names_the_valid_ones():
    doc = _doc("TestAtt10")
    try:
        base, pin = _base_and_pin(doc)
        _raises(lambda: attach_objects(pin, base, "TOP_FRONT_RIGHT", "TOP"),
                "TOP_FRONT_RIGHT", "BOTTOM_RIM")
    finally:
        FreeCAD.closeDocument(doc.Name)


def test_failed_attach_leaves_the_document_unchanged():
    doc = _doc("TestAtt11")
    try:
        base, pin = _base_and_pin(doc)
        before = pin.Shape.BoundBox.ZMin
        try:
            attach_objects(pin, base, "NOPE", "TOP")
        except ValueError:
            pass
        assert _approx(pin.Shape.BoundBox.ZMin, before)
    finally:
        FreeCAD.closeDocument(doc.Name)


# ── Dialog ───────────────────────────────────────────────────────────────────

def test_dialog_defaults_and_swapping_the_moving_part():
    from partikus.gui import attach as att
    if not att.HAS_GUI:
        return
    doc = _doc("TestAtt13")
    try:
        base, pin = _base_and_pin(doc)
        dlg = att.AttachDialog(pin, base)
        v = dlg.values()
        assert v["child_obj"] is pin and v["parent_obj"] is base
        assert (v["child_anchor"], v["parent_anchor"]) == ("BOTTOM", "TOP")
        assert v["offset"] == 0.0 and v["rotation_deg"] == 0.0 and v["weld"] is False
        # Swap which part moves: both anchor lists must follow their parts.
        dlg.move_box.setCurrentIndex(1)
        v = dlg.values()
        assert v["child_obj"] is base and v["parent_obj"] is pin
        items = [dlg.child_box.itemText(i) for i in range(dlg.child_box.count())]
        assert "TOP_FRONT_RIGHT" in items, "moving part's list should now be the box's"
        attach_objects(**v)     # the dialog's values are accepted as-is
        assert _approx(base.Shape.BoundBox.ZMin, 5)
    finally:
        FreeCAD.closeDocument(doc.Name)


# ── Dialog helpers ───────────────────────────────────────────────────────────

def test_anchor_names_lists_what_the_part_has():
    doc = _doc("TestAtt12")
    try:
        base, pin = _base_and_pin(doc)
        assert "TOP_FRONT_RIGHT" in anchor_names(base)
        assert set(anchor_names(pin)) == {"CENTER", "TOP", "BOTTOM", "TOP_RIM", "BOTTOM_RIM"}
    finally:
        FreeCAD.closeDocument(doc.Name)
