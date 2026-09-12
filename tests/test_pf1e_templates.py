"""
Tests for examples/pf1e_burst_templates.py.

Examples are entry points that nothing imports, so a partikus refactor can
break one silently for months. These tests pin the two things that matter:
the Pathfinder distance rule the grid outline is derived from, and the fact
that every exported part is a single valid solid that fits the print bed.

Both outline styles are covered — "circle" is the default, "grid" is the
fallback, and a change that breaks either should fail here. Heavy boolean work
is kept to the 10 ft ring (whole-part path) and the 20 ft ring (split + socket
path); the 30 ft ring is checked arithmetically, since it uses the identical
code path as 20 ft.
"""
import sys, os, math, importlib.util

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _ROOT)


def _load_example():
    """Load the example under a name that suppresses its build-and-export."""
    path = os.path.join(_ROOT, "examples", "pf1e_burst_templates.py")
    spec = importlib.util.spec_from_file_location("pf1e_templates_under_test", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


pf = _load_example()


def _eq(a, b, tol=0.01):
    return abs(a - b) < tol


# ── Pathfinder 1E distance rule ───────────────────────────────────────────────

def test_distance_orthogonal_is_linear():
    assert pf.pf1e_distance(0, 0) == 0
    assert pf.pf1e_distance(3, 0) == 3
    assert pf.pf1e_distance(0, 6) == 6

def test_distance_first_diagonal_costs_one():
    # 1-2-1 rule: the first diagonal step is 5 ft, the second is 10 ft.
    assert pf.pf1e_distance(1, 1) == 1
    assert pf.pf1e_distance(2, 2) == 3
    assert pf.pf1e_distance(3, 3) == 4
    assert pf.pf1e_distance(4, 4) == 6

def test_distance_mixed_axes():
    assert pf.pf1e_distance(4, 2) == 5
    assert pf.pf1e_distance(6, 1) == 6
    assert pf.pf1e_distance(5, 3) == 6

def test_distance_is_symmetric():
    for a in range(7):
        for b in range(7):
            assert pf.pf1e_distance(a, b) == pf.pf1e_distance(b, a)

def test_distance_rejects_negative():
    try:
        pf.pf1e_distance(-1, 0)
    except ValueError:
        return
    raise AssertionError("negative square count should raise")


# ── Affected-square sets ──────────────────────────────────────────────────────

def test_square_mode_cell_counts():
    # Hand-counted from the 1-2-1 rule for radius 2 / 4 / 6 squares.
    assert len(pf.cell_set(2, "square")) == 21
    assert len(pf.cell_set(4, "square")) == 61
    assert len(pf.cell_set(6, "square")) == 121

def test_square_mode_keeps_centre_and_clips_corners():
    cells = pf.cell_set(2, "square")
    assert (0, 0) in cells          # the miniature stands here
    assert (2, 0) in cells          # 10 ft straight out
    assert (2, 2) not in cells      # 15 ft by the diagonal rule — outside
    assert (3, 0) not in cells

def test_intersection_mode_spans_2n():
    cells = pf.cell_set(4, "intersection")
    assert max(i for i, _ in cells) == 3      # cells 0..3 on the plus side
    assert min(i for i, _ in cells) == -4
    assert (0, 0) in cells                     # no empty centre square

def test_cell_sets_have_fourfold_symmetry():
    # Congruent segments depend on this: a 90-degree rotation must map the
    # affected-square set onto itself.
    for n in (2, 4, 6):
        square = pf.cell_set(n, "square")
        assert {(-j, i) for i, j in square} == square
        crossing = pf.cell_set(n, "intersection")
        assert {(-j - 1, i) for i, j in crossing} == crossing

def test_unknown_centre_mode_rejected():
    try:
        pf.cell_set(2, "corner")
    except ValueError:
        return
    raise AssertionError("unknown CENTER_ON should raise")


# ── Circle vs grid ────────────────────────────────────────────────────────────

def test_circle_uses_literal_scale():
    # 10 ft = 2 inches, so the ring is 4 inches across.
    assert _eq(pf.outer_extent(2, "square", "circle"), 2 * pf.GRID_MM)
    assert _eq(pf.outer_extent(4, "square", "circle"), 4 * pf.GRID_MM)
    assert _eq(pf.outer_extent(6, "square", "circle"), 6 * pf.GRID_MM)

def test_grid_outline_is_larger_than_the_circle():
    # The stepped outline encloses whole squares; the circle bisects them.
    for n in (2, 4, 6):
        assert (pf.outer_extent(n, "square", "grid")
                > pf.outer_extent(n, "square", "circle"))

def test_unknown_outline_rejected():
    for call in (lambda: pf.outer_extent(2, "square", "hexagon"),
                 lambda: pf.build_band(2, "square", "hexagon")):
        try:
            call()
        except ValueError:
            continue
        raise AssertionError("unknown OUTLINE should raise")

def test_circle_misses_only_diagonal_squares():
    # The documented compromise: squares affected by the rules whose centres
    # fall outside the literal-scale circle are always off-axis ones.
    for n in (2, 4, 6):
        missed = pf.cells_missed_by_circle(n, "square")
        assert missed, "some diagonal squares should fall outside the circle"
        for i, j in missed:
            assert i != 0 and j != 0, f"({i},{j}) is on an axis — should be covered"

def test_circle_covers_every_square_on_the_axes():
    # Straight-line reach is exact: the centre of the square N out sits on the
    # circle, so nothing on an axis is lost to the approximation.
    for n in (2, 4, 6):
        r = pf.outer_extent(n, "square", "circle")
        for k in range(-n, n + 1):
            cx, cy = pf.cell_center(k, 0, "square")
            assert math.hypot(cx, cy) <= r + 0.001
            cx, cy = pf.cell_center(0, k, "square")
            assert math.hypot(cx, cy) <= r + 0.001


# ── Outline solids ────────────────────────────────────────────────────────────

def test_circle_band_is_one_valid_annulus():
    band = pf.build_band(2, "square", "circle")
    pf.verify(band, "10 ft circle band")
    bb = band.shape.BoundBox
    assert _eq(bb.XLength, 2 * 2 * pf.GRID_MM, tol=0.5)
    assert _eq(bb.ZLength, pf.THICK)

def test_circle_band_is_hollow():
    band = pf.build_band(2, "square", "circle")
    r = 2 * pf.GRID_MM
    expected = math.pi * (r ** 2 - (r - pf.BAND_W) ** 2) * pf.THICK
    assert _eq(band.shape.Volume, expected, tol=expected * 0.01)

def test_circle_band_refuses_a_radius_thinner_than_the_band():
    try:
        pf.build_circle_band(0)
    except ValueError as e:
        assert "BAND_W" in str(e)
        return
    raise AssertionError("a radius inside BAND_W should raise, not invert")

def test_concave_corners_get_patched():
    # The staircase has inward corners where two inset bars would otherwise
    # meet along a single edge and refuse to fuse. Every ring here has some.
    for n in (2, 4, 6):
        assert pf.corner_patches(pf.cell_set(n, "square"), "square")

def test_grid_band_is_one_connected_solid():
    band = pf.build_band(2, "square", "grid")
    pf.verify(band, "10 ft grid band")


# ── Printable parts, both outlines ────────────────────────────────────────────

def test_small_ring_is_whole_and_valid():
    for outline, across in (("circle", 4 * pf.GRID_MM), ("grid", 5 * pf.GRID_MM)):
        kind, part, _ = pf.build_ring(2, "square", pf.BED_MM, outline)
        assert kind == "whole", f"{outline} 10 ft should fit the bed whole"
        pf.verify(part, f"10 ft {outline}")
        bb = part.shape.BoundBox
        assert _eq(bb.XLength, across, tol=0.5)
        assert _eq(bb.ZLength, pf.THICK)

def test_large_ring_is_split_and_fits_bed():
    for outline in ("circle", "grid"):
        kind, part, whole = pf.build_ring(4, "square", pf.BED_MM, outline)
        assert kind == "segment", f"{outline} 20 ft should need splitting"
        pf.verify(part, f"20 ft {outline} segment")
        pf.verify(whole, f"20 ft {outline} assembled")
        bb = part.shape.BoundBox
        assert max(bb.XLength, bb.YLength) <= pf.BED_MM
        # A cardinal-cut quarter occupies exactly one quadrant.
        assert _eq(bb.XMin, 0.0, tol=0.05)
        assert _eq(bb.YMin, 0.0, tol=0.05)
        assert _eq(bb.XMax, pf.outer_extent(4, "square", outline), tol=0.05)

def test_pads_never_stand_proud_of_the_circle():
    # Unclipped pads would poke past the arc and break the round silhouette.
    r = pf.outer_extent(4, "square", "circle")
    for pad in pf.pad_solids(4, "square", "circle"):
        for v in pad.shape.Vertexes:
            assert math.hypot(v.X, v.Y) <= r + 0.01

def test_segment_is_a_quarter_of_the_ring():
    for outline in ("circle", "grid"):
        _, part, whole = pf.build_ring(4, "square", pf.BED_MM, outline)
        assert _eq(part.shape.Volume, whole.shape.Volume / 4, tol=1.0)

def test_thirty_foot_quarter_fits_the_bed():
    # Arithmetic only — same code path as the 20 ft ring, which is built above.
    for outline in ("circle", "grid"):
        quarter = pf.outer_extent(6, "square", outline)
        assert quarter <= pf.BED_MM, f"{outline} 30 ft quarter is {quarter:.1f} mm"
        assert 2 * quarter > pf.BED_MM, "30 ft should need splitting at all"

def test_circle_gains_bed_margin_over_the_grid():
    # The whole point of the switch: round parts are smaller.
    assert (pf.outer_extent(6, "square", "circle")
            < pf.outer_extent(6, "square", "grid"))

def test_oversize_radius_is_refused_not_silently_shrunk():
    try:
        pf.build_ring(6, "square", 100.0, "circle")
    except ValueError as e:
        assert "bed" in str(e)
        return
    raise AssertionError("a segment larger than the bed should raise")


# ── Joint and centring parts ──────────────────────────────────────────────────

def test_joint_key_is_valid_and_thin():
    key = pf.verify(pf.joint_key(), "joint key")
    bb = key.shape.BoundBox
    assert _eq(bb.YLength, pf.KEY_LEN, tol=0.05)
    assert _eq(bb.XLength, pf.KEY_END_W, tol=0.05)
    assert _eq(bb.ZLength, pf.THICK)

def test_key_is_smaller_than_its_socket():
    # Otherwise the bowtie will not seat no matter how hard you press.
    key = pf.bowtie_profile().BoundBox
    socket = pf.bowtie_profile(pf.KEY_CLEAR).BoundBox
    assert _eq(socket.XLength - key.XLength, 2 * pf.KEY_CLEAR, tol=0.001)
    assert _eq(socket.YLength - key.YLength, 2 * pf.KEY_CLEAR, tol=0.001)

def test_centre_collar_accepts_a_one_inch_base():
    collar = pf.verify(pf.centre_collar(), "centre collar")
    bb = collar.shape.BoundBox
    assert pf.COLLAR_OPEN >= pf.GRID_MM, "opening must clear a 1-inch base"
    assert _eq(bb.XLength, pf.COLLAR_OPEN + 2 * pf.COLLAR_BAND, tol=0.05)
    assert _eq(bb.ZLength, pf.THICK)


# ── Guards ────────────────────────────────────────────────────────────────────

def test_verify_rejects_a_disconnected_shape():
    from partikus.tier01_primitives import box
    from partikus.tier09_boolean import union
    from partikus.tier14_assembly import translate
    apart = union(box(5, 5, 5), translate(box(5, 5, 5), dx=50))
    try:
        pf.verify(apart, "two islands")
    except ValueError as e:
        assert "solid" in str(e)
        return
    raise AssertionError("verify should reject a multi-solid shape")

def test_importing_the_example_does_not_build_and_export():
    # The example guards its main() on __name__ == "pf1e_burst_templates",
    # which freecadcmd sets when running the file directly. Loading it under
    # any other name must skip the build — otherwise every test run would
    # rewrite examples/out/ as a side effect.
    assert pf.__name__ == "pf1e_templates_under_test"
    assert callable(pf.main)

def test_default_outline_is_the_circle():
    assert pf.OUTLINE == "circle"
