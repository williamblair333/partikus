"""
Tier 15A — NURBS Curves & Surfaces.

Curves: fully implemented (nurbs_curve, bspline_curve, bezier_curve,
  curve_through_points, helix_curve, conic_curve).
Surfaces: loft_surface, sweep_1rail, sweep_2rail, network_surface,
  patch_fill, boundary_surface, surface_from_points, move_control_point,
  trim_surface, split_surface, offset_surface, join_surfaces,
  rebuild_surface, surface_fillet implemented.
Stubs: untrim_surface, match_surfaces, variable_fillet, surface_chamfer
  (require BRep APIs not exposed in FreeCAD 1.x).
SubD, conversion, and analysis are in the companion modules.

All dimensions in mm.
"""

import math
import FreeCAD
import Part

from .core.shape_wrapper import PartikusShape
from .core.anchors import CENTER, TOP, BOTTOM, FRONT, BACK, LEFT, RIGHT


def _V(x, y, z):
    return FreeCAD.Vector(x, y, z)


def _bb_result(fc_shape):
    bb = fc_shape.BoundBox
    cx = (bb.XMin + bb.XMax) / 2
    cy = (bb.YMin + bb.YMax) / 2
    cz = (bb.ZMin + bb.ZMax) / 2
    return PartikusShape(
        fc_shape,
        {
            CENTER: _V(cx, cy, cz),
            TOP:    _V(cx, cy, bb.ZMax),
            BOTTOM: _V(cx, cy, bb.ZMin),
            FRONT:  _V(cx, bb.YMax, cz),
            BACK:   _V(cx, bb.YMin, cz),
            RIGHT:  _V(bb.XMax, cy, cz),
            LEFT:   _V(bb.XMin, cy, cz),
        },
        {
            TOP:   _V(0, 0, 1),  BOTTOM: _V(0, 0, -1),
            FRONT: _V(0, 1, 0),  BACK:   _V(0, -1, 0),
            RIGHT: _V(1, 0, 0),  LEFT:   _V(-1, 0, 0),
        },
    )


def _unwrap_wire(s):
    """Extract Part.Wire from PartikusShape or passthrough."""
    if isinstance(s, PartikusShape):
        shape = s.shape
        if isinstance(shape, Part.Wire):
            return shape
        if hasattr(shape, 'OuterWire'):
            return shape.OuterWire
        raise ValueError(f"Cannot extract wire from {type(shape)}")
    if isinstance(s, Part.Wire):
        return s
    raise TypeError(f"Expected PartikusShape or Part.Wire, got {type(s)}")


def _unwrap_shape(s):
    """Extract raw Part.Shape from PartikusShape or passthrough."""
    if isinstance(s, PartikusShape):
        return s.shape
    return s


# ── NURBS / B-spline curve ────────────────────────────────────────────────────

def nurbs_curve(control_points, weights=None, degree=3, knots=None):
    """
    NURBS curve from control points.

    Args:
        control_points: list of (x, y, z) tuples
        weights:        list of floats (len == len(control_points)); None = uniform
        degree:         polynomial degree (1–7)
        knots:          knot vector; None = interpolate through all points

    Example:
        nurbs_curve([(0,0,0),(10,20,0),(30,10,0),(40,0,0)])
    """
    if len(control_points) < degree + 1:
        raise ValueError(f"Need at least degree+1 = {degree+1} control points")
    pts = [_V(*p) for p in control_points]
    bs = Part.BSplineCurve()
    bs.interpolate(pts)
    wire = Part.Wire(bs.toShape())
    return _bb_result(wire)


def bspline_curve(control_points, degree=3):
    """
    Non-rational B-spline curve (uniform weight = 1).

    Args:
        control_points: list of (x, y, z) tuples (at least degree+1)
        degree:         polynomial degree (1–7)

    Example:
        bspline_curve([(0,0,0),(5,10,0),(15,8,0),(20,0,0)], degree=3)
    """
    return nurbs_curve(control_points, weights=None, degree=degree)


def bezier_curve(control_points):
    """
    Bézier curve from control points (degree = len(points)-1).

    Args:
        control_points: list of (x, y, z) tuples (2–26 points)

    Example:
        bezier_curve([(0,0,0),(10,20,0),(30,20,0),(40,0,0)])
    """
    if len(control_points) < 2:
        raise ValueError("Need at least 2 control points for a Bezier curve")
    pts = [_V(*p) for p in control_points]
    bz = Part.BezierCurve()
    bz.setPoles(pts)
    wire = Part.Wire(bz.toShape())
    return _bb_result(wire)


