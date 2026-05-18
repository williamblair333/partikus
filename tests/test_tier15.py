"""Tests for Tier 15 — NURBS Curves, Surfaces, Conversion, Analysis."""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import FreeCAD, Part
from partikus.tier15a_nurbs import (
    nurbs_curve, bspline_curve, bezier_curve, curve_through_points,
    helix_curve, conic_curve,
    loft_surface, sweep_1rail, sweep_2rail, network_surface,
    patch_fill, boundary_surface,
    surface_from_points, move_control_point, offset_surface,
    join_surfaces, rebuild_surface,
    trim_surface, split_surface, surface_fillet,
    match_surfaces, surface_chamfer,        # stubs — BRep API unavailable
)
from partikus.tier15b_subd import subd_primitive, subd_subdivide
from partikus.tier15c_conversion import (
    subd_to_nurbs, nurbs_to_subd, mesh_to_subd, mesh_to_nurbs,
)
from partikus.tier15d_analysis import (
    analyze_curvature, analyze_zebra, analyze_draft, analyze_deviation,
)
from partikus.tier01_primitives import box, cylinder

def _approx(a, b, tol=1.0):
    return abs(a - b) < tol


def _make_grid(rows=4, cols=4, z_amp=5.0):
    return [[(i * 10.0, j * 10.0, z_amp * math.sin(i * 0.5) * math.cos(j * 0.5))
             for j in range(cols)]
            for i in range(rows)]


# ── nurbs_curve ───────────────────────────────────────────────────────────────

def test_nurbs_curve_valid():
    s = nurbs_curve([(0,0,0),(10,20,0),(30,10,0),(40,0,0)])
    assert s.shape.isValid()

def test_nurbs_curve_wire_type():
    s = nurbs_curve([(0,0,0),(10,20,0),(30,10,0),(40,0,0)])
    assert isinstance(s.shape, Part.Wire)

def test_nurbs_curve_too_few_points():
    try:
        nurbs_curve([(0,0,0),(5,5,0)], degree=3)
        assert False, "expected ValueError"
    except ValueError:
        pass


# ── bspline_curve ─────────────────────────────────────────────────────────────

def test_bspline_curve_valid():
    s = bspline_curve([(0,0,0),(5,10,0),(15,8,0),(20,0,0)])
    assert s.shape.isValid()

def test_bspline_curve_anchors():
    s = bspline_curve([(0,0,0),(10,10,0),(20,0,0),(30,10,0)])
    assert "CENTER" in s.anchors


# ── bezier_curve ──────────────────────────────────────────────────────────────

def test_bezier_curve_valid():
    s = bezier_curve([(0,0,0),(10,20,0),(30,20,0),(40,0,0)])
    assert s.shape.isValid()

def test_bezier_curve_wire_type():
    s = bezier_curve([(0,0,0),(10,20,0),(40,0,0)])
    assert isinstance(s.shape, Part.Wire)

def test_bezier_curve_too_few_points():
    try:
        bezier_curve([(0,0,0)])
        assert False, "expected ValueError"
    except ValueError:
        pass


# ── curve_through_points ──────────────────────────────────────────────────────

def test_curve_through_points_smooth():
    s = curve_through_points([(0,0,0),(10,5,2),(20,0,4),(30,5,0)])
    assert s.shape.isValid()

def test_curve_through_points_polyline():
    s = curve_through_points([(0,0,0),(10,5,0),(20,0,0)], smooth=False)
    assert s.shape.isValid()

def test_curve_through_points_too_few():
    try:
        curve_through_points([(0,0,0)])
        assert False, "expected ValueError"
    except ValueError:
        pass


# ── helix_curve ───────────────────────────────────────────────────────────────

def test_helix_curve_valid():
    s = helix_curve(diameter=20, pitch=5, turns=4)
    assert s.shape.isValid()

def test_helix_curve_height():
    s = helix_curve(diameter=20, pitch=5, turns=4)
    bb = s.shape.BoundBox
    assert _approx(bb.ZLength, 20.0, tol=1.0)

def test_helix_curve_bad_params():
    try:
        helix_curve(diameter=0, pitch=5, turns=3)
        assert False, "expected ValueError"
    except ValueError:
        pass


# ── conic_curve ───────────────────────────────────────────────────────────────

def test_conic_parabola_valid():
    s = conic_curve("parabola", focal_length=30, extent=60)
    assert s.shape.isValid()

