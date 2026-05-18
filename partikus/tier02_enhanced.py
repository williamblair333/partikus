"""
Tier 2 — Enhanced Primitives.

Convenience constructors built on Tier 1 primitives and Tier 10 modifiers.
All shapes centered at origin. All dimensions in mm.
"""

import math
import FreeCAD
import Part

from .core.shape_wrapper import PartikusShape
from .core.anchors import CENTER, TOP, BOTTOM, FRONT, BACK, LEFT, RIGHT, TOP_RIM, BOTTOM_RIM
from .tier01_primitives import box, cylinder, cone, sphere
from .tier09_boolean import difference, union
from .tier10_modifiers import fillet, chamfer, shell
from .tier14_assembly import translate


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
            TOP:   _V(0, 0, 1), BOTTOM: _V(0, 0, -1),
            FRONT: _V(0, 1, 0), BACK:   _V(0, -1, 0),
            RIGHT: _V(1, 0, 0), LEFT:   _V(-1, 0, 0),
        },
    )


# ── Rounded / chamfered box ───────────────────────────────────────────────────

def rounded_box(length=10.0, width=10.0, height=10.0, fillet_radius=1.0, edges=None):
    """
    Box with rounded (filleted) edges.

    Args:
        length, width, height: dimensions (mm)
        fillet_radius: edge rounding radius (mm)
        edges: list of Part.Edge to fillet; None = fillet all 12 edges

    Example:
        rounded_box(40, 30, 15, fillet_radius=3)
    """
    return fillet(box(length, width, height), fillet_radius, edges)


def chamfered_box(length=10.0, width=10.0, height=10.0, chamfer_size=1.0, edges=None):
    """
    Box with bevelled (chamfered) edges.

    Args:
        length, width, height: dimensions (mm)
        chamfer_size: edge bevel size (mm)
        edges: list of Part.Edge to chamfer; None = chamfer all 12 edges

    Example:
        chamfered_box(40, 30, 15, chamfer_size=2)
    """
    return chamfer(box(length, width, height), chamfer_size, edges)


# ── Rounded cylinder ──────────────────────────────────────────────────────────

def rounded_cylinder(diameter=10.0, height=20.0, fillet_radius=1.0,
                     ends="BOTH", *, radius=None):
    """
    Cylinder with filleted rim edge(s).

    Args:
        diameter:      outer diameter (mm)
        height:        height (mm)
        fillet_radius: fillet radius (mm)
        ends:          "BOTH", "TOP", or "BOTTOM"
        radius:        overrides diameter

    Example:
        rounded_cylinder(diameter=20, height=30, fillet_radius=2)
    """
    c = cylinder(diameter=diameter, height=height, radius=radius)
    rim_edges = [
        e for e in c.shape.Edges
        if isinstance(e.Curve, Part.Circle)
        and (
            ends == "BOTH"
            or (ends == "TOP"    and e.CenterOfMass.z > 0)
            or (ends == "BOTTOM" and e.CenterOfMass.z < 0)
        )
    ]
    if not rim_edges:
        return c
    return fillet(c, fillet_radius, edges=rim_edges)


# ── Tubes ─────────────────────────────────────────────────────────────────────

def tube(outer_diameter=20.0, inner_diameter=14.0, height=20.0):
    """
    Hollow cylinder (tube).

    Args:
        outer_diameter: outside diameter (mm)
        inner_diameter: bore diameter (mm)
        height:         height (mm)

    Example:
        tube(outer_diameter=25, inner_diameter=20, height=40)
    """
    outer = cylinder(diameter=outer_diameter, height=height)
    inner = cylinder(diameter=inner_diameter, height=height * 1.01)
    return difference(outer, inner)


def tube_by_wall(outer_diameter=20.0, wall_thickness=3.0, height=20.0):
    """
    Hollow cylinder specified by wall thickness instead of inner diameter.

    Args:
        outer_diameter: outside diameter (mm)
        wall_thickness: wall thickness (mm)
        height:         height (mm)

    Example:
        tube_by_wall(outer_diameter=30, wall_thickness=3, height=50)
    """
    inner_d = outer_diameter - 2 * wall_thickness
    if inner_d <= 0:
        raise ValueError("wall_thickness too large for outer_diameter")
    return tube(outer_diameter=outer_diameter, inner_diameter=inner_d, height=height)


# ── Hollow box ────────────────────────────────────────────────────────────────

def hollow_box(length=20.0, width=20.0, height=20.0,
               wall_thickness=2.0, open_face=TOP):
    """
    Open-topped (or open-sided) box with uniform wall thickness.

    Args:
        length, width, height: outer dimensions (mm)
        wall_thickness:        wall thickness (mm)
        open_face:             anchor name of the face to remove ("TOP", "BOTTOM",
                               "FRONT", "BACK", "LEFT", "RIGHT")

    Example:
        hollow_box(50, 40, 30, wall_thickness=3)
    """
    return shell(box(length, width, height), wall_thickness, [open_face])


# ── Hemisphere ────────────────────────────────────────────────────────────────