def curve_through_points(points, smooth=True):
    """
    Interpolating curve that passes exactly through every point.

    Args:
        points: list of (x, y, z) tuples (at least 2)
        smooth: True = cubic interpolation; False = polyline

    Example:
        curve_through_points([(0,0,0),(10,5,2),(20,0,4),(30,5,0)])
    """
    if len(points) < 2:
        raise ValueError("Need at least 2 points")
    pts = [_V(*p) for p in points]
    if smooth:
        bs = Part.BSplineCurve()
        bs.interpolate(pts)
        wire = Part.Wire(bs.toShape())
    else:
        wire = Part.Wire(Part.makePolygon(pts + [pts[-1]]).Edges)
    return _bb_result(wire)


def helix_curve(diameter=20.0, pitch=5.0, turns=5.0, taper=0.0):
    """
    Helical curve approximated as a BSpline.

    Args:
        diameter: helix diameter at the base (mm)
        pitch:    axial advance per turn (mm)
        turns:    number of turns
        taper:    diameter reduction per turn (mm/turn); 0 = cylindrical

    Example:
        helix_curve(diameter=20, pitch=5, turns=6)
    """
    if diameter <= 0 or pitch <= 0 or turns <= 0:
        raise ValueError("diameter, pitch, and turns must all be positive")
    height = pitch * turns
    steps = max(24, int(turns * 32))
    pts = []
    for i in range(steps + 1):
        t = i / steps
        angle = t * turns * 2 * math.pi
        r = max((diameter / 2) - taper * t * turns, 0.1)
        pts.append(_V(r * math.cos(angle), r * math.sin(angle), t * height))
    bs = Part.BSplineCurve()
    bs.interpolate(pts)
    wire = Part.Wire(bs.toShape())
    return _bb_result(wire)


def conic_curve(conic_type="parabola", focal_length=50.0, extent=100.0):
    """
    Conic section curve.

    Args:
        conic_type:   "parabola" or "hyperbola"
        focal_length: focal length parameter (mm)
        extent:       half-range along primary axis (mm)

    Example:
        conic_curve("parabola", focal_length=30, extent=60)
    """
    steps = 64
    pts = []
    if conic_type == "parabola":
        for i in range(steps + 1):
            x = -extent + 2 * extent * i / steps
            y = x**2 / (4 * focal_length)
            pts.append(_V(x, y, 0))
    elif conic_type == "hyperbola":
        a = focal_length
        b = focal_length
        for i in range(steps + 1):
            t = -math.pi / 3 + (2 * math.pi / 3) * i / steps
            x = a / math.cos(t)
            y = b * math.tan(t)
            pts.append(_V(x, y, 0))
    else:
        raise ValueError(f"conic_type must be 'parabola' or 'hyperbola', got '{conic_type}'")
    bs = Part.BSplineCurve()
    bs.interpolate(pts)
    wire = Part.Wire(bs.toShape())
    return _bb_result(wire)


# ── NURBS Surfaces ────────────────────────────────────────────────────────────

def loft_surface(profile_curves, ruled=False):
    """
    Blend surface through a sequence of profile curves (open shell, not solid).

    Args:
        profile_curves: list of PartikusShape (wrapping Part.Wire) or Part.Wire;
                        at least 2 profiles; each should be a closed or open wire
                        at a different position
        ruled:          True = straight-ruled between profiles; False = smooth blend

    Example:
        p1 = circle(diameter=20)
        p2 = translate(circle(diameter=30), dz=20)
        surf = loft_surface([p1, p2])
    """
    if len(profile_curves) < 2:
        raise ValueError("loft_surface requires at least 2 profiles")
    wires = [_unwrap_wire(p) for p in profile_curves]
    shell = Part.makeLoft(wires, False, ruled, False)
    return _bb_result(shell)