def test_conic_hyperbola_valid():
    s = conic_curve("hyperbola", focal_length=20, extent=40)
    assert s.shape.isValid()

def test_conic_bad_type():
    try:
        conic_curve("ellipse")
        assert False, "expected ValueError"
    except ValueError:
        pass


# ── loft_surface ──────────────────────────────────────────────────────────────

def _make_circle_wire(r, z):
    c = Part.Circle(FreeCAD.Vector(0,0,z), FreeCAD.Vector(0,0,1), r)
    return Part.Wire(c.toShape())

def test_loft_surface_valid():
    p1 = _make_circle_wire(10, 0)
    p2 = _make_circle_wire(15, 20)
    p3 = _make_circle_wire(10, 40)
    s = loft_surface([p1, p2, p3])
    assert s.shape.isValid()

def test_loft_surface_volume_positive():
    p1 = _make_circle_wire(10, 0)
    p2 = _make_circle_wire(10, 20)
    s = loft_surface([p1, p2])
    assert s.shape.Volume > 0 or s.shape.Area > 0

def test_loft_surface_ruled():
    p1 = _make_circle_wire(10, 0)
    p2 = _make_circle_wire(20, 30)
    s = loft_surface([p1, p2], ruled=True)
    assert s.shape.isValid()

def test_loft_surface_too_few():
    try:
        loft_surface([_make_circle_wire(10, 0)])
        assert False, "expected ValueError"
    except ValueError:
        pass


# ── sweep_1rail ───────────────────────────────────────────────────────────────

def test_sweep_1rail_straight_valid():
    # straight line path
    path_pts = [FreeCAD.Vector(0,0,i*5) for i in range(6)]
    bs = Part.BSplineCurve(); bs.interpolate(path_pts)
    rail = Part.Wire(bs.toShape())
    profile = Part.Wire(Part.Circle(
        FreeCAD.Vector(0,0,0), FreeCAD.Vector(0,0,1), 4).toShape())
    s = sweep_1rail(profile, rail)
    assert s.shape.isValid()

def test_sweep_1rail_volume_positive():
    path_pts = [FreeCAD.Vector(0,0,i*3) for i in range(5)]
    bs = Part.BSplineCurve(); bs.interpolate(path_pts)
    rail = Part.Wire(bs.toShape())
    profile = Part.Wire(Part.Circle(
        FreeCAD.Vector(0,0,0), FreeCAD.Vector(0,0,1), 3).toShape())
    s = sweep_1rail(profile, rail)
    assert s.shape.Volume > 0

def test_sweep_1rail_accepts_partikusshape():
    rail_ps = helix_curve(diameter=20, pitch=5, turns=2)
    profile = Part.Wire(Part.Circle(
        FreeCAD.Vector(0,0,0), FreeCAD.Vector(0,0,1), 3).toShape())
    s = sweep_1rail(profile, rail_ps)
    assert s.shape.isValid()


# ── patch_fill ────────────────────────────────────────────────────────────────

def _tri_patch():
    r = 15
    pts = [FreeCAD.Vector(r*math.cos(a), r*math.sin(a), 0)
           for a in (0, 2*math.pi/3, 4*math.pi/3)]
    segs = []
    for i in range(3):
        p0, p1 = pts[i], pts[(i+1)%3]
        segs.append(Part.Wire(Part.LineSegment(p0, p1).toShape()))
    return segs

def test_patch_fill_valid():
    segs = _tri_patch()
    s = patch_fill(segs)
    assert s.shape.isValid()

def test_patch_fill_area_positive():
    segs = _tri_patch()
    s = patch_fill(segs)
    assert s.shape.Area > 0


# ── boundary_surface ──────────────────────────────────────────────────────────

def test_boundary_surface_3_curves():
    segs = _tri_patch()
    s = boundary_surface(segs)
    assert s.shape.isValid()

def test_boundary_surface_4_curves():
    pts = [
        (FreeCAD.Vector(-10, 0, 0), FreeCAD.Vector(10, 0, 0)),
        (FreeCAD.Vector(10, 0, 0),  FreeCAD.Vector(10, 10, 0)),
        (FreeCAD.Vector(10, 10, 0), FreeCAD.Vector(-10, 10, 0)),
        (FreeCAD.Vector(-10, 10, 0),FreeCAD.Vector(-10, 0, 0)),
    ]
    segs = [Part.Wire(Part.LineSegment(a, b).toShape()) for a, b in pts]
    s = boundary_surface(segs)
    assert s.shape.isValid()

