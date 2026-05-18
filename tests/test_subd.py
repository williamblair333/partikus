"""
Tests for Tier 15B/C SubD — SubDMesh engine, subd_* functions,
subd_to_nurbs, mesh_to_subd, analyze_zebra, analyze_reflection.
"""

import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from partikus.subd_mesh import (
    SubDMesh, cube_mesh, sphere_mesh, cylinder_mesh, cone_mesh, torus_mesh,
)
from partikus.tier15b_subd import (
    subd_primitive, subd_push_pull, subd_insert_loop,
    subd_bevel_edge, subd_bevel_vertex, subd_bridge,
    subd_subdivide, subd_crease, subd_symmetry,
    subd_soft_select, subd_sculpt_brush,
)
from partikus.tier15c_conversion import subd_to_nurbs, nurbs_to_subd, mesh_to_subd
from partikus.tier15d_analysis import analyze_zebra, analyze_reflection
from partikus.core.shape_wrapper import PartikusShape
from partikus import box, surface_from_points


def _approx(a, b, tol=1e-3):
    return abs(a - b) <= tol


# ── SubDMesh primitives ────────────────────────────────────────────────────────

def test_cube_mesh_vertex_count():
    m = cube_mesh(size=10)
    assert len(m.vertices) == 8

def test_cube_mesh_face_count():
    m = cube_mesh(size=10)
    assert len(m.faces) == 6

def test_cube_mesh_all_quads():
    m = cube_mesh(size=10)
    assert all(len(f) == 4 for f in m.faces)

def test_sphere_mesh_is_subd_mesh():
    m = sphere_mesh(diameter=10)
    assert isinstance(m, SubDMesh)

def test_sphere_mesh_all_verts_on_sphere():
    r = 5.0
    m = sphere_mesh(diameter=10, seed_subdivisions=2)
    for v in m.vertices:
        d = math.sqrt(sum(c**2 for c in v))
        assert _approx(d, r, tol=1e-3), f"vertex distance {d} != {r}"

def test_cylinder_mesh_vertex_count():
    m = cylinder_mesh(diameter=10, height=20, segments=8)
    assert len(m.vertices) == 8 * 2 + 2  # two rings + two cap centres

def test_cone_mesh_face_count():
    m = cone_mesh(base_diameter=10, height=15, segments=6)
    # 6 side tris + 6 base tris
    assert len(m.faces) == 12

def test_torus_mesh_all_quads():
    m = torus_mesh(major_diameter=30, minor_diameter=8, major_seg=8, minor_seg=4)
    assert all(len(f) == 4 for f in m.faces)

def test_torus_mesh_face_count():
    m = torus_mesh(major_diameter=30, minor_diameter=8, major_seg=8, minor_seg=4)
    assert len(m.faces) == 8 * 4


# ── Catmull-Clark subdivision ──────────────────────────────────────────────────

def test_subdivide_increases_vertex_count():
    m = cube_mesh(size=10)
    n_before = len(m.vertices)
    m.subdivide(1)
    assert len(m.vertices) > n_before

def test_subdivide_cube_face_count():
    m = cube_mesh(size=10)
    m.subdivide(1)
    # 6 faces × 4 sub-quads = 24
    assert len(m.faces) == 24

def test_subdivide_twice_face_count():
    m = cube_mesh(size=10)
    m.subdivide(2)
    assert len(m.faces) == 6 * 4 * 4  # 96

def test_subdivide_all_quads():
    m = cube_mesh(size=10)
    m.subdivide(2)
    assert all(len(f) == 4 for f in m.faces)

def test_subdivide_no_degenerate_faces():
    m = cube_mesh(size=10)
    m.subdivide(1)
    for face in m.faces:
        assert len(set(face)) == len(face), "Degenerate face with repeated vertex"


# ── SubD operations ────────────────────────────────────────────────────────────