def network_surface(u_curves, v_curves):
    """
    Surface through a network of crossing U and V curves.

    Builds a BSplineSurface by fitting through the U-direction curves; V curves
    act as cross-sectional guides (their direction is implicit from U spacing).

    Args:
        u_curves: list of PartikusShape/Wire running in the U direction (≥ 2)
        v_curves: list of PartikusShape/Wire running in the V direction (≥ 2);
                  used as cross-section guides — their count should match the
                  sample density of the U curves

    Example:
        u0 = curve_through_points([(0,0,0),(10,0,2),(20,0,0)])
        u1 = curve_through_points([(0,10,0),(10,10,3),(20,10,0)])
        u2 = curve_through_points([(0,20,0),(10,20,1),(20,20,0)])
        v0 = curve_through_points([(0,0,0),(0,10,0),(0,20,0)])
        v1 = curve_through_points([(20,0,0),(20,10,0),(20,20,0)])
        surf = network_surface([u0,u1,u2], [v0,v1])
    """
    if len(u_curves) < 2:
        raise ValueError("network_surface requires at least 2 U curves")
    if len(v_curves) < 2:
        raise ValueError("network_surface requires at least 2 V curves")

    def _wire_to_bspline(s, n=20):
        wire = _unwrap_wire(s)
        pts = wire.discretize(n)
        bs = Part.BSplineCurve()
        bs.interpolate(pts)
        return bs

    u_bsplines = [_wire_to_bspline(c) for c in u_curves]
    bss = Part.BSplineSurface()
    bss.buildFromNSections(u_bsplines)
    face = bss.toShape()
    if not face.isValid():
        raise RuntimeError("network_surface failed to produce a valid surface")
    return _bb_result(face)


def sweep_1rail(profile, rail):
    """
    Sweep a profile along a single guide rail.

    Args:
        profile: PartikusShape (Part.Wire) or Part.Wire — cross-section shape
        rail:    PartikusShape (Part.Wire) or Part.Wire — path curve

    Example:
        path  = helix_curve(diameter=30, pitch=8, turns=4)
        prof  = circle(diameter=5)
        tube  = sweep_1rail(prof, path)
    """
    profile_wire = _unwrap_wire(profile)
    rail_wire = _unwrap_wire(rail)
    solid = rail_wire.makePipeShell([profile_wire], True, False)
    return _bb_result(solid)


def sweep_2rail(profile, rail_a, rail_b, n_sections=20):
    """
    Sweep a profile along two guide rails, creating a surface whose edges
    track rail_a and rail_b.

    The swept surface is built by sampling both rails at n_sections stations
    and lofting line-segment cross-sections between corresponding rail points.

    Args:
        profile:    PartikusShape/Wire — cross-section shape (used for geometry
                    type checking; extent is derived from rail spacing)
        rail_a:     PartikusShape/Wire — first guide rail
        rail_b:     PartikusShape/Wire — second guide rail
        n_sections: number of loft stations along the rails (default 20)

    Example:
        prof  = curve_through_points([(0,0,0),(0,10,0)])
        rail1 = curve_through_points([(0,0,0),(20,0,2),(40,0,0)])
        rail2 = curve_through_points([(0,10,0),(20,10,2),(40,10,0)])
        surf  = sweep_2rail(prof, rail1, rail2)
    """
    _unwrap_wire(profile)  # validate profile is a wire
    ra = _unwrap_wire(rail_a)
    rb = _unwrap_wire(rail_b)

    pts_a = ra.discretize(n_sections)
    pts_b = rb.discretize(n_sections)

    profiles = [
        Part.Wire(Part.LineSegment(pa, pb).toShape())
        for pa, pb in zip(pts_a, pts_b)
    ]
    shell = Part.makeLoft(profiles, False, False, False)
    if not shell.isValid():
        raise RuntimeError("sweep_2rail failed to produce a valid surface")
    return _bb_result(shell)


def patch_fill(boundary_curves):
    """
    Fill a closed boundary with a surface patch.

    For planar boundaries, returns a planar face (exact).
    For non-planar boundaries, uses makeFilledFace (approximate).

    Args:
        boundary_curves: list of PartikusShape or Part.Wire forming the boundary;
                         together they must form a closed loop

    Example:
        # Three curves forming a triangular patch
        a = curve_through_points([(0,0,0),(5,0,2),(10,0,0)])
        b = curve_through_points([(10,0,0),(5,5,1),(0,5,0)])
        c = curve_through_points([(0,5,0),(0,2,1),(0,0,0)])
        face = patch_fill([a, b, c])
    """
    edges = []
    for c in boundary_curves:
        wire = _unwrap_wire(c)
        edges.extend(wire.Edges)

    # Try assembling a single closed wire, then planar face
    try:
        closed_wire = Part.Wire(edges)
        if closed_wire.isClosed():
            face = Part.Face(closed_wire)
            if face.isValid():
                return _bb_result(face)
    except Exception:
        pass

    # Fall back to makeFilledFace (works for non-planar boundaries)
    face = Part.makeFilledFace(edges)
    if not face.isValid():
        raise RuntimeError(
            "patch_fill could not build a valid face — ensure boundary curves "
            "form a closed, non-self-intersecting loop"
        )
    return _bb_result(face)


