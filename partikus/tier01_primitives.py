"""
Tier 1 — Raw 3D Primitives.

All shapes are centered at the world origin (bounding-box center = (0,0,0)).
All dimensions in mm.  Use keyword arguments for clarity.
"""

import FreeCAD
import Part

from .core.shape_wrapper import PartikusShape
from .core.anchors import (
    CENTER, TOP, BOTTOM, FRONT, BACK, LEFT, RIGHT,
    TOP_FRONT_LEFT, TOP_FRONT_RIGHT, TOP_BACK_LEFT, TOP_BACK_RIGHT,
    BOTTOM_FRONT_LEFT, BOTTOM_FRONT_RIGHT, BOTTOM_BACK_LEFT, BOTTOM_BACK_RIGHT,
    TOP_FRONT_EDGE, TOP_BACK_EDGE, TOP_LEFT_EDGE, TOP_RIGHT_EDGE,
    BOTTOM_FRONT_EDGE, BOTTOM_BACK_EDGE, BOTTOM_LEFT_EDGE, BOTTOM_RIGHT_EDGE,
    FRONT_LEFT_EDGE, FRONT_RIGHT_EDGE, BACK_LEFT_EDGE, BACK_RIGHT_EDGE,
    TOP_RIM, BOTTOM_RIM,
)


def _V(x, y, z):
    return FreeCAD.Vector(x, y, z)


# ─────────────────────────────── BOX ─────────────────────────────────────────

def _box_anchors(l, w, h):
    hl, hw, hh = l / 2, w / 2, h / 2
    return {
        CENTER: _V(0, 0, 0),
        TOP:    _V(0, 0,  hh),
        BOTTOM: _V(0, 0, -hh),
        FRONT:  _V(0,  hw, 0),
        BACK:   _V(0, -hw, 0),
        RIGHT:  _V( hl, 0, 0),
        LEFT:   _V(-hl, 0, 0),
        # corners
        TOP_FRONT_RIGHT:   _V( hl,  hw,  hh),
        TOP_FRONT_LEFT:    _V(-hl,  hw,  hh),
        TOP_BACK_RIGHT:    _V( hl, -hw,  hh),
        TOP_BACK_LEFT:     _V(-hl, -hw,  hh),
        BOTTOM_FRONT_RIGHT: _V( hl,  hw, -hh),
        BOTTOM_FRONT_LEFT:  _V(-hl,  hw, -hh),
        BOTTOM_BACK_RIGHT:  _V( hl, -hw, -hh),
        BOTTOM_BACK_LEFT:   _V(-hl, -hw, -hh),
        # edge midpoints
        TOP_FRONT_EDGE:    _V(0,   hw,  hh),
        TOP_BACK_EDGE:     _V(0,  -hw,  hh),
        TOP_LEFT_EDGE:     _V(-hl,  0,  hh),
        TOP_RIGHT_EDGE:    _V( hl,  0,  hh),
        BOTTOM_FRONT_EDGE:  _V(0,   hw, -hh),
        BOTTOM_BACK_EDGE:   _V(0,  -hw, -hh),
        BOTTOM_LEFT_EDGE:   _V(-hl,  0, -hh),
        BOTTOM_RIGHT_EDGE:  _V( hl,  0, -hh),
        FRONT_LEFT_EDGE:    _V(-hl,  hw,  0),
        FRONT_RIGHT_EDGE:   _V( hl,  hw,  0),
        BACK_LEFT_EDGE:     _V(-hl, -hw,  0),
        BACK_RIGHT_EDGE:    _V( hl, -hw,  0),
    }


_BOX_ORIENTATIONS = {
    TOP:    _V(0,  0,  1),
    BOTTOM: _V(0,  0, -1),
    FRONT:  _V(0,  1,  0),
    BACK:   _V(0, -1,  0),
    RIGHT:  _V(1,  0,  0),
    LEFT:   _V(-1, 0,  0),
}


def box(length=10.0, width=10.0, height=10.0):
    """
    Axis-aligned rectangular box centered at the origin.

    Args:
        length: extent along X (mm)
        width:  extent along Y (mm)
        height: extent along Z (mm)

    Example:
        box(40, 20, 10)
    """
    shape = Part.makeBox(
        length, width, height,
        _V(-length / 2, -width / 2, -height / 2),
    )
    return PartikusShape(shape, _box_anchors(length, width, height), dict(_BOX_ORIENTATIONS))


# ─────────────────────────────── CYLINDER ────────────────────────────────────

