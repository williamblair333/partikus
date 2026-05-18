# Partikus — Developer Handoff

**Last updated:** 2026-05-18  
**Status:** Milestone 2 complete — 193 tests passing  
**Next milestone:** Milestone 3 — Mechanical Depth (Tiers 4, 5, 6)

This document is the single source of truth for picking up development in a new session. Read it top-to-bottom before touching any code.

---

## 1. What This Project Is

Partikus is a **Python parametric CAD toolkit** on top of FreeCAD/OpenCASCADE. Goals:

1. Comprehensive library of parametric shapes organised into 16 tiers
2. Every shape exposed through auto-generated GUI dialogs (no GUI code per function)
3. First-class anchor system for coordinate-free positioning
4. Architecture designed so an AI agent can later take an image → decompose → emit assembly script

The architecture is API-first. Dialogs call the same functions an AI would call. Same names, same parameters, same return types.

---

## 2. Environment

| Item | Value |
|---|---|
| OS | Linux (Debian-based) |
| FreeCAD | 1.1.1 AppImage |
| AppImage path | `/opt/proj/partikus/FreeCAD_1.1.1-Linux-x86_64-py311.AppImage` |
| Python | 3.11 (bundled inside AppImage) |
| freecadcmd | `squashfs-root/usr/bin/freecadcmd` (relative to working dir) |
| Working directory | `/opt/proj/partikus/` |

### Running scripts

```bash
cd /opt/proj/partikus
squashfs-root/usr/bin/freecadcmd tests/run_tests.py
squashfs-root/usr/bin/freecadcmd my_script.py
```

### Critical freecadcmd quirks

1. **stdout is captured** — `print()` output is invisible. Use `sys.stderr.write()` or `FreeCAD.Console.PrintMessage()`.
2. **`__name__` is the script filename**, not `"__main__"`. Put bare `main()` calls at module level, never under `if __name__ == "__main__":`.
3. **`--console` flag conflict** — if you try to pass `--console`, freecadcmd rejects it as a duplicate. Don't pass it.

---

## 3. Repository Layout

```
partikus/
├── README.md
├── CHANGELOG.md
├── HANDOFF.md                       ← this file
├── partikus/
│   ├── __init__.py                  # public API — import everything from here
│   ├── core/
│   │   ├── anchors.py               # anchor name string constants
│   │   ├── shape_wrapper.py         # PartikusShape class
│   │   ├── transforms.py            # rotation_from_to, placement_for_rotation
│   │   └── document.py              # FreeCAD document helpers
│   ├── tier00_foundations.py
│   ├── tier01_primitives.py
│   ├── tier02_enhanced.py
│   ├── tier03_profiles_2d.py
│   ├── tier09_boolean.py
│   ├── tier10_modifiers.py
│   ├── tier11_patterns.py
│   ├── tier12_sweep_loft.py
│   ├── tier14_assembly.py
│   └── gui/
│       ├── auto_dialog.py
│       └── workbench.py
├── tests/
│   ├── run_tests.py                 # headless runner — start here
│   ├── test_core.py
│   ├── test_tier01.py
│   ├── test_tier02.py
│   ├── test_tier03.py
│   ├── test_tier09.py
│   ├── test_tier10.py
│   ├── test_tier11.py
│   ├── test_tier12.py
│   └── test_tier14.py
└── examples/
    └── capped_cylinder.py
```

Tiers 4–8, 13, 15 are **not yet implemented** — they are specified in the original handoff (`partikus-handoff.md`) and in `README.md §Roadmap`.

---

## 4. Core Concepts You Must Understand

### PartikusShape

```python
class PartikusShape:
    __slots__ = ("shape", "anchors", "orientations")
    shape        # Part.Shape — raw OpenCASCADE geometry
    anchors      # dict[str, FreeCAD.Vector] — named world-coordinate points
    orientations # dict[str, FreeCAD.Vector] — outward normals per anchor
```

Every public function returns one of these, never a raw `Part.Shape`.

### Internal helpers (defined at top of each tier module)

```python
def _V(x, y, z):  return FreeCAD.Vector(x, y, z)
def _unwrap(s):   return s.shape if isinstance(s, PartikusShape) else s
def _bb_anchors(fc_shape) -> dict:  # computes CENTER/TOP/BOTTOM/etc from bounding box
def _bb_result(fc_shape) -> PartikusShape:  # wraps shape with _bb_anchors
def _preserve(src, new_fc_shape) -> PartikusShape:  # copy anchors from src onto new shape
```

### Anchor system

Anchor names are string constants in `core/anchors.py`. Every shape guarantees at least `CENTER`, `TOP`, `BOTTOM`, `FRONT`, `BACK`, `LEFT`, `RIGHT`. Box shapes add 8 corners + 12 edge midpoints. Cylinders add `TOP_RIM`, `BOTTOM_RIM`.

`attach()` in `tier14_assembly.py` uses these to snap shapes together without raw coordinate math.

### Coordinate convention

