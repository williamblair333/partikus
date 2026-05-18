"""
Tier 14 — Assembly / Positioning System.

All functions return a new PartikusShape; none mutate the input.
"""

import FreeCAD

from .core.shape_wrapper import PartikusShape
from .core.anchors import CENTER, TOP, BOTTOM, LEFT, RIGHT, FRONT, BACK
from .core.transforms import rotation_from_to, placement_for_rotation


def _V(x, y, z):
    return FreeCAD.Vector(x, y, z)


def _vec(v):
    """Accept FreeCAD.Vector or (x,y,z) tuple."""
    return v if isinstance(v, FreeCAD.Vector) else FreeCAD.Vector(*v)


# ── Primitives ────────────────────────────────────────────────────────────────

def translate(shape, dx=0.0, dy=0.0, dz=0.0):
    """
    Move shape by (dx, dy, dz) mm.  Returns a new PartikusShape.

    Example:
        translate(my_box, dz=10)
    """
    m = FreeCAD.Matrix()
    m.move(_V(dx, dy, dz))
    new_fc = shape.shape.copy()
    new_fc.transformShape(m)
    new_anchors = {k: _V(v.x + dx, v.y + dy, v.z + dz)
                   for k, v in shape.anchors.items()}
    return PartikusShape(new_fc, new_anchors, dict(shape.orientations))


def rotate(shape, axis=None, angle_deg=0.0, center=None):
    """
    Rotate shape by *angle_deg* around *axis* (default Z), optionally
    about a *center* point (default world origin).  Returns a new PartikusShape.

    Args:
        shape:     PartikusShape to rotate
        axis:      rotation axis — FreeCAD.Vector or (x,y,z) tuple; default Z
        angle_deg: rotation angle in degrees
        center:    center of rotation — FreeCAD.Vector or (x,y,z); default origin

    Example:
        rotate(my_box, axis=(0,0,1), angle_deg=45)
    """
    axis   = _vec(axis)   if axis   is not None else _V(0, 0, 1)
    center = _vec(center) if center is not None else _V(0, 0, 0)

    rotation  = FreeCAD.Rotation(axis, angle_deg)
    placement = placement_for_rotation(rotation, center)

    new_fc = shape.shape.copy()
    new_fc.transformShape(placement.Matrix)
    new_anchors      = {k: placement.multVec(v)  for k, v in shape.anchors.items()}
    new_orientations = {k: rotation.multVec(v)   for k, v in shape.orientations.items()}
    return PartikusShape(new_fc, new_anchors, new_orientations)


def scale(shape, factor=1.0, fx=None, fy=None, fz=None):
    """
    Scale shape uniformly by *factor*, or non-uniformly with fx/fy/fz.

    Note: non-uniform scaling on curved surfaces may introduce approximation
    errors in the underlying NURBS representation.

    Example:
        scale(my_sphere, 2.0)
        scale(my_box, fx=2, fy=1, fz=0.5)
    """
    sx = fx if fx is not None else factor
    sy = fy if fy is not None else factor
    sz = fz if fz is not None else factor

    m = FreeCAD.Matrix()
    m.A11, m.A22, m.A33 = sx, sy, sz

    new_fc = shape.shape.copy()
    new_fc.transformShape(m)

    new_anchors = {k: _V(v.x * sx, v.y * sy, v.z * sz)
                   for k, v in shape.anchors.items()}

    new_orientations = {}
    for k, v in shape.orientations.items():
        sv = _V(v.x * sx, v.y * sy, v.z * sz)
        ln = sv.Length
        new_orientations[k] = _V(sv.x / ln, sv.y / ln, sv.z / ln) if ln > 1e-10 else sv

    return PartikusShape(new_fc, new_anchors, new_orientations)


def mirror_position(shape, plane="XY"):
    """
    Reflect shape position through *plane* without keeping the original.

    Args:
        shape: PartikusShape
        plane: "XY", "XZ", or "YZ"

    Example:
        mirror_position(bracket, "XZ")
    """
    sx, sy, sz = 1.0, 1.0, 1.0
    if plane == "XY":
        sz = -1.0
    elif plane == "XZ":
        sy = -1.0
    elif plane == "YZ":
        sx = -1.0
    else:
        raise ValueError(f"plane must be 'XY', 'XZ', or 'YZ', got {plane!r}")
    return scale(shape, fx=sx, fy=sy, fz=sz)


# ── Attach ────────────────────────────────────────────────────────────────────

