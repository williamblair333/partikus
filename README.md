# Partikus

> **A parametric CAD toolkit for FreeCAD. Every part has its place.**

[![Tests](https://img.shields.io/badge/tests-552%20passing-brightgreen)](#testing)
[![Python](https://img.shields.io/badge/python-3.11-blue)](https://www.python.org/)
[![FreeCAD](https://img.shields.io/badge/FreeCAD-1.1.1-orange)](https://www.freecad.org/)
[![License](https://img.shields.io/badge/license-LGPL--2.1-lightgrey)](LICENSE)
[![Milestone](https://img.shields.io/badge/milestone-6%20of%206-yellow)](#roadmap)

---

## What Is Partikus?

Partikus is a **Python parametric CAD toolkit** layered on top of FreeCAD's OpenCASCADE kernel. It provides a clean, composable function API for building 3D geometry — from primitive solids through swept surfaces — with a first-class **anchor system** that lets shapes snap together without manual coordinate arithmetic.

The architecture is built for three audiences at once:

| Audience | How they use it |
|---|---|
| **Human designers** | Call Python functions, combine results, export to STEP/STL |
| **FreeCAD GUI users** | Auto-generated dialogs appear for every function (no GUI code to write) |
| **AI agents (future)** | Decompose an image → emit toolkit calls → iterate on render feedback |

---

## Table of Contents

- [Quick Start](#quick-start)
- [Architecture Overview](#architecture-overview)
- [Tier Reference](#tier-reference)
  - [Tier 0 — Foundations](#tier-0--foundations)
  - [Tier 1 — Raw Primitives](#tier-1--raw-3d-primitives)
  - [Tier 2 — Enhanced Primitives](#tier-2--enhanced-primitives)
  - [Tier 3 — 2D Profiles](#tier-3--2d-profiles)
  - [Tier 7 — Container / Enclosure Features](#tier-7--container--enclosure-features)
  - [Tier 8 — Electronics Mounting](#tier-8--electronics-mounting)
  - [Tier 9 — Boolean Operations](#tier-9--boolean-operations)
  - [Tier 10 — Edge & Surface Modifiers](#tier-10--edge--surface-modifiers)
  - [Tier 11 — Pattern / Array Operations](#tier-11--pattern--array-operations)
  - [Tier 12 — Sweep / Loft](#tier-12--sweep--loft)
  - [Tier 13 — Architectural](#tier-13--architectural)
  - [Tier 14 — Assembly & Positioning](#tier-14--assembly--positioning)
  - [Tier 15A — NURBS Curves](#tier-15a--nurbs-curves)
- [Anchor System](#anchor-system)
- [Parameter Conventions](#parameter-conventions)
- [Testing](#testing)
- [Project Structure](#project-structure)
- [Roadmap](#roadmap)
- [Contributing](#contributing)
- [References](#references)

---

## Quick Start

### Prerequisites

- [FreeCAD 1.1.1](https://www.freecad.org/downloads.php) (AppImage or installed)
- Python 3.11 (bundled with FreeCAD)

### Headless / scripting

```bash
# Run any script via freecadcmd (no GUI required)
/path/to/FreeCAD_1.1.1.AppImage/squashfs-root/usr/bin/freecadcmd my_script.py
```

### Basic usage

```python
from partikus import box, cylinder, difference, attach, TOP, BOTTOM

# A box with a cylindrical hole through it
body = box(40, 20, 10)
hole = cylinder(diameter=8, height=15)
part = difference(body, hole)

# Stack a rounded boss on top
from partikus import rounded_cylinder, stack_on
boss = rounded_cylinder(diameter=12, height=6, fillet_radius=1)
assembly = stack_on(boss, part)
```

### Sweep a profile along a path

```python
import Part, FreeCAD
from partikus import circle, sweep

path = Part.Wire([Part.LineSegment(
    FreeCAD.Vector(0, 0, 0),
    FreeCAD.Vector(0, 0, 50)
).toShape()])

pipe = sweep(circle(diameter=10), path)
```

### 2D profile → extruded solid

```python
from partikus import rounded_rectangle, extrude

profile = rounded_rectangle(30, 20, fillet_radius=3)
solid   = extrude(profile, height=8)
```

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        partikus API                             │
│  tier00  tier01  tier02  tier03  tier09  tier10  tier11  tier12 │
│                       tier14                                    │
└──────────────────────────┬──────────────────────────────────────┘
                           │  PartikusShape wrapper
                           │  .shape  .anchors  .orientations
                           │
              ┌────────────▼────────────────┐
              │   FreeCAD / OpenCASCADE     │
              │   Part.Shape, Part.Wire     │
              └─────────────────────────────┘
```

### `PartikusShape` — the core wrapper

Every shape-producing function returns a `PartikusShape`, not a raw `Part.Shape`:

```python
class PartikusShape:
    shape        # Part.Shape — the raw OpenCASCADE geometry
    anchors      # dict[str, FreeCAD.Vector] — named 3D points
    orientations # dict[str, FreeCAD.Vector] — outward normals per anchor
```

Anchors persist through transforms. After `translate(s, dz=10)`, `s.anchors["TOP"]` moves by 10 automatically.

### Design decisions

| Decision | Choice | Reason |
|---|---|---|
| Subclass vs compose `Part.Shape` | **Compose** | Avoids OCCT ABI hazards; keeps wrapper testable outside FreeCAD |
| Parametric history | **No** (non-parametric `Part::Feature`) | Simpler; AI workflow doesn't need edit history |
| Eager vs lazy anchors | **Eager** | Computed once at construction; no staleness risk |
| Arrays | `Part.makeCompound` not fuse | Order-of-magnitude faster for large arrays |
| 2D profile plane | **XY plane (Z=0)** | Consistent; `revolve` around Z uses `polyline(Y=0)` |

---

## Tier Reference

### Tier 0 — Foundations

Coordinate constants imported automatically with `from partikus import *`.

**Orientation vectors**

| Name | Value |
|---|---|
| `UP` / `DOWN` | `(0, 0, ±1)` |
| `NORTH` / `SOUTH` | `(0, ±1, 0)` |
| `EAST` / `WEST` | `(±1, 0, 0)` |

**Anchor name constants**

```
CENTER   TOP       BOTTOM    FRONT     BACK      LEFT      RIGHT

TOP_FRONT_LEFT     TOP_FRONT_RIGHT    TOP_BACK_LEFT     TOP_BACK_RIGHT
BOTTOM_FRONT_LEFT  BOTTOM_FRONT_RIGHT BOTTOM_BACK_LEFT  BOTTOM_BACK_RIGHT

TOP_FRONT_EDGE  TOP_BACK_EDGE  TOP_LEFT_EDGE  TOP_RIGHT_EDGE
BOTTOM_FRONT_EDGE  BOTTOM_BACK_EDGE  BOTTOM_LEFT_EDGE  BOTTOM_RIGHT_EDGE
FRONT_LEFT_EDGE    FRONT_RIGHT_EDGE  BACK_LEFT_EDGE    BACK_RIGHT_EDGE

TOP_RIM   BOTTOM_RIM   (cylinders / disks)
```

**Reference planes & axes**

```python
PLANE_XY, PLANE_XZ, PLANE_YZ
AXIS_X, AXIS_Y, AXIS_Z
ORIGIN
```

---

### Tier 1 — Raw 3D Primitives

All shapes are **bounding-box centred at the world origin**.

```python
box(length=10, width=10, height=10)

cylinder(diameter=10, height=20)          # also: radius=
sphere(diameter=10)                       # also: radius=
cone(base_diameter=20, top_diameter=0, height=20)
torus(major_diameter=20, minor_diameter=4)

wedge(length, width, height)              # right-triangular ramp
pyramid(base_length, base_width, height)  # rectangular-base pyramid
disk(diameter, thickness)                 # thin flat puck
polyhedron(vertices, faces)               # arbitrary closed shell
```

> **Coordinate convention:** X+ = RIGHT, Y+ = FRONT, Z+ = UP. All dimensions in **mm**.

---

### Tier 2 — Enhanced Primitives

Tier 1 shapes with common modifications pre-applied.

```python
rounded_box(length, width, height, fillet_radius, edges=None)
chamfered_box(length, width, height, chamfer_size, edges=None)
rounded_cylinder(diameter, height, fillet_radius, ends="BOTH")
  # ends: "BOTH" | "TOP" | "BOTTOM"

tube(outer_diameter, inner_diameter, height)
tube_by_wall(outer_diameter, wall_thickness, height)
hollow_box(length, width, height, wall_thickness, open_face="TOP")

hemisphere(diameter)
spherical_cap(diameter, height)           # partial sphere section
frustum(base_diameter, top_diameter, height)  # truncated cone

prism(sides, diameter, height)            # regular n-sided prism (n ≥ 3)
rounded_prism(sides, diameter, height, fillet_radius)
stepped_cylinder(diameters, heights)      # lists of equal length
```

**Example — stepped shaft**

```python
shaft = stepped_cylinder(
    diameters=[20, 15, 10],
    heights=[10,   8,  5],
)
```

---

### Tier 3 — 2D Profiles

All profiles return a `Part.Wire` in the **XY plane** at Z=0, centred at origin. Feed them into `extrude`, `sweep`, `loft`, or `revolve`.

```python
rectangle(length=10, width=10)
rounded_rectangle(length, width, fillet_radius)   # raises ValueError if radius too large
chamfered_rectangle(length, width, chamfer_size)

circle(diameter=10)                       # also: radius=
ellipse(major_diameter, minor_diameter)
regular_polygon(sides, diameter)          # sides ≥ 3
star(points, outer_diameter, inner_diameter)

slot(length, width)                       # oblong; length == width → circle
teardrop(diameter, angle=45)              # 3D-print-friendly horizontal hole profile
arc(radius, start_angle_deg, end_angle_deg)  # open wire
polyline(points, closed=False)            # 2D (x,y) or 3D (x,y,z) tuples
```

> **Revolve tip:** for shapes revolved around the Z axis, use `polyline` with Y=0 (points in the XZ plane). The Y=0 constraint keeps the profile on the correct side of the axis.

---

### Tier 7 — Container / Enclosure Features

```python
lid(length=60, width=40, rim_height=5, rim_inset=1, wall_thickness=2)
  # flat lid with downward seating rim

snap_fit_box(length, width, height, wall_thickness=2, snap_count=4)
  # open-top box with snap-tab clips on outer walls

hinged_box(length, width, height, wall_thickness=2, hinge_side="BACK")
  # two-piece box joined by a living-hinge strip; hinge_side: FRONT|BACK|LEFT|RIGHT

magnetic_recess(magnet_diameter, magnet_thickness, count=1, spacing=10)
  # cylindrical press-fit pockets for disc magnets

battery_compartment(battery_type="AA", count=1, wall_thickness=1.5, contact_clearance=2)
  # tray for AA | AAA | C | D | 9V | 18650 | CR2032 | CR2025 | CR2016

cable_channel(width, depth, length, wall_thickness=1.5)
  # U-shaped cable routing channel

strain_relief(cable_diameter, length, wall_thickness=2, clamp_gap=1)
  # split-collar cable clamp

vent_slots(length, width, slot_count=5, slot_width=2, depth=2, wall_thickness=1)
  # panel with evenly-spaced rectangular ventilation slots

display_window(length, width, recess_depth=0, border_thickness=3, panel_thickness=2)
  # panel with rectangular viewing aperture; optional stepped recess

button_cutout(diameter, panel_thickness=2, shape="round")
  # panel through-hole for a button; shape: "round" | "square"
```

---

### Tier 8 — Electronics Mounting

```python
pcb_standoff(height=8, hole_diameter=3.2, base_diameter=6)
  # hollow cylindrical standoff for M2.5/M3 PCB screws

raspberry_pi_mount(model="4B", standoff_height=8, hole_diameter=2.9)
  # mounting plate + standoffs for: 3B | 3B+ | 4B | 5 | Zero | Zero2

arduino_mount(model="uno", standoff_height=8, hole_diameter=3.2)
  # mounting plate + standoffs for: uno | mega | nano | leonardo | micro

led_holder(led_diameter=5, panel_thickness=2, retention_lip=0.5)
  # press-fit panel mount for 3 mm / 5 mm / 10 mm LEDs

usb_cutout(connector_type="USB-C", panel_thickness=2, clearance=0.3)
  # connector_type: USB-A | USB-B | USB-C | Micro-USB | Mini-USB

hdmi_cutout(connector_type="full", panel_thickness=2, clearance=0.3)
  # connector_type: full | mini | micro

barrel_jack_cutout(outer_diameter=8, panel_thickness=2, clearance=0.2)
  # common sizes: 5.5 mm, 6.3 mm, 8.0 mm

din_rail_clip(rail_type="35mm", clip_length=40, wall_thickness=2.5)
  # snap-on clip for EN 60715 TS 35 or TS 15 DIN rails

heatsink_fin_array(base_length, base_width, fin_count=8,
                   fin_height=15, fin_thickness=1.5, base_thickness=3)
  # rectangular extruded-fin heatsink on flat base plate
```

---

### Tier 9 — Boolean Operations

```python
union(*shapes)          # alias: fuse(*shapes)
difference(base, *subs) # alias: cut(base, *subs)
intersection(*shapes)   # alias: intersect(*shapes)

hull(*shapes)           # NotImplementedError — planned Milestone 3
minkowski_sum(a, b)     # NotImplementedError — planned Milestone 3
```

---

### Tier 10 — Edge & Surface Modifiers

```python
fillet(shape, radius, edges=None)
  # edges=None → all edges; pass a list of Part.Edge for selective filleting

chamfer(shape, size, edges=None)

shell(shape, wall_thickness, open_faces=None)
  # open_faces: list of anchor name strings, e.g. ["TOP", "BOTTOM"]
  # open_faces=None → opens TOP face

offset(shape, distance)
  # positive → inflates; negative → deflates
```

---

### Tier 11 — Pattern / Array Operations

All array functions return a `Part.makeCompound` (not a fused solid), so volume = sum of parts.

```python
linear_array(shape, count, spacing, axis=(1,0,0))
  # centred on origin along axis; count ≥ 1

grid_array(shape, count_x, count_y, spacing_x, spacing_y)
  # centred 2D grid in XY plane

polar_array(shape, count, radius, center_axis=(0,0,1), full_angle_deg=360)
  # evenly-spaced copies around center_axis

mirror(shape, plane)
  # plane: "XY" | "XZ" | "YZ"
  # returns compound of original + mirrored copy
```

---

### Tier 12 — Sweep / Loft

```python
extrude(profile_2d, height, taper_angle_deg=0)
  # taper_angle_deg != 0 → NotImplementedError (draft via Tier 10)

revolve(profile_2d, axis=(0,0,1), angle_deg=360)

sweep(profile_2d, path_curve, twist_deg=0)
  # path_curve: Part.Wire

loft(profile_list, closed=False, ruled=False)
  # profile_list: list of Part.Wire at different Z positions

pipe(path_curve, diameter, wall_thickness=0)
  # convenience: sweeps a circle (or tube) along path
  # wall_thickness > diameter/2 → ValueError
```

---

### Tier 13 — Architectural

All dimensions in **mm**.

```python
wall(length=3000, height=2400, thickness=200, openings=[])
  # openings: list of {"x_offset", "z_offset", "width", "height"} dicts

door(width=900, height=2100, thickness=40)
window(width=1200, height=1200, frame_thickness=50, depth=80)

stairs(total_rise=2400, total_run=3600, tread_count=12, width=900)

roof_gable(length=6000, width=4000, peak_height=1500, overhang=300)
roof_hip(length=6000, width=4000, peak_height=1500, overhang=300)
roof_shed(length=4000, width=3000, low_height=2000, high_height=2800)

column(diameter=300, height=3000, base_size=None, capital_size=None)
  # base_size / capital_size: square plinth/capital side length (mm)

beam(length=3000, cross_section_profile=None, width=100, height=200)
  # cross_section_profile: Part.Wire in YZ plane; None → rectangular section

slab(length=6000, width=4000, thickness=200)

truss_simple(length=6000, height=800, panel_count=6,
             member_width=50, member_height=100)
  # planar Pratt truss — top/bottom chords, verticals, alternating diagonals
```

---

### Tier 15A — NURBS Curves & Surfaces

Curves and surface operations are implemented. `untrim_surface`, `match_surfaces`, `variable_fillet`, and `surface_chamfer` are stubbed (require BRep editing APIs not exposed in FreeCAD 1.x).

**Curves**

```python
nurbs_curve(control_points, weights=None, degree=3, knots=None)
bspline_curve(control_points, degree=3)
bezier_curve(control_points)
curve_through_points(points, smooth=True)
helix_curve(diameter=20, pitch=5, turns=5, taper=0)
conic_curve(conic_type="parabola", focal_length=50, extent=100)
  # conic_type: "parabola" | "hyperbola"
```

**Surfaces** — return PartikusShape wrapping a Part.Face or Part.Shell

```python
loft_surface(profile_curves, ruled=False)
  # profile_curves: list of PartikusShape (Wire) or Part.Wire — at least 2

sweep_1rail(profile, rail)
  # profile: cross-section wire; rail: path wire

patch_fill(boundary_curves)
  # list of wires forming a closed boundary; planar → exact; curved → approximate

boundary_surface(curves)
  # alias of patch_fill for 3 or 4 boundary curves

surface_from_points(point_grid_2d)
  # 2-D list of (x,y,z) tuples → interpolated BSplineSurface
```

**Surface editing**

```python
move_control_point(surface, u_index, v_index, new_position)
  # u_index, v_index: 1-based; new_position: (x, y, z)

offset_surface(surface, distance)
  # positive = outward inflation; negative = inward

join_surfaces(*surfaces)
  # join 2+ Part.Face/PartikusShape into a shell

rebuild_surface(surface, u_count=10, v_count=10, degree=3)
  # re-approximate from sampled point grid
```

**Tier 15C — Conversion**

```python
mesh_to_nurbs(mesh, patch_size="auto", degree=3, tolerance=0.1)
  # mesh: PartikusShape or Part.Shape; patch_size: "coarse" | "auto" | "fine"
  # Fits a BSplineSurface to the mesh vertex cloud
```

**Tier 15D — Analysis** — return plain dicts, not PartikusShape

```python
analyze_curvature(surface, mode="gaussian")
  # mode: "gaussian" | "mean" | "max" | "min"
  # returns {"mode", "min", "max", "mean", "sample_count", "unit"}

analyze_draft(shape, pull_direction=(0, 0, 1))
  # returns {"faces": [...], "min_draft_deg", "max_draft_deg", "mean_draft_deg"}
  # each face entry: {"area_mm2", "draft_angle_deg", "ok"}

analyze_deviation(surface, reference, sample_count=10)
  # returns {"min_deviation", "max_deviation", "mean_deviation", "rms_deviation"}
```

---

### Tier 14 — Assembly & Positioning

```python
translate(shape, dx=0, dy=0, dz=0)
rotate(shape, axis, angle_deg, center=None)
scale(shape, factor=None, fx=None, fy=None, fz=None)
mirror_position(shape, plane)  # flip, no copy

attach(child, parent,
       child_anchor="BOTTOM", parent_anchor="TOP",
       offset=0, rotation_deg=0)
  # aligns child_anchor normal to oppose parent_anchor normal
  # then snaps the points together; offset separates along joining axis

stack_on(child, parent)           # attach(BOTTOM → TOP)
place_beside(child, parent, side, gap=0)
align(shape_a, shape_b, axis_name, anchor="CENTER")
coaxial(shape_a, shape_b)         # share X and Y centres
```

---

## Anchor System

Anchors are the heart of Partikus. They let you write:

```python
lid = hollow_box(60, 40, 20, wall_thickness=2)
knob = rounded_cylinder(diameter=15, height=10, fillet_radius=2)

assembly = attach(
    child=knob,
    parent=lid,
    child_anchor="BOTTOM",
    parent_anchor="TOP",
    offset=2,           # 2mm gap (countersunk)
    rotation_deg=0,
)
```

…instead of manually calculating where the top face of the lid is and offsetting from it.

### How attach() works

```
1.  rotation_from_to(child_normal, -parent_normal)
    → rotate child so its anchor faces the parent anchor

2.  rotate child by rotation_deg around the parent normal axis

3.  translate child so child_anchor_pos == parent_anchor_pos + parent_normal * offset
```

### Anchor positions after transforms

| Operation | Anchor behaviour |
|---|---|
| `translate` | All anchor positions shift by `(dx, dy, dz)` |
| `rotate` | Positions and orientation vectors both rotated |
| `scale` | Positions scaled; orientation vectors renormalised |
| `fillet` / `chamfer` | Original anchors preserved (face centres unchanged) |
| `shell` / `offset` | Recomputed from new bounding box |
| `linear_array` / `polar_array` | Compound centred; anchors reflect compound BB |

---

## Parameter Conventions

All dimensions are **mm** unless the parameter name carries a suffix.

| Suffix | Meaning |
|---|---|
| `_deg` | degrees |
| `_count` | dimensionless integer |
| *(none)* | millimetres |

**Vocabulary rules** — consistent across every function in the library:

| Concept | Use | Never |
|---|---|---|
| X extent | `length` | `len`, `l`, `size_x` |
| Y extent | `width` | `wid`, `w`, `size_y` |
| Z extent | `height` | `hgt`, `h`, `depth` |
| circle size | `diameter` (primary), `radius` (alias) | `dia`, `d` |
| hollow outer | `outer_diameter` | `od` |
| hollow inner | `inner_diameter` | `id` |
| shell thickness | `wall_thickness` | `thick`, `wall`, `t` |
| face recess | `depth` | `recess` |
| edge round | `fillet_radius` | `radius`, `round` |
| edge bevel | `chamfer_size` | `bevel`, `c` |
| repetitions | `count` | `n`, `num`, `qty` |
| angle value | `<name>_deg` | bare `angle` |

---

## Testing

```bash
# Full test suite (552 tests, all tiers)
squashfs-root/usr/bin/freecadcmd tests/run_tests.py

# Single module
squashfs-root/usr/bin/freecadcmd tests/test_tier15.py
```

> **Note:** `freecadcmd` captures stdout. The test runner uses `FreeCAD.Console.PrintMessage` + `sys.stderr` so all output is visible in the terminal.

### Test coverage by tier

| Tier | Module | Tests |
|---|---|---|
| Core | `test_core.py` | anchor/wrapper/transform primitives |
| 1 | `test_tier01.py` | all 9 primitives |
| 9 | `test_tier09.py` | union/difference/intersection |
| 14 | `test_tier14.py` | translate/rotate/scale/attach |
| 10 | `test_tier10.py` | fillet/chamfer/shell/offset |
| 11 | `test_tier11.py` | linear/grid/polar/mirror |
| 3 | `test_tier03.py` | all 2D profile types |
| 2 | `test_tier02.py` | all enhanced primitives |
| 12 | `test_tier12.py` | extrude/revolve/sweep/loft/pipe |
| 4 | `test_tier04.py` | all 20 mechanical features |
| 5 | `test_tier05.py` | fasteners + presets |
| 6 | `test_tier06.py` | gears/pulleys/bearings |
| 7 | `test_tier07.py` | enclosure/container features |
| 8 | `test_tier08.py` | electronics mounting |
| 13 | `test_tier13.py` | architectural elements |
| 15 | `test_tier15.py` | NURBS curves + surfaces + analysis |

**Total: 552 tests — 552 passing**

---

## Project Structure

```
partikus/
├── README.md
├── CHANGELOG.md
├── HANDOFF.md
├── partikus/
│   ├── __init__.py                      # public API surface
│   ├── core/
│   │   ├── anchors.py                   # anchor name constants
│   │   ├── shape_wrapper.py             # PartikusShape class
│   │   ├── transforms.py                # rotation_from_to, placement_for_rotation
│   │   └── document.py                  # FreeCAD document management
│   ├── presets/
│   │   ├── screws.py                    # ISO metric screw tables M2–M20
│   │   └── bearings.py                  # ISO ball bearing tables
│   ├── tier00_foundations.py            # UP/DOWN/NORTH/…/PLANE_XY/…
│   ├── tier01_primitives.py             # box/cylinder/sphere/…
│   ├── tier02_enhanced.py               # rounded_box/tube/hemisphere/…
│   ├── tier03_profiles_2d.py            # rectangle/circle/slot/…  → Part.Wire
│   ├── tier04_mechanical.py             # boss/rib/bracket/snap features
│   ├── tier05_fasteners.py              # bolts/nuts/washers/inserts
│   ├── tier06_mechanical_components.py  # gears/pulleys/bearings/couplings
│   ├── tier07_enclosures.py             # lid/snap_fit_box/cable_channel/…
│   ├── tier08_electronics.py            # pcb_standoff/rpi_mount/usb_cutout/…
│   ├── tier09_boolean.py                # union/difference/intersection
│   ├── tier10_modifiers.py              # fillet/chamfer/shell/offset
│   ├── tier11_patterns.py               # linear_array/grid_array/polar_array/mirror
│   ├── tier12_sweep_loft.py             # extrude/revolve/sweep/loft/pipe
│   ├── tier13_architectural.py          # wall/stairs/roof/column/beam/slab/truss
│   ├── tier14_assembly.py               # translate/rotate/attach/…
│   ├── tier15a_nurbs.py                 # NURBS/B-spline curves (surfaces stubbed)
│   ├── tier15b_subd.py                  # SubD stubs — no FreeCAD 1.1.1 native SubD
│   ├── tier15c_conversion.py            # mesh_to_nurbs (real); SubD conversions stubbed
│   ├── tier15d_analysis.py              # curvature/draft/deviation (real); zebra/reflection stubbed
│   └── gui/
│       ├── auto_dialog.py               # introspection-based PySide2 dialog builder
│       └── workbench.py                 # FreeCAD workbench registration
├── tests/
│   ├── run_tests.py                     # headless test runner
│   ├── test_core.py
│   ├── test_tier01.py  test_tier02.py  test_tier03.py
│   ├── test_tier04.py  test_tier05.py  test_tier06.py
│   ├── test_tier07.py  test_tier08.py
│   ├── test_tier09.py  test_tier10.py  test_tier11.py  test_tier12.py
│   ├── test_tier13.py  test_tier14.py  test_tier15.py
└── examples/
    └── capped_cylinder.py
```

---

## Roadmap

```
Milestone 1 ✅  Foundation
  Core PartikusShape wrapper, anchor system, Tiers 0 / 1 / 9 / 14 + GUI dialogs
  70 tests — all passing

Milestone 2 ✅  Practical Utility
  Tiers 2 / 3 / 10 / 11 / 12
  193 tests — all passing

Milestone 3 ✅  Mechanical Depth
  Tier 4 — bosses, ribs, brackets, snap features
  Tier 5 — fasteners (hex bolts, socket heads, nuts, washers, inserts)
  Tier 6 — gears, hinges, bearing pockets, pulleys
  340 tests — all passing

Milestone 4 ✅  Application Domains
  Tier 7  — enclosures (lids, snap-fit, hinged, battery, vents, cable routing)
  Tier 8  — electronics (RPi/Arduino mounts, LED, USB/HDMI/barrel/DIN cutouts)
  Tier 13 — architectural (walls, stairs, roofs, columns, beams, trusses)
  Tier 15 — NURBS curves implemented; surfaces/SubD/analysis stubbed
  491 tests — all passing

Milestone 5 ✅  Freeform Surfaces
  Tier 15A — NURBS surfaces: loft_surface, sweep_1rail, patch_fill, boundary_surface,
             surface_from_points, move_control_point, offset_surface, join_surfaces,
             rebuild_surface
  Tier 15B — SubD: all stubbed (FreeCAD 1.1.1 has no native SubD support)
  Tier 15C — mesh_to_nurbs implemented; SubD conversions stubbed
  Tier 15D — analyze_curvature, analyze_draft, analyze_deviation implemented;
             zebra/reflection stubs remain
  532 tests — all passing

Milestone 6 ✅  Surface Editing Operations  ← current
  Tier 15A — network_surface, sweep_2rail, trim_surface, split_surface, surface_fillet
             (untrim, match_surfaces, variable_fillet, surface_chamfer remain stubbed —
              BRep editing APIs not in FreeCAD 1.x Python)
  552 tests — all passing

Milestone 7 ⬜  AI Integration (separate project)
  Image → decomposition → toolkit call sequence
  Rendered feedback loop for dimension iteration
  Provenance metadata on all AI-generated objects
```

---

## Contributing

1. Each tier lives in its own module — keep changes localised
2. Every new function needs a corresponding test in `tests/test_tierXX.py`
3. Run the full suite before committing: `freecadcmd tests/run_tests.py`
4. Parameter names must follow the [conventions table](#parameter-conventions) — no exceptions
5. New functions must return `PartikusShape`, not raw `Part.Shape`
6. Anchors must be documented in the function's docstring if non-standard

---

## References

- [FreeCAD](https://www.freecad.org/) — host application and CAD kernel bridge
- [OpenCASCADE Technology](https://dev.opencascade.org/) — underlying B-rep geometry kernel
- [BOSL2](https://github.com/BelfrySCAD/BOSL2) — closest analog in OpenSCAD; reference for naming conventions and attachment system design
- [NopSCADlib](https://github.com/nophead/NopSCADlib) — comprehensive parts library; reference for Tiers 5/6/8
- ISO 4014 / ISO 4032 / ISO 7089 — metric bolt, nut, and washer standards (Milestone 3)

---

*Partikus — Every part has its place.*