- X+ = RIGHT, Y+ = FRONT, Z+ = UP
- All shapes bounding-box centred at origin when first created
- All dimensions in **mm**

---

## 5. Completed Work

### Milestone 1 (2026-05-15)

- `core/` — `PartikusShape`, anchors, transforms, document management
- `tier00` — coordinate constants
- `tier01` — 9 raw primitives (box, cylinder, sphere, cone, torus, wedge, pyramid, disk, polyhedron)
- `tier09` — union/difference/intersection
- `tier14` — full assembly system (translate/rotate/scale/attach/stack_on/place_beside/align/coaxial)
- `gui/auto_dialog.py` — auto-dialog from function signature
- `gui/workbench.py` — FreeCAD workbench registration
- 70 tests

### Milestone 2 (2026-05-18)

- `tier02` — 12 enhanced primitives (rounded_box, tube, hemisphere, stepped_cylinder, etc.)
- `tier03` — 11 2D profile types returning `Part.Wire`
- `tier10` — fillet/chamfer/shell/offset
- `tier11` — linear_array/grid_array/polar_array/mirror
- `tier12` — extrude/revolve/sweep/loft/pipe
- 123 new tests → **193 total, all passing**
- Fixed: `Part.makeEllipse` doesn't exist in FreeCAD 1.1.1 — use `Part.Ellipse(center, major_r, minor_r).toShape()`

---

## 6. What to Build Next — Milestone 3

### Tier 4 — Mechanical Features

All return `PartikusShape` centred at origin.

```python
boss(diameter, height, hole_diameter=None)
counterbore_hole(thru_diameter, bore_diameter, bore_depth, depth)
countersink_hole(thru_diameter, head_diameter, head_angle_deg=82, depth)
slot_hole(length, width, depth)
keyway(width, depth, length)
rib(length, height, thickness, draft_angle_deg=0)
gusset(length, height, thickness)
flange(inner_diameter, outer_diameter, thickness, hole_pattern=None)
lip(outer_diameter, height, lip_width, lip_height)
l_bracket(length, height, thickness, width)
t_bracket(arm_length, stem_length, width, thickness)
u_bracket(length, height, width, thickness, leg_height)
tab(width, height, thickness)
slot_cutout(width, height, depth)
dovetail_pin(length, narrow_width, wide_width, height)
dovetail_slot(...)
tongue(length, width, height)
groove(length, width, depth)
living_hinge(length, thickness, hinge_width)
snap_clip(length, width, hook_height, flex_arm_length)
```

### Tier 5 — Fasteners & Standard Parts

Use ISO standard dimension tables (stored in `partikus/presets/screws.py`, `bearings.py`).

```python
# Threaded
threaded_rod(diameter, length, pitch=None, thread_form="metric")
tapped_hole(diameter, depth, pitch=None)

# Bolts
hex_bolt(diameter, length, ...)
socket_head_bolt(diameter, length)
button_head_bolt(diameter, length)
flat_head_bolt(diameter, length)

# Nuts / washers
hex_nut(diameter, ...)
flat_washer(bolt_diameter, ...)
lock_washer(bolt_diameter)

# Holes / inserts
heat_set_insert_pocket(insert_size)   # e.g. "M3", "M4"
clearance_hole(bolt_size, depth, fit="close")
screw_size_preset(name)               # returns dict with all ISO dims

# Other
standoff(diameter, length, thread_size=None)
dowel_pin(diameter, length)
```

### Tier 6 — Mechanical Components

```python
spur_gear(teeth, module, thickness, pressure_angle_deg=20)
bevel_gear(teeth, module, cone_angle_deg, thickness)
rack(teeth, module, length, height)
pulley_timing(teeth, belt_type, width)    # "GT2", "HTD"
sprocket(teeth, chain_pitch, thickness)
bearing_pocket(bearing_id, depth)         # "608", "6004", etc.
shaft_coupling(shaft1_diameter, shaft2_diameter, length)
```

### Adding a new tier — checklist

1. Create `partikus/tierXX_name.py`
2. Import `FreeCAD`, `Part`, `PartikusShape`, `_bb_result`, `_V`, `_unwrap`, `_preserve` at the top
3. Every function returns `PartikusShape`
4. Add `from .tierXX_name import (...)` to `partikus/__init__.py`
5. Add symbols to `__all__` in `__init__.py`
6. Create `tests/test_tierXX.py` with at minimum: volume test, validity test, anchor test
7. Add `"tests.test_tierXX"` to `_MODULES` in `tests/run_tests.py`
8. Add entry to `CHANGELOG.md` under `[Unreleased]`

---

## 7. Known Limitations & Gotchas

### FreeCAD 1.1.1 API surface

| What you might try | What actually works |
|---|---|
| `Part.makeEllipse(a, b)` | `Part.Ellipse(V(0,0,0), a, b).toShape()` |
| `shape.makeOffset3D(d)` | `shape.makeOffsetShape(d, 1e-3, False, False, 0, 0)` |
| `Part.makeLoft(profiles, True, False, False)` | Works — solid=True, ruled=False, closed=False |
| `path.makePipeShell([wire], True, False)` | Works — but `path.makePipe(face)` is simpler |