def test_crease_stores_sharpness():
    m = cube_mesh(size=10)
    m.crease([(0, 1)], sharpness=2.0)
    key = (0, 1)
    assert key in m.creases
    assert _approx(m.creases[key], 2.0)

def test_crease_subdivision_sharper_than_smooth():
    """A creased edge stays sharper than an uncreased one after subdivision."""
    m_sharp  = cube_mesh(size=10)
    m_smooth = cube_mesh(size=10)
    m_sharp.crease([(0, 1), (1, 2), (2, 3), (3, 0)], sharpness=3.0)
    m_sharp.subdivide(2)
    m_smooth.subdivide(2)
    # The total vertex spread of sharp mesh should be >= smooth (sharp stays near original)
    def _spread(verts):
        xs = [v[0] for v in verts]
        return max(xs) - min(xs)
    assert _spread(m_sharp.vertices) >= _spread(m_smooth.vertices) - 1e-3

def test_symmetry_doubles_faces():
    m = cube_mesh(size=10)
    n_before = len(m.faces)
    m.symmetry("YZ", "mirror")
    assert len(m.faces) == n_before * 2

def test_symmetry_doubles_vertices():
    m = cube_mesh(size=10)
    n_before = len(m.vertices)
    m.symmetry("XZ", "mirror")
    assert len(m.vertices) == n_before * 2

def test_soft_select_center_has_weight_one():
    m = cube_mesh(size=10)
    w = m.soft_select(0, falloff_radius=50)
    assert _approx(w.get(0, 0), 1.0)

def test_soft_select_distant_vertex_excluded():
    m = cube_mesh(size=10)
    # vertex 6 is far from vertex 0 in a 10mm cube (distance ~ 17mm)
    w = m.soft_select(0, falloff_radius=5)
    assert 6 not in w or w[6] < 0.1

def test_sculpt_pull_moves_vertices():
    m = sphere_mesh(diameter=20, seed_subdivisions=1)
    v0 = [list(v) for v in m.vertices]
    m.sculpt((0, 0, 0), "pull", strength=2, radius=15)
    moved = sum(1 for i, v in enumerate(m.vertices) if any(
        not _approx(v[c], v0[i][c], tol=0.01) for c in range(3)
    ))
    assert moved > 0


# ── subd_* API functions ───────────────────────────────────────────────────────

def test_subd_primitive_cube_returns_partikus_shape():
    ps = subd_primitive("cube", size=20)
    assert isinstance(ps, PartikusShape)

def test_subd_primitive_cube_has_subd_mesh():
    ps = subd_primitive("cube", size=20)
    assert hasattr(ps, "subd_mesh")
    assert isinstance(ps.subd_mesh, SubDMesh)

def test_subd_primitive_sphere():
    ps = subd_primitive("sphere", diameter=30)
    assert isinstance(ps, PartikusShape)
    assert ps.shape.Volume > 0

def test_subd_primitive_cylinder():
    ps = subd_primitive("cylinder", diameter=20, height=40)
    assert isinstance(ps, PartikusShape)

def test_subd_primitive_cone():
    ps = subd_primitive("cone", base_diameter=20, height=30)
    assert isinstance(ps, PartikusShape)

def test_subd_primitive_torus():
    ps = subd_primitive("torus", major_diameter=40, minor_diameter=10)
    assert isinstance(ps, PartikusShape)

def test_subd_primitive_invalid_type():
    try:
        subd_primitive("banana")
        assert False, "Expected ValueError"
    except ValueError:
        pass

def test_subd_subdivide_returns_partikus_shape():
    body = subd_primitive("cube", size=20)
    smooth = subd_subdivide(body, iterations=2)
    assert isinstance(smooth, PartikusShape)

def test_subd_subdivide_more_faces():
    body   = subd_primitive("cube", size=20)
    smooth = subd_subdivide(body, iterations=2)
    assert len(smooth.subd_mesh.faces) > len(body.subd_mesh.faces)

