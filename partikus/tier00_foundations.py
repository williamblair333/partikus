"""
Tier 0 — Foundations / Coordinate System.

Convention:
    X+  →  RIGHT / EAST
    Y+  →  FRONT / NORTH
    Z+  →  TOP   / UP

All distances in mm.  All angles in degrees (suffix _deg on parameter names).
"""

import FreeCAD as _FC
from .core.anchors import *  # re-export all anchor name constants

# ── Orientation vectors ───────────────────────────────────────────────────────

UP    = _FC.Vector(0,  0,  1)
DOWN  = _FC.Vector(0,  0, -1)
NORTH = _FC.Vector(0,  1,  0)   # +Y / FRONT
SOUTH = _FC.Vector(0, -1,  0)   # -Y / BACK
EAST  = _FC.Vector(1,  0,  0)   # +X / RIGHT
WEST  = _FC.Vector(-1, 0,  0)   # -X / LEFT

# ── Reference plane string constants (used by mirror, draft, etc.) ────────────

PLANE_XY = "XY"
PLANE_XZ = "XZ"
PLANE_YZ = "YZ"

# ── Axis vectors ──────────────────────────────────────────────────────────────

AXIS_X = _FC.Vector(1, 0, 0)
AXIS_Y = _FC.Vector(0, 1, 0)
AXIS_Z = _FC.Vector(0, 0, 1)

# ── Origin ────────────────────────────────────────────────────────────────────

ORIGIN = _FC.Vector(0, 0, 0)