def hemisphere(diameter=10.0, *, radius=None):
    """
    Dome: upper half-sphere (flat face down). Centered at origin so the flat
    face is at z = −r and the apex is at z = +r.

    Args:
        diameter: full sphere diameter (mm)
        radius:   overrides diameter

    Example:
        hemisphere(diameter=30)
    """
    r = radius if radius is not None else diameter / 2
    raw = Part.makeSphere(r, _V(0, 0, 0), _V(0, 0, 1), 0, 90, 360)
    # raw: flat face at z=0, apex at z=r  →  centre bounding box to origin
    m = FreeCAD.Matrix()
    m.move(_V(0, 0, -r / 2))
    shape = raw.copy()
    shape.transformShape(m)
    return PartikusShape(
        shape,
        {CENTER: _V(0, 0, 0), TOP: _V(0, 0, r / 2), BOTTOM: _V(0, 0, -r / 2)},
        {TOP: _V(0, 0, 1), BOTTOM: _V(0, 0, -1)},
    )


# ── Spherical cap ─────────────────────────────────────────────────────────────

def spherical_cap(diameter=10.0, height=3.0):
    """
    A segment of a sphere: a circular cap with base *diameter* and dome *height*.

    Args:
        diameter: base circle diameter (mm)
        height:   height from flat base to apex (mm)

    Example:
        spherical_cap(diameter=20, height=5)
    """
    r_base = diameter / 2
    # Sphere radius derived from cap geometry:
    # r_sphere = (r_base² + height²) / (2 * height)
    r_sphere = (r_base ** 2 + height ** 2) / (2 * height)

    # Latitude angle of the cap base:
    # sin(θ₀) = (r_sphere − height) / r_sphere
    sin_theta = (r_sphere - height) / r_sphere
    sin_theta = max(-1.0, min(1.0, sin_theta))
    theta0_deg = math.degrees(math.asin(sin_theta))

    raw = Part.makeSphere(r_sphere, _V(0, 0, 0), _V(0, 0, 1), theta0_deg, 90, 360)
    # raw: flat face at z = r_sphere - height, apex at z = r_sphere
    # Centre: translate by -(r_sphere - height/2)
    centre_z = r_sphere - height / 2
    m = FreeCAD.Matrix()
    m.move(_V(0, 0, -centre_z))
    shape = raw.copy()
    shape.transformShape(m)

    hh = height / 2
    return PartikusShape(
        shape,
        {CENTER: _V(0, 0, 0), TOP: _V(0, 0, hh), BOTTOM: _V(0, 0, -hh)},
        {TOP: _V(0, 0, 1), BOTTOM: _V(0, 0, -1)},
    )


# ── Frustum ───────────────────────────────────────────────────────────────────

def frustum(base_diameter=20.0, top_diameter=10.0, height=20.0):
    """
    Truncated cone (frustum).  Alias for cone() with both diameters > 0.

    Example:
        frustum(base_diameter=30, top_diameter=15, height=25)
    """
    return cone(base_diameter=base_diameter,
                top_diameter=top_diameter,
                height=height)


# ── Prism ─────────────────────────────────────────────────────────────────────

def prism(sides=6, diameter=10.0, height=20.0):
    """
    Regular n-sided prism (extruded regular polygon). Centered at origin.

    Args:
        sides:    number of faces (>= 3)
        diameter: circumscribed circle diameter (mm)
        height:   height (mm)

    Example:
        prism(sides=6, diameter=10, height=20)  # hex rod
    """
    if sides < 3:
        raise ValueError("sides must be >= 3")
    r = diameter / 2
    hh = height / 2
    pts = [
        _V(r * math.cos(2 * math.pi * i / sides),
           r * math.sin(2 * math.pi * i / sides),
           -hh)
        for i in range(sides)
    ]
    pts.append(pts[0])
    wire = Part.makePolygon(pts)
    face = Part.Face(wire)
    raw = face.extrude(_V(0, 0, height))
    return PartikusShape(
        raw,
        {CENTER: _V(0, 0, 0), TOP: _V(0, 0, hh), BOTTOM: _V(0, 0, -hh)},
        {TOP: _V(0, 0, 1), BOTTOM: _V(0, 0, -1)},
    )


def rounded_prism(sides=6, diameter=10.0, height=20.0, fillet_radius=1.0):
    """
    Regular prism with filleted vertical edges.

    Example:
        rounded_prism(sides=6, diameter=20, height=30, fillet_radius=2)
    """
    p = prism(sides=sides, diameter=diameter, height=height)
    # Vertical edges: length ≈ height
    vert_edges = [e for e in p.shape.Edges
                  if abs(e.Length - height) < height * 0.01]
    if not vert_edges:
        return p
    return fillet(p, fillet_radius, edges=vert_edges)


# ── Stepped cylinder ──────────────────────────────────────────────────────────

def stepped_cylinder(diameters, heights):
    """
    Stack of coaxial cylinders with varying diameters. Centered at origin.

    Args:
        diameters: list of diameters, bottom to top (mm)
        heights:   list of heights (same length as diameters) (mm)

    Example:
        stepped_cylinder([20, 15, 10], [10, 8, 5])
    """
    if len(diameters) != len(heights):
        raise ValueError("diameters and heights must have the same length")
    if not diameters:
        raise ValueError("need at least one step")

    total_h = sum(heights)
    z = -total_h / 2  # start at bottom of centred stack

    solids = []
    for d, h in zip(diameters, heights):
        solids.append(Part.makeCylinder(d / 2, h, _V(0, 0, z)))
        z += h

    result = solids[0]
    for s in solids[1:]:
        result = result.fuse(s)

    hh = total_h / 2
    return PartikusShape(
        result,
        {CENTER: _V(0, 0, 0), TOP: _V(0, 0, hh), BOTTOM: _V(0, 0, -hh)},
        {TOP: _V(0, 0, 1), BOTTOM: _V(0, 0, -1)},
    )