def test_boundary_surface_bad_count():
    segs = _tri_patch()
    try:
        boundary_surface(segs[:2])
        assert False, "expected ValueError"
    except ValueError:
        pass


# ── surface_from_points ───────────────────────────────────────────────────────

def test_surface_from_points_valid():
    s = surface_from_points(_make_grid())
    assert s.shape.isValid()

def test_surface_from_points_area_positive():
    s = surface_from_points(_make_grid())
    assert s.shape.Area > 0

def test_surface_from_points_flat_grid():
    grid = [[(float(i), float(j), 0.0) for j in range(3)] for i in range(3)]
    s = surface_from_points(grid)
    assert s.shape.isValid()

def test_surface_from_points_too_few_rows():
    try:
        surface_from_points([[(0,0,0),(1,0,0)]])
        assert False, "expected ValueError"
    except ValueError:
        pass

def test_surface_from_points_jagged():
    try:
        surface_from_points([[(0,0,0),(1,0,0)],[(0,1,0)]])
        assert False, "expected ValueError"
    except ValueError:
        pass


# ── move_control_point ────────────────────────────────────────────────────────

def test_move_control_point_valid():
    s = surface_from_points(_make_grid())
    s2 = move_control_point(s, 2, 2, (15, 15, 30))
    assert s2.shape.isValid()

def test_move_control_point_changes_surface():
    s = surface_from_points(_make_grid(z_amp=0))
    s2 = move_control_point(s, 2, 2, (10, 10, 25))
    # bounding box Z should increase
    assert s2.shape.BoundBox.ZLength > s.shape.BoundBox.ZLength


# ── offset_surface ────────────────────────────────────────────────────────────

def test_offset_surface_valid():
    s = surface_from_points(_make_grid())
    off = offset_surface(s, 2.0)
    assert off.shape.isValid()

def test_offset_surface_shifts_bounds():
    s = surface_from_points([[(float(i), float(j), 0.0) for j in range(3)] for i in range(3)])
    off = offset_surface(s, 5.0)
    assert off.shape.BoundBox.ZMax > s.shape.BoundBox.ZMax - 0.1


# ── join_surfaces ─────────────────────────────────────────────────────────────

def test_join_surfaces_valid():
    g1 = [[(float(i), float(j), 0.0) for j in range(3)] for i in range(3)]
    g2 = [[(float(i), float(j)+5, 0.0) for j in range(3)] for i in range(3)]
    s1 = surface_from_points(g1)
    s2 = surface_from_points(g2)
    shell = join_surfaces(s1, s2)
    assert shell.shape.isValid()

def test_join_surfaces_area_sum():
    g1 = [[(float(i), float(j), 0.0) for j in range(3)] for i in range(3)]
    g2 = [[(float(i), float(j)+5, 0.0) for j in range(3)] for i in range(3)]
    s1 = surface_from_points(g1)
    s2 = surface_from_points(g2)
    shell = join_surfaces(s1, s2)
    assert _approx(shell.shape.Area, s1.shape.Area + s2.shape.Area, tol=5.0)

def test_join_surfaces_too_few():
    s1 = surface_from_points(_make_grid())
    try:
        join_surfaces(s1)
        assert False, "expected ValueError"
    except ValueError:
        pass


# ── rebuild_surface ───────────────────────────────────────────────────────────

def test_rebuild_surface_valid():
    s = surface_from_points(_make_grid())
    s2 = rebuild_surface(s, u_count=6, v_count=6, degree=3)
    assert s2.shape.isValid()

def test_rebuild_surface_area_similar():
    s = surface_from_points(_make_grid(z_amp=0))
    s2 = rebuild_surface(s, u_count=5, v_count=5)
    assert _approx(s2.shape.Area, s.shape.Area, tol=20.0)

def test_rebuild_surface_bad_count():
    s = surface_from_points(_make_grid())
    try:
        rebuild_surface(s, u_count=1, v_count=5)
        assert False, "expected ValueError"
    except ValueError:
        pass


# ── network_surface ───────────────────────────────────────────────────────────

def _make_u_curve(y, z_fn=None):
    pts = [(x, y, (z_fn(x) if z_fn else 0.0)) for x in [0, 10, 20]]
    return curve_through_points(pts)

def _make_v_curve(x):
    return curve_through_points([(x, y, 0.0) for y in [0, 10, 20]])

