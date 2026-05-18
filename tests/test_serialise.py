"""Tests for anchor serialisation (save_to_doc / load_from_doc)."""

import sys, os, tempfile
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import FreeCAD
from partikus import box, cylinder
from partikus.core.serialise import save_to_doc, load_from_doc
from partikus.core.anchors import CENTER, TOP, BOTTOM


def _approx(a, b, tol=1e-3):
    return abs(a - b) <= tol


# ── save_to_doc ───────────────────────────────────────────────────────────────

def test_save_creates_feature():
    doc = FreeCAD.newDocument("TestSer1")
    try:
        obj = save_to_doc(box(40, 30, 20), "TestBox", doc)
        assert obj is not None
        assert doc.getObject("TestBox") is not None
    finally:
        FreeCAD.closeDocument(doc.Name)


def test_save_preserves_volume():
    doc = FreeCAD.newDocument("TestSer2")
    try:
        obj = save_to_doc(box(40, 30, 20), "TestBox", doc)
        assert _approx(obj.Shape.Volume, 40 * 30 * 20, tol=1.0)
    finally:
        FreeCAD.closeDocument(doc.Name)


def test_save_stores_anchor_names():
    doc = FreeCAD.newDocument("TestSer3")
    try:
        obj = save_to_doc(box(40, 30, 20), "TestBox", doc)
        for name in (CENTER, TOP, BOTTOM):
            assert name in obj.PartikusAnchors, f"anchor {name!r} missing"
    finally:
        FreeCAD.closeDocument(doc.Name)


def test_save_stores_center_at_origin():
    doc = FreeCAD.newDocument("TestSer4")
    try:
        obj = save_to_doc(box(40, 30, 20), "TestBox", doc)
        cx, cy, cz = obj.PartikusAnchors[CENTER]
        assert _approx(cx, 0.0) and _approx(cy, 0.0) and _approx(cz, 0.0)
    finally:
        FreeCAD.closeDocument(doc.Name)


def test_save_stores_top_z_orientation():
    doc = FreeCAD.newDocument("TestSer5")
    try:
        obj = save_to_doc(box(40, 30, 20), "TestBox", doc)
        assert TOP in obj.PartikusOrientations
        ox, oy, oz = obj.PartikusOrientations[TOP]
        assert _approx(oz, 1.0), f"TOP orientation z expected 1.0, got {oz}"
    finally:
        FreeCAD.closeDocument(doc.Name)


# ── load_from_doc ─────────────────────────────────────────────────────────────

def test_load_reconstructs_volume():
    doc = FreeCAD.newDocument("TestSer6")
    try:
        shape = box(40, 30, 20)
        obj = save_to_doc(shape, "TestBox", doc)
        loaded = load_from_doc(obj)
        assert _approx(loaded.shape.Volume, shape.shape.Volume, tol=1.0)
    finally:
        FreeCAD.closeDocument(doc.Name)


def test_load_reconstructs_center_anchor():
    doc = FreeCAD.newDocument("TestSer7")
    try:
        shape = box(40, 30, 20)
        obj = save_to_doc(shape, "TestBox", doc)
        loaded = load_from_doc(obj)
        orig = shape.anchors[CENTER]
        reco = loaded.anchors[CENTER]
        assert _approx(orig.x, reco.x) and _approx(orig.y, reco.y) and _approx(orig.z, reco.z)
    finally:
        FreeCAD.closeDocument(doc.Name)


def test_load_reconstructs_orientations():
    doc = FreeCAD.newDocument("TestSer8")
    try:
        shape = cylinder(diameter=20, height=40)
        obj = save_to_doc(shape, "TestCyl", doc)
        loaded = load_from_doc(obj)
        assert TOP in loaded.orientations
        assert _approx(loaded.orientations[TOP].z, 1.0)
    finally:
        FreeCAD.closeDocument(doc.Name)


def test_load_anchor_count_matches():
    doc = FreeCAD.newDocument("TestSer9")
    try:
        shape = box(10, 10, 10)
        obj = save_to_doc(shape, "TestBox", doc)
        loaded = load_from_doc(obj)
        assert len(loaded.anchors) == len(shape.anchors)
    finally:
        FreeCAD.closeDocument(doc.Name)


def test_load_returns_partikus_shape():
    from partikus.core.shape_wrapper import PartikusShape
    doc = FreeCAD.newDocument("TestSer10")
    try:
        obj = save_to_doc(box(10, 10, 10), "TestBox", doc)
        loaded = load_from_doc(obj)
        assert isinstance(loaded, PartikusShape)
    finally:
        FreeCAD.closeDocument(doc.Name)


# ── FCStd round-trip ──────────────────────────────────────────────────────────

def test_fcstd_roundtrip_anchors():
    """Anchors survive save-to-disk and reload."""
    with tempfile.NamedTemporaryFile(suffix=".FCStd", delete=False) as f:
        path = f.name
    doc_name = None
    try:
        shape = box(50, 40, 30)
        doc = FreeCAD.newDocument("TestRT")
        doc_name = doc.Name
        save_to_doc(shape, "RTBox", doc)
        doc.saveAs(path)
        FreeCAD.closeDocument(doc_name)
        doc_name = None

        doc2 = FreeCAD.open(path)
        doc_name = doc2.Name
        obj2 = doc2.getObject("RTBox")
        assert obj2 is not None, "feature not found after reload"
        assert CENTER in obj2.PartikusAnchors, "CENTER anchor missing after reload"
        cx, cy, cz = obj2.PartikusAnchors[CENTER]
        assert _approx(cx, 0.0) and _approx(cy, 0.0) and _approx(cz, 0.0)
    finally:
        if doc_name:
            try:
                FreeCAD.closeDocument(doc_name)
            except Exception:
                pass
        try:
            os.unlink(path)
        except Exception:
            pass