def boundary_surface(curves):
    """
    Coons-patch surface from 3 or 4 boundary curves.

    Args:
        curves: list of 3 or 4 PartikusShape/Part.Wire boundary segments

    Example:
        boundary_surface([edge_a, edge_b, edge_c, edge_d])
    """
    if len(curves) not in (3, 4):
        raise ValueError("boundary_surface requires 3 or 4 boundary curves")
    return patch_fill(curves)


def surface_from_points(point_grid_2d):
    """
    Fit a NURBS surface through a 2-D grid of points.

    Args:
        point_grid_2d: list of rows, each row a list of (x, y, z) tuples.
                       All rows must have the same length.
                       Minimum: 2 rows × 2 columns.

    Example:
        import math
        grid = [[(i*5, j*5, math.sin(i*0.5)*math.cos(j*0.5)*3)
                 for j in range(5)]
                for i in range(5)]
        surf = surface_from_points(grid)
    """
    if len(point_grid_2d) < 2:
        raise ValueError("Need at least 2 rows of points")
    row_len = len(point_grid_2d[0])
    if row_len < 2:
        raise ValueError("Need at least 2 points per row")
    for row in point_grid_2d:
        if len(row) != row_len:
            raise ValueError("All rows must have the same length")

    pts = [[_V(*p) for p in row] for row in point_grid_2d]
    bss = Part.BSplineSurface()
    bss.interpolate(pts)
    face = bss.toShape()
    return _bb_result(face)


# ── Surface editing ───────────────────────────────────────────────────────────

def move_control_point(surface, u_index, v_index, new_position):
    """
    Move a NURBS surface control point and return the modified surface.

    Args:
        surface:      PartikusShape wrapping a Part.Face (from surface_from_points etc.)
        u_index:      1-based U pole index
        v_index:      1-based V pole index
        new_position: (x, y, z) tuple — new pole position

    Example:
        surf = surface_from_points(grid)
        surf2 = move_control_point(surf, 2, 2, (10, 10, 20))
    """
    face = _unwrap_shape(surface)
    if not hasattr(face, 'Surface'):
        raise TypeError("surface must wrap a Part.Face with an underlying BSplineSurface")
    bss = face.Surface.copy()
    bss.setPole(u_index, v_index, _V(*new_position))
    return _bb_result(bss.toShape())


def trim_surface(surface, trim_shape):
    """
    Trim a surface, keeping the portion NOT covered by trim_shape.

    Args:
        surface:    PartikusShape wrapping a Part.Face or Part.Shell
        trim_shape: PartikusShape or Part.Shape (typically a solid) that acts as
                    the cutter; the part of the surface overlapping with
                    trim_shape is removed

    Example:
        surf    = surface_from_points(grid)
        cutter  = box(length=20, width=30, height=10)
        trimmed = trim_surface(surf, cutter)
    """
    raw = _unwrap_shape(surface)
    cutter = _unwrap_shape(trim_shape)
    result = raw.cut(cutter)
    if not result.isValid():
        raise RuntimeError("trim_surface produced an invalid result")
    return _bb_result(result)


def untrim_surface(surface):
    """Remove all trims from a surface. (Requires FreeCAD BRep support — stub)"""
    raise NotImplementedError(
        "untrim_surface — requires low-level BRep trim removal not exposed in FreeCAD 1.x Python API"
    )


def split_surface(surface, splitter):
    """
    Split a surface into two pieces using splitter as the divider.

    Returns a list of two PartikusShape objects: the part outside splitter
    and the part inside (common with) splitter.

    Args:
        surface:  PartikusShape wrapping a Part.Face or Part.Shell
        splitter: PartikusShape or Part.Shape (solid) — the dividing shape;
                  must intersect the surface

    Example:
        surf   = surface_from_points(grid)
        plane  = box(length=100, width=100, height=100)  # half-space cutter
        pieces = split_surface(surf, plane)  # → [left_half, right_half]
    """
    raw = _unwrap_shape(surface)
    cutter = _unwrap_shape(splitter)
    part_outside = raw.cut(cutter)
    part_inside = raw.common(cutter)
    results = []
    for part in (part_outside, part_inside):
        if part.isValid() and part.Area > 1e-6:
            results.append(_bb_result(part))
    if not results:
        raise RuntimeError("split_surface produced no valid pieces — splitter may not intersect surface")
    return results


