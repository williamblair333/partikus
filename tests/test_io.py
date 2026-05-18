"""Tests for partikus.io — export and import functions."""
import sys, os, tempfile
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import FreeCAD, Part
from partikus.tier01_primitives import box, cylinder, sphere
from partikus.tier09_boolean import difference
from partikus.io import (
    to_step, to_stl, to_iges, to_brep, to_obj, save_fcstd,
    from_step, from_brep, from_stl,
)

TMPDIR = tempfile.mkdtemp(prefix="partikus_io_test_")

def _tmp(name):
    return os.path.join(TMPDIR, name)

def _approx(a, b, tol=1.0):
    return abs(a - b) < tol


# ── to_step ───────────────────────────────────────────────────────────────────

def test_to_step_single_creates_file():
    b = box(20, 20, 20)
    p = _tmp("single.step")
    to_step(b, p)
    assert os.path.exists(p)

def test_to_step_single_nonempty():
    b = box(20, 20, 20)
    p = _tmp("single2.step")
    to_step(b, p)
    assert os.path.getsize(p) > 100

def test_to_step_returns_path():
    b = box(20, 20, 20)
    p = _tmp("ret.step")
    result = to_step(b, p)
    assert result == p

def test_to_step_multi_shapes():
    b = box(20, 20, 20)
    c = cylinder(diameter=10, height=30)
    p = _tmp("multi.step")
    to_step([b, c], p)
    assert os.path.getsize(p) > 100

def test_to_step_labeled_tuples():
    b = box(20, 20, 20)
    c = cylinder(diameter=10, height=30)
    p = _tmp("labeled.step")
    to_step([(b, "Body"), (c, "Bore")], p)
    assert os.path.exists(p)

def test_to_step_nested_dir():
    b = box(20, 20, 20)
    p = _tmp("subdir/part.step")
    to_step(b, p)
    assert os.path.exists(p)


# ── to_stl ────────────────────────────────────────────────────────────────────

def test_to_stl_creates_file():
    b = box(20, 20, 20)
    p = _tmp("part.stl")
    to_stl(b, p)
    assert os.path.exists(p)

def test_to_stl_nonempty():
    b = box(20, 20, 20)
    p = _tmp("part2.stl")
    to_stl(b, p)
    assert os.path.getsize(p) > 100

def test_to_stl_deflection_accepted():
    # Verify deflection parameter is accepted without error at both extremes.
    b = box(20, 20, 20)
    to_stl(b, _tmp("coarse.stl"), deflection=5.0)
    to_stl(b, _tmp("fine.stl"), deflection=0.01)
    assert os.path.exists(_tmp("coarse.stl"))
    assert os.path.exists(_tmp("fine.stl"))

def test_to_stl_multi_shapes():
    b = box(20, 20, 20)
    c = cylinder(diameter=10, height=30)
    p = _tmp("multi.stl")
    to_stl([b, c], p)
    assert os.path.exists(p)

def test_to_stl_returns_path():
    b = box(20, 20, 20)
    p = _tmp("stl_ret.stl")
    result = to_stl(b, p)
    assert result == p


# ── to_iges ───────────────────────────────────────────────────────────────────

def test_to_iges_creates_file():
    b = box(20, 20, 20)
    p = _tmp("part.iges")
    to_iges(b, p)
    assert os.path.exists(p)

def test_to_iges_nonempty():
    b = box(20, 20, 20)
    p = _tmp("part2.iges")
    to_iges(b, p)
    assert os.path.getsize(p) > 100

def test_to_iges_multi():
    b = box(20, 20, 20)
    c = cylinder(diameter=10, height=30)
    p = _tmp("multi.iges")
    to_iges([b, c], p)
    assert os.path.exists(p)


# ── to_brep ───────────────────────────────────────────────────────────────────

def test_to_brep_creates_file():
    b = box(20, 20, 20)
    p = _tmp("part.brep")
    to_brep(b, p)
    assert os.path.exists(p)

def test_to_brep_nonempty():
    b = box(20, 20, 20)
    p = _tmp("part2.brep")
    to_brep(b, p)
    assert os.path.getsize(p) > 50

def test_to_brep_returns_path():
    b = box(20, 20, 20)
    p = _tmp("brep_ret.brep")
    result = to_brep(b, p)
    assert result == p


# ── to_obj ────────────────────────────────────────────────────────────────────

def test_to_obj_creates_file():
    b = box(20, 20, 20)
    p = _tmp("part.obj")
    to_obj(b, p)
    assert os.path.exists(p)

