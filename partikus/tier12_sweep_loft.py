"""
Tier 12 — Sweep / Loft Operations.

Generate 3D solids from 2D profiles (Part.Wire objects from Tier 3).
All results are bounding-box centred at the origin.

Coordinate note:
    Tier 3 profiles live in the XY plane.
    For revolve around Z, build your profile in the XZ plane
    using polyline() with Y=0 coordinates.
"""

import FreeCAD
import Part

from .core.shape_wrapper import PartikusShape
from .core.anchors import CENTER, TOP, BOTTOM, FRONT, BACK, LEFT, RIGHT
from .tier03_profiles_2d import circle as _circle_profile


def _V(x, y, z):
    return FreeCAD.Vector(x, y, z)


def _to_wire(profile):
    """Accept Part.Wire, Part.Edge, or a list of edges; return Part.Wire."""
    if isinstance(profile, Part.Wire):
        return profile
    if isinstance(profile, Part.Edge):
        return Part.Wire([profile])
    if isinstance(profile, (list, tuple)):
        return Part.Wire(list(profile))
    raise TypeError(f"Expected Part.Wire or Part.Edge, got {type(profile).__name__}")


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
            TOP:   _V(0, 0, 1), BOTTOM: _V(0, 0, -1),
            FRONT: _V(0, 1, 0), BACK:   _V(0, -1, 0),
            RIGHT: _V(1, 0, 0), LEFT:   _V(-1, 0, 0),
        },
    )


def _centre(fc_shape):
    """Translate shape so its bounding-box centre is at the world origin."""
    bb = fc_shape.BoundBox
    dx = -(bb.XMin + bb.XMax) / 2
    dy = -(bb.YMin + bb.YMax) / 2
    dz = -(bb.ZMin + bb.ZMax) / 2
    if abs(dx) + abs(dy) + abs(dz) < 1e-6:
        return fc_shape
    m = FreeCAD.Matrix()
    m.move(_V(dx, dy, dz))
    s = fc_shape.copy()
    s.transformShape(m)
    return s


# ── Extrude ───────────────────────────────────────────────────────────────────

def extrude(profile_2d, height, taper_angle_deg=0):
    """
    Extrude a closed 2D profile upward by *height* mm.
    Result is centred at origin.

    Args:
        profile_2d:     Part.Wire from Tier 3 (must be closed and planar)
        height:         extrusion height (mm)
        taper_angle_deg: not yet implemented; must be 0

    Example:
        extrude(rectangle(20, 30), height=10)
        extrude(circle(15), height=25)
        extrude(regular_polygon(6, diameter=12), height=20)
    """
    if taper_angle_deg != 0:
        raise NotImplementedError("taper_angle_deg not yet implemented")
    wire = _to_wire(profile_2d)
    face = Part.Face(wire)
    raw  = face.extrude(_V(0, 0, height))
    return _bb_result(_centre(raw))


# ── Revolve ───────────────────────────────────────────────────────────────────

def revolve(profile_2d, axis=None, angle_deg=360.0):
    """
    Revolve a 2D profile around an axis through the world origin.
    Result is centred at origin.

    Tip: for axisymmetric solids (cylinder-like shapes), build your profile in
    the XZ plane using polyline() with Y=0 coordinates, then revolve around Z.

    Args:
        profile_2d: Part.Wire (must be planar; need not be closed for angle_deg < 360)
        axis:       axis of revolution as FreeCAD.Vector or (x,y,z); default Z
        angle_deg:  sweep angle in degrees (default 360 = full revolution)

    Example:
        # Hollow cylinder from XZ-plane profile
        prof = polyline([(5,0,0),(15,0,0),(15,0,20),(5,0,20)], closed=True)
        revolve(prof, axis=(0,0,1), angle_deg=360)
    """
    if axis is None:
        axis = _V(0, 0, 1)
    elif not isinstance(axis, FreeCAD.Vector):
        axis = FreeCAD.Vector(*axis)

    wire = _to_wire(profile_2d)
    face = Part.Face(wire)
    raw  = face.revolve(_V(0, 0, 0), axis, angle_deg)
    return _bb_result(_centre(raw))


# ── Sweep ─────────────────────────────────────────────────────────────────────

def sweep(profile_2d, path_curve, twist_deg=0):
    """
    Sweep a closed 2D cross-section profile along a 3D path.
    Result is centred at origin.

    Args:
        profile_2d: Part.Wire cross-section (must be closed)
        path_curve: Part.Wire spine to sweep along
        twist_deg:  not yet implemented; must be 0

    Example:
        # Straight pipe
        import Part, FreeCAD
        path = Part.Wire([Part.LineSegment(FreeCAD.Vector(0,0,0),
                                           FreeCAD.Vector(0,0,50)).toShape()])
        sweep(circle(10), path)
    """
    if twist_deg != 0:
        raise NotImplementedError("twist_deg not yet implemented")
    profile_wire = _to_wire(profile_2d)
    path_wire    = _to_wire(path_curve)
    face = Part.Face(profile_wire)
    raw  = path_wire.makePipe(face)
    return _bb_result(_centre(raw))


# ── Loft ──────────────────────────────────────────────────────────────────────

def loft(profile_list, closed=False, ruled=False):
    """
    Blend a solid through a sequence of cross-section profiles.
    Result is centred at origin.

    Profiles must be placed at different positions before calling loft.
    All profiles must be closed wires.

    Args:
        profile_list: list of Part.Wire objects at different positions
        closed:       if True, blend the last profile back to the first
        ruled:        if True, use ruled (linear) blending between profiles

    Example:
        import FreeCAD
        w1 = circle(20)  # at z=0 (default from Tier 3)
        # Move second profile to z=30
        m = FreeCAD.Matrix(); m.move(FreeCAD.Vector(0, 0, 30))
        w2 = circle(10).copy(); w2.transformShape(m)
        loft([w1, w2])
    """
    wires = [_to_wire(p) for p in profile_list]
    raw   = Part.makeLoft(wires, True, ruled, closed)
    return _bb_result(_centre(raw))


# ── Pipe ──────────────────────────────────────────────────────────────────────

def pipe(path_curve, diameter=10.0, wall_thickness=0.0):
    """
    Circular pipe (or tube) swept along a 3D path.  Result is centred at origin.

    Args:
        path_curve:     Part.Wire spine
        diameter:       outer diameter of the pipe (mm)
        wall_thickness: if > 0, creates a hollow pipe (tube); (mm)

    Example:
        import Part, FreeCAD
        path = Part.Wire([Part.LineSegment(FreeCAD.Vector(0,0,-25),
                                           FreeCAD.Vector(0,0, 25)).toShape()])
        pipe(path, diameter=12, wall_thickness=2)
    """
    from .tier09_boolean import difference as _diff
    outer = sweep(_circle_profile(diameter), path_curve)
    if wall_thickness > 0:
        inner_d = diameter - 2 * wall_thickness
        if inner_d <= 0:
            raise ValueError("wall_thickness too large for pipe diameter")
        inner = sweep(_circle_profile(inner_d), path_curve)
        return _diff(outer, inner)
    return outer