def test_subd_crease_and_subdivide():
    body  = subd_primitive("cube", size=20)
    creased = subd_crease(body, edges=[(0, 1), (1, 2), (2, 3), (3, 0)], sharpness=2.0)
    result  = subd_subdivide(creased, iterations=2)
    assert isinstance(result, PartikusShape)
    assert result.shape.Volume > 0

def test_subd_symmetry_mirror():
    body   = subd_primitive("cube", size=10)
    mirror = subd_symmetry(body, plane="YZ")
    assert len(mirror.subd_mesh.faces) == len(body.subd_mesh.faces) * 2

def test_subd_push_pull_returns_partikus_shape():
    body   = subd_primitive("cube", size=20)
    result = subd_push_pull(body, faces=[1], distance=5)
    assert isinstance(result, PartikusShape)

def test_subd_soft_select_returns_dict():
    body = subd_primitive("cube", size=20)
    w    = subd_soft_select(body, vertices=[0], falloff_radius=20)
    assert isinstance(w, dict)
    assert len(w) > 0

def test_subd_sculpt_brush_returns_partikus_shape():
    body   = subd_primitive("sphere", diameter=20)
    body   = subd_subdivide(body, iterations=1)
    result = subd_sculpt_brush(body, point=(0, 0, 5), brush_type="pull",
                                strength=2, radius=8)
    assert isinstance(result, PartikusShape)

def test_subd_bevel_edge_returns_partikus_shape():
    body   = subd_primitive("cube", size=20)
    result = subd_bevel_edge(body, edges=[(0, 1)], size=0.1)
    assert isinstance(result, PartikusShape)

def test_subd_bevel_vertex_returns_partikus_shape():
    body   = subd_primitive("cube", size=20)
    result = subd_bevel_vertex(body, vertices=[0], size=0.1)
    assert isinstance(result, PartikusShape)

def test_subd_bridge_returns_partikus_shape():
    body   = subd_primitive("cylinder", diameter=20, height=40, segments=6)
    n_caps = 6  # 6 cap triangles per end
    bottom = list(range(6, 6 + n_caps))
    top    = list(range(6 + n_caps, 6 + n_caps * 2))
    result = subd_bridge(body, bottom, top)
    assert isinstance(result, PartikusShape)

def test_subd_insert_loop_returns_partikus_shape():
    body   = subd_primitive("cube", size=20)
    result = subd_insert_loop(body, edge=(0, 1))
    assert isinstance(result, PartikusShape)


# ── to_part_shape ──────────────────────────────────────────────────────────────

def test_cube_to_part_shape_has_volume():
    m  = cube_mesh(size=20)
    ps = m.to_partikus_shape()
    assert ps.shape.Volume > 0

def test_cube_to_part_shape_has_anchors():
    from partikus.core.anchors import CENTER, TOP
    ps = cube_mesh(size=20).to_partikus_shape()
    assert CENTER in ps.anchors
    assert TOP in ps.anchors

def test_subdivided_cube_to_part_shape():
    m  = cube_mesh(size=20)
    m.subdivide(2)
    ps = m.to_partikus_shape()
    assert ps.shape.Volume > 0
    assert ps.shape.isValid()


# ── mesh_to_subd ───────────────────────────────────────────────────────────────

def test_mesh_to_subd_returns_subd_mesh():
    b    = box(30, 20, 10)
    subd = mesh_to_subd(b)
    assert isinstance(subd, SubDMesh)

def test_mesh_to_subd_has_vertices():
    b    = box(30, 20, 10)
    subd = mesh_to_subd(b)
    assert len(subd.vertices) > 0

def test_mesh_to_subd_has_faces():
    b    = box(30, 20, 10)
    subd = mesh_to_subd(b)
    assert len(subd.faces) > 0

def test_mesh_to_subd_preserve_features_adds_creases():
    b    = box(30, 20, 10)
    subd = mesh_to_subd(b, preserve_features=True)
    assert len(subd.creases) > 0