def test_to_obj_nonempty():
    b = box(20, 20, 20)
    p = _tmp("part2.obj")
    to_obj(b, p)
    assert os.path.getsize(p) > 50

def test_to_obj_returns_path():
    b = box(20, 20, 20)
    p = _tmp("obj_ret.obj")
    result = to_obj(b, p)
    assert result == p


# ── save_fcstd ────────────────────────────────────────────────────────────────

def test_save_fcstd_creates_file():
    b = box(20, 20, 20)
    p = _tmp("project.FCStd")
    save_fcstd(b, p)
    assert os.path.exists(p)

def test_save_fcstd_nonempty():
    b = box(20, 20, 20)
    p = _tmp("project2.FCStd")
    save_fcstd(b, p)
    assert os.path.getsize(p) > 100

def test_save_fcstd_labeled():
    body = box(30, 20, 10)
    cap  = box(30, 20, 3)
    p = _tmp("asm.FCStd")
    save_fcstd([(body, "Body"), (cap, "Cap")], p)
    assert os.path.exists(p)

def test_save_fcstd_returns_path():
    b = box(20, 20, 20)
    p = _tmp("fcstd_ret.FCStd")
    result = save_fcstd(b, p)
    assert result == p


# ── from_step (round-trip) ────────────────────────────────────────────────────

def test_from_step_valid():
    b = box(20, 15, 10)
    p = _tmp("rt.step")
    to_step(b, p)
    s = from_step(p)
    assert s.shape.isValid()

def test_from_step_volume_preserved():
    b = box(20, 15, 10)
    p = _tmp("vol_rt.step")
    to_step(b, p)
    s = from_step(p)
    assert _approx(s.shape.Volume, 20 * 15 * 10, tol=1.0)

def test_from_step_returns_partikusshape():
    b = box(20, 15, 10)
    p = _tmp("ps_rt.step")
    to_step(b, p)
    s = from_step(p)
    from partikus.core.shape_wrapper import PartikusShape
    assert isinstance(s, PartikusShape)

def test_from_step_anchors_present():
    b = box(20, 15, 10)
    p = _tmp("anch_rt.step")
    to_step(b, p)
    s = from_step(p)
    from partikus.core.anchors import CENTER
    assert CENTER in s.anchors

def test_from_step_missing_file():
    try:
        from_step(_tmp("nonexistent.step"))
        assert False
    except FileNotFoundError:
        pass

def test_from_step_complex_shape():
    b = box(30, 20, 15)
    hole = cylinder(diameter=8, height=20)
    part = difference(b, hole)
    p = _tmp("complex_rt.step")
    to_step(part, p)
    s = from_step(p)
    assert s.shape.isValid()
    assert s.shape.Volume < 30 * 20 * 15


# ── from_brep (round-trip) ────────────────────────────────────────────────────

def test_from_brep_valid():
    b = box(20, 15, 10)
    p = _tmp("rt.brep")
    to_brep(b, p)
    s = from_brep(p)
    assert s.shape.isValid()

def test_from_brep_volume_exact():
    b = box(20, 15, 10)
    p = _tmp("vol_rt.brep")
    to_brep(b, p)
    s = from_brep(p)
    assert _approx(s.shape.Volume, 20 * 15 * 10, tol=0.01)

def test_from_brep_missing_file():
    try:
        from_brep(_tmp("nonexistent.brep"))
        assert False
    except FileNotFoundError:
        pass


# ── from_stl (round-trip) ─────────────────────────────────────────────────────

def test_from_stl_valid():
    b = box(20, 15, 10)
    p = _tmp("rt.stl")
    to_stl(b, p, deflection=0.1)
    s = from_stl(p)
    assert s.shape.isValid()

def test_from_stl_returns_partikusshape():
    b = box(20, 15, 10)
    p = _tmp("ps_rt.stl")
    to_stl(b, p)
    s = from_stl(p)
    from partikus.core.shape_wrapper import PartikusShape
    assert isinstance(s, PartikusShape)

def test_from_stl_missing_file():
    try:
        from_stl(_tmp("nonexistent.stl"))
        assert False
    except FileNotFoundError:
        pass

def test_from_stl_anchors_present():
    b = box(20, 15, 10)
    p = _tmp("anch_rt.stl")
    to_stl(b, p)
    s = from_stl(p)
    from partikus.core.anchors import CENTER
    assert CENTER in s.anchors