### Shell / makeThickness

`makeThickness` takes a **negative** thickness value to shell inward:

```python
Part.BRep_API.makeThickness([face], -wall_thickness, 1e-3)
```

Passing a positive value shells outward (usually not what you want).

### polar_array radial direction

The implementation computes the initial radial direction by crossing `center_axis` with an arbitrary perpendicular. If `center_axis` is nearly parallel to `(1,0,0)`, it falls back to `(0,1,0)`. Don't rely on which direction the first copy lands — rely on symmetry.

### makeCompound vs fuse for arrays

All array functions use `Part.makeCompound`. This means:
- Volume = sum of child volumes (correct for non-overlapping shapes)
- The compound is **not** a merged solid — you can't fillet it as one
- If you need a fused array, call `union(*copies)` on the result

### Tier 3 profile plane

All 2D profiles are in the **XY plane (Z=0)**. To revolve around the Z axis, the profile must be in the XZ plane (Y=0). Use `polyline([(x,0,z), ...])` — that's the only profile type that handles 3D points natively.

### Tests use `_approx(a, b, tol)` not `pytest`

The test runner is a hand-rolled loop (no pytest dependency — pytest isn't bundled with FreeCAD). Tolerances are geometry-specific; see each test file's `_approx` definition.

---

## 8. Test Runner

```python
# tests/run_tests.py — how it works
_MODULES = [
    "tests.test_core",
    "tests.test_tier01",
    "tests.test_tier09",
    "tests.test_tier14",
    "tests.test_tier10",
    "tests.test_tier11",
    "tests.test_tier03",
    "tests.test_tier02",
    "tests.test_tier12",
]

# Imports each module, finds test_* functions, calls them,
# reports PASS/FAIL via FreeCAD.Console.PrintMessage + sys.stderr
```

Add new modules to `_MODULES` in the order you want them run.

---

## 9. GUI Layer (not needed for headless work)

`gui/auto_dialog.py` builds PySide2 dialogs by introspecting function signatures:

```python
from partikus.gui.auto_dialog import auto_dialog
auto_dialog(rounded_box)   # opens a dialog for rounded_box parameters
```

Widget mapping:
- `float` → `QDoubleSpinBox`
- `int` → `QSpinBox`
- `bool` → `QCheckBox`
- `Literal["a","b","c"]` → `QComboBox`

The workbench (`gui/workbench.py`) registers commands for Tier 1 only. Expand it for each new tier by adding entries to `_COMMANDS` and `_TOOLBAR`.

---

## 10. Parameter Naming — Non-Negotiable

These rules apply to every function in every tier:

| Concept | Parameter name |
|---|---|
| X extent | `length` |
| Y extent | `width` |
| Z extent | `height` |
| primary circle size | `diameter` |
| hollow outer | `outer_diameter` |
| hollow inner | `inner_diameter` |
| shell / wall | `wall_thickness` |
| face recess | `depth` |
| edge rounding | `fillet_radius` |
| edge beveling | `chamfer_size` |
| repetition count | `count` |
| angle | `<name>_deg` |

Never shorten (`dia`, `wid`, `h`, `len`, etc.). The AI downstream needs to guess parameter names from natural language.

---

## 11. Design Questions Left Open

These were deferred and still need decisions before implementing the relevant tiers:

1. **Threaded geometry (Tier 5):** Real helical threads are expensive. Offer `cosmetic=True` (visual-only) as default, `cosmetic=False` for full geometry? Or always cosmetic at this level?

2. **Gear involute (Tier 6):** OpenCASCADE can't generate involute gear profiles natively. Either: (a) approximate with polyline from precomputed points, (b) integrate a gear library (e.g. `cadquery`'s approach), or (c) use FreeCAD's `PartDesign.InvoluteGear` if accessible.

3. **SubD (Tier 15B):** FreeCAD 1.1.1 has no native SubD support. Options: (a) integrate OpenSubDiv via ctypes, (b) delegate to Blender + OBJ exchange, (c) stub with `NotImplementedError` and revisit. Decision needed before Milestone 5.

4. **Anchor serialisation:** Anchors are currently only in-memory. For saving/loading `PartikusShape` from `.FCStd`, anchors must be serialised (e.g., as a `FreeCAD.PropertyPythonObject` on the feature). Not needed for scripting workflows; needed for GUI round-trips.

---

## 12. Original Specification

The full original spec (all 16 tiers, GUI spec, AI workflow, open questions) is in `partikus-handoff.md` at the repo root. That document has not been modified — treat it as the authoritative spec.

---

## 13. Quick Sanity Check

Run this before writing a single line:

```bash
cd /opt/proj/partikus
squashfs-root/usr/bin/freecadcmd tests/run_tests.py 2>&1 | tail -5
```

Expected output:

```
============================================================
  193 passed  |  0 failed
```

If anything is failing, fix it before adding new code.

---

*End of handoff. Pick up at Milestone 3.*
