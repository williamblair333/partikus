# Partikus — Developer Handoff

**Last updated:** 2026-05-18  
**Status:** Milestones 1–12 complete — 697 tests passing  
**Next milestone:** Visual zebra/reflection (rendering pipeline) / visual regression tests

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
├── HANDOFF.md                           ← this file
├── partikus/
│   ├── __init__.py                      # public API — import everything from here
│   ├── core/
│   │   ├── anchors.py                   # anchor name string constants
│   │   ├── shape_wrapper.py             # PartikusShape class
│   │   ├── transforms.py                # rotation_from_to, placement_for_rotation
│   │   └── document.py                  # FreeCAD document helpers
│   ├── presets/
│   │   ├── __init__.py
│   │   ├── screws.py                    # ISO metric screw dimensions M2–M20
│   │   └── bearings.py                  # ISO ball bearing dimensions (600/620/630 series)
│   ├── tier00_foundations.py
│   ├── tier01_primitives.py
│   ├── tier02_enhanced.py
│   ├── tier03_profiles_2d.py
│   ├── tier04_mechanical.py             # boss, brackets, dovetails, snap clips, etc.
│   ├── tier05_fasteners.py              # bolts, nuts, washers, inserts, standoffs
│   ├── tier06_mechanical_components.py  # gears, rack, pulleys, sprockets, bearings
│   ├── tier07_enclosures.py             # lid, snap_fit_box, cable_channel, vents, etc.
│   ├── tier08_electronics.py            # pcb_standoff, rpi/arduino mounts, cutouts
│   ├── tier09_boolean.py
│   ├── tier10_modifiers.py
│   ├── tier11_patterns.py
│   ├── tier12_sweep_loft.py
│   ├── tier13_architectural.py          # wall, stairs, roofs, column, beam, truss
│   ├── tier14_assembly.py
│   ├── tier15a_nurbs.py                 # NURBS curves + most surfaces (real); BRep ops stubbed
│   ├── tier15b_subd.py                  # all stubs — no FreeCAD 1.1.1 SubD support
│   ├── tier15c_conversion.py            # mesh_to_nurbs (real); SubD conversions stubbed
│   ├── tier15d_analysis.py              # curvature/draft/deviation (real); zebra/reflection stubbed
│   ├── io.py                            # export (STEP/STL/IGES/BREP/OBJ/FCStd) + import (STEP/BREP/STL)
│   ├── ai/
│   │   ├── __init__.py                  # exports analyze_image/text, generate_script, run_script
│   │   ├── _http.py                     # stdlib-only Anthropic API client (no external deps)
│   │   ├── analyzer.py                  # ImageAnalyzer — image/text → decomposition JSON
│   │   ├── generator.py                 # ScriptGenerator — analysis dict → runnable Python
│   │   └── pipeline.py                  # high-level: analyze_image, analyze_text, generate_script, run_script
│   └── gui/
│       ├── auto_dialog.py
│       └── workbench.py
├── tests/
│   ├── run_tests.py                     # headless runner — start here
│   ├── test_core.py
│   ├── test_tier01.py  test_tier02.py  test_tier03.py
│   ├── test_tier04.py  test_tier05.py  test_tier06.py
│   ├── test_tier07.py  test_tier08.py
│   ├── test_tier09.py  test_tier10.py  test_tier11.py  test_tier12.py
│   ├── test_tier13.py  test_tier14.py  test_tier15.py
│   ├── test_io.py
│   └── test_ai.py
└── examples/
    └── capped_cylinder.py