def test_mesh_to_subd_no_creases_when_disabled():
    b    = box(30, 20, 10)
    subd = mesh_to_subd(b, preserve_features=False)
    assert len(subd.creases) == 0

def test_mesh_to_subd_then_subdivide():
    b      = box(20, 20, 20)
    subd   = mesh_to_subd(b, preserve_features=True)
    subd.subdivide(1)
    ps     = subd.to_partikus_shape()
    assert ps.shape.Volume > 0


# ── subd_to_nurbs ──────────────────────────────────────────────────────────────

def test_subd_to_nurbs_returns_partikus_shape():
    body  = subd_primitive("cube", size=20)
    body  = subd_subdivide(body, iterations=2)
    nurbs = subd_to_nurbs(body)
    assert isinstance(nurbs, PartikusShape)

def test_subd_to_nurbs_has_area():
    body  = subd_primitive("cube", size=20)
    body  = subd_subdivide(body, iterations=2)
    nurbs = subd_to_nurbs(body)
    assert nurbs.shape.Area > 0


# ── nurbs_to_subd ──────────────────────────────────────────────────────────────

def _make_flat_grid(n=5, size=10):
    pts = []
    for i in range(n):
        row = []
        for j in range(n):
            row.append([i * size / (n - 1) - size / 2,
                        j * size / (n - 1) - size / 2,
                        0.0])
        pts.append(row)
    return pts

def test_nurbs_to_subd_returns_subd_mesh():
    grid = _make_flat_grid()
    surf = surface_from_points(grid)
    m    = nurbs_to_subd(surf, density="coarse")
    assert isinstance(m, SubDMesh)

def test_nurbs_to_subd_coarse_grid():
    grid = _make_flat_grid()
    surf = surface_from_points(grid)
    m    = nurbs_to_subd(surf, density="coarse")
    assert len(m.vertices) == 4 * 4  # 4×4 grid
    assert len(m.faces)    == 3 * 3  # (n-1)² quads

def test_nurbs_to_subd_then_subdivide():
    grid = _make_flat_grid()
    surf = surface_from_points(grid)
    m    = nurbs_to_subd(surf, density="medium")
    m.subdivide(1)
    assert len(m.faces) > 0


# ── analyze_zebra ──────────────────────────────────────────────────────────────

def _flat_surf():
    grid = _make_flat_grid(n=5, size=20)
    return surface_from_points(grid)

def test_analyze_zebra_returns_dict():
    result = analyze_zebra(_flat_surf())
    assert isinstance(result, dict)

def test_analyze_zebra_has_required_keys():
    result = analyze_zebra(_flat_surf())
    for key in ("stripe_ids", "stripe_count", "continuity_hint", "sample_count"):
        assert key in result, f"Missing key: {key}"

def test_analyze_zebra_sample_count():
    result = analyze_zebra(_flat_surf(), sample_grid=4)
    assert result["sample_count"] == 4 * 4

def test_analyze_zebra_flat_surface_g1():
    result = analyze_zebra(_flat_surf(), stripe_count=8, sample_grid=4)
    assert result["continuity_hint"] == "likely_G1"


# ── analyze_reflection ────────────────────────────────────────────────────────

def test_analyze_reflection_returns_dict():
    result = analyze_reflection(_flat_surf())
    assert isinstance(result, dict)

def test_analyze_reflection_has_required_keys():
    result = analyze_reflection(_flat_surf())
    for key in ("samples", "mean_divergence", "continuity_hint", "sample_count"):
        assert key in result, f"Missing key: {key}"

def test_analyze_reflection_flat_surface_g1():
    result = analyze_reflection(_flat_surf(), sample_grid=4)
    assert result["continuity_hint"] == "likely_G1"

def test_analyze_reflection_mean_divergence_finite():
    result = analyze_reflection(_flat_surf(), sample_grid=4)
    assert math.isfinite(result["mean_divergence"])