def test_network_surface_basic():
    u = [_make_u_curve(y) for y in [0, 10, 20]]
    v = [_make_v_curve(x) for x in [0, 20]]
    s = network_surface(u, v)
    assert s.shape.isValid()

def test_network_surface_area():
    u = [_make_u_curve(y) for y in [0, 10, 20]]
    v = [_make_v_curve(x) for x in [0, 20]]
    s = network_surface(u, v)
    assert s.shape.Area > 0

def test_network_surface_curved():
    u = [curve_through_points([(0, y, math.sin(y*0.2)*3), (10, y, 2), (20, y, 0)])
         for y in [0, 10, 20]]
    v = [curve_through_points([(x, 0, 0), (x, 10, 1), (x, 20, 0)])
         for x in [0, 20]]
    s = network_surface(u, v)
    assert s.shape.isValid()

def test_network_surface_bad_u():
    v = [_make_v_curve(x) for x in [0, 20]]
    try:
        network_surface([_make_u_curve(0)], v)
        assert False
    except ValueError:
        pass

def test_network_surface_bad_v():
    u = [_make_u_curve(y) for y in [0, 10, 20]]
    try:
        network_surface(u, [_make_v_curve(0)])
        assert False
    except ValueError:
        pass

def test_network_surface_anchors():
    u = [_make_u_curve(y) for y in [0, 10, 20]]
    v = [_make_v_curve(x) for x in [0, 20]]
    s = network_surface(u, v)
    from partikus.core.anchors import CENTER
    assert CENTER in s.anchors


# ── sweep_2rail ───────────────────────────────────────────────────────────────

def test_sweep_2rail_basic():
    prof  = curve_through_points([(0, 0, 0), (0, 8, 0)])
    rail1 = curve_through_points([(0, 0, 0), (20, 0, 2), (40, 0, 0)])
    rail2 = curve_through_points([(0, 8, 0), (20, 8, 2), (40, 8, 0)])
    s = sweep_2rail(prof, rail1, rail2)
    assert s.shape.isValid()

def test_sweep_2rail_area():
    prof  = curve_through_points([(0, 0, 0), (0, 10, 0)])
    rail1 = curve_through_points([(0, 0, 0), (30, 0, 0)])
    rail2 = curve_through_points([(0, 10, 0), (30, 10, 0)])
    s = sweep_2rail(prof, rail1, rail2)
    assert s.shape.Area > 0

def test_sweep_2rail_curved_rails():
    prof  = curve_through_points([(0, 0, 0), (0, 15, 0)])
    rail1 = curve_through_points([(0, 0, 0), (15, 0, 5), (30, 0, 0)])
    rail2 = curve_through_points([(0, 15, 0), (15, 15, 5), (30, 15, 0)])
    s = sweep_2rail(prof, rail1, rail2)
    assert s.shape.isValid()
    assert s.shape.Area > 0

def test_sweep_2rail_anchors():
    prof  = curve_through_points([(0, 0, 0), (0, 10, 0)])
    rail1 = curve_through_points([(0, 0, 0), (20, 0, 0)])
    rail2 = curve_through_points([(0, 10, 0), (20, 10, 0)])
    s = sweep_2rail(prof, rail1, rail2)
    from partikus.core.anchors import CENTER
    assert CENTER in s.anchors

def test_sweep_2rail_bad_profile():
    try:
        sweep_2rail("not_a_wire", None, None)
        assert False
    except (TypeError, AttributeError):
        pass


# ── trim_surface ──────────────────────────────────────────────────────────────

def _flat_face_shape():
    import Part as _Part
    from partikus.core.shape_wrapper import PartikusShape
    from partikus.core.anchors import CENTER, TOP, BOTTOM, FRONT, BACK, LEFT, RIGHT
    import FreeCAD as _FC
    w = _Part.Wire(_Part.makePolygon([
        _FC.Vector(0,0,0), _FC.Vector(30,0,0),
        _FC.Vector(30,20,0), _FC.Vector(0,20,0), _FC.Vector(0,0,0)
    ]))
    face = _Part.Face(w)
    bb = face.BoundBox
    def V(x,y,z): return _FC.Vector(x,y,z)
    cx,cy,cz = (bb.XMin+bb.XMax)/2, (bb.YMin+bb.YMax)/2, (bb.ZMin+bb.ZMax)/2
    return PartikusShape(face,
        {CENTER:V(cx,cy,cz),TOP:V(cx,cy,bb.ZMax),BOTTOM:V(cx,cy,bb.ZMin),
         FRONT:V(cx,bb.YMax,cz),BACK:V(cx,bb.YMin,cz),
         RIGHT:V(bb.XMax,cy,cz),LEFT:V(bb.XMin,cy,cz)},
        {})