```

Tier 15B (SubD) and 4 Tier 15A BRep-editing functions are **stubbed** — raise `NotImplementedError`. Blocked on missing FreeCAD 1.1.1 API surface.

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

### Milestone 3 (2026-05-18)

- `presets/screws.py` — ISO metric screw dimension tables M2–M20 (thread, head, nut, washer, clearance, heat-set insert dims)
- `presets/bearings.py` — ISO ball bearing tables (600/620/630 series)
- `tier04` — 20 mechanical features: boss, counterbore_hole, countersink_hole, slot_hole, keyway, rib, gusset, flange, lip, l_bracket, t_bracket, u_bracket, tab, slot_cutout, dovetail_pin/slot, tongue, groove, living_hinge, snap_clip
- `tier05` — 14 fastener functions: threaded_rod, tapped_hole, hex/socket/button/flat head bolts, hex_nut, flat/lock washer, heat_set_insert_pocket, clearance_hole, screw_size_preset, standoff, dowel_pin. Cosmetic (smooth cylinder) — no helical thread geometry.
- `tier06` — 7 mechanical components: spur_gear (true 16-pt/flank involute polyline via `Part.makePolygon`), bevel_gear (frustum), rack, pulley_timing, sprocket, bearing_pocket, shaft_coupling
- 147 new tests → **340 total, all passing**
- Key fix: `Part.Wire(edges)` fails on non-connected edges — always use `Part.makePolygon(pts)` for complex profiles

### Milestone 4 (2026-05-18)

- `tier07` — 10 enclosure functions: lid, snap_fit_box, hinged_box, magnetic_recess, battery_compartment (AA/AAA/C/D/9V/18650/CR2032/CR2025/CR2016), cable_channel, strain_relief, vent_slots, display_window, button_cutout
- `tier08` — 9 electronics functions: pcb_standoff, raspberry_pi_mount (3B/3B+/4B/5/Zero/Zero2), arduino_mount (uno/mega/nano/leonardo/micro), led_holder, usb_cutout (USB-A/B/C/Micro/Mini), hdmi_cutout (full/mini/micro), barrel_jack_cutout, din_rail_clip (35mm/15mm), heatsink_fin_array
- `tier13` — 11 architectural functions: wall (with openings list), door, window, stairs, roof_gable, roof_hip, roof_shed, column, beam, slab, truss_simple
- `tier15a` — 6 NURBS curve functions (real): nurbs_curve, bspline_curve, bezier_curve, curve_through_points, helix_curve, conic_curve; 17 surface/editing stubs (NotImplementedError)
- `tier15b` — 11 SubD stubs; `tier15c` — 4 conversion stubs; `tier15d` — 5 analysis stubs
- 151 new tests → **491 total, all passing**

### Milestone 5 (2026-05-18)

- `tier15a` — 9 surface/editing functions (real): loft_surface, sweep_1rail, patch_fill, boundary_surface, surface_from_points, move_control_point, offset_surface, join_surfaces, rebuild_surface; 9 stubs remain (trim, match, fillet variants)
- `tier15c` — `mesh_to_nurbs` (real); 3 SubD-related stubs remain
- `tier15d` — 3 analysis functions (real): analyze_curvature, analyze_draft, analyze_deviation; 2 stubs remain (zebra, reflection)
- Key fix: `patch_fill` — `Part.makeFilledFace` invalid for planar straight edges; now tries `Part.Face(wire)` first
- 41 new tests → **532 total, all passing**

### Milestone 6 (partial) (2026-05-18)

- `tier15a` — 5 more surface functions (real):
  - `network_surface(u_curves, v_curves)` — `BSplineSurface.buildFromNSections` from U-direction wires (discretize → interpolate → BSplineCurve); V curves accepted as guides
  - `sweep_2rail(profile, rail_a, rail_b)` — discretize both rails → line-segment profiles → `Part.makeLoft(solid=False)` open shell
  - `trim_surface(surface, trim_shape)` — `raw.cut(cutter)` keeps the portion not covered
  - `split_surface(surface, splitter)` — `raw.cut(splitter)` + `raw.common(splitter)` → list of PartikusShapes
  - `surface_fillet(surface_a, surface_b, radius)` — `Part.makeShell` + detect shared edges via `ancestorsOfType` + `shell.makeFillet(r, shared_edges)`
- Key discoveries:
  - `Part.makeLoft(profiles, solid=True)` fails for line-segment profiles (isValid=False); `solid=False` (open shell) works
  - `BSplineSurface.buildFromNSections` requires BSplineCurve objects (not wires); extract via `wire.discretize` + `BSplineCurve.interpolate`
  - `face.cut(half_space_solid)` and `face.common(half_space_solid)` are the reliable split primitives
  - `untrim_surface`, `match_surfaces`, `variable_fillet`, `surface_chamfer` remain stubs — BRep editing APIs not exposed in FreeCAD 1.x Python
- 20 new tests → **552 total, all passing**

### Milestone 7 (2026-05-18)

- `partikus/io.py` — full export/import module:
  - Export: `to_step`, `to_stl`, `to_iges`, `to_brep`, `to_obj`, `save_fcstd`
  - Import: `from_step`, `from_brep`, `from_stl`
  - All functions accept PartikusShape, list of PartikusShape, or list of (PartikusShape, label) tuples
  - All auto-create parent directories
- Key discoveries:
  - `Part.export([shape], file)` produces STEP that `Part.read()` cannot parse back; single exports must use `shape.exportStep(file)`
  - `shape.exportStl()` ignores deflection; use `Mesh.Mesh(shape.tessellate(deflection)).write()` instead
  - `Part.read()` works for STEP and BREP via the same API call
  - FreeCAD sphere tessellation has a minimum ~8000 facets regardless of deflection until < 0.05 mm
- 37 new tests → **589 total, all passing**

### Milestone 8 (2026-05-18)

- `partikus/ai/` — new subpackage for AI-driven shape decomposition (no external deps — stdlib only)
  - `_http.py` — minimal Anthropic API client using `urllib.request`; resolves FreeCAD AppImage SSL
    by loading `/etc/ssl/certs/ca-certificates.crt` via `ssl.create_default_context(cafile=...)`
  - `analyzer.py` — `ImageAnalyzer` class: `analyze(image_path, hint)` (vision) and
    `analyze_text(description, hint)` (text-only); robust JSON parsing (`_extract_json` handles
    fenced blocks, preamble, bare JSON); validates required keys + sets defaults
  - `generator.py` — `ScriptGenerator.generate(analysis, export_step, export_stl)` produces runnable
    Python with safe identifier sanitisation (`_safe_id`), import block, shape definitions, assembly
    ops, optional export calls; `validate_syntax(script)` uses `ast.parse()`
  - `pipeline.py` — high-level: `analyze_image`, `analyze_text`, `generate_script`, `run_script`
    (runs via `freecadcmd`); `_find_freecadcmd()` checks `squashfs-root/` relative path then PATH
- AI decomposition JSON schema:
  ```json
  {"description": "...", "shapes": [{"id": "body", "function": "box", "params": {...}, "note": "..."}],
   "assembly": [{"result": "asm", "op": "stack_on", "args": ["cap","body"], "params": {}}],
   "final": "asm", "estimated_dimensions_mm": {"x": 80, "y": 50, "z": 30}}
  ```
- Integration tests use `if not _has_api_key(): return` — skip silently when `ANTHROPIC_API_KEY` absent
- 36 new tests → **625 total, all passing**

---

## 6. What to Build Next

Remaining stubs in Tier 15A (BRep editing — blocked on FreeCAD Python API):

| Function | File | Blocker |
|---|---|---|
| `untrim_surface` | `tier15a_nurbs.py` | BRep trim removal not in FreeCAD Python API |
| `match_surfaces` | `tier15a_nurbs.py` | BRep shape healing not in FreeCAD Python API |
| `variable_fillet` | `tier15a_nurbs.py` | Variable-radius fillet not in FreeCAD Python API |
| `surface_chamfer` | `tier15a_nurbs.py` | Surface chamfer not in FreeCAD Python API |
| `analyze_zebra` (visual) | `tier15d_analysis.py` | Rendering pipeline needed for actual stripe image |
| `analyze_reflection` (visual) | `tier15d_analysis.py` | Rendering pipeline needed |

Milestones 9–12 done. Candidate next steps:

1. **Visual zebra/reflection** — integrate a headless renderer (e.g., FreeCAD's `FreeCADGui.offscreen_render`) for actual stripe images
2. **Visual regression tests** — render reference shapes; detect drift
3. **Anchor serialisation round-trip tests** — already done; extend to test `from_step` + `save_to_doc` pipeline

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

## 7. Decided Design Questions

These were open in §11 — now decided:

1. **Threaded geometry (Tier 5):** Cosmetic (smooth cylinder at nominal diameter). `cosmetic=False` reserved but raises `NotImplementedError`. Decision rationale: real helices make OpenCASCADE booleans unreliable and add no fabrication value.

2. **Gear involute (Tier 6):** 16-point polyline approximation per flank via `Part.makePolygon`. Do NOT use `Part.Wire(edges)` — it fails on non-connected edges. Always collect all points into a flat list and call `Part.makePolygon` for complex profiles.

3. **SubD (Tier 15B):** Deferred — no native FreeCAD 1.1.1 support. Stub with `NotImplementedError`.

4. **Anchor serialisation:** Still deferred. Not needed for scripting workflows.

## 8. Known Limitations & Gotchas

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

## 9. Test Runner

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
    "tests.test_tier04",
    "tests.test_tier05",
    "tests.test_tier06",
    "tests.test_tier07",
    "tests.test_tier08",
    "tests.test_tier13",
    "tests.test_tier15",
    "tests.test_io",
    "tests.test_ai",
]

# Imports each module, finds test_* functions, calls them,
# reports PASS/FAIL via FreeCAD.Console.PrintMessage + sys.stderr
```