def attach(child, parent, child_anchor=BOTTOM, parent_anchor=TOP,
           offset=0.0, rotation_deg=0.0):
    """
    Place *child* so that its *child_anchor* coincides with *parent*'s
    *parent_anchor*.

    The child is first rotated so its anchor's outward normal opposes the
    parent anchor's outward normal (the two surfaces face each other).
    *offset* separates them along the joining axis (mm).
    *rotation_deg* spins the child about the joining axis after placement.

    Args:
        child:         PartikusShape to position
        parent:        PartikusShape providing the reference anchor
        child_anchor:  anchor name on child (default BOTTOM)
        parent_anchor: anchor name on parent (default TOP)
        offset:        gap along joining axis in mm (default 0)
        rotation_deg:  spin of child about joining axis in degrees (default 0)

    Returns:
        Repositioned child as a new PartikusShape.

    Example:
        lid = attach(lid_shape, box_shape, child_anchor=BOTTOM, parent_anchor=TOP)
    """
    p_pos  = parent.anchors[parent_anchor]
    p_norm = parent.orientations.get(parent_anchor)
    c_pos  = child.anchors[child_anchor]
    c_norm = child.orientations.get(child_anchor)

    result = child

    # ── Step 1: align child's anchor normal to oppose parent's ──────────────
    if c_norm is not None and p_norm is not None:
        target = _V(-p_norm.x, -p_norm.y, -p_norm.z)
        r = rotation_from_to(c_norm, target)
        pl = placement_for_rotation(r, c_pos)

        new_fc = result.shape.copy()
        new_fc.transformShape(pl.Matrix)
        result = PartikusShape(
            new_fc,
            {k: pl.multVec(v) for k, v in result.anchors.items()},
            {k: r.multVec(v)  for k, v in result.orientations.items()},
        )
        c_pos  = result.anchors[child_anchor]

    # ── Step 2: spin child about joining axis ────────────────────────────────
    if rotation_deg != 0.0 and p_norm is not None:
        result = rotate(result, axis=p_norm, angle_deg=rotation_deg, center=c_pos)
        c_pos  = result.anchors[child_anchor]

    # ── Step 3: translate so child anchor lands on (parent anchor + offset) ──
    if offset != 0.0 and p_norm is not None:
        target_pos = _V(p_pos.x + p_norm.x * offset,
                        p_pos.y + p_norm.y * offset,
                        p_pos.z + p_norm.z * offset)
    else:
        target_pos = p_pos

    delta = target_pos - c_pos
    return translate(result, delta.x, delta.y, delta.z)


# ── Convenience wrappers ──────────────────────────────────────────────────────

def stack_on(child, parent, alignment=CENTER):
    """
    Attach child's BOTTOM to parent's TOP (simple stacking).

    Example:
        stack_on(lid, body)
    """
    return attach(child, parent, child_anchor=BOTTOM, parent_anchor=TOP)


_OPPOSITE = {
    TOP: BOTTOM, BOTTOM: TOP,
    FRONT: BACK, BACK: FRONT,
    LEFT: RIGHT, RIGHT: LEFT,
}


def place_beside(child, parent, side, gap=0.0):
    """
    Place *child* adjacent to *parent* on the given *side*.

    Args:
        child:  shape to position
        parent: reference shape
        side:   which side of parent to place child against
                (TOP, BOTTOM, LEFT, RIGHT, FRONT, BACK)
        gap:    separation distance in mm (default 0)

    Example:
        place_beside(spacer, bracket, side=RIGHT, gap=2)
    """
    child_anchor = _OPPOSITE[side]
    return attach(child, parent,
                  child_anchor=child_anchor,
                  parent_anchor=side,
                  offset=gap)


def align(shape_a, shape_b, axis_name, anchor=CENTER):
    """
    Align shape_a to share the same coordinate as shape_b along *axis_name*
    at the given *anchor*.

    Args:
        shape_a:   shape to move
        shape_b:   reference shape
        axis_name: "X", "Y", or "Z"
        anchor:    which anchor point to align (default CENTER)

    Example:
        align(pin, hole_body, "Z", anchor=BOTTOM)
    """
    a_pos = shape_a.anchors[anchor]
    b_pos = shape_b.anchors[anchor]
    dx = dy = dz = 0.0
    if axis_name == "X":
        dx = b_pos.x - a_pos.x
    elif axis_name == "Y":
        dy = b_pos.y - a_pos.y
    elif axis_name == "Z":
        dz = b_pos.z - a_pos.z
    else:
        raise ValueError(f"axis_name must be 'X', 'Y', or 'Z', got {axis_name!r}")
    return translate(shape_a, dx, dy, dz)


def coaxial(shape_a, shape_b):
    """Translate shape_a so its CENTER shares X and Y with shape_b's CENTER."""
    a = shape_a.anchors[CENTER]
    b = shape_b.anchors[CENTER]
    return translate(shape_a, b.x - a.x, b.y - a.y, 0)