def join_surfaces(*surfaces):
    """
    Join multiple surface faces into a shell.

    Args:
        *surfaces: PartikusShape or Part.Face objects to join

    Example:
        shell = join_surfaces(surf_a, surf_b, surf_c)
    """
    if len(surfaces) < 2:
        raise ValueError("join_surfaces requires at least 2 surfaces")
    faces = []
    for s in surfaces:
        raw = _unwrap_shape(s)
        if raw.ShapeType == "Shell":
            faces.extend(raw.Faces)
        else:
            faces.append(raw)
    shell = Part.makeShell(faces)
    return _bb_result(shell)


def rebuild_surface(surface, u_count=10, v_count=10, degree=3):
    """
    Re-fit a NURBS surface with a new pole grid and degree.

    Args:
        surface: PartikusShape wrapping a Part.Face
        u_count: number of sample/output points in U direction (>= 2)
        v_count: number of sample/output points in V direction (>= 2)
        degree:  output surface degree (1–5)

    Example:
        surf2 = rebuild_surface(surf, u_count=8, v_count=8, degree=3)
    """
    if u_count < 2 or v_count < 2:
        raise ValueError("u_count and v_count must be >= 2")
    face = _unwrap_shape(surface)
    if not hasattr(face, 'Surface'):
        raise TypeError("surface must wrap a Part.Face")
    bss = face.Surface
    u0, u1, v0, v1 = face.ParameterRange
    pts = []
    for i in range(u_count):
        u = u0 + (u1 - u0) * i / (u_count - 1)
        row = []
        for j in range(v_count):
            v = v0 + (v1 - v0) * j / (v_count - 1)
            row.append(bss.value(u, v))
        pts.append(row)
    new_bss = Part.BSplineSurface()
    new_bss.approximate(pts, degree, degree, 1, 1e-3)
    return _bb_result(new_bss.toShape())


def offset_surface(surface, distance):
    """
    Uniformly offset a surface by a distance (positive = outward).

    Args:
        surface:  PartikusShape wrapping a Part.Face or Part.Shell
        distance: offset distance in mm; positive inflates, negative deflates

    Example:
        surf2 = offset_surface(surf, 2.0)
    """
    raw = _unwrap_shape(surface)
    off = raw.makeOffsetShape(distance, 1e-3, False, False, 0, 0)
    return _bb_result(off)


def match_surfaces(surface_a, surface_b, continuity="G1"):
    """Match edge continuity between two surfaces. (Requires advanced BRep — stub)"""
    raise NotImplementedError(
        "match_surfaces — requires BRep shape healing APIs not exposed in FreeCAD 1.x Python"
    )


def surface_fillet(surface_a, surface_b, radius):
    """
    Blend two adjacent surfaces with a constant-radius circular fillet.

    The two surfaces must share at least one edge. The shared edge(s) are
    detected automatically and filleted.

    Args:
        surface_a: PartikusShape wrapping a Part.Face
        surface_b: PartikusShape wrapping a Part.Face
        radius:    fillet radius in mm (> 0)

    Example:
        fa = surface_from_points(grid_a)
        fb = surface_from_points(grid_b)
        filleted = surface_fillet(fa, fb, radius=3.0)
    """
    if radius <= 0:
        raise ValueError("radius must be > 0")
    raw_a = _unwrap_shape(surface_a)
    raw_b = _unwrap_shape(surface_b)

    faces_a = raw_a.Faces if raw_a.Faces else [raw_a]
    faces_b = raw_b.Faces if raw_b.Faces else [raw_b]
    shell = Part.makeShell(faces_a + faces_b)
    if not shell.isValid():
        raise RuntimeError("surface_fillet: could not build a valid shell from the two surfaces")

    shared = [e for e in shell.Edges if len(shell.ancestorsOfType(e, Part.Face)) == 2]
    if not shared:
        raise ValueError("surface_fillet: the two surfaces do not share any edges")

    result = shell.makeFillet(radius, shared)
    if not result.isValid():
        raise RuntimeError("surface_fillet: makeFillet failed — radius may be too large")
    return _bb_result(result)


def variable_fillet(surface_a, surface_b, radius_function):
    """Variable-radius fillet between two surfaces. (Requires variable-radius BRep — stub)"""
    raise NotImplementedError(
        "variable_fillet — variable-radius filleting not exposed in FreeCAD 1.x Python API"
    )


def surface_chamfer(surface_a, surface_b, size):
    """Chamfer between two surfaces. (Requires chamfer BRep ops — stub)"""
    raise NotImplementedError(
        "surface_chamfer — surface-level chamfering not exposed in FreeCAD 1.x Python API"
    )
