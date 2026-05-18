# Partikus — Project Handoff

**Project name:** `partikus`
**Tagline:** A parametric CAD toolkit. Every part has its place.
**Target:** FreeCAD-based parametric shape library with GUI dialogs, structured for future AI-driven image-to-model decomposition
**Document purpose:** Complete specification for a Claude Code (or equivalent) implementation session. This document is the single source of truth for scope, architecture, and conventions.

---

## 1. Executive Summary

Build a Python-based parametric CAD toolkit on top of FreeCAD that:

1. Provides a comprehensive library of pre-made parametric shapes ("tools"), organized into 16 tiers from raw primitives through freeform NURBS/SubD surfaces.
2. Exposes each shape through a GUI dialog where parameters are entered and the result is generated as a FreeCAD object.
3. Uses a consistent anchor/attachment system so shapes can be programmatically positioned relative to one another without hand-calculated coordinates.
4. Is structured so that an AI agent can later parse an image, decompose it into toolkit components, and generate the assembly script automatically — with no human-facing dialog required in the steady state.

The architecture must be coherent from day one even if implementation is phased. Naming, parameter conventions, and the anchor system must be designed for AI legibility from the start.

---

## 2. Vision & Roadmap

**Phase 1 — Manual Toolkit (MVP)**
The user invokes a tool, a dialog pops up, parameters are entered, a FreeCAD object is created. Multiple objects can be combined manually using boolean operation tools. This phase delivers immediate utility and validates the core architecture.

**Phase 2 — AI-Assisted Decomposition**
The user provides a reference image. An AI agent analyzes the image, decomposes it into toolkit primitives and operations, generates a Python build script, and presents it for review before execution. The dialog system still exists as a manual fallback.

**Phase 3 — Full Automation**
The AI generates and executes build scripts directly. Dialogs and review steps remain available but are not the default path.

**Architectural implication:** The dialog layer is a thin wrapper over a pure-Python API. The API itself must always be the primary interface. Dialogs call the API; AI calls the same API. Same functions, same parameter names, same return values.

---

## 3. Target Environment & Stack

