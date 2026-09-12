# Partikus — Developer Handoff

**Last updated:** 2026-09-12  
**Status:** Milestones 1–13 complete + visual regression suite + AI-prompt expansion + PF1e template example — 750 tests passing — **GUI workbench now actually installs and loads**  
**Next milestone:** `Literal[...]` annotations for constrained string params (Tiers 1–8), then a new tier / BRep-stub workarounds (when FreeCAD exposes the APIs)

> **Start here if you are picking up the GUI work:** §2a below. The workbench was
> unreachable on every FreeCAD 1.x install until 2026-09-12; three root causes are fixed
> and committed, and the remaining work is a manual click-through test plan plus the
> `Literal` annotation pass.

**Repo hosting:** Primary remote is self-hosted **Gitea** — `origin` = `http://10.0.0.100:3000/bill/partikus`, `remote.pushDefault=origin`. GitHub (`github` remote → `williamblair333/partikus`) is secondary/mirror. Plain `git push` goes to Gitea. Note: GitHub `main` was force-rewound to `f2dc1d0` on 2026-08-07 (dropped PR #1); local/Gitea `main` is the source of truth.

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

### First-time setup

```bash
cd /opt/proj/partikus
./install.sh   # detects system freecadcmd >= 1.1, or extracts the AppImage automatically
```

### Running scripts

```bash
squashfs-root/usr/bin/freecadcmd tests/run_tests.py
squashfs-root/usr/bin/freecadcmd my_script.py
```

## 2a. Installing the GUI Workbench

```bash
cd /opt/proj/partikus
./install.sh          # symlinks this checkout into FreeCAD's user Mod directory
```

Then restart FreeCAD and pick **Partikus** from the workbench dropdown.

How it works, and the three ways it used to fail silently:

| Piece | Why it exists |
|---|---|
| `Init.py` | FreeCAD executes this by name from the root of every Mod directory, console and GUI. An add-on without it is skipped with no error. |
| `InitGui.py` | Same, GUI sessions only. This is the *only* thing that ever imports `partikus/gui/workbench.py`. Without it the registration code never runs. |
| `install.sh` symlink | Puts the checkout on FreeCAD's Mod path at `FreeCAD.getUserAppDataDir()/Mod/partikus`. |

**Do not delete `Init.py` or `InitGui.py`.** They are nearly empty and look like stray
files at the repo root. They are load-bearing; both carry a header saying so.

**Never reference `__file__` in either loader.** FreeCAD does not import them as modules —
it compiles the source and `exec`s it in a fresh namespace with **no `__file__` bound**.
The idiom every Python file starts with,

```python
_root = os.path.dirname(os.path.realpath(__file__))     # NameError under FreeCAD
```

raises before the loader reaches its first import, and the only symptom is one line of
startup log:

```
During initialization the error "name '__file__' is not defined"
occurred in .../Mod/partikus/InitGui.py
```

The workbench is then absent from the dropdown, which is indistinguishable from "not
installed". This cost a session already. `tests/test_gui_loader.py` guards it by exec'ing
both loaders in a namespace without `__file__`, exactly the way FreeCAD does.

No `sys.path` setup is needed either — FreeCAD puts every Mod entry on `sys.path` before
running the loader, which is why `fasteners/InitGui.py` and every other well-behaved
add-on just imports its package directly. Keep `InitGui.py` down to that one import.

**The Mod path is version-stamped** (`~/.local/share/FreeCAD/v1-1/`). A FreeCAD upgrade
moves it and the workbench disappears with no error — re-run `./install.sh`. The script
resolves the path from FreeCAD itself and refuses to guess; if the probe comes back empty
it skips the step loudly rather than installing somewhere FreeCAD does not read.

**Qt binding:** use `from PySide import ...`, never `PySide2` or `PySide6` directly.
`PySide` is FreeCAD's own shim (`squashfs-root/usr/Ext/PySide/`) and forwards to whichever
binding the running FreeCAD was built against — PySide6 on FreeCAD 1.x. A `PySide2` import
inside `try/except ImportError` is how this project shipped a GUI layer that imported
cleanly and did nothing for an entire release line. Both GUI modules now warn to the
Report view on the except path; keep it that way.

**Verifying GUI code headlessly.** Two levels, and the difference matters:

```bash
# Widgets and dialogs — fast, no display, no real GUI
QT_QPA_PLATFORM=offscreen squashfs-root/usr/bin/freecadcmd your_probe.py

# Workbench registration — a real GUI session, offscreen
QT_QPA_PLATFORM=offscreen app/FreeCAD_1.1.3-Linux-x86_64-py311.AppImage your_probe.py
```

Under `freecadcmd` the full Qt widget set imports fine, so `auto_dialog._build_dialog(fn)`
/ `.get_values()` can be exercised end-to-end. **But `FreeCADGui` there is a stub** — it
imports, and `HAS_GUI` comes out `True`, while `addCommand` and `listWorkbenches` do not
exist. Anything about registration must run under the second form, which starts a real GUI
session offscreen and prints FreeCAD's own startup errors. End the probe with
`FreeCADGui.getMainWindow().close()` so it exits.

Remember `sys.stderr.write` — `print()` is swallowed.

**FreeCAD caches imported modules.** After editing anything under `partikus/gui/`, a
running FreeCAD keeps the old code. Fully restart it, or the fix will look like it did
nothing.

**`save_to_doc` must set `obj.ViewObject.Proxy = 0`.** A `Part::FeaturePython` gets
`ViewProviderPartExt`, which asks a Python proxy which display mode to use. With no proxy
on the `ViewObject` it selects none, and the part is valid, `Visibility=True`, listed in
the tree — and invisible, with no error anywhere. Measured on 1.1.3:

| `ViewObject.Proxy` | `DisplayMode` | rendered |
|---|---|---|
| `None` | `None` | no |
| `0` | `'Flat Lines'` | yes |

Guard it on `ViewObject is not None` — it is `None` under `freecadcmd`, and an unguarded
assignment breaks every headless caller. A blank **Display Mode** in the View panel is the
signature of this failure; check it first when a part does not appear.

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
├── Init.py                              # FreeCAD add-on loader, console — DO NOT DELETE
├── InitGui.py                           # FreeCAD add-on loader, GUI — DO NOT DELETE
├── install.sh                           # finds FreeCAD + symlinks into its Mod dir
├── partikus/
│   ├── __init__.py                      # public API — import everything from here
│   ├── core/
│   │   ├── anchors.py                   # anchor name string constants
│   │   ├── shape_wrapper.py             # PartikusShape class (has subd_mesh slot)
│   │   ├── transforms.py                # rotation_from_to, placement_for_rotation
│   │   ├── document.py                  # FreeCAD document helpers
│   │   ├── serialise.py                 # save_to_doc / load_from_doc (anchor round-trip)
│   │   └── render.py                    # write_png — stdlib-only PNG encoder
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
│   ├── tier15b_subd.py                  # 11 SubD functions (pure-Python Catmull-Clark)
│   ├── tier15c_conversion.py            # mesh_to_nurbs, subd_to_nurbs, mesh_to_subd, nurbs_to_subd
│   ├── tier15d_analysis.py              # curvature/draft/deviation/zebra/reflection (all real)
│   ├── subd_mesh.py                     # SubDMesh class — Catmull-Clark engine + 5 primitives
│   ├── io.py                            # export (STEP/STL/IGES/BREP/OBJ/FCStd) + import (STEP/BREP/STL)
│   ├── ai/
│   │   ├── __init__.py                  # exports analyze_image/text, generate_script, run_script
│   │   ├── _http.py                     # stdlib-only Anthropic API client (no external deps)
│   │   ├── analyzer.py                  # ImageAnalyzer — image/text → decomposition JSON
│   │   ├── generator.py                 # ScriptGenerator — analysis dict → runnable Python
│   │   └── pipeline.py                  # high-level: analyze_image, analyze_text, generate_script, run_script
│   └── gui/
│       ├── auto_dialog.py               # uses save_to_doc for anchor-preserving GUI shapes
│       └── workbench.py                 # Tiers 1–8 commands (84 functions, 8 toolbars)
├── tests/
│   ├── run_tests.py                     # headless runner — start here
│   ├── run_integration_tests.py         # AI pipeline tests (requires ANTHROPIC_API_KEY)
│   ├── test_core.py
│   ├── test_tier01.py  test_tier02.py  test_tier03.py
│   ├── test_tier04.py  test_tier05.py  test_tier06.py
│   ├── test_tier07.py  test_tier08.py
│   ├── test_tier09.py  test_tier10.py  test_tier11.py  test_tier12.py
│   ├── test_tier13.py  test_tier14.py  test_tier15.py
│   ├── test_io.py
│   ├── test_ai.py
│   ├── test_serialise.py                # anchor save/load round-trip tests
│   ├── test_subd.py                     # Catmull-Clark + SubD op tests
│   ├── test_visual_regression.py        # zebra/reflection PNG output vs baselines
│   ├── test_pf1e_templates.py           # PF1e example: distance rule + printable parts
│   └── baselines/                       # committed reference PNGs for visual regression
└── examples/
    ├── capped_cylinder.py
    ├── pf1e_burst_templates.py      # printable Pathfinder 1E area-of-effect rings
    └── rpi4_enclosure.py            # full-API showcase (see docs/rpi4_enclosure_walkthrough.md)
```

4 Tier 15A BRep-editing functions are **stubbed** — raise `NotImplementedError`. Blocked on missing FreeCAD 1.1.1 API surface. Everything else is implemented.

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

### Milestones 9–13 (2026-05-18)

See `CHANGELOG.md [0.9.0]` and `[0.10.0]` for full details.

- **M9 — Anchor serialisation**: `core/serialise.py` — `save_to_doc`/`load_from_doc` persist anchors across `.FCStd` save/load. 11 tests.
- **M10 — GUI expansion**: `gui/workbench.py` extended to Tiers 1–8 (84 functions, 8 toolbars, full menu tree).
- **M11 — CI integration runner**: `tests/run_integration_tests.py` — standalone AI pipeline test suite (requires `ANTHROPIC_API_KEY`).
- **M12 — SubD** (pure-Python Catmull-Clark): `subd_mesh.py` + all 11 `tier15b_subd.py` functions real. `tier15c_conversion.py` conversions real. `analyze_zebra`/`analyze_reflection` numerical. 61 tests.
- **M13 — Visual renderer**: `core/render.py` stdlib PNG writer. `analyze_zebra` and `analyze_reflection` now produce real PNG images via UV-grid sampling + stripe mapping. No GUI, no display required. 7 tests.

### Showcase example (2026-05-18)

- `examples/rpi4_enclosure.py` — single runnable script demonstrating Tiers 2, 4, 7, 8, 9, 10, 11, 14, 15A, 15D, I/O, and AI pipeline in a realistic Raspberry Pi 4B enclosure design.
- `docs/rpi4_enclosure_walkthrough.md` — companion doc covering every section, the cutout-through-wall pattern, anchor-based positioning, and a parameters table for experimenting.
- Key implementation notes captured there:
  - `shell(rounded_box(...))` is untested — use `hollow_box` for enclosure bodies; call `shell()` directly only on plain `box()` shapes
  - Cutout-through-wall: rotate cutout 90° to align its depth axis with the target wall, then translate centre to the wall face; use `CUT_D = WALL * 6` for safe overlap
  - `analyze_zebra` requires a `Part.Face` with an underlying `BSplineSurface` (output of `surface_from_points`, `rebuild_surface`, etc.) — not a solid

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

These four are genuinely blocked — no workaround exists in FreeCAD 1.x Python. Leave as `NotImplementedError` until FreeCAD exposes the underlying OCC APIs.

Candidate next steps (no hard blockers):

1. ~~**Visual regression tests**~~ — DONE (2026-08-07). `tests/test_visual_regression.py` renders a flat grid + Gaussian dome through `analyze_zebra`/`analyze_reflection`, compares PNGs pixel-for-pixel against committed baselines in `tests/baselines/`. Recapture with `PARTIKUS_UPDATE_BASELINES=1`.
2. ~~**Expand AI system prompt**~~ — DONE (2026-08-07), but scoped differently than originally worded. The AI pipeline decomposes an object into **shape constructors + assembly ops** producing a final `PartikusShape`. `analyze_zebra`/`analyze_reflection` return analysis dicts/PNGs (not shapes) and `subd_*` operate on `SubDMesh` (not the shape/assembly schema) — adding them would generate broken scripts, so they're **deliberately excluded**. Instead the prompt catalogue + `_ALLOWED_FUNCTIONS` grew from ~20 to ~90 real constructive functions (Tiers 1–14: fasteners, gears, enclosures, electronics, mechanical features, patterns, architectural). Guard tests in `test_ai.py` enforce prompt ⊆ whitelist ⊆ real callable exports, and that the 4 Tier-15A stubs are never offered. To surface analysis/SubD to the AI later, add a separate post-processing schema slot — don't put them in `shapes`/`assembly`.
3. **`Literal[...]` annotations for constrained string params — the next GUI task.**
   `auto_dialog` already turns a `Literal["a","b","c"]` annotation into a validated combo
   box. 28 exported functions take a constrained string with no annotation, so the dialog
   offers free text and a typo becomes a traceback instead of an impossible input. The
   full list, from a signature sweep of `partikus.__all__`:

   | Tier | Function(s) and parameter |
   |---|---|
   | 2 | `rounded_cylinder(ends='BOTH')` |
   | 5 | `clearance_hole(bolt_size='M6', fit='close')`, `heat_set_insert_pocket(insert_size='M3')`, `screw_size_preset(name='M6')`, `threaded_rod(thread_form='metric')` |
   | 6 | `bearing_pocket(bearing_id='608')`, `pulley_timing(belt_type='GT2')` |
   | 7 | `battery_compartment(battery_type='AA')`, `button_cutout(shape='round')`, `hinged_box(hinge_side='BACK')`, `hollow_box(open_face='TOP')` |
   | 8 | `arduino_mount(model='uno')`, `din_rail_clip(rail_type='35mm')`, `hdmi_cutout(connector_type='full')`, `raspberry_pi_mount(model='4B')`, `usb_cutout(connector_type='USB-C')` |
   | 11 | `mirror(plane='XY')`, `mirror_position(plane='XY')` |
   | 14 | `align(anchor='CENTER')`, `attach(parent_anchor='TOP', child_anchor='BOTTOM')`, `stack_on(alignment='CENTER')` |
   | 15 | `analyze_curvature(mode='gaussian')`, `conic_curve(conic_type='parabola')`, `match_surfaces(continuity='G1')`, `mesh_to_nurbs(patch_size='auto')`, `nurbs_to_subd(density='medium')`, `subd_symmetry(plane='YZ', mode='mirror')` |
   | io | `save_fcstd(doc_name='Partikus')` — free text, correctly so; leave it |

   The accepted values are already in each function's body (usually a dict lookup or an
   `if/elif` chain that raises on an unknown key) — lift them into the annotation. Tiers
   1–8 are the ones wired into the workbench, so do those first. Prioritise over the
   hardcoded face-list heuristic in `_make_widget`, which this would make redundant.

4. **Finish the GUI click-through test plan.** Everything below step 2 is untested:
   1. ~~Restart FreeCAD, Ctrl+N, Partikus → Enhanced → Hollow Box → OK~~ — the underlying
      defect is fixed and verified headlessly (dialog values → valid solid); confirm in
      the GUI that the Open Face dropdown appears.
   2. Partikus → Primitives → Cylinder → OK.
   3. Select the cylinder → Data → Placement → offset it to overlap the box.
   4. Part workbench → select both → Part → Boolean → Cut, then Undo and Fuse.
      This is the step with real risk: it depends on `save_to_doc` producing a
      `Part::FeaturePython` whose `Shape` the Part booleans accept. Unconfirmed.
   5. File → Export → STL.

   Commands are disabled until a document exists (`_Cmd.IsActive` returns
   `FreeCAD.ActiveDocument is not None`), and nothing tells the user why — a fresh launch
   on the Start page shows greyed buttons with no explanation. Either auto-create a
   document in `Activated()` (`_add_to_doc` already does) and return `True`, or add a
   tooltip.

5. **New tier** — Tier 16 or domain-specific (e.g., jewellery, robotics, sheet metal)

6. **Recipe pattern (discussed, not started).** The stated want is "pick a part from the
   library → set parameters → cut → weld", with no AI. Tiers 4–8 plus the auto-dialog are
   already that; what is missing is discoverability and the combine step. A recipe module
   (top-level parameters + `build(**params)` + one generic re-run-on-change dialog,
   OpenSCAD Customizer style) is the cheap route.

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

4. **Anchor serialisation:** Done in M9 — `core/serialise.py`.

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
    "tests.test_serialise",
    "tests.test_subd",
    "tests.test_visual_regression",   # visual regression: zebra/reflection PNG baselines
    "tests.test_pf1e_templates",      # example guard: PF1e distance rule + printable parts
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

Widget mapping, in the order `_make_widget` tests it:
- `Literal["a","b","c"]` → `QComboBox` (validated — the preferred form)
- `str` → `QComboBox` if the default is one of the six face anchors, else `QLineEdit`
- `bool` → `QCheckBox`
- `int` → `QSpinBox`
- everything else → `QDoubleSpinBox`

The `str` branch is a stopgap. A string parameter used to fall through to the float
spinbox and arrive at the geometry call as `0.0`; the face-anchor list is a heuristic that
covers four parameters. See §6 item 3 — annotating the other 28 with `Literal` makes it
redundant and turns typos into impossible inputs instead of tracebacks.

The workbench (`gui/workbench.py`) registers Tiers 1–8 — 84 functions across 8 toolbars
and a full menu tree. Expand it for each new tier by adding entries to `_COMMANDS` and
`_TOOLBAR`.

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

1. **SubD (Tier 15B):** Resolved — pure-Python Catmull-Clark in `subd_mesh.py`. All 11 functions real.

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
  750 passed  |  0 failed
```

If anything is failing, fix it before adding new code.

---

*End of handoff. Milestones 1–13 complete + visual regression suite + AI-prompt expansion + PF1e template example. 750 tests passing. GUI workbench installs and loads as of 2026-09-12. Next: `Literal` annotations for Tiers 1–8, then the GUI click-through test plan.*