def test_trim_surface_basic():
    face = _flat_face_shape()
    cutter = box(length=15, width=100, height=10)
    result = trim_surface(face, cutter)
    assert result.shape.isValid()

def test_trim_surface_area_reduced():
    face = _flat_face_shape()
    # Cut away the left half (x=0..15 of a 30x20 face)
    cutter = box(length=15, width=100, height=10)
    result = trim_surface(face, cutter)
    assert result.shape.Area < 600.0

def test_trim_surface_surface_from_points():
    flat = [[(float(i)*5, float(j)*5, 0.0) for j in range(5)] for i in range(5)]
    s = surface_from_points(flat)
    cutter = box(length=10, width=100, height=10)
    result = trim_surface(s, cutter)
    assert result.shape.isValid()


# ── split_surface ─────────────────────────────────────────────────────────────

def test_split_surface_basic():
    face = _flat_face_shape()
    # Splitter covers left half → produces 2 pieces
    splitter = box(length=15, width=100, height=10)
    pieces = split_surface(face, splitter)
    assert len(pieces) >= 1

def test_split_surface_pieces_valid():
    face = _flat_face_shape()
    splitter = box(length=15, width=100, height=10)
    pieces = split_surface(face, splitter)
    for p in pieces:
        assert p.shape.isValid()

def test_split_surface_area_preserved():
    face = _flat_face_shape()
    splitter = box(length=15, width=100, height=10)
    pieces = split_surface(face, splitter)
    total = sum(p.shape.Area for p in pieces)
    assert _approx(total, 600.0, tol=5.0)

def test_split_surface_returns_list():
    face = _flat_face_shape()
    splitter = box(length=15, width=100, height=10)
    result = split_surface(face, splitter)
    assert isinstance(result, list)


# ── surface_fillet ────────────────────────────────────────────────────────────

def _make_adjacent_faces():
    """Two planar quads sharing the edge at x=0, z=0..10."""
    import Part as _Part, FreeCAD as _FC
    from partikus.core.shape_wrapper import PartikusShape
    from partikus.core.anchors import CENTER, TOP, BOTTOM, FRONT, BACK, LEFT, RIGHT
    def V(x,y,z): return _FC.Vector(x,y,z)
    def _ps(fc_face):
        bb = fc_face.BoundBox
        cx,cy,cz = (bb.XMin+bb.XMax)/2,(bb.YMin+bb.YMax)/2,(bb.ZMin+bb.ZMax)/2
        return PartikusShape(fc_face,{CENTER:V(cx,cy,cz)},{})
    w1 = _Part.Wire(_Part.makePolygon([V(0,0,0),V(10,0,0),V(10,10,0),V(0,10,0),V(0,0,0)]))
    w2 = _Part.Wire(_Part.makePolygon([V(0,0,0),V(0,10,0),V(0,10,10),V(0,0,10),V(0,0,0)]))
    return _ps(_Part.Face(w1)), _ps(_Part.Face(w2))

def test_surface_fillet_basic():
    fa, fb = _make_adjacent_faces()
    result = surface_fillet(fa, fb, radius=1.0)
    assert result.shape.isValid()

def test_surface_fillet_bad_radius():
    fa, fb = _make_adjacent_faces()
    try:
        surface_fillet(fa, fb, radius=0)
        assert False
    except ValueError:
        pass

def test_surface_fillet_negative_radius():
    fa, fb = _make_adjacent_faces()
    try:
        surface_fillet(fa, fb, radius=-1.0)
        assert False
    except ValueError:
        pass


# ── BRep stubs still raise NotImplementedError ────────────────────────────────

def test_match_surfaces_stub():
    try:
        match_surfaces(None, None)
        assert False
    except NotImplementedError:
        pass

def test_untrim_surface_stub():
    from partikus.tier15a_nurbs import untrim_surface
    try:
        untrim_surface(None)
        assert False
    except NotImplementedError:
        pass

def test_variable_fillet_stub():
    from partikus.tier15a_nurbs import variable_fillet
    try:
        variable_fillet(None, None, None)
        assert False
    except NotImplementedError:
        pass

def test_surface_chamfer_stub():
    try:
        surface_chamfer(None, None, 1.0)
        assert False
    except NotImplementedError:
        pass