- **CAD kernel:** FreeCAD (uses OpenCASCADE under the hood)
- **Language:** Python 3 (FreeCAD's embedded Python)
- **GUI toolkit:** PySide2 / Qt (FreeCAD's bundled GUI framework)
- **File format:** Native FreeCAD `.FCStd` for working files; export to STEP, STL, OBJ, IGES as needed
- **Distribution:** Initially a FreeCAD macro/workbench; later potentially a standalone Python package
- **Units:** Millimeters as the canonical internal unit. All parameters are mm unless suffix indicates otherwise (`_deg` for degrees, `_count` for integer counts, `_mm` is implicit and omitted for brevity).

---

## 4. Architectural Principles

1. **Pure API first.** Every shape and operation is a Python function that takes parameters and returns a FreeCAD `Part.Shape` or `Part::Feature` object. The dialog is a wrapper.
2. **Consistent parameter naming.** See §6. Same concepts use the same words across all functions. `length`, `width`, `height`, `diameter`, `radius`, `wall_thickness`, `inner_diameter`, `outer_diameter`, etc. Never `len`, `wid`, `dia`, `thick`.
3. **Anchors are first-class.** Every shape exposes named anchor points. Positioning is done by anchor-to-anchor attachment, not by raw coordinates. See §7.
4. **Stateless functions where possible.** Shape constructors should not mutate global state. They return objects. A separate document/scene layer manages what gets added to the FreeCAD document.
5. **Composable.** The output of any shape function must be a valid input to any boolean or modifier function. No special-case "this only works on cylinders" logic.
6. **Self-documenting.** Every function has a docstring listing parameters, units, default values, and one usage example. This serves both humans and the future AI consumer.
7. **AI legibility.** Function names and parameter names should be guessable from a natural-language description. If an AI sees "a cylinder with a flat cap on top, 50mm tall, 20mm diameter, 3mm wall," it should be able to write `capped_cylinder(height=50, diameter=20, wall_thickness=3, cap_style="flat")` without reading source code.

---

## 5. Complete Tier Specification

### Tier 0 — Foundations / Coordinate System

The scaffolding everything else depends on. Implement first.

- Anchor point constants: `TOP`, `BOTTOM`, `FRONT`, `BACK`, `LEFT`, `RIGHT`, `CENTER`
- Box-specific corner anchors: `TOP_FRONT_LEFT`, `TOP_FRONT_RIGHT`, etc. (8 corners)
- Box-specific edge midpoint anchors: `TOP_FRONT_EDGE`, `BOTTOM_LEFT_EDGE`, etc. (12 edges)
- Orientation vectors: `UP`, `DOWN`, `NORTH`, `SOUTH`, `EAST`, `WEST`
- Reference planes: `PLANE_XY`, `PLANE_XZ`, `PLANE_YZ`
- Axis constants: `AXIS_X`, `AXIS_Y`, `AXIS_Z`
- Origin / datum point primitive

### Tier 1 — Raw 3D Primitives

The universal building blocks.

- `box(length, width, height)`
- `cylinder(diameter, height)` — also accepts `radius`
- `sphere(diameter)` — also accepts `radius`
- `cone(base_diameter, top_diameter, height)` — `top_diameter=0` gives a point
- `torus(major_diameter, minor_diameter)` — donut
- `wedge(length, width, height)` — right-triangular ramp
- `pyramid(base_length, base_width, height)` — square or rectangular base
- `disk(diameter, thickness)` — flat puck
- `polyhedron(vertices, faces)` — generic, for custom shapes

### Tier 2 — Enhanced Primitives

Same primitives, common variations baked in.

- `rounded_box(length, width, height, fillet_radius, edges=ALL)` — fillet can target specific edges
- `chamfered_box(length, width, height, chamfer_size, edges=ALL)`
- `rounded_cylinder(diameter, height, fillet_radius, ends=BOTH)`
- `tube(outer_diameter, inner_diameter, height)` — hollow cylinder
- `tube_by_wall(outer_diameter, wall_thickness, height)` — alternate spec
- `hollow_box(length, width, height, wall_thickness, open_face=TOP)` — open container
- `hemisphere(diameter)` — half sphere
- `spherical_cap(diameter, height)` — partial sphere cap
- `frustum(base_diameter, top_diameter, height)` — truncated cone (alias of cone with both diameters > 0)
- `prism(sides, diameter, height)` — n-sided regular prism
- `rounded_prism(sides, diameter, height, fillet_radius)`
- `stepped_cylinder(diameters, heights)` — accepts lists; creates stacked cylinders

### Tier 3 — 2D Profiles

Building blocks for extrusion, revolution, sweep, and loft.

- `rectangle(length, width)`
- `rounded_rectangle(length, width, fillet_radius)`
- `chamfered_rectangle(length, width, chamfer_size)`
- `circle(diameter)`
- `ellipse(major_diameter, minor_diameter)`
- `regular_polygon(sides, diameter)`
- `star(points, outer_diameter, inner_diameter)`
- `slot(length, width)` — rounded-end rectangle
- `teardrop(diameter, angle=45)` — for 3D-printable horizontal holes
- `arc(radius, start_angle_deg, end_angle_deg)`
- `polyline(points)` — list of 2D points

### Tier 4 — Mechanical Features

Compound functional shapes used constantly in mechanical design.

- `boss(diameter, height, hole_diameter=None)` — raised cylinder for screw mount
- `counterbore_hole(thru_diameter, bore_diameter, bore_depth, depth)`
- `countersink_hole(thru_diameter, head_diameter, head_angle_deg=82, depth)`
- `slot_hole(length, width, depth)`
- `keyway(width, depth, length)`
- `rib(length, height, thickness, draft_angle_deg=0)`
- `gusset(length, height, thickness)` — triangular reinforcement
- `flange(inner_diameter, outer_diameter, thickness, hole_pattern=None)`
- `lip(outer_diameter, height, lip_width, lip_height)` — for snap-fit rim
- `l_bracket(length, height, thickness, width)`
- `t_bracket(arm_length, stem_length, width, thickness)`
- `u_bracket(length, height, width, thickness, leg_height)`
- `tab(width, height, thickness)` and `slot_cutout(width, height, depth)` — mating pair
- `dovetail_pin(length, narrow_width, wide_width, height)`
- `dovetail_slot(...)` — mating partner
- `tongue(length, width, height)` and `groove(length, width, depth)` — mating pair
- `living_hinge(length, thickness, hinge_width)` — thin flex region
- `snap_clip(length, width, hook_height, flex_arm_length)`

### Tier 5 — Fasteners & Standard Parts

Standardized hardware. Use ISO/ANSI standard dimensions internally; expose presets for common sizes.

**Threaded rods & nuts:**
- `threaded_rod(diameter, length, pitch=None, thread_form="metric")` — default pitch from standard table
- `tapped_hole(diameter, depth, pitch=None)`
- `threaded_rod_acme(...)`, `threaded_rod_trapezoidal(...)`

**Bolts & screws:**
- `hex_bolt(diameter, length, head_height=None, head_across_flats=None)`
- `socket_head_bolt(diameter, length)`
- `button_head_bolt(diameter, length)`
- `flat_head_bolt(diameter, length)` — countersunk
- `wood_screw(diameter, length)`

**Nuts:**
- `hex_nut(diameter, height=None, across_flats=None)`
- `square_nut(diameter)`
- `wing_nut(diameter)`
- `lock_nut(diameter)` — nyloc style

**Washers:**
- `flat_washer(bolt_diameter, outer_diameter=None, thickness=None)`
- `lock_washer(bolt_diameter)`
- `spring_washer(bolt_diameter)`
- `fender_washer(bolt_diameter)`

**Inserts & holes:**
- `heat_set_insert_pocket(insert_size)` — e.g. M3, M4
- `clearance_hole(bolt_size, depth, fit="close")` — "close", "normal", or "loose"
- `screw_size_preset(name)` — returns dict for M2, M2.5, M3, M4, M5, M6, M8, M10, M12, #2, #4, #6, #8, #10, 1/4-20, etc.

**Other standards:**
- `standoff(diameter, length, thread_size=None)`
- `dowel_pin(diameter, length)`
- `rivet(diameter, head_diameter, length)`

### Tier 6 — Mechanical Components

Functional assemblies, often interfacing with off-the-shelf hardware.

- `spur_gear(teeth, module, thickness, pressure_angle_deg=20)` — involute profile
- `bevel_gear(teeth, module, cone_angle_deg, thickness)`
- `worm(diameter, length, pitch)` and `worm_wheel(...)`
- `rack(teeth, module, length, height)`
- `pulley_timing(teeth, belt_type, width)` — GT2, HTD, etc.
- `pulley_v_belt(diameter, groove_count, width)`
- `pulley_smooth(diameter, width)`
- `sprocket(teeth, chain_pitch, thickness)`
- `hinge_pin(length, pin_diameter, leaf_count)`
- `hinge_continuous(length, ...)`
- `living_hinge_pattern(length, width, thickness)` — laser-cuttable flex pattern
- `bearing_pocket(bearing_id, depth)` — `bearing_id` is "608", "6004", "6800", etc.
- `linear_bearing_mount(bearing_type)` — LM8UU, LM10UU, etc.
- `belt_clamp(belt_type, width)`
- `shaft_coupling(shaft1_diameter, shaft2_diameter, length)`

### Tier 7 — Container / Enclosure Features

- `lid(outer_dim, rim_height, rim_inset, wall_thickness)` — fits matching container
- `snap_fit_box(length, width, height, wall_thickness, snap_count=4)`
- `hinged_box(length, width, height, wall_thickness, hinge_side=BACK)`
- `magnetic_recess(magnet_diameter, magnet_thickness, count=1)`
- `battery_compartment(battery_type, count, contact_style="spring")` — "AA", "AAA", "18650", "CR2032", etc.
- `cable_channel(width, depth, length)`
- `strain_relief(cable_diameter, length)`
- `vent_slots(length, width, slot_count, slot_width)`
- `display_window(length, width, recess_depth=0)`
- `button_cutout(diameter, shape="round")` — also "square"

### Tier 8 — Electronics Mounting (optional but high-value)

- `pcb_standoff(height, hole_diameter, base_diameter)`
- `raspberry_pi_mount(model)` — "3B", "4B", "Zero", "5", etc.
- `arduino_mount(model)` — "uno", "mega", "nano", "leonardo"
- `led_holder(led_diameter, panel_thickness)` — 3mm, 5mm, 10mm common sizes
- `usb_cutout(connector_type)` — "USB-A", "USB-B", "USB-C", "Micro-USB", "Mini-USB"
- `hdmi_cutout(connector_type)` — "full", "mini", "micro"
- `barrel_jack_cutout(outer_diameter, inner_diameter)`
- `din_rail_clip(rail_type="35mm")`
- `heatsink_fin_array(base_length, base_width, fin_count, fin_height, fin_thickness)`

### Tier 9 — Boolean Operations

The three classics plus two power tools.

- `union(*shapes)` / `fuse(*shapes)` — same function, two names
- `difference(base, *to_subtract)` / `cut(...)` — same function, two names
- `intersection(*shapes)` / `intersect(...)`
- `hull(*shapes)` — convex hull encompassing all inputs
- `minkowski_sum(shape, kernel)` — useful for offset/rounding via small sphere kernel

### Tier 10 — Edge & Surface Modifiers

Applied to existing shapes.

- `fillet(shape, radius, edges=ALL)` — round edges
- `chamfer(shape, size, edges=ALL)` — bevel edges
- `shell(shape, wall_thickness, open_faces=[])` — hollow out a solid
- `offset(shape, distance)` — uniform inflation/deflation
- `draft(shape, angle_deg, face, neutral_plane)` — taper walls
- `emboss(shape, profile_2d, depth, face)` — raised pattern/text
- `deboss(shape, profile_2d, depth, face)` — recessed pattern/text
- `knurl(shape, pattern="diamond", depth, pitch)` — surface texture
- `surface_texture(shape, texture, depth)` — repeating pattern

### Tier 11 — Pattern / Array Operations

- `linear_array(shape, count, spacing, axis=AXIS_X)`
- `grid_array(shape, count_x, count_y, spacing_x, spacing_y)`
- `polar_array(shape, count, radius, center_axis=AXIS_Z, full_angle_deg=360)`
- `mirror(shape, plane)` — keeps both copies; use `mirror_replace` to replace original
- `helix_array(shape, count, radius, pitch, turns)`
- `honeycomb_fill(area_shape, cell_diameter, wall_thickness)`
- `path_array(shape, path_curve, count)` — copies follow an arbitrary curve

### Tier 12 — Sweep / Loft Operations

Generating 3D solids from 2D profiles.

- `extrude(profile_2d, height, taper_angle_deg=0)`
- `revolve(profile_2d, axis, angle_deg=360)`
- `sweep(profile_2d, path_curve, twist_deg=0)`
- `loft(profile_list, closed=False, ruled=False)` — blend between cross-sections
- `pipe(path_curve, diameter, wall_thickness=0)` — convenience: sweep a circle/tube

### Tier 13 — Architectural

- `wall(length, height, thickness, openings=[])` — openings are list of door/window dicts
- `door(width, height, thickness=40)`
- `window(width, height, frame_thickness=50)`
- `stairs(total_rise, total_run, tread_count, width)`
- `roof_gable(length, width, peak_height, overhang=0)`
- `roof_hip(length, width, peak_height)`
- `roof_shed(length, width, low_height, high_height)`
- `column(diameter, height, base_size=None, capital_size=None)`
- `beam(length, cross_section_profile)`
- `slab(length, width, thickness)`
- `truss_simple(length, height, panel_count)`

### Tier 14 — Assembly / Positioning System

The make-or-break tier. Without this, AI-driven assembly is unworkable.

- `attach(child, parent, child_anchor, parent_anchor, offset=0, rotation_deg=0)` — places child's anchor at parent's anchor
- `stack_on(child, parent, alignment=CENTER)` — convenience: attach child BOTTOM to parent TOP
- `place_beside(child, parent, side, alignment=CENTER, gap=0)`
- `align(shape_a, shape_b, axis, anchor=CENTER)` — align two shapes along an axis
- `coaxial(shape_a, shape_b)` — share central axis
- `concentric(shape_a, shape_b)` — same center point (2D)
- `tangent(shape_a, shape_b, side)` — touch externally on given side
- `translate(shape, dx, dy, dz)` — raw move
- `rotate(shape, axis, angle_deg, center=None)` — raw rotate
- `scale(shape, factor)` or `scale(shape, fx, fy, fz)` — uniform or per-axis
- `mirror_position(shape, plane)` — flip position without keeping original

**Anchor system requirement:** Every shape returned by any Tier 1–13 function must carry metadata describing its anchor points in world coordinates. After any transform, anchors update automatically. Implementation likely involves a wrapper class around `Part.Shape` that tracks anchors as a dict.

### Tier 15 — Freeform / NURBS & SubD Surfaces

**15A — NURBS curves & surfaces (precise freeform):**

*Curves:*
- `nurbs_curve(control_points, weights=None, degree=3, knots=None)`
- `bspline_curve(control_points, degree=3)`
- `bezier_curve(control_points)`
- `curve_through_points(points, smooth=True)`
- `helix_curve(diameter, pitch, turns, taper=0)`
- `conic_curve(type, params)` — "parabola", "hyperbola", "ellipse"

*Surfaces:*
- `loft_surface(profile_curves, ruled=False)`
- `network_surface(u_curves, v_curves)`
- `sweep_1rail(profile, rail)`
- `sweep_2rail(profile, rail_a, rail_b)`
- `patch_fill(boundary_curves)`
- `boundary_surface(curves)` — 3 or 4 edge curves
- `surface_from_points(point_grid_2d)`

*Surface editing:*
- `move_control_point(surface, u_index, v_index, new_position)`
- `trim_surface(surface, trim_curve)`
- `untrim_surface(surface)`
- `split_surface(surface, splitter)`
- `join_surfaces(*surfaces)`
- `rebuild_surface(surface, u_count, v_count, degree=3)`
- `offset_surface(surface, distance)`
- `match_surfaces(surface_a, surface_b, continuity="G1")` — "G0", "G1", "G2"
- `surface_fillet(surface_a, surface_b, radius)`
- `variable_fillet(surface_a, surface_b, radius_function)`
- `surface_chamfer(surface_a, surface_b, size)`

**15B — Subdivision surfaces (organic freeform):**

- `subd_primitive(type, ...)` — "cube", "sphere", "cylinder", "cone", "torus" as SubD
- `subd_push_pull(subd, faces, distance)`
- `subd_insert_loop(subd, edge, position=0.5)`
- `subd_bevel_edge(subd, edges, size, segments=1)`
- `subd_bevel_vertex(subd, vertices, size)`
- `subd_bridge(subd, faces_a, faces_b)`
- `subd_subdivide(subd, iterations=1)`
- `subd_crease(subd, edges, sharpness=1.0)`
- `subd_symmetry(subd, plane, mode="mirror")`
- `subd_soft_select(subd, vertices, falloff_radius)`
- `subd_sculpt_brush(subd, point, brush_type, strength, radius)` — "push", "pull", "smooth", "pinch", "inflate", "flatten"

**15C — Conversion bridges:**

- `subd_to_nurbs(subd, target_tolerance=0.01)`
- `nurbs_to_subd(surface, density="medium")`
- `mesh_to_subd(mesh, preserve_features=True)`
- `mesh_to_nurbs(mesh, patch_size="auto")`

**15D — Continuity & quality analysis:**

- `analyze_curvature(surface, mode="gaussian")` — "gaussian", "mean", "max", "min"
- `analyze_zebra(surface)` — reflection stripes for continuity check
- `analyze_reflection(surface, environment_map=None)`
- `analyze_draft(shape, pull_direction)` — moldability check
- `analyze_deviation(surface, reference)` — compare to scan or target

---

## 6. Parameter Naming Conventions

**Required vocabulary:**

| Concept | Use this | Never use |
|---|---|---|
| linear extent X | `length` | `len`, `l`, `size_x` |
| linear extent Y | `width` | `wid`, `w`, `size_y` |
| linear extent Z | `height` | `hgt`, `h`, `size_z`, `depth` (depth means something else) |
| cylinder/circle size | `diameter` | `dia`, `d` (use `radius` only if diameter would be awkward) |
| hollow shape, outside | `outer_diameter` | `od`, `outer_dia` |
| hollow shape, inside | `inner_diameter` | `id`, `inner_dia` |
| material thickness | `wall_thickness` or `thickness` | `thick`, `t`, `wall` |
| recess into a face | `depth` | `dep`, `recess` |
| edge rounding | `fillet_radius` | `radius`, `r`, `round` |
| edge beveling | `chamfer_size` | `bevel`, `cham`, `c` |
| count of features | `count` or `<thing>_count` | `n`, `num`, `qty` |
| angular value | suffix `_deg` (e.g., `taper_angle_deg`) | bare `angle` |
| pitch (threads, gears) | `pitch` | `p` |

**Defaults:** Provide sensible defaults for everything possible. M3 hardware defaults to ISO standard dimensions. Box defaults to 10×10×10. Cylinder defaults to D=10, H=20.

**Units:** mm everywhere unless suffixed otherwise. Document this once at module level; don't repeat in every docstring.

---

## 7. Anchor / Attachment System Specification

This is the keystone. Without this working cleanly, the AI workflow fails.

**Every shape returned by toolkit functions must be wrapped in an object exposing:**
- `.shape` — the underlying `Part.Shape`
- `.anchors` — dict mapping anchor name → 3D position in world coordinates
- `.orientations` — dict mapping anchor name → outward-facing normal vector
- `.transform(matrix)` — applies a transform, returns new object with updated anchors

**Standard anchor names** (always present where geometrically meaningful):
`CENTER`, `TOP`, `BOTTOM`, `FRONT`, `BACK`, `LEFT`, `RIGHT`

**Box-specific anchors (additional):**
8 corners: `TOP_FRONT_LEFT`, `TOP_FRONT_RIGHT`, `TOP_BACK_LEFT`, `TOP_BACK_RIGHT`, `BOTTOM_FRONT_LEFT`, `BOTTOM_FRONT_RIGHT`, `BOTTOM_BACK_LEFT`, `BOTTOM_BACK_RIGHT`
12 edge midpoints: `TOP_FRONT_EDGE`, `TOP_BACK_EDGE`, `TOP_LEFT_EDGE`, `TOP_RIGHT_EDGE`, etc.

**Cylinder-specific:**
`TOP_RIM`, `BOTTOM_RIM` (the circular edges)

**Custom anchors:**
Functions may expose additional named anchors specific to that shape. Example: `boss(...)` exposes `SCREW_HOLE_TOP` and `SCREW_HOLE_BOTTOM`. Document custom anchors in the function's docstring.

**`attach()` semantics:**
```python
attach(child, parent, child_anchor=BOTTOM, parent_anchor=TOP, offset=0, rotation_deg=0)
```
Places `child` such that `child.anchors[child_anchor]` coincides with `parent.anchors[parent_anchor]`, aligned so that `child`'s anchor outward-normal opposes `parent`'s anchor outward-normal (parts face each other). `offset` separates them along the joining axis. `rotation_deg` rotates child about the joining axis.

---

## 8. GUI Dialog Specification

Each tool gets a dialog auto-generated from its function signature using Qt/PySide2.

**Layout:**
- Title: function name in human-readable form ("Rounded Box", "Spur Gear")
- Body: one labeled input field per parameter
- Field types: numeric spin box (with unit suffix label), dropdown for enum-style params (e.g., "edges"), checkbox for booleans
- Default values pre-filled
- Live preview pane (Phase 2 — not required for MVP)
- Buttons: Generate, Cancel, Help (opens docstring)

**Implementation:**
A single `auto_dialog(function)` utility introspects the function's signature, parameter types, and docstring to build the dialog dynamically. New tools require no GUI code — the dialog appears automatically once the function exists.

**Parameter type hints drive widget choice:**
- `float` → spin box with decimals
- `int` → spin box, integer only
- `bool` → checkbox
- `Literal["a", "b", "c"]` → dropdown
- `list[...]` → table widget with add/remove buttons
- Anchor constant → dropdown populated from anchor list

---

## 9. File / Module Organization

Suggested layout:

```
partikus/
├── README.md
├── HANDOFF.md                    # this document
├── partikus/
│   ├── __init__.py
│   ├── core/
│   │   ├── shape_wrapper.py      # the anchor-aware wrapper class
│   │   ├── anchors.py            # anchor constants and helpers
│   │   ├── transforms.py         # translate, rotate, scale
│   │   └── document.py           # FreeCAD document management
│   ├── tier01_primitives.py
│   ├── tier02_enhanced.py
│   ├── tier03_profiles_2d.py
│   ├── tier04_mechanical.py
│   ├── tier05_fasteners.py
│   ├── tier06_components.py
│   ├── tier07_enclosures.py
│   ├── tier08_electronics.py
│   ├── tier09_boolean.py
│   ├── tier10_modifiers.py
│   ├── tier11_patterns.py
│   ├── tier12_sweep_loft.py
│   ├── tier13_architectural.py
│   ├── tier14_assembly.py
│   ├── tier15a_nurbs.py
│   ├── tier15b_subd.py
│   ├── tier15c_conversion.py
│   ├── tier15d_analysis.py
│   ├── gui/
│   │   ├── auto_dialog.py        # introspection-based dialog builder
│   │   └── workbench.py          # FreeCAD workbench registration
│   └── presets/
│       ├── screws.py             # standard screw size tables
│       ├── bearings.py           # standard bearing dimensions
│       └── ...
├── tests/
│   ├── test_tier01.py
│   └── ...
└── examples/
    ├── capped_cylinder.py
    ├── enclosure_with_mounts.py
    └── ...
```

---

## 10. Implementation Roadmap

**Milestone 1 — Foundation (minimum to demonstrate the architecture):**
1. Core shape wrapper class with anchors
2. Tier 0 constants and helpers
3. Tier 1 primitives (all of them)
4. Tier 9 boolean operations (union, difference, intersection)
5. Tier 14 basic assembly: `attach`, `translate`, `rotate`
6. `auto_dialog()` utility
7. FreeCAD workbench registration so tools appear in the GUI

**Milestone 2 — Practical utility:**
8. Tier 2 enhanced primitives
9. Tier 3 2D profiles
10. Tier 10 modifiers (fillet, chamfer, shell)
11. Tier 11 patterns (linear, grid, polar, mirror)
12. Tier 12 sweep/loft

**Milestone 3 — Mechanical depth:**
13. Tier 4 mechanical features
14. Tier 5 fasteners with standard presets
15. Tier 6 mechanical components (gears, hinges, bearing pockets)

**Milestone 4 — Application-specific:**
16. Tier 7 enclosures
17. Tier 8 electronics
18. Tier 13 architectural

**Milestone 5 — Freeform:**
19. Tier 15A NURBS
20. Tier 15B SubD
21. Tier 15C conversion
22. Tier 15D analysis

**Milestone 6 — AI integration (separate project):**
23. Image analysis service that decomposes an image into a sequence of toolkit calls
24. Script generator that emits valid partikus Python
25. Review/preview interface

The toolkit must be useful at Milestone 1. Each subsequent milestone adds capability without changing earlier APIs.

---

## 11. Testing & Validation

- **Unit tests per tier:** each function tested with default params, edge params, and one combined-use case
- **Anchor consistency tests:** after every transform, every anchor's position must remain consistent with the underlying geometry
- **Round-trip tests:** export to STEP, re-import, verify geometry matches within tolerance
- **Visual regression tests:** render reference shapes to images; flag any pixel-level drift after code changes
- **AI legibility test:** for each tier, write 5 natural-language descriptions and verify they map unambiguously to function calls. This catches naming ambiguity early.

---

## 12. Future: Image-to-Model Workflow

For the eventual Phase 2/3 AI workflow, the architecture must support:

1. **Function discovery:** an introspection endpoint that returns the full function catalog with signatures, parameter names, types, defaults, and docstrings. The AI uses this as its tool list.
2. **Script execution sandbox:** generated scripts run in an isolated FreeCAD session; errors are returned as structured data the AI can reason about.
3. **Visual feedback:** rendered output is returned as an image so the AI can compare its work to the reference and iterate.
4. **Provenance:** every generated object carries metadata about the AI-generated source (prompt, decomposition steps, generation timestamp).

**Decomposition strategy the AI should follow:**
1. Identify the gross overall shape (which Tier 1 or Tier 2 primitive is the rough envelope?)
2. Identify secondary masses (more primitives, attached or subtracted)
3. Identify functional features (Tier 4 boss/rib/bracket, Tier 5 fastener interfaces)
4. Identify edge treatments (Tier 10 fillet/chamfer)
5. Identify patterns (Tier 11 array if repeated features exist)
6. Estimate dimensions from image scale references
7. Emit the script
8. Render and compare; iterate on dimension estimates

---

## 13. Open Questions for Implementation

These are decisions left to the implementer's judgment but worth flagging:

- Should the wrapper class subclass `Part.Shape` or compose around it? Composition is cleaner but requires forwarding many methods.
- Should anchors be computed lazily (on access) or eagerly (at construction)? Lazy is more memory-efficient but complicates serialization.
- Should the toolkit support FreeCAD's history-based parametric editing (`Part::FeaturePython`), or work purely with non-parametric `Part::Feature`? History-based is more powerful but more complex to implement correctly.
- For Tier 15 SubD, FreeCAD does not have native SubD support. Implementation likely requires integrating OpenSubDiv or a similar library, or punting SubD to a sister tool (Blender, with a STEP/OBJ exchange).
- For Tier 5 threaded parts, real threads are expensive geometrically. Provide a "cosmetic thread" mode (visual only) and "true thread" mode (full helical geometry)?

---

## 14. References

- FreeCAD Part Workbench: provides primitives, boolean operations, and the OpenCASCADE foundation
- FreeCAD Python scripting documentation: `Part.makeBox`, `Part.makeCylinder`, etc.
- BOSL2 (Belfry OpenSCAD Library v2): the closest existing analog to this toolkit's scope; useful reference for naming, parameter conventions, and the attachment/anchor system design. https://github.com/BelfrySCAD/BOSL2
- NopSCADlib: comprehensive parts library covering many Tier 5/6/8 items. https://github.com/nophead/NopSCADlib
- OpenCASCADE Technology documentation: the underlying CAD kernel FreeCAD uses; relevant for Tier 15 NURBS work.
- ISO standards for metric hardware (ISO 4014 hex bolts, ISO 4032 hex nuts, ISO 7089 washers, ISO 7045 pan head screws, etc.)

---

**End of handoff.**