def cylinder(diameter=10.0, height=20.0, *, radius=None):
    """
    Upright cylinder (axis along Z) centered at the origin.

    Args:
        diameter: outer diameter (mm)
        height:   height (mm)
        radius:   if given, overrides diameter

    Example:
        cylinder(diameter=20, height=50)
    """
    r = radius if radius is not None else diameter / 2
    hh = height / 2
    shape = Part.makeCylinder(r, height, _V(0, 0, -hh))
    anchors = {
        CENTER:     _V(0, 0, 0),
        TOP:        _V(0, 0,  hh),
        BOTTOM:     _V(0, 0, -hh),
        TOP_RIM:    _V(0, 0,  hh),
        BOTTOM_RIM: _V(0, 0, -hh),
    }
    orientations = {
        TOP:    _V(0, 0,  1),
        BOTTOM: _V(0, 0, -1),
    }
    return PartikusShape(shape, anchors, orientations)


# ─────────────────────────────── SPHERE ──────────────────────────────────────

def sphere(diameter=10.0, *, radius=None):
    """
    Sphere centered at the origin.

    Args:
        diameter: diameter (mm)
        radius:   if given, overrides diameter

    Example:
        sphere(diameter=25)
    """
    r = radius if radius is not None else diameter / 2
    shape = Part.makeSphere(r)
    anchors = {
        CENTER: _V(0, 0, 0),
        TOP:    _V(0, 0,  r),
        BOTTOM: _V(0, 0, -r),
        FRONT:  _V(0,  r, 0),
        BACK:   _V(0, -r, 0),
        RIGHT:  _V( r, 0, 0),
        LEFT:   _V(-r, 0, 0),
    }
    orientations = {
        TOP:    _V(0, 0,  1),
        BOTTOM: _V(0, 0, -1),
        FRONT:  _V(0,  1, 0),
        BACK:   _V(0, -1, 0),
        RIGHT:  _V(1,  0, 0),
        LEFT:   _V(-1, 0, 0),
    }
    return PartikusShape(shape, anchors, orientations)


# ─────────────────────────────── CONE ────────────────────────────────────────

def cone(base_diameter=20.0, top_diameter=0.0, height=20.0, *,
         base_radius=None, top_radius=None):
    """
    Cone or frustum centered on Z axis, centered at the origin.

    Args:
        base_diameter: diameter at z = -height/2 (mm)
        top_diameter:  diameter at z = +height/2; 0 gives a sharp point (mm)
        height:        height (mm)
        base_radius:   overrides base_diameter
        top_radius:    overrides top_diameter

    Example:
        cone(base_diameter=30, top_diameter=0, height=40)
    """
    br = base_radius if base_radius is not None else base_diameter / 2
    tr = top_radius  if top_radius  is not None else top_diameter  / 2
    hh = height / 2
    shape = Part.makeCone(br, tr, height, _V(0, 0, -hh))
    anchors = {
        CENTER: _V(0, 0, 0),
        TOP:    _V(0, 0,  hh),
        BOTTOM: _V(0, 0, -hh),
    }
    orientations = {
        TOP:    _V(0, 0,  1),
        BOTTOM: _V(0, 0, -1),
    }
    return PartikusShape(shape, anchors, orientations)


# ─────────────────────────────── TORUS ───────────────────────────────────────

def torus(major_diameter=20.0, minor_diameter=4.0, *,
          major_radius=None, minor_radius=None):
    """
    Torus (donut) centered at the origin in the XY plane.

    Args:
        major_diameter: center-to-tube-center diameter (mm)
        minor_diameter: tube diameter (mm)
        major_radius:   overrides major_diameter
        minor_radius:   overrides minor_diameter

    Example:
        torus(major_diameter=30, minor_diameter=6)
    """
    R = major_radius if major_radius is not None else major_diameter / 2
    r = minor_radius if minor_radius is not None else minor_diameter / 2
    shape = Part.makeTorus(R, r)
    anchors = {
        CENTER: _V(0, 0, 0),
        TOP:    _V(0, 0,  r),
        BOTTOM: _V(0, 0, -r),
    }
    orientations = {
        TOP:    _V(0, 0,  1),
        BOTTOM: _V(0, 0, -1),
    }
    return PartikusShape(shape, anchors, orientations)


# ─────────────────────────────── WEDGE ───────────────────────────────────────

def wedge(length=10.0, width=10.0, height=10.0):
    """
    Right-triangular ramp.  Triangle cross-section in the XZ plane,
    extruded along Y.  The slope runs from the bottom-front edge
    (x=−length/2, z=−height/2) up to the top-back edge (x=+length/2, z=+height/2).
    Bounding box is centered at the origin.

    Args:
        length: extent along X (mm)
        width:  extent along Y (mm)
        height: extent along Z (mm)

    Example:
        wedge(30, 20, 15)
    """
    # Build in local coords, then center.
    pts = [_V(0, 0, 0), _V(length, 0, 0), _V(0, 0, height), _V(0, 0, 0)]
    wire = Part.makePolygon(pts)
    face = Part.Face(wire)
    raw = face.extrude(_V(0, width, 0))

    # Centre bounding box at origin.
    bb = raw.BoundBox
    dx = -(bb.XMin + bb.XLength / 2)
    dy = -(bb.YMin + bb.YLength / 2)
    dz = -(bb.ZMin + bb.ZLength / 2)
    m = FreeCAD.Matrix()
    m.move(_V(dx, dy, dz))
    shape = raw.copy()
    shape.transformShape(m)

    hh = height / 2
    anchors = {
        CENTER: _V(0, 0, 0),
        TOP:    _V(0, 0,  hh),
        BOTTOM: _V(0, 0, -hh),
    }
    orientations = {
        BOTTOM: _V(0, 0, -1),
    }
    return PartikusShape(shape, anchors, orientations)