Add new modules to `_MODULES` in the order you want them run.

---

## 10. GUI Layer (not needed for headless work)

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

## 11. Parameter Naming — Non-Negotiable

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

## 12. Design Questions Remaining

1. **SubD (Tier 15B):** FreeCAD 1.1.1 has no native SubD support. Options: (a) integrate OpenSubDiv via ctypes, (b) delegate to Blender + OBJ exchange, (c) stub with `NotImplementedError` and revisit. Decision needed before Milestone 5.

2. **Anchor serialisation:** Anchors are currently only in-memory. For saving/loading `PartikusShape` from `.FCStd`, anchors must be serialised (e.g., as a `FreeCAD.PropertyPythonObject` on the feature). Not needed for scripting workflows; needed for GUI round-trips.

---

## 13. Original Specification

The full original spec (all 16 tiers, GUI spec, AI workflow, open questions) is in `partikus-handoff.md` at the repo root. That document has not been modified — treat it as the authoritative spec.

---

## 14. Quick Sanity Check

Run this before writing a single line:

```bash
cd /opt/proj/partikus
squashfs-root/usr/bin/freecadcmd tests/run_tests.py 2>&1 | tail -5
```

Expected output:

```
============================================================
  697 passed  |  0 failed
```

If anything is failing, fix it before adding new code.

---

*End of handoff. Milestones 1–8 complete. 625 tests passing. Next: GUI expansion, SubD, or anchor serialisation.*