# ── SubD stubs ────────────────────────────────────────────────────────────────

def test_subd_primitive_stub():
    try:
        subd_primitive("cube")
        assert False
    except NotImplementedError:
        pass

def test_subd_subdivide_stub():
    try:
        subd_subdivide(None)
        assert False
    except NotImplementedError:
        pass


# ── mesh_to_nurbs ─────────────────────────────────────────────────────────────

def test_mesh_to_nurbs_from_face_valid():
    b = box(40, 30, 20)
    top_face = b.shape.Faces[0]
    s = mesh_to_nurbs(top_face)
    assert s.shape.isValid()

def test_mesh_to_nurbs_area_positive():
    b = box(40, 30, 20)
    top_face = b.shape.Faces[0]
    s = mesh_to_nurbs(top_face)
    assert s.shape.Area > 0

def test_mesh_to_nurbs_from_partikusshape():
    b = box(40, 30, 20)
    # pass PartikusShape wrapping a box solid
    s = mesh_to_nurbs(b, patch_size="coarse")
    assert s.shape.isValid()

def test_mesh_to_nurbs_bad_patch_size():
    b = box(20, 20, 10)
    try:
        mesh_to_nurbs(b.shape.Faces[0], patch_size="huge")
        assert False, "expected ValueError"
    except ValueError:
        pass

def test_subd_to_nurbs_stub():
    try:
        subd_to_nurbs(None)
        assert False
    except NotImplementedError:
        pass


# ── analyze_curvature ─────────────────────────────────────────────────────────

def test_analyze_curvature_mean():
    s = surface_from_points(_make_grid())
    info = analyze_curvature(s, mode="mean")
    assert "mean" in info
    assert "min" in info and "max" in info
    assert info["sample_count"] > 0

def test_analyze_curvature_gaussian():
    s = surface_from_points(_make_grid())
    info = analyze_curvature(s, mode="gaussian")
    assert "mean" in info

def test_analyze_curvature_flat_surface():
    grid = [[(float(i)*10, float(j)*10, 0.0) for j in range(4)] for i in range(4)]
    s = surface_from_points(grid)
    info = analyze_curvature(s, mode="mean")
    assert _approx(abs(info["mean"]), 0.0, tol=0.01)

def test_analyze_curvature_bad_mode():
    s = surface_from_points(_make_grid())
    try:
        analyze_curvature(s, mode="zebra")
        assert False
    except ValueError:
        pass


# ── analyze_draft ─────────────────────────────────────────────────────────────

def test_analyze_draft_box():
    b = box(40, 30, 20)
    info = analyze_draft(b, pull_direction=(0, 0, 1))
    assert "faces" in info
    assert len(info["faces"]) == 6
    assert "min_draft_deg" in info

def test_analyze_draft_min_max_range():
    b = box(40, 30, 20)
    info = analyze_draft(b, pull_direction=(0, 0, 1))
    assert info["min_draft_deg"] <= info["max_draft_deg"]

def test_analyze_draft_cylinder():
    c = cylinder(diameter=20, height=30)
    info = analyze_draft(c, pull_direction=(0, 0, 1))
    assert info["min_draft_deg"] >= 0

def test_analyze_draft_zero_pull():
    b = box(20, 20, 20)
    try:
        analyze_draft(b, pull_direction=(0, 0, 0))
        assert False
    except ValueError:
        pass


# ── analyze_deviation ─────────────────────────────────────────────────────────

def test_analyze_deviation_identical():
    s = surface_from_points(_make_grid(z_amp=0))
    # compare to itself — should be near-zero deviation
    info = analyze_deviation(s, s, sample_count=4)
    assert _approx(info["max_deviation"], 0.0, tol=0.1)

def test_analyze_deviation_offset():
    grid = [[(float(i)*5, float(j)*5, 0.0) for j in range(4)] for i in range(4)]
    s = surface_from_points(grid)
    ref = offset_surface(s, 3.0)
    info = analyze_deviation(s, ref, sample_count=5)
    assert _approx(info["mean_deviation"], 3.0, tol=0.5)

def test_analyze_deviation_keys():
    s = surface_from_points(_make_grid(z_amp=0))
    info = analyze_deviation(s, s, sample_count=3)
    for k in ("min_deviation","max_deviation","mean_deviation","rms_deviation","sample_count"):
        assert k in info

def test_analyze_zebra_stub():
    try:
        analyze_zebra(None)
        assert False
    except NotImplementedError:
        pass
