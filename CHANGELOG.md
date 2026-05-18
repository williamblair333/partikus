# Changelog

All notable changes to Partikus are documented here.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Versions follow [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

*Changes staged for the next release go here.*

---

## [0.6.0] — 2026-05-18 — Milestone 6: Surface Editing Operations

### Added

**Tier 15A — NURBS Surface Editing** (`tier15a_nurbs.py`) — new real implementations

- `network_surface(u_curves, v_curves)` — BSplineSurface through a network of crossing curves;
  builds via `BSplineSurface.buildFromNSections` using U-direction wires (discretized → BSplineCurve);
  V curves provide cross-sectional guidance; requires ≥2 curves in each direction
- `sweep_2rail(profile, rail_a, rail_b, n_sections=20)` — sweep a profile between two guide rails;
  discretizes both rails → builds line-segment cross-sections at each station →
  lofts open shell via `Part.makeLoft(solid=False)`; key fix: `solid=True` fails for line-segment profiles
- `trim_surface(surface, trim_shape)` — keep the portion of a surface NOT covered by a solid cutter
  via `raw.cut(cutter)`; returns Shell with the remaining geometry
- `split_surface(surface, splitter)` — divide a surface into two pieces via `raw.cut(splitter)` and
  `raw.common(splitter)`; returns `list[PartikusShape]` with both halves; area-additive
- `surface_fillet(surface_a, surface_b, radius)` — constant-radius fillet between two adjacent faces;
  auto-detects shared edges via `shell.ancestorsOfType`; uses `shell.makeFillet(r, shared_edges)`

**Stubs clarified** (BRep APIs not exposed in FreeCAD 1.x Python):
- `untrim_surface` — low-level BRep trim removal unavailable
- `match_surfaces` — shape healing API unavailable  
- `variable_fillet` — variable-radius fillet API unavailable
- `surface_chamfer` — surface chamfer API unavailable

### Key discoveries (Milestone 6)

- `Part.makeLoft(profiles, solid=True)` returns `isValid=False` for line-segment profiles;
  `solid=False` (open shell) is required for surface sweeps
- `BSplineSurface.buildFromNSections` requires BSplineCurve objects; extract via
  `wire.discretize(N)` → `BSplineCurve.interpolate(pts)`
- `face.cut(half_space) + face.common(half_space)` is the reliable split pair in FreeCAD
- `shell.ancestorsOfType(edge, Part.Face)` correctly identifies shared edges for fillet targeting

### Tests

- 20 new tests covering network_surface, sweep_2rail, trim_surface, split_surface, surface_fillet
- **552 total tests — all passing**

---

## [0.5.0] — 2026-05-18 — Milestone 5: Freeform Surfaces

### Added

**Tier 15A — NURBS Surfaces** (`tier15a_nurbs.py`) — real implementations
- `loft_surface(profile_curves, ruled=False)` — blend shell through ≥2 profile wires via `Part.makeLoft`
- `sweep_1rail(profile, rail)` — sweep cross-section along a path via `makePipeShell`
- `patch_fill(boundary_curves)` — closed-boundary fill; planar → `Part.Face(wire)`; curved → `makeFilledFace`
- `boundary_surface(curves)` — alias of `patch_fill` for 3 or 4 boundary curves
- `surface_from_points(point_grid_2d)` — interpolated BSplineSurface through a 2-D point grid
- `move_control_point(surface, u_index, v_index, new_position)` — edit a pole of a BSplineSurface face
- `offset_surface(surface, distance)` — uniform offset via `makeOffsetShape`
- `join_surfaces(*surfaces)` — join ≥2 faces into a shell via `Part.makeShell`
- `rebuild_surface(surface, u_count, v_count, degree=3)` — sample + re-approximate to new grid density

**Tier 15A — Stubs** (Milestone 6)
- `network_surface`, `sweep_2rail`, `trim_surface`, `untrim_surface`, `split_surface`, `match_surfaces`, `surface_fillet`, `variable_fillet`, `surface_chamfer`

**Tier 15C — Conversion** (`tier15c_conversion.py`)
- `mesh_to_nurbs(mesh, patch_size="auto", degree=3, tolerance=0.1)` — fit BSplineSurface to mesh vertex cloud; accepts PartikusShape, Part.Solid, Part.Shell, or Part.Face; `patch_size`: "coarse" (4×4), "auto" (8×8), "fine" (16×16)
- `subd_to_nurbs`, `nurbs_to_subd`, `mesh_to_subd` — stubbed (Milestone 6)

**Tier 15D — Quality Analysis** (`tier15d_analysis.py`)
- `analyze_curvature(surface, mode)` — samples BSplineSurface curvature at 5×5 grid; mode: "gaussian", "mean", "max", "min"; returns `{mode, min, max, mean, sample_count, unit}`
- `analyze_draft(shape, pull_direction=(0,0,1))` — per-face draft angle vs pull direction; returns face list + min/max/mean; flags faces below 0.5° threshold
- `analyze_deviation(surface, reference, sample_count=10)` — sample-based distance comparison; returns min/max/mean/rms deviation
- `analyze_zebra`, `analyze_reflection` — stubbed (require rendering pipeline; Milestone 6)

**Tests**
- `tests/test_tier15.py` fully rewritten: 41 new real tests (surfaces, analysis, conversion) + 12 stub-verification tests
- Total test count: **532** (all passing)

### Fixed
- `patch_fill`: `Part.makeFilledFace` returns invalid faces for planar straight-edge boundaries — now tries `Part.Face(wire)` first, falls back to `makeFilledFace` for non-planar inputs

### Notes
- FreeCAD 1.1.1 curvature API: valid type strings are `"Mean"`, `"Max"`, `"Min"`; Gaussian is computed as κ_max × κ_min
- `surface_from_points` and `rebuild_surface` use `BSplineSurface.interpolate` / `.approximate` — results are exact through the sample points
- SubD (Tier 15B): no native FreeCAD 1.1.1 support; full 11-function stub set kept for Milestone 6

---

## [0.4.0] — 2026-05-18 — Milestone 4: Application Domains

### Added

**Tier 7 — Container / Enclosure Features** (`tier07_enclosures.py`)
- `lid(length, width, rim_height, rim_inset, wall_thickness)` — flat lid with seating rim
- `snap_fit_box(length, width, height, wall_thickness, snap_count=4)` — open-top box with snap tabs
- `hinged_box(length, width, height, wall_thickness, hinge_side="BACK")` — two-piece box with living-hinge strip
- `magnetic_recess(magnet_diameter, magnet_thickness, count=1, spacing=10)` — press-fit disc magnet pockets
- `battery_compartment(battery_type, count, wall_thickness, contact_clearance)` — tray for AA/AAA/C/D/9V/18650/CR2032/CR2025/CR2016
- `cable_channel(width, depth, length, wall_thickness)` — U-shaped cable routing channel
- `strain_relief(cable_diameter, length, wall_thickness, clamp_gap)` — split-collar cable clamp
- `vent_slots(length, width, slot_count, slot_width, depth, wall_thickness)` — panel with ventilation slots
- `display_window(length, width, recess_depth, border_thickness, panel_thickness)` — viewing aperture panel
- `button_cutout(diameter, panel_thickness, shape="round")` — round or square panel cutout

**Tier 8 — Electronics Mounting** (`tier08_electronics.py`)
- `pcb_standoff(height, hole_diameter, base_diameter)` — threaded standoff column
- `raspberry_pi_mount(model, standoff_height, hole_diameter)` — mounting plate for 3B/3B+/4B/5/Zero/Zero2
- `arduino_mount(model, standoff_height, hole_diameter)` — mounting plate for Uno/Mega/Nano/Leonardo/Micro
- `led_holder(led_diameter, panel_thickness, retention_lip)` — press-fit LED panel mount
- `usb_cutout(connector_type, panel_thickness, clearance)` — USB-A/B/C/Micro/Mini panel aperture
- `hdmi_cutout(connector_type, panel_thickness, clearance)` — full/mini/micro HDMI aperture
- `barrel_jack_cutout(outer_diameter, panel_thickness, clearance)` — barrel power jack aperture
- `din_rail_clip(rail_type, clip_length, wall_thickness)` — EN 60715 TS 35 / TS 15 snap-on clip
- `heatsink_fin_array(base_length, base_width, fin_count, fin_height, fin_thickness, base_thickness)` — rectangular fin heatsink

**Tier 13 — Architectural** (`tier13_architectural.py`)
- `wall(length, height, thickness, openings=[])` — solid wall with optional door/window cutouts
- `door(width, height, thickness=40)` — solid door panel
- `window(width, height, frame_thickness, depth)` — hollow window frame
- `stairs(total_rise, total_run, tread_count, width)` — solid stringer staircase
- `roof_gable(length, width, peak_height, overhang)` — pitched gable roof (triangular cross-section)
- `roof_hip(length, width, peak_height, overhang)` — hip roof (four sloped faces, lofted)
- `roof_shed(length, width, low_height, high_height)` — monopitch shed roof
- `column(diameter, height, base_size=None, capital_size=None)` — round column with optional plinth/capital
- `beam(length, cross_section_profile=None, width, height)` — structural beam; accepts custom profile wire
- `slab(length, width, thickness)` — flat structural slab
- `truss_simple(length, height, panel_count, member_width, member_height)` — planar Pratt truss

**Tier 15A — NURBS Curves** (`tier15a_nurbs.py`) — real implementations
- `nurbs_curve(control_points, weights=None, degree=3, knots=None)`
- `bspline_curve(control_points, degree=3)` — uniform-weight B-spline
- `bezier_curve(control_points)` — degree = len(points)-1
- `curve_through_points(points, smooth=True)` — interpolating curve or polyline
- `helix_curve(diameter, pitch, turns, taper=0)` — cylindrical or tapered helix
- `conic_curve(conic_type, focal_length, extent)` — "parabola" or "hyperbola"

**Tier 15A — NURBS Surfaces / Editing** (`tier15a_nurbs.py`) — stubbed (Milestone 5)
- `loft_surface`, `network_surface`, `sweep_1rail`, `sweep_2rail`, `patch_fill`, `boundary_surface`, `surface_from_points`
- `move_control_point`, `trim_surface`, `untrim_surface`, `split_surface`, `join_surfaces`, `rebuild_surface`, `offset_surface`, `match_surfaces`, `surface_fillet`, `variable_fillet`, `surface_chamfer`

**Tier 15B — Subdivision Surfaces** (`tier15b_subd.py`) — all stubbed (Milestone 5)
- `subd_primitive`, `subd_push_pull`, `subd_insert_loop`, `subd_bevel_edge`, `subd_bevel_vertex`, `subd_bridge`, `subd_subdivide`, `subd_crease`, `subd_symmetry`, `subd_soft_select`, `subd_sculpt_brush`

**Tier 15C — Conversion Bridges** (`tier15c_conversion.py`) — all stubbed (Milestone 5)
- `subd_to_nurbs`, `nurbs_to_subd`, `mesh_to_subd`, `mesh_to_nurbs`

**Tier 15D — Quality Analysis** (`tier15d_analysis.py`) — all stubbed (Milestone 5)
- `analyze_curvature`, `analyze_zebra`, `analyze_reflection`, `analyze_draft`, `analyze_deviation`

**Tests**
- `tests/test_tier07.py` — 37 tests covering all enclosure functions
- `tests/test_tier08.py` — 38 tests covering all electronics mounting functions
- `tests/test_tier13.py` — 36 tests covering all architectural functions
- `tests/test_tier15.py` — 40 tests covering NURBS curves + stub verification
- Total test count: **491** (all passing)

### Notes
- Tier 15B (SubD): FreeCAD 1.1.1 has no native SubD support. All functions raise `NotImplementedError`. Options (OpenSubDiv integration, Blender exchange) deferred to Milestone 5.
- `helix_curve` approximates via BSpline interpolation through 32 × turns sampled points — sufficient for sweep paths; not exact NURBS helix.

---

## [0.3.0] — 2026-05-18 — Milestone 3: Mechanical Depth

### Added

**Presets** (`presets/screws.py`, `presets/bearings.py`)
- ISO metric screw dimension tables M2–M20 (thread, head, nut, washer, clearance, heat-set insert dims)
- ISO ball bearing tables — 600/620/630 series

**Tier 4 — Mechanical Features** (`tier04_mechanical.py`)
- 20 functions: `boss`, `counterbore_hole`, `countersink_hole`, `slot_hole`, `keyway`, `rib`, `gusset`, `flange`, `lip`, `l_bracket`, `t_bracket`, `u_bracket`, `tab`, `slot_cutout`, `dovetail_pin`, `dovetail_slot`, `tongue`, `groove`, `living_hinge`, `snap_clip`

**Tier 5 — Fasteners** (`tier05_fasteners.py`)
- 14 functions: `threaded_rod`, `tapped_hole`, `hex_bolt`, `socket_head_bolt`, `button_head_bolt`, `flat_head_bolt`, `hex_nut`, `flat_washer`, `lock_washer`, `heat_set_insert_pocket`, `clearance_hole`, `screw_size_preset`, `standoff`, `dowel_pin`
- Cosmetic thread geometry; `cosmetic=False` raises `NotImplementedError`

**Tier 6 — Mechanical Components** (`tier06_mechanical_components.py`)
- 7 functions: `spur_gear` (16-pt involute polyline), `bevel_gear`, `rack`, `pulley_timing`, `sprocket`, `bearing_pocket`, `shaft_coupling`

**Tests**
- `tests/test_tier04.py`, `test_tier05.py`, `test_tier06.py` — 147 new tests
- Total at end of Milestone 3: **340** (all passing)

### Fixed
- `Part.Wire(edges)` fails on non-connected edges — replaced with `Part.makePolygon(pts)` for complex profiles (spur gear involute)

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

[Unreleased]: https://github.com/williamblair333/partikus/compare/v0.6.0...HEAD
[0.6.0]: https://github.com/williamblair333/partikus/compare/v0.5.0...v0.6.0
[0.5.0]: https://github.com/williamblair333/partikus/compare/v0.4.0...v0.5.0
[0.4.0]: https://github.com/williamblair333/partikus/compare/v0.3.0...v0.4.0
[0.3.0]: https://github.com/williamblair333/partikus/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/williamblair333/partikus/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/williamblair333/partikus/releases/tag/v0.1.0
