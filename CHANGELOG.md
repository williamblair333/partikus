# Changelog

All notable changes to Partikus are documented here.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Versions follow [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

*Changes staged for the next release go here.*

---

## [0.2.0] — 2026-05-18 — Milestone 2: Practical Utility

### Added

**Tier 2 — Enhanced Primitives** (`tier02_enhanced.py`)
- `rounded_box(length, width, height, fillet_radius, edges=None)`
- `chamfered_box(length, width, height, chamfer_size, edges=None)`
- `rounded_cylinder(diameter, height, fillet_radius, ends="BOTH")` — `ends` accepts `"BOTH"`, `"TOP"`, `"BOTTOM"`
- `tube(outer_diameter, inner_diameter, height)`
- `tube_by_wall(outer_diameter, wall_thickness, height)` — raises `ValueError` when wall ≥ radius
- `hollow_box(length, width, height, wall_thickness, open_face="TOP")`
- `hemisphere(diameter)`
- `spherical_cap(diameter, height)`
- `frustum(base_diameter, top_diameter, height)` — alias of `cone()` with both diameters explicit
- `prism(sides, diameter, height)` — raises `ValueError` when `sides < 3`
- `rounded_prism(sides, diameter, height, fillet_radius)`
- `stepped_cylinder(diameters, heights)` — raises `ValueError` on mismatched list lengths or empty input

**Tier 3 — 2D Profiles** (`tier03_profiles_2d.py`)
- `rectangle(length=10, width=10)` → `Part.Wire`
- `rounded_rectangle(length, width, fillet_radius)` — raises `ValueError` when radius too large
- `chamfered_rectangle(length, width, chamfer_size)`
- `circle(diameter=10)` — alias: `radius=`
- `ellipse(major_diameter, minor_diameter)`
- `regular_polygon(sides, diameter)` — raises `ValueError` when `sides < 3`
- `star(points, outer_diameter, inner_diameter)`
- `slot(length, width)` — degenerates to circle when `length == width`; raises `ValueError` when `length < width`
- `teardrop(diameter, angle=45)` — printable horizontal-hole profile
- `arc(radius, start_angle_deg, end_angle_deg)` — open wire
- `polyline(points, closed=False)` — accepts 2D `(x,y)` or 3D `(x,y,z)` tuples

**Tier 10 — Edge & Surface Modifiers** (`tier10_modifiers.py`)
- `fillet(shape, radius, edges=None)` — `edges=None` fillets all edges
- `chamfer(shape, size, edges=None)`
- `shell(shape, wall_thickness, open_faces=None)` — `open_faces` is list of anchor-name strings; default opens `TOP`; raises `ValueError` on unrecognised anchor
- `offset(shape, distance)` — positive inflates, negative deflates
- `draft`, `emboss`, `deboss`, `knurl`, `surface_texture` → `NotImplementedError`

**Tier 11 — Pattern / Array Operations** (`tier11_patterns.py`)
- `linear_array(shape, count, spacing, axis=(1,0,0))` — centred; raises `ValueError` when `count < 1`
- `grid_array(shape, count_x, count_y, spacing_x, spacing_y)` — centred 2D grid
- `polar_array(shape, count, radius, center_axis=(0,0,1), full_angle_deg=360)`
- `mirror(shape, plane)` — `plane` ∈ `{"XY","XZ","YZ"}`; returns compound; raises `ValueError` on unknown plane
- `helix_array`, `honeycomb_fill`, `path_array` → `NotImplementedError`

**Tier 12 — Sweep / Loft** (`tier12_sweep_loft.py`)
- `extrude(profile_2d, height, taper_angle_deg=0)` — `taper_angle_deg != 0` → `NotImplementedError`
- `revolve(profile_2d, axis=(0,0,1), angle_deg=360)`
- `sweep(profile_2d, path_curve, twist_deg=0)`
- `loft(profile_list, closed=False, ruled=False)`
- `pipe(path_curve, diameter, wall_thickness=0)` — raises `ValueError` when wall ≥ radius

**Tests**
- `tests/test_tier02.py` — 35 tests covering all enhanced primitives
- `tests/test_tier03.py` — 28 tests covering all 2D profile types
- `tests/test_tier10.py` — 17 tests covering fillet/chamfer/shell/offset
- `tests/test_tier11.py` — 18 tests covering all pattern functions
- `tests/test_tier12.py` — 23 tests covering all sweep/loft functions
- Total test count: **193** (all passing)

### Fixed
- `ellipse()` used `Part.makeEllipse()` which does not exist in FreeCAD 1.1.1; replaced with `Part.Ellipse(center, major_r, minor_r).toShape()`

### Changed
- `partikus/__init__.py` now exports all Tier 2/3/10/11/12 public symbols
- `tests/run_tests.py` `_MODULES` list expanded with five new test modules

---

## [0.1.0] — 2026-05-15 — Milestone 1: Foundation

### Added

**Core infrastructure**
- `PartikusShape` wrapper class (`core/shape_wrapper.py`) — composes `Part.Shape` with `.anchors` dict and `.orientations` dict
- `core/anchors.py` — all anchor name string constants (`CENTER`, `TOP`, `BOTTOM`, corners, edge midpoints, `TOP_RIM`, `BOTTOM_RIM`)
- `core/transforms.py` — `rotation_from_to(from_vec, to_vec)`, `placement_for_rotation(rotation, center)`
- `core/document.py` — `active_doc(name)`, `add_shape(partikus_shape, label, doc)`
- Internal helpers: `_bb_result(shape)`, `_bb_anchors(shape)`, `_unwrap(shape)`, `_preserve(src, new_shape)`, `_V(x,y,z)`

**Tier 0 — Foundations** (`tier00_foundations.py`)
- Orientation vectors: `UP`, `DOWN`, `NORTH`, `SOUTH`, `EAST`, `WEST`
- Reference planes: `PLANE_XY`, `PLANE_XZ`, `PLANE_YZ`
- Axis constants: `AXIS_X`, `AXIS_Y`, `AXIS_Z`, `ORIGIN`

**Tier 1 — Raw Primitives** (`tier01_primitives.py`)
- `box(length, width, height)` — bounding-box centred at origin; full 26-anchor set
- `cylinder(diameter, height)` — centred; includes `TOP_RIM`, `BOTTOM_RIM`
- `sphere(diameter)`
- `cone(base_diameter, top_diameter, height)`
- `torus(major_diameter, minor_diameter)`
- `wedge(length, width, height)` — extruded right triangle
- `pyramid(base_length, base_width, height)` — closed shell from 5 faces
- `disk(diameter, thickness)`
- `polyhedron(vertices, faces)` — generic closed shell

**Tier 9 — Boolean Operations** (`tier09_boolean.py`)
- `union(*shapes)` / `fuse(*shapes)`
- `difference(base, *subs)` / `cut(base, *subs)`
- `intersection(*shapes)` / `intersect(*shapes)`
- `hull`, `minkowski_sum` → `NotImplementedError`

**Tier 14 — Assembly & Positioning** (`tier14_assembly.py`)
- `translate(shape, dx, dy, dz)`
- `rotate(shape, axis, angle_deg, center=None)`
- `scale(shape, factor, fx, fy, fz)`
- `mirror_position(shape, plane)`
- `attach(child, parent, child_anchor, parent_anchor, offset, rotation_deg)` — full normal-opposing alignment
- `stack_on(child, parent)`
- `place_beside(child, parent, side, gap)`
- `align(shape_a, shape_b, axis_name, anchor)`
- `coaxial(shape_a, shape_b)`

**GUI layer**
- `gui/auto_dialog.py` — `auto_dialog(fn)` introspects signature to build PySide2 dialog automatically; `Literal` → `QComboBox`, `bool` → `QCheckBox`, numeric → spin boxes
- `gui/workbench.py` — `PartikusWorkbench` registers all Tier 1 commands; guard for `HAS_GUI`

**Tests**
- `tests/run_tests.py` — headless runner using `FreeCAD.Console.PrintMessage` + `sys.stderr`
- `tests/test_core.py`, `test_tier01.py`, `test_tier09.py`, `test_tier14.py`
- Baseline: **70 tests — all passing**

### Notes
- FreeCAD 1.1.1 AppImage at `/opt/proj/partikus/FreeCAD_1.1.1-Linux-x86_64-py311.AppImage`
- `freecadcmd` captures stdout; all test output routed through `sys.stderr`
- `__name__` in `freecadcmd` is the script filename, not `"__main__"` — bare `main()` call required

---

[Unreleased]: https://github.com/williamblair333/partikus/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/williamblair333/partikus/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/williamblair333/partikus/releases/tag/v0.1.0
