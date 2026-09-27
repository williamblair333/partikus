# Partikus

> **A parametric CAD toolkit for FreeCAD. Every part has its place.**

[![Tests](https://img.shields.io/badge/tests-835%20passing-brightgreen)](#testing)
[![Python](https://img.shields.io/badge/python-3.11-blue)](https://www.python.org/)
[![FreeCAD](https://img.shields.io/badge/FreeCAD-1.1.1-orange)](https://www.freecad.org/)
[![License](https://img.shields.io/badge/license-LGPL--2.1-lightgrey)](LICENSE)
[![Milestone](https://img.shields.io/badge/milestone-13%20complete-brightgreen)](#roadmap)

> **👉 New here?** Set up with the [Quick Start](#quick-start), then pick a way in:
>
> - **With the mouse:** [Using the GUI](#using-the-gui) builds a Raspberry Pi wall
>   plate in FreeCAD, start to STL.
> - **Make something useful now:** [Make a replacement knob](#make-a-replacement-knob)
>   for an appliance whose knob broke: measure, print, fit.
> - **With code:** the [Getting Started tutorial](docs/getting-started.md), twenty
>   minutes to a real part on disk.
>
> The rest of this README is reference, for looking things up.

---

## What Is Partikus?

Partikus is a **Python parametric CAD toolkit** layered on top of FreeCAD's OpenCASCADE kernel. It provides a clean, composable function API for building 3D geometry — from primitive solids through swept surfaces — with a first-class **anchor system** that lets shapes snap together without manual coordinate arithmetic.

**The problem it solves.** Scripting FreeCAD directly means positioning everything by absolute coordinate. A lid sits on a box because you worked out that its Z centre is `box_height/2 + lid_thickness/2`, and that expression is now load-bearing — change the wall thickness and the arithmetic silently stops being true. Real assemblies accumulate dozens of these, and they all have to be maintained by hand.

Partikus replaces the arithmetic with intent. Every shape carries named points on its surface — `TOP`, `BOTTOM`, `TOP_FRONT_RIGHT`, `BOTTOM_RIM` — and `attach(lid, box, child_anchor=BOTTOM, parent_anchor=TOP)` says *put the lid's underside on the box's top*. Change any dimension and the parts stay together, because nothing ever recorded where they were. That is what makes a model genuinely parametric rather than merely written in Python.

The architecture is built for three audiences at once:

| Audience | How they use it |
|---|---|
| **Human designers** | Call Python functions, combine results, export to STEP/STL |
| **FreeCAD GUI users** | Auto-generated dialogs appear for every function (no GUI code to write) |
| **AI agents** | `partikus.ai` — image/description → decompose → emit Partikus script |

---

## Table of Contents

- [Quick Start](#quick-start) ← setup; do this first
- [**Getting Started tutorial**](docs/getting-started.md) ← learn the Python API
- [**Using the GUI**](#using-the-gui) ← no code; a worked example, start to STL
- [**Make a replacement knob**](#make-a-replacement-knob) ← measure, print, fit
- [Examples](#examples)
- [Architecture Overview](#architecture-overview)
- [Tier Reference](#tier-reference)
  - [Tier 0 — Foundations](#tier-0--foundations)
  - [Tier 1 — Raw Primitives](#tier-1--raw-3d-primitives)
  - [Tier 2 — Enhanced Primitives](#tier-2--enhanced-primitives)
  - [Tier 3 — 2D Profiles](#tier-3--2d-profiles)
  - [Tier 4 — Mechanical Features](#tier-4--mechanical-features)
  - [Tier 5 — Fasteners](#tier-5--fasteners)
  - [Tier 6 — Mechanical Components](#tier-6--mechanical-components)
  - [Tier 7 — Container / Enclosure Features](#tier-7--container--enclosure-features)
  - [Tier 8 — Electronics Mounting](#tier-8--electronics-mounting)
  - [Tier 9 — Boolean Operations](#tier-9--boolean-operations)
  - [Tier 10 — Edge & Surface Modifiers](#tier-10--edge--surface-modifiers)
  - [Tier 11 — Pattern / Array Operations](#tier-11--pattern--array-operations)
  - [Tier 12 — Sweep / Loft](#tier-12--sweep--loft)
  - [Tier 13 — Architectural](#tier-13--architectural)
  - [Tier 14 — Assembly & Positioning](#tier-14--assembly--positioning)
  - [Tier 15A — NURBS Curves & Surfaces](#tier-15a--nurbs-curves--surfaces)
  - [Tier 15B — Subdivision Surfaces](#tier-15b--subdivision-surfaces)
- [Anchor System](#anchor-system)
- [Document Serialisation](#document-serialisation)
- [Parameter Conventions](#parameter-conventions)
- [Testing](#testing)
- [Project Structure](#project-structure)
- [Roadmap](#roadmap)
- [Contributing](#contributing)
- [References](#references)

---

## Quick Start

### Setup (once)

**Linux.** `install.sh` is a bash script and the tested FreeCAD is the Linux AppImage.
Windows and macOS are untested.

1. **Get Partikus:**
   ```bash
   git clone https://github.com/williamblair333/partikus.git
   cd partikus
   ```
2. **Get FreeCAD 1.1 or newer**, either way:
   - **AppImage (what this README's commands assume):** download the Linux AppImage
     from [freecad.org/downloads](https://www.freecad.org/downloads.php), e.g.
     `FreeCAD_1.1.1-Linux-x86_64-py311.AppImage`, and put it **in the `partikus`
     folder**. `install.sh` unpacks it into `squashfs-root/`.
   - **Installed FreeCAD:** fine too if `freecadcmd` is on your PATH (`freecadcmd
     --version` prints 1.1 or later).
3. **Run the installer:**
   ```bash
   ./install.sh
   ```
   A good run prints green ✓ lines ending with `Workbench installed: …/Mod/partikus ->
   …/partikus` and "Restart FreeCAD, then pick "Partikus" from the workbench dropdown."
   A ✗ line says what is missing. No `sudo` is needed. The script makes the AppImage
   executable itself, unpacks it into `squashfs-root/` here, and adds one link in your
   FreeCAD user folder. Run all the commands below from the `partikus` folder.

**Which command to type.** This README writes `squashfs-root/usr/bin/freecadcmd`
(run a script, no window) and `squashfs-root/AppRun` (open FreeCAD). If `install.sh`
used your installed FreeCAD instead, type `freecadcmd` and `freecad` in their place.

```bash
squashfs-root/usr/bin/freecadcmd examples/getting_started.py   # run a script
squashfs-root/AppRun                                          # open the FreeCAD window
```

### Basic usage

```python
from partikus import box, cylinder, difference

# A box with a cylindrical hole through it
body = box(40, 20, 10)
hole = cylinder(diameter=8, height=15)
part = difference(body, hole)

# Stack a rounded boss on top.
# stack_on() *positions* the boss — it returns the moved boss, not a combined
# solid — so fuse the two together with union() to get one part.
from partikus import rounded_cylinder, stack_on, union
boss  = rounded_cylinder(diameter=12, height=6, fillet_radius=1)
boss  = stack_on(boss, part)
assembly = union(part, boss)

# Export — nothing appears on disk until you do this
from partikus import to_step, to_stl
to_step(assembly, "examples/out/quickstart.step")
to_stl(assembly, "examples/out/quickstart.stl")
```

> Geometry lives in memory until exported. A script that builds shapes and never calls `to_step` / `to_stl` runs cleanly and produces nothing — see [`partikus/io.py`](partikus/io.py) for the other formats (IGES, OBJ, BREP, native `.FCStd`).

### Sweep a profile along a path

```python
import Part, FreeCAD
from partikus import circle, sweep

path = Part.Wire([Part.LineSegment(
    FreeCAD.Vector(0, 0, 0),
    FreeCAD.Vector(0, 0, 50)
).toShape()])

pipe = sweep(circle(diameter=10), path)
# nothing is on disk yet: export with to_stl(pipe, "pipe.stl") as above
```

### 2D profile → extruded solid

```python
from partikus import rounded_rectangle, extrude

profile = rounded_rectangle(30, 20, fillet_radius=3)
solid   = extrude(profile, height=8)
# export with to_step / to_stl as above
```

---

## Using the GUI

Everything below is done with the mouse; no Python. Verified step by step in FreeCAD 1.1.1.

### Open the workbench

`./install.sh` (see [Quick Start](#quick-start)) also installs the workbench into FreeCAD.
Start FreeCAD (`squashfs-root/AppRun`, or your installed FreeCAD) and pick **Partikus**
from the workbench dropdown in the toolbar, or **View → Workbench → Partikus**. A
**Partikus** menu appears, plus one toolbar per tier. Re-run `./install.sh` after
upgrading FreeCAD; the workbench is installed per FreeCAD version.

### How the commands work

- **Every command opens a dialog built from its function's parameters.** Field names are
  the parameter names with the underscores turned into spaces: `fillet_radius` is
  *Fillet Radius*. So the [Tier Reference](#tier-reference) below doubles as a guide to
  every dialog. Lengths are mm, and fields ending in *Deg* are degrees. A field showing
  **auto** means "let the function work it out".
- **Menu name → Tier Reference section:** Primitives → Tier 1, Enhanced → Tier 2,
  Profiles 2D → Tier 3, Mechanical → Tier 4, Fasteners → Tier 5, Components → Tier 6,
  Enclosures → Tier 7, Electronics → Tier 8.
- **New parts appear centred on the origin**, like everything in Partikus.
- **Commands marked *(cutter)* make a negative volume**: holes, slots, connector
  cutouts. They are also gathered on the *Partikus — Cutters* toolbar. A cutter removes
  nothing by itself. Subtract it with FreeCAD's **Part → Boolean → Cut**.
- **The dialogs have no position fields.** Place parts with **Partikus → Attach**
  ([below](#in-the-freecad-gui-partikus--attach)), which snaps named points together, or
  by hand: select the part and edit **Placement → Position** in the Property view.

### Worked example: a Raspberry Pi 4 wall-mount plate

A 120 × 70 mm backplate with the Pi 4 mount on top and two countersunk screw holes, so
the Pi screws flat to a wall or the side of a cabinet. About ten minutes.

**Finding your way around first.** The panel on the left is **Model**. Its top half is
the tree: every part you make gets a line there, named after the command that made it
(`rounded_box`, `countersink_hole`, `countersink_hole001`, …). Its bottom half is the
property editor, with two tabs at the bottom, **View** and **Data**; positions are on
**Data**. To *select* a part, click its name in the tree (or the part in the 3D view).
**Ctrl+click** adds a second part to the selection, and the order you click in
matters for step 6. **Ctrl+Z** undoes any step. You don't need *File → New* first:
the first part you make creates a document called *Partikus*. If a part is off
screen, **View → Standard Views → Fit All** (or press **V** then **F**) brings
everything into view. If the Model panel isn't showing, turn it on with **View →
Panels → Model**.

**Hardware:** four **M2.5 × 6 mm** screws for the Pi, and two **M4 countersunk**
screws for the wall. For **#8 wood screws** instead, change only Head Angle Deg to
**82** in step 2; everything else is the same.

1. **The plate.** Menu **Partikus → Enhanced → Rounded Box**. In the dialog set
   Length **120**, Width **70**, Height **4**, Fillet Radius **1.5**; leave Edges on
   *auto*. Click **OK**. `rounded_box` appears in the tree. That's the plate.

2. **Two screw-hole cutters.** **Partikus → Mechanical → Countersink Hole (cutter)**:
   Thru Diameter **4.5**, Head Diameter **9**, Head Angle Deg **90**, Depth **10**,
   **OK**. (4.5 rather than 4 gives an M4 screw room to pass; printed holes come out a
   little small.)
   Do it a second time with the same numbers. You now have `countersink_hole` and
   `countersink_hole001`, both in the middle of the plate and sticking out above and
   below it. That's expected; step 3 sets their height.

3. **Sink each cutter into the plate.** In the tree click `countersink_hole`, then
   Ctrl+click `rounded_box`. Choose **Partikus → Attach** and set:

   | Field | Set to |
   |---|---|
   | Move | `countersink_hole` |
   | Its point | BOTTOM |
   | Onto point of `rounded_box` | TOP |
   | Gap | **-10** |

   Click **OK**, then do the same for `countersink_hole001`.
   *Why −10:* the gap is measured outward from the plate's top face, so a negative
   gap pushes the cutter *into* the plate. A gap of −Depth (−10) leaves the
   countersink's wide mouth exactly level with the plate's top.

4. **Slide the cutters out to the ends.** Click `countersink_hole` in the tree. In the
   property editor click the **Data** tab and open **Base → Placement → Position**
   (click the small arrows). Set **x** to **52** and press Enter. Click
   `countersink_hole001` and set its **x** to **-52**. Leave y and z as they are; z
   already reads −3 mm because Attach set it. (Attach only snaps to named points, so
   any position in between is a hand move like this one.)

5. **Add the Pi mount and weld it on.** **Partikus → Electronics → Raspberry Pi
   Mount**. Model is already **4B**. Set Hole Diameter to **2.2** and click **OK**.
   (The default 2.9 is a clearance hole for a bolt and nut, but the plate will close
   off the underside, so 2.2 lets the M2.5 screws cut their own thread into the
   plastic instead.) Click `raspberry_pi_mount`, Ctrl+click `rounded_box`,
   **Partikus → Attach**: Move `raspberry_pi_mount`, BOTTOM onto TOP, Gap **0**, tick
   **Weld into one solid**, **OK**. A new part called `Weld` appears; `rounded_box` and
   `raspberry_pi_mount` are hidden (greyed out in the tree) because they're now inside it.
   The mount is 89 × 60 mm, so it ends 3 mm short of the screw heads at x = ±47.5.

6. **Cut the holes.** Switch workbench: in the toolbar dropdown that now reads
   *Partikus*, choose **Part**. Click `Weld`, Ctrl+click `countersink_hole`, then
   **Part → Boolean → Cut**. **Click `Weld` first**: the first part selected is kept
   and the second is cut away. The result is `Cut`. Now click `Cut`, Ctrl+click
   `countersink_hole001`, and **Part → Boolean → Cut** again, giving `Cut001`: the
   finished part. You should see two countersunk holes near the plate's short ends.

7. **Export it for printing.** Click `Cut001`, then **File → Export…**. In the
   file-type list choose **STL Mesh (\*.stl \*.ast)**. Pick a folder, type a file name
   such as `pi4_wall_plate.stl`, and click **Save**.
   (Don't pick "FEM mesh formats". It also lists `.stl`, but it fails with "No FEM mesh
   for export selected".) Open the `.stl` in your slicer and print it flat side down.
   To keep the design itself, also use **File → Save As…** (a `.FCStd` file).

> **Position first, combine second.** Attach works only on Partikus parts. The result
> of *Part → Boolean → Cut* is not one, so it cannot be attached. A *Weld* is a Partikus
> part, but a combined shape keeps only CENTER, TOP and BOTTOM, measured from its
> bounding box. Here the Weld's TOP is the top of the Pi standoffs, not the plate. That
> is why step 3 attaches the cutters to the plate *before* step 5 welds.

When the menus run out (a custom-shaped cutter, a ring of grip flutes, a pattern),
the shape has to be written as a Python script. The
[Getting Started tutorial](docs/getting-started.md) teaches that, and
[`examples/replacement_knob.py`](examples/replacement_knob.py) is a complete part
written that way.

---

## Make a replacement knob

The knob on your stove, oven, washer, dryer, fan or amp broke, and nobody sells that
one any more. [`examples/replacement_knob.py`](examples/replacement_knob.py) builds one
from your measurements. This section takes you from the broken knob to a fitted one.

**You need:** digital calipers set to **mm**, a 3D printer (PETG or ASA filament for
anything near heat), a text editor, and the [Quick Start](#quick-start) setup done.

### 1. Measure the shaft

**Before you pull anything, turn the control to OFF.** That's the reference for the
pointer, and on a gas cooker it's the safe position. Then pull the old knob straight
off; a stuck one levers off with a butter knife under its skirt. If a metal spring
clip stays on the shaft, pull that off too. The new knob doesn't use one.

Look at the end of the shaft. It should be round with one flat side (a **D shaft**) or
two (a **double-D**). **Splined, knurled, slotted or set-screw shafts are not
covered**; this example won't fit them.

```
   D shaft, end-on                double-D shaft, end-on

      ________  <- flat               ________  <- flat
     (        )   ^                  (        )   ^
    (          )  | SHAFT_FLAT      (          )  | SHAFT_FLAT
    (          )  |                 (          )  |
     (        )   v                  (________)   v  <- flat
       '----'
    <---------->  SHAFT_DIA          <---------->  SHAFT_DIA
```

| Setting | How to measure it | Default |
|---|---|---|
| `SHAFT_DIA` | Jaws on the two **curved** sides, parallel to the flat, so neither touches it | 6.35 |
| `SHAFT_FLAT` | One jaw flat against the flat, the other on the far curved side. On a double-D, flat to flat | 4.75 |
| `SHAFT_FLATS` | Count the flats: `1` or `2` | 1 |
| `SHAFT_ENGAGE` | How deep the shaft went into the old knob: rest the end of the calipers on the old knob's **bottom rim** (the edge that faced the panel) and push the depth rod down to the bottom of its hole. No old knob? Measure the shaft from the **panel face** to its tip and subtract 2 mm, so the new knob clears the panel | 13 |
| `POINTER_DEG` | With the control still at OFF and facing the panel: the angle from the way the flat faces to the panel's OFF mark, anticlockwise positive. `0` = the flat faces the OFF mark (the usual layout), `90` = OFF is a quarter turn anticlockwise from it, `180` = opposite. On a clock face, each hour is 30°. On a **double-D**, measure from either flat; the fit check in step 6 catches a knob that went on half a turn out | 0 |

For the knob itself, measure the old one, or a surviving knob on the same panel so
the new one matches its neighbours: `KNOB_DIA` (across) and `KNOB_HEIGHT` (top to
bottom). The defaults (a 1/4 in shaft with a 4.75 mm flat, a 40 × 24 mm knob) fit
many cookers.

### 2. Type the numbers in

Make your own copy first, one per knob, so your numbers are never overwritten. Keep
it in `examples/`:

```bash
cp examples/replacement_knob.py examples/stove_knob.py
```

Open `examples/stove_knob.py` in a text editor. Near the top is a block headed
**Parameters — your measurements go here**:

```python
SHAFT_DIA     = 6.35    # round diameter of the shaft
SHAFT_FLAT    = 4.75    # flat to far side (double-D: flat to flat)
SHAFT_FLATS   = 1       # 1 = D shaft, 2 = double-D
SHAFT_ENGAGE  = 13.0    # how deep the shaft goes into the knob
FIT_CLEARANCE = 0.15    # per side; tune with the fit coupon

KNOB_DIA      = 40.0
KNOB_HEIGHT   = 24.0
...
POINTER_DEG   = 0.0     # pointer angle from the flat, anticlockwise
```

Change the numbers to yours (millimetres), leave everything else, and save.

### 3. Build it

From the repo folder:

```bash
squashfs-root/usr/bin/freecadcmd examples/stove_knob.py
```

Among FreeCAD's own progress messages you'll see a summary like this, then the files
it wrote. **Check the numbers against your measurements** before printing anything:

```
replacement knob
  shaft   : D 6.35 mm, flat 4.75 mm, 13.0 mm deep
  bore    : +0.15 mm per side
  knob    : dia 40.0 x 24.0 mm, 20 grip flutes, pointer at 0.0 deg from the flat
  plastic : 11.3 cm^3
```

If a measurement can't make a working knob, it stops with a message naming the setting
and why, for example `SHAFT_FLAT 3.0 must be between 3.17 and SHAFT_DIA 6.35` (on a
D shaft the flat reading can't be less than half the diameter). Fix
that number and run it again. The three files are in `examples/out/`, named after
your copy:

| File | What it is |
|---|---|
| `stove_knob_fit_coupon.stl` | a 5 mm ring with the knob's exact hole. **Print this first** |
| `stove_knob.stl` | the knob, already upside down for printing |
| `stove_knob.step` | the knob as fitted, to look at: `squashfs-root/AppRun examples/out/stove_knob.step` |

### 4. Print the fit coupon and tune the fit

Print `stove_knob_fit_coupon.stl` (a few minutes) **in the same filament and
settings you'll use for the knob**, and push it onto the shaft. The notch in its rim
marks the flat side (on a double-D, one of the flats).

Nothing but friction holds the knob on, so this fit matters.

| The coupon… | Do this |
|---|---|
| pushes on by hand with firm pressure, doesn't turn on the shaft, and stays put when you tug it gently | Good. Go to step 5 |
| won't go on, or needs a tool | Raise `FIT_CLEARANCE` by 0.05, re-run step 3, print a new coupon |
| slides on freely, wobbles, falls off, or turns on the shaft | Lower `FIT_CLEARANCE` by 0.05, re-run step 3, print a new coupon |

The knob grips a little harder than the coupon, because its hole is longer. So a
coupon that is only just snug is right. Every printer is different; this is why the
coupon exists. Five minutes of coupon saves an hour of knob. If three rounds haven't
got it right, re-measure `SHAFT_DIA` and `SHAFT_FLAT` before changing the clearance
further.

### 5. Print the knob

Print `stove_knob.stl` **as it comes. Don't rotate it.** It's already upside
down, so the hole and the hollow underside open upward and nothing needs supports.
Use PETG or ASA for a cooker; PLA softens at about 60 °C. Three or more walls keep
the bore and the grip solid.

### 6. Fit it and check the pointer

Push the knob on. With the control at OFF, check the pointer reads OFF. On a
**double-D**, if it points exactly the opposite way, pull the knob off, turn it half
a turn, and push it back on.

If the pointer is off by some other angle, judge it on the clock face (each hour is
30°). If it sits clockwise of OFF, *add* that angle to `POINTER_DEG`; if
anticlockwise, subtract it. Re-run step 3 and reprint the knob. The coupon can't
check this.

Then work the control through its whole range. **On a gas cooker, push and turn
exactly as you would with the old knob.** The knob must turn the valve without
slipping on the shaft, must not rub the panel, and must come back to OFF and read
OFF. A pointer that lies is worse than no knob, and on a gas valve it's the knob you
trust to say OFF. If it slips or rubs, don't use it: lower `FIT_CLEARANCE` for a
slip, or reduce `SHAFT_ENGAGE` for a rub, and reprint.

---

## Examples

### `examples/getting_started.py` — start here

A parametric pillar mount in ~30 lines: base plate, attached pillar, bore straight
through, exported to STEP and STL. Built step by step in the
**[Getting Started tutorial](docs/getting-started.md)**, which this file accompanies.

```bash
./install.sh
squashfs-root/usr/bin/freecadcmd examples/getting_started.py
```

### `examples/replacement_knob.py` — the part you can't buy

A replacement knob for a D or double-D shaft (stove, oven, washer, dryer, fan, amp)
built from caliper readings, with a fit coupon to tune the fit before the full print.
**Step-by-step instructions: [Make a replacement knob](#make-a-replacement-knob).**

```bash
squashfs-root/usr/bin/freecadcmd examples/replacement_knob.py
```

### `examples/rpi4_enclosure.py` — full-API showcase

A single runnable script that builds a parametric Raspberry Pi 4B enclosure and exercises
every major feature of the library:

| Section | Tiers | What it shows |
|---|---|---|
| Body shell | 2 + 10 | `hollow_box`, `shell` (cable guide trough) |
| Connector openings | 7 + 8 + 9 | `usb_cutout`, `hdmi_cutout`, `vent_slots`, `button_cutout`, `slot_hole`, `difference` |
| Internal features | 4 + 8 + 10 + 11 | `raspberry_pi_mount`, `boss` + `fillet`, `grid_array`, `rib` + `linear_array`, `gusset` |
| Lid | 7 + 4 + 9 | `lid`, `vent_slots`, `snap_clip`, `difference` |
| NURBS surfaces | 2 + 15A | `rounded_box`, `surface_from_points`, `bspline_curve` |
| Surface analysis | 15D | `analyze_draft`, `analyze_zebra` → PNG |
| Assembly | 14 | `stack_on`, `translate`, `rotate` |
| Export | I/O | `to_step`, `to_stl`, `save_fcstd` |
| AI pipeline | AI | `generate_script` (key-guarded) |

```bash
# Headless — no display required, outputs files to examples/out/
squashfs-root/usr/bin/freecadcmd examples/rpi4_enclosure.py

# Live GUI — watch it build step-by-step in FreeCAD's 3-D view
PARTIKUS_GUI=1 squashfs-root/AppRun freecad examples/rpi4_enclosure.py

# View result after a headless run
squashfs-root/AppRun examples/out/rpi4_enclosure.FCStd
```

See **[docs/rpi4_enclosure_walkthrough.md](docs/rpi4_enclosure_walkthrough.md)** for a
section-by-section explanation of every design pattern used.

### `examples/capped_cylinder.py` — minimal intro

A hollow cylinder with a snap-fit cap, exported to `examples/out/capped_cylinder.{step,stl}`.
Good second read, after `getting_started.py` and before the enclosure example.

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
    subd_mesh    # SubDMesh | None — set on shapes from subd_* functions
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

### Tier 4 — Mechanical Features

Functions marked **cutter** return a negative volume to subtract with `difference()`
(GUI: *Part → Boolean → Cut*). Every cutter is centred on the origin and grows both ways.

```python
boss(diameter=10, height=5, hole_diameter=None)        # raised post, optional bore
rib(length=20, height=15, thickness=3, draft_angle_deg=0)
gusset(length=20, height=20, thickness=3)               # right-triangle corner plate
flange(inner_diameter=20, outer_diameter=40, thickness=5, hole_pattern=None)
lip(outer_diameter=40, height=20, lip_width=3, lip_height=5)
tab(width=10, height=5, thickness=2)
tongue(length=15, width=6, height=3)                    # mates with groove()

l_bracket(length=30, height=30, thickness=3, width=20)
t_bracket(arm_length=40, stem_length=20, width=20, thickness=3)
u_bracket(length=40, height=20, width=20, thickness=3, leg_height=15)

dovetail_pin(length=20, narrow_width=6, wide_width=10, height=5)
snap_clip(length=20, width=5, hook_height=2, flex_arm_length=12)
living_hinge(length=40, thickness=0.5, hinge_width=10)

# cutters
counterbore_hole(thru_diameter=5, bore_diameter=9, bore_depth=4, depth=10)
countersink_hole(thru_diameter=3, head_diameter=6, head_angle_deg=82, depth=10)
  # 82° is the imperial wood/sheet screw angle; ISO metric flat heads are 90°
slot_hole(length=20, width=6, depth=5)                  # round-ended
slot_cutout(width=10, height=5, depth=3)                # square-ended
keyway(width=4, depth=2, length=20)
groove(length=15, width=6, depth=3)
dovetail_slot(length=20, narrow_width=6, wide_width=10, height=5)
```

---

### Tier 5 — Fasteners

ISO dimensions (M2–M20) come from `partikus/presets/screws.py`. Any `None` argument
takes the ISO value for that `diameter`. Threads are cosmetic (smooth at nominal size).

```python
hex_bolt(diameter=6, length=20, pitch=None, across_flats=None, head_height=None)    # ISO 4014
socket_head_bolt(diameter=6, length=20, ...)            # ISO 4762
button_head_bolt(diameter=6, length=20, ...)            # ISO 7380
flat_head_bolt(diameter=6, length=20, ...)              # ISO 10642, countersunk
hex_nut(diameter=6, pitch=None, across_flats=None, height=None)                     # ISO 4032
flat_washer(bolt_diameter=6, ...)                       # ISO 7089
lock_washer(bolt_diameter=6, ...)                       # ISO 7980
threaded_rod(diameter=6, length=20, pitch=None, thread_form="metric")
standoff(diameter=8, length=10, thread_size=None)
dowel_pin(diameter=4, length=20)
screw_size_preset(name="M6")                            # → dict of ISO dimensions

# cutters
clearance_hole(bolt_size="M6", depth=10, fit="close", hole_diameter=None)
  # fit: "close" | "normal" | "loose"  (ISO 273)
tapped_hole(diameter=6, depth=10, pitch=None)           # tap-drill size
heat_set_insert_pocket(insert_size="M3", outer_diameter=None, length=None)
```

---

### Tier 6 — Mechanical Components

```python
spur_gear(teeth=20, module=1.0, thickness=5, pressure_angle_deg=20)   # involute
bevel_gear(teeth=20, module=1.0, cone_angle_deg=45, thickness=10)
rack(teeth=10, module=1.0, width=None, length=None, height=None)
sprocket(teeth=16, chain_pitch=12.7, thickness=5)
pulley_timing(teeth=20, belt_type="GT2", width=7)       # "GT2" | "HTD"
shaft_coupling(shaft1_diameter=6, shaft2_diameter=6, length=25)

# cutter
bearing_pocket(bearing_id="608", depth=None, outer_diameter=None)
  # 606–609, 6000–6008, 6200–6208, 6300–6308
```

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
  # cutter — cylindrical press-fit pockets for disc magnets

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
  # cutter — panel through-hole for a button; shape: "round" | "square"
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
  # cutter — connector_type: USB-A | USB-B | USB-C | Micro-USB | Mini-USB

hdmi_cutout(connector_type="full", panel_thickness=2, clearance=0.3)
  # cutter — connector_type: full | mini | micro

barrel_jack_cutout(outer_diameter=8, panel_thickness=2, clearance=0.2)
  # cutter — common sizes: 5.5 mm, 6.3 mm, 8.0 mm

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

mesh_to_subd(mesh, preserve_features=True)
  # Extract SubDMesh topology from a Part.Shape or PartikusShape
  # preserve_features=True auto-creases edges with dihedral angle > 30°

nurbs_to_subd(surface, density="medium")
  # Sample a BSplineSurface onto a regular quad grid → SubDMesh
  # density: "coarse" (4×4) | "medium" (8×8) | "fine" (16×16)

subd_to_nurbs(subd, target_tolerance=0.01)
  # Subdivide a SubDMesh until smooth, then fit a BSplineSurface
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

analyze_zebra(surface, stripe_count=8, sample_grid=8)
  # Numerical zebra analysis via normal reflection against a virtual stripe env
  # returns {"stripe_ids", "continuity_hint": "likely_G1" | "possible_G0", ...}

analyze_reflection(surface, camera_direction=(0,0,1), sample_grid=8)
  # Numerical reflection analysis — reflected camera vectors across the surface
  # returns {"samples", "mean_divergence", "continuity_hint", ...}
```

---

### Tier 15B — Subdivision Surfaces

Pure-Python Catmull-Clark SubD engine with full `subd_*` API. Shapes carry a `subd_mesh` attribute (`SubDMesh`) alongside the BRep solid.

**Primitives**

```python
subd_primitive(prim_type, **dims)
  # prim_type: "cube" | "sphere" | "cylinder" | "cone" | "torus"
  # dims: same keyword arguments as the Tier 1 counterparts
  # Returns PartikusShape with .subd_mesh set
```

**Editing operations**

```python
subd_push_pull(shape, faces, distance)
  # offset a list of face indices along their average normal

subd_insert_loop(shape, edge)
  # insert an edge loop through the given edge (u, v) — splits all traversed quads

subd_bevel_edge(shape, edges, size=0.1)
  # bevel one or more edges; each (u, v) pair splits into a new quad strip

subd_bevel_vertex(shape, vertices, size=0.1)
  # bevel vertices by cutting each adjacent quad

subd_bridge(shape, face_group_a, face_group_b)
  # connect two open face groups with a tube of quads
```

**Mesh control**

```python
subd_crease(shape, edges, sharpness=2.0)
  # semi-sharp creases; sharpness ≥ 1 = sharp, decays by 1 per subdivision pass

subd_symmetry(shape, plane="YZ", mode="mirror")
  # mirror the mesh about "XY" | "XZ" | "YZ" and double the face count

subd_soft_select(shape, vertices, falloff_radius)
  # returns dict {vertex_index: weight} for falloff-weighted editing

subd_sculpt_brush(shape, point, brush_type, strength, radius)
  # brush_type: "pull" | "push" | "smooth"
  # pulls/pushes vertices within radius toward/away from point
```

**Subdivision**

```python
subd_subdivide(shape, iterations=1)
  # Catmull-Clark subdivision; returns new PartikusShape with finer mesh
```

**Conversion** (see also Tier 15C)

```python
subd_to_nurbs(shape)          # → BSplineSurface PartikusShape
mesh_to_subd(mesh, preserve_features=True)   # → SubDMesh
nurbs_to_subd(surface, density="medium")     # → SubDMesh
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
    offset=2,           # float 2 mm above the lid; a NEGATIVE offset sinks it in
    rotation_deg=0,
)
```

…instead of manually calculating where the top face of the lid is and offsetting from it.

### In the FreeCAD GUI: Partikus → Attach

The same operation, with no code. Select two Partikus parts (Ctrl+click), then choose
**Partikus → Attach** or the button on the *Partikus — Assemble* toolbar:

| Field | Meaning |
|---|---|
| Move | which of the two parts moves |
| Its point | anchor on the moving part (default `BOTTOM`) |
| Onto point of … | anchor on the other part (default `TOP`) |
| Gap / Rotate | `offset` and `rotation_deg` above. A negative gap pushes the part *into* the other one; that's how you sink a cutter to a depth |
| Weld into one solid | also fuse both into one new part and hide the originals |

It is one undo step (Ctrl+Z). Parts you have already moved by hand are handled — anchors
follow the part.

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

## Document Serialisation

`save_to_doc` and `load_from_doc` persist `PartikusShape` objects — including all anchors and orientations — into a FreeCAD `.FCStd` document. Shapes survive a full save/reload round-trip.

```python
from partikus import save_to_doc, load_from_doc
import FreeCAD

doc  = FreeCAD.newDocument("Assembly")
body = box(40, 20, 10)

# Save: creates a Part::FeaturePython with the shape + anchor data serialised
obj  = save_to_doc(body, label="Baseplate", doc=doc)

doc.save("/tmp/assembly.FCStd")

# Load: reconstruct PartikusShape with original anchors intact
doc2 = FreeCAD.openDocument("/tmp/assembly.FCStd")
ps   = load_from_doc(doc2.getObjectsByLabel("Baseplate")[0])

print(ps.anchors["TOP"])   # FreeCAD.Vector — same position as before save
```

**Functions**

| Function | Description |
|---|---|
| `save_to_doc(shape, label, doc=None)` | Create `Part::FeaturePython` in `doc` (default: active doc); returns the FreeCAD object |
| `load_from_doc(obj)` | Reconstruct `PartikusShape` from a previously saved feature object |

Anchors are stored as `(x, y, z)` tuples via `App::PropertyPythonObject` (pickle). Orientations are stored the same way. A shape saved without orientations loads with `{}` — anchors are always preserved.

---

## AI Integration

`partikus.ai` converts images or text descriptions into runnable Partikus scripts using Claude's vision API.

```python
from partikus.ai import generate_script, run_script

# From a text description (no image needed)
script = generate_script("a flanged cylinder 30mm diameter × 60mm tall, flange diameter 50mm")
print(script)
# → from partikus import cylinder, stack_on
#   shaft  = cylinder(diameter=30, height=60)
#   flange = cylinder(diameter=50, height=8)
#   result = stack_on(shaft, flange)

# Execute via freecadcmd
out, err, rc = run_script(script)

# From an image
script = generate_script("photo.jpg", hint="a DIN rail mounting bracket")

# With export
script = generate_script("a hex nut M8", export_step="nut.step")

# Low-level: analyse then generate
from partikus.ai import ImageAnalyzer, ScriptGenerator
analysis = ImageAnalyzer().analyze("photo.jpg")
# analysis = {"description": "...", "shapes": [...], "assembly": [...], "final": "..."}
script   = ScriptGenerator().generate(analysis, export_step="out.step")
ok, err  = validate_syntax(script)
```

**Requirements:** set `ANTHROPIC_API_KEY` in your environment before use. The module uses only Python stdlib for HTTP (no `requests` / `anthropic` SDK needed).

**Functions:**

| Function | Description |
|---|---|
| `analyze_image(path, hint, model)` | Vision analysis → shape decomposition dict |
| `analyze_text(description, hint, model)` | Text analysis → same dict (no image) |
| `generate_script(source, hint, export_step, export_stl)` | End-to-end → Python string |
| `run_script(script, freecadcmd, timeout)` | Execute script → (stdout, stderr, rc) |
| `ImageAnalyzer().analyze(path)` | Low-level vision call |
| `ScriptGenerator().generate(analysis)` | Low-level code generation |
| `validate_syntax(script)` | AST syntax check → (bool, error_or_None) |

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
# Full test suite (835 tests, all tiers)
squashfs-root/usr/bin/freecadcmd tests/run_tests.py

# Single module
squashfs-root/usr/bin/freecadcmd tests/test_tier15.py

# CI integration tests (requires ANTHROPIC_API_KEY)
squashfs-root/usr/bin/freecadcmd tests/run_integration_tests.py
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
| I/O | `test_io.py` | export/import (STEP/STL/IGES/BREP/OBJ/FCStd) |
| AI | `test_ai.py` | code generator, JSON parser, integration (skipped without key) |
| Serialise | `test_serialise.py` | `save_to_doc` / `load_from_doc` anchor round-trips |
| SubD | `test_subd.py` | SubDMesh engine, all `subd_*` functions, conversions, analysis |
| Visual | `test_visual_regression.py` | zebra/reflection PNG output vs committed baselines |

**Total: 835 tests — 835 passing**

---

## Project Structure

```
partikus/
├── README.md
├── CHANGELOG.md
├── HANDOFF.md
├── install.sh                               # one-time setup: finds/extracts FreeCAD >= 1.1
├── run_tests.sh                             # shortcut: runs full test suite via freecadcmd
├── partikus/
│   ├── __init__.py                      # public API surface
│   ├── core/
│   │   ├── anchors.py                   # anchor name constants
│   │   ├── shape_wrapper.py             # PartikusShape class (shape/anchors/orientations/subd_mesh)
│   │   ├── transforms.py                # rotation_from_to, placement_for_rotation
│   │   ├── document.py                  # FreeCAD document management
│   │   └── serialise.py                 # save_to_doc / load_from_doc anchor serialisation
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
│   ├── tier15a_nurbs.py                 # NURBS curves + surfaces + editing
│   ├── tier15b_subd.py                  # pure-Python Catmull-Clark SubD; all subd_* functions
│   ├── tier15c_conversion.py            # mesh_to_nurbs, mesh_to_subd, nurbs_to_subd, subd_to_nurbs
│   ├── tier15d_analysis.py              # curvature/draft/deviation/zebra/reflection analysis
│   ├── subd_mesh.py                     # SubDMesh engine: CC subdivision, primitives, to_partikus_shape
│   ├── io.py                            # export/import: STEP/STL/IGES/BREP/OBJ/FCStd
│   ├── ai/                              # AI integration (image/text → Partikus script)
│   │   ├── __init__.py
│   │   ├── _http.py                     # stdlib-only Anthropic API client
│   │   ├── analyzer.py                  # ImageAnalyzer — vision decomposition
│   │   ├── generator.py                 # ScriptGenerator — analysis → Python
│   │   └── pipeline.py                  # analyze_image, generate_script, run_script
│   └── gui/
│       ├── auto_dialog.py               # introspection-based dialog builder (FreeCAD's PySide shim)
│       ├── attach.py                    # Partikus → Attach command and attach_objects()
│       └── workbench.py                 # FreeCAD workbench registration
├── tests/
│   ├── run_tests.py                     # headless test runner
│   ├── run_integration_tests.py         # end-to-end AI tests (requires ANTHROPIC_API_KEY)
│   ├── test_core.py
│   ├── test_tier01.py  test_tier02.py  test_tier03.py
│   ├── test_tier04.py  test_tier05.py  test_tier06.py
│   ├── test_tier07.py  test_tier08.py
│   ├── test_tier09.py  test_tier10.py  test_tier11.py  test_tier12.py
│   ├── test_tier13.py  test_tier14.py  test_tier15.py
│   ├── test_io.py  test_ai.py
│   ├── test_serialise.py                # anchor serialisation round-trip tests
│   ├── test_gui_loader.py  test_auto_dialog.py  test_attach_command.py   # GUI
│   ├── test_pf1e_templates.py  test_replacement_knob.py                  # examples
│   ├── test_subd.py                     # SubDMesh + subd_* + conversion + analysis tests
│   ├── test_visual_regression.py        # zebra/reflection PNG output vs baselines
│   └── baselines/                       # committed reference PNGs for visual regression
└── examples/
    ├── getting_started.py               # the tutorial's finished part
    ├── capped_cylinder.py               # minimal intro example
    ├── hand_mirror.py                   # mirror frame with a rebated window
    ├── replacement_knob.py              # D-shaft knob from caliper readings
    ├── pf1e_burst_templates.py          # tabletop area-of-effect templates
    └── rpi4_enclosure.py                # full-API showcase
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

Milestone 6 ✅  Surface Editing Operations
  Tier 15A — network_surface, sweep_2rail, trim_surface, split_surface, surface_fillet
             (untrim, match_surfaces, variable_fillet, surface_chamfer remain stubbed —
              BRep editing APIs not in FreeCAD 1.x Python)
  552 tests — all passing

Milestone 7 ✅  I/O — Export and Import
  partikus/io.py — to_step, to_stl, to_iges, to_brep, to_obj, save_fcstd
                   from_step, from_brep, from_stl
  37 new tests — 589 total, all passing

Milestone 8 ✅  AI Integration
  partikus/ai/ — analyze_image, analyze_text, generate_script, run_script
  ImageAnalyzer (vision decomposition via Claude API, stdlib HTTP only)
  ScriptGenerator (analysis dict → valid Python), validate_syntax
  36 new tests (generator/parser unit tests; 3 integration tests skip without API key)
  625 total tests — all passing

Milestone 9 ✅  Anchor Serialisation
  partikus/core/serialise.py — save_to_doc / load_from_doc
  Anchors + orientations persist through .FCStd save/reload via Part::FeaturePython
  + App::PropertyPythonObject (pickle). 11 new tests.

Milestone 10 ✅  GUI Expansion — Tiers 1–8
  partikus/gui/workbench.py rewritten: 8 toolbars, 8 &Partikus submenus
  84 functions exposed; auto_dialog.py wired to save_to_doc

Milestone 11 ✅  CI Integration Tests
  tests/run_integration_tests.py — 7 end-to-end AI tests
  Exits cleanly with error if ANTHROPIC_API_KEY is unset

Milestone 12 ✅  Tier 15B SubD — pure-Python Catmull-Clark
  partikus/subd_mesh.py — SubDMesh, cube/sphere/cylinder/cone/torus primitives,
    full Catmull-Clark subdivision, semi-sharp creases, soft-select, sculpt brushes,
    symmetry, edge loops, bevel, bridge, to_partikus_shape
  tier15b_subd.py — all 11 subd_* functions real (no stubs)
  tier15c_conversion.py — mesh_to_subd, nurbs_to_subd, subd_to_nurbs real
  tier15d_analysis.py — analyze_zebra, analyze_reflection numerical (software-based)
  72 new tests in test_subd.py — 697 total tests

Milestone 13 ✅  Visual PNG renderer  ← current
  core/render.py — pure-stdlib PNG writer (no GUI, no display required)
  analyze_zebra / analyze_reflection — now produce real stripe-map PNG images
    via UV-grid sampling + Gaussian-weighted stripe blending
  7 new tests — 704 total tests, all passing

Showcase example ✅  examples/rpi4_enclosure.py
  Single runnable script exercising Tiers 2, 4, 7, 8, 9, 10, 11, 14, 15A, 15D,
  I/O, and AI pipeline.  Companion: docs/rpi4_enclosure_walkthrough.md

Next
  Visual regression tests — render reference shapes; detect drift on re-render
  Expand AI system prompt — subd_* / analyze_zebra not yet in the AI prompt
  New tier (16) — domain-specific: jewellery, robotics, sheet metal
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