# ─────────────────────────────── PYRAMID ─────────────────────────────────────

def pyramid(base_length=10.0, base_width=10.0, height=10.0):
    """
    Square-base pyramid centered at the origin.

    Args:
        base_length: base extent along X (mm)
        base_width:  base extent along Y (mm)
        height:      height from base to apex (mm)

    Example:
        pyramid(20, 20, 15)
    """
    hl, hw, hh = base_length / 2, base_width / 2, height / 2

    # Vertices with base centered in XY at z = -hh, apex at z = +hh.
    v0 = _V(-hl, -hw, -hh)
    v1 = _V( hl, -hw, -hh)
    v2 = _V( hl,  hw, -hh)
    v3 = _V(-hl,  hw, -hh)
    apex = _V(0, 0, hh)

    def _face(*pts):
        return Part.Face(Part.makePolygon(list(pts) + [pts[0]]))

    # Base — CW from above so normal points −Z (outward for bottom face).
    base = _face(v0, v3, v2, v1)
    # Sides — order chosen so outward normals point away from interior.
    side0 = _face(v0, v1, apex)   # −Y face
    side1 = _face(v1, v2, apex)   # +X face
    side2 = _face(v2, v3, apex)   # +Y face
    side3 = _face(v3, v0, apex)   # −X face

    shell = Part.makeShell([base, side0, side1, side2, side3])
    solid = Part.makeSolid(shell)

    anchors = {
        CENTER: _V(0, 0, 0),
        TOP:    _V(0, 0,  hh),
        BOTTOM: _V(0, 0, -hh),
    }
    orientations = {
        TOP:    _V(0, 0,  1),
        BOTTOM: _V(0, 0, -1),
    }
    return PartikusShape(solid, anchors, orientations)


# ─────────────────────────────── DISK ────────────────────────────────────────

def disk(diameter=10.0, thickness=2.0, *, radius=None):
    """
    Flat puck (thin cylinder) centered at the origin.

    Args:
        diameter:  outer diameter (mm)
        thickness: height (mm)
        radius:    overrides diameter

    Example:
        disk(diameter=30, thickness=3)
    """
    r = radius if radius is not None else diameter / 2
    ht = thickness / 2
    shape = Part.makeCylinder(r, thickness, _V(0, 0, -ht))
    anchors = {
        CENTER:     _V(0, 0, 0),
        TOP:        _V(0, 0,  ht),
        BOTTOM:     _V(0, 0, -ht),
        TOP_RIM:    _V(0, 0,  ht),
        BOTTOM_RIM: _V(0, 0, -ht),
    }
    orientations = {
        TOP:    _V(0, 0,  1),
        BOTTOM: _V(0, 0, -1),
    }
    return PartikusShape(shape, anchors, orientations)


# ─────────────────────────────── POLYHEDRON ──────────────────────────────────

def polyhedron(vertices, faces):
    """
    Generic solid from vertex positions and face index lists.
    Bounding-box center is placed at the origin.

    Args:
        vertices: list of (x, y, z) tuples (mm)
        faces:    list of lists of 0-based vertex indices; each list defines
                  one planar polygon face.  Winding order must be consistent
                  (outward normals via right-hand rule).

    Example:
        # Tetrahedron
        import math
        polyhedron(
            [(0,0,0),(1,0,0),(0.5,math.sqrt(3)/2,0),(0.5,math.sqrt(3)/6,math.sqrt(6)/3)],
            [[0,2,1],[0,1,3],[1,2,3],[0,3,2]],
        )
    """
    verts = [_V(*v) for v in vertices]

    fc_faces = []
    for fi in faces:
        pts = [verts[i] for i in fi]
        wire = Part.makePolygon(pts + [pts[0]])
        fc_faces.append(Part.Face(wire))

    shell = Part.makeShell(fc_faces)
    raw = Part.makeSolid(shell)

    bb = raw.BoundBox
    dx = -(bb.XMin + bb.XLength / 2)
    dy = -(bb.YMin + bb.YLength / 2)
    dz = -(bb.ZMin + bb.ZLength / 2)
    m = FreeCAD.Matrix()
    m.move(_V(dx, dy, dz))
    shape = raw.copy()
    shape.transformShape(m)

    return PartikusShape(shape, {CENTER: _V(0, 0, 0)}, {})
