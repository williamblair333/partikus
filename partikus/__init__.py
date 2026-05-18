"""
Partikus — parametric CAD toolkit.  Every part has its place.

Usage (inside FreeCAD / freecadcmd):

    from partikus import box, cylinder, difference, attach, TOP, BOTTOM
    body = box(40, 20, 10)
    hole = cylinder(diameter=8, height=15)
    part = difference(body, hole)

All dimensions are in mm unless a parameter name carries a suffix:
    _deg    → degrees
    _count  → dimensionless integer count
"""

# Coordinate / anchor constants
from .tier00_foundations import (
    UP, DOWN, NORTH, SOUTH, EAST, WEST,
    PLANE_XY, PLANE_XZ, PLANE_YZ,
    AXIS_X, AXIS_Y, AXIS_Z, ORIGIN,
)
from .core.anchors import (
    CENTER, TOP, BOTTOM, FRONT, BACK, LEFT, RIGHT,
    TOP_FRONT_LEFT, TOP_FRONT_RIGHT, TOP_BACK_LEFT, TOP_BACK_RIGHT,
    BOTTOM_FRONT_LEFT, BOTTOM_FRONT_RIGHT, BOTTOM_BACK_LEFT, BOTTOM_BACK_RIGHT,
    TOP_FRONT_EDGE, TOP_BACK_EDGE, TOP_LEFT_EDGE, TOP_RIGHT_EDGE,
    BOTTOM_FRONT_EDGE, BOTTOM_BACK_EDGE, BOTTOM_LEFT_EDGE, BOTTOM_RIGHT_EDGE,
    FRONT_LEFT_EDGE, FRONT_RIGHT_EDGE, BACK_LEFT_EDGE, BACK_RIGHT_EDGE,
    TOP_RIM, BOTTOM_RIM,
)

# Tier 1 — primitives
from .tier01_primitives import (
    box, cylinder, sphere, cone, torus, wedge, pyramid, disk, polyhedron,
)

# Tier 2 — enhanced primitives
from .tier02_enhanced import (
    rounded_box, chamfered_box, rounded_cylinder,
    tube, tube_by_wall, hollow_box,
    hemisphere, spherical_cap, frustum,
    prism, rounded_prism, stepped_cylinder,
)

# Tier 3 — 2D profiles
from .tier03_profiles_2d import (
    rectangle, rounded_rectangle, chamfered_rectangle,
    circle, ellipse, regular_polygon, star,
    slot, teardrop, arc, polyline,
)

# Tier 9 — booleans
from .tier09_boolean import (
    union, fuse,
    difference, cut,
    intersection, intersect,
)

# Tier 10 — modifiers
from .tier10_modifiers import (
    fillet, chamfer, shell, offset,
)

# Tier 11 — patterns
from .tier11_patterns import (
    linear_array, grid_array, polar_array, mirror,
)

# Tier 12 — sweep / loft
from .tier12_sweep_loft import (
    extrude, revolve, sweep, loft, pipe,
)

# Tier 14 — assembly
from .tier14_assembly import (
    translate, rotate, scale, mirror_position,
    attach, stack_on, place_beside, align, coaxial,
)

# Core type
from .core.shape_wrapper import PartikusShape

__all__ = [
    # foundations
    "UP", "DOWN", "NORTH", "SOUTH", "EAST", "WEST",
    "PLANE_XY", "PLANE_XZ", "PLANE_YZ",
    "AXIS_X", "AXIS_Y", "AXIS_Z", "ORIGIN",
    # anchors
    "CENTER", "TOP", "BOTTOM", "FRONT", "BACK", "LEFT", "RIGHT",
    "TOP_FRONT_LEFT", "TOP_FRONT_RIGHT", "TOP_BACK_LEFT", "TOP_BACK_RIGHT",
    "BOTTOM_FRONT_LEFT", "BOTTOM_FRONT_RIGHT", "BOTTOM_BACK_LEFT", "BOTTOM_BACK_RIGHT",
    "TOP_FRONT_EDGE", "TOP_BACK_EDGE", "TOP_LEFT_EDGE", "TOP_RIGHT_EDGE",
    "BOTTOM_FRONT_EDGE", "BOTTOM_BACK_EDGE", "BOTTOM_LEFT_EDGE", "BOTTOM_RIGHT_EDGE",
    "FRONT_LEFT_EDGE", "FRONT_RIGHT_EDGE", "BACK_LEFT_EDGE", "BACK_RIGHT_EDGE",
    "TOP_RIM", "BOTTOM_RIM",
    # tier 1
    "box", "cylinder", "sphere", "cone", "torus", "wedge", "pyramid", "disk", "polyhedron",
    # tier 2
    "rounded_box", "chamfered_box", "rounded_cylinder",
    "tube", "tube_by_wall", "hollow_box",
    "hemisphere", "spherical_cap", "frustum",
    "prism", "rounded_prism", "stepped_cylinder",
    # tier 3
    "rectangle", "rounded_rectangle", "chamfered_rectangle",
    "circle", "ellipse", "regular_polygon", "star",
    "slot", "teardrop", "arc", "polyline",
    # tier 9
    "union", "fuse", "difference", "cut", "intersection", "intersect",
    # tier 10
    "fillet", "chamfer", "shell", "offset",
    # tier 11
    "linear_array", "grid_array", "polar_array", "mirror",
    # tier 12
    "extrude", "revolve", "sweep", "loft", "pipe",
    # tier 14
    "translate", "rotate", "scale", "mirror_position",
    "attach", "stack_on", "place_beside", "align", "coaxial",
    # core
    "PartikusShape",
]
