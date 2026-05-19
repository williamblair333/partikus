# RPi 4B Enclosure — Partikus Walkthrough

`examples/rpi4_enclosure.py` builds a parametric Raspberry Pi 4B enclosure from scratch,
deliberately touching every major API surface so a reader can see them all working together
in a realistic design context.

---

## Run it

```bash
cd /opt/proj/partikus
squashfs-root/usr/bin/freecadcmd examples/rpi4_enclosure.py
```

All output goes to `examples/out/`.  Diagnostic messages print on **stderr** (stdout is
captured by FreeCAD's headless runner).

---

## What gets built

| Part | Description |
|---|---|
| `body` | Open-top enclosure, 105 × 75 × 42 mm, with USB-C/HDMI/USB-A/GPIO openings |
| `internals` | RPi 4B mount, M3 corner bosses, stability ribs, gussets, cable guide |
| `lid_seated` | Snap-fit lid with vent grid and LED hole, seated on the body |
| `dome_surf` | NURBS Gaussian dome — reference surface for reflection analysis |

---

## API tour by section

### §1 — Body shell  `[Tier 2 + Tier 10]`

```python
body_shell = hollow_box(OUTER_L, OUTER_W, OUTER_H,
                        wall_thickness=WALL, open_face=TOP)
```

`hollow_box` is the Tier 2 shortcut: it calls Tier 1's `box()` then Tier 10's `shell()` to
carve out the interior, leaving a WALL-thick floor and side walls with an open top.

To use `shell()` directly — e.g., when you want non-uniform wall thickness or multiple open
faces — the API is identical to what `hollow_box` calls internally:

```python
cable_guide = shell(box(22, 60, 14), wall_thickness=1.5, open_faces=[FRONT, BACK])
```

The `open_faces` list accepts any anchor name (`TOP`, `BOTTOM`, `FRONT`, `BACK`, `LEFT`,
`RIGHT`).  Multiple entries produce a tube.

---

### §2 — Connector cutouts  `[Tier 7 + Tier 8 + Tier 9]`

Cutout shapes from Tier 7 and Tier 8 are all born with their depth dimension along **X**
(perpendicular to a YZ panel).  One rotate + one translate is all it takes to place any
cutout through any wall:

```python
# Rotate depth axis from X to Y, then centre on the front wall
usbc = usb_cutout("USB-C", panel_thickness=CUT_D, clearance=0.3)
usbc = rotate(usbc, axis=(0, 0, 1), angle_deg=90)
usbc = translate(usbc, dx=-20, dy=OUTER_W / 2, dz=_z_conn)
```

| Wall | Rotate axis | Angle | Translate |
|---|---|---|---|
| Front (Y+) | Z | +90° | `dy = +OUTER_W/2` |
| Back  (Y-) | Z | −90° | `dy = −OUTER_W/2` |
| Right (X+) | Y | +90° | `dx = +OUTER_L/2` |
| Left  (X-) | Y | −90° | `dx = −OUTER_L/2` |

All cutouts are subtracted together in a single `difference()` call — Tier 9's boolean
engine handles the full list:

```python
body = difference(body_shell, usbc, mhdmi, usba, gpio_slot, side_vent, led_wall)
```

#### Tier 8 functions used

| Function | What it produces |
|---|---|
| `usb_cutout("USB-C")` | 9.4 × 3.4 mm aperture (USB-C spec + clearance) |
| `usb_cutout("USB-A")` | 14.5 × 7.0 mm aperture |
| `hdmi_cutout("micro")` | 6.4 × 2.8 mm micro-HDMI aperture |

#### Tier 7 functions used

| Function | What it produces |
|---|---|
| `vent_slots(...)` | Rectangular louvred panel |
| `button_cutout(diameter=5, shape="round")` | Circular panel hole |
| `slot_hole(length=28, width=8, ...)` | Oblong slot (Tier 4, also used as a cutout) |

---

### §3 — Internal features  `[Tier 4 + Tier 8 + Tier 10 + Tier 11]`

#### PCB mount  `[Tier 8]`

```python
rpi_mount = raspberry_pi_mount(model="4B", standoff_height=6.0)
```

`raspberry_pi_mount` knows the exact hole pattern for every standard Pi board.  It returns
a base plate plus four M2.5 standoffs.  Anchoring it to the floor uses the `BOTTOM` anchor:

```python
dz = _z_floor - rpi_mount.anchors[BOTTOM].z
rpi_mount = translate(rpi_mount, dz=dz)
```

#### Corner bosses  `[Tier 4 + Tier 10 + Tier 11]`

```python
boss_raw  = boss(diameter=6.0, height=_boss_h, hole_diameter=3.2)
boss_unit = fillet(boss_raw, radius=0.4)          # Tier 10: smooth the top rim
boss_corners = grid_array(boss_unit,              # Tier 11: 2 × 2 layout
                          count_x=2, count_y=2,
                          spacing_x=90, spacing_y=60)
```

`grid_array` centers the 2 × 2 pattern at the origin, so spacing values equal the
centre-to-centre distance directly.

`fillet(shape, radius)` with no `edges` argument rounds every edge.  Pass a list of
`Part.Edge` objects to fillet selectively.

#### Structural ribs  `[Tier 4 + Tier 11]`

```python
rib_unit = rib(length=60, height=5, thickness=2.5)
rib_pair = linear_array(rib_unit, count=2, spacing=52.5, axis=(1, 0, 0))
```

`linear_array` **centres** the array at the shape's current position.  For two copies spaced
52.5 mm apart, each copy ends up at ±26.25 mm from the input shape's X position.

#### Gussets  `[Tier 4 + Tier 11]`

```python
gusset_corners = grid_array(gusset(length=8, height=8, thickness=2.5), ...)
```

`gusset` makes a triangular stiffener plate.  Used here at the rib-to-floor junction to
resist racking loads.

---

### §4 — Lid  `[Tier 7 + Tier 4 + Tier 9]`

```python
encl_lid = lid(length=OUTER_L, width=OUTER_W,
               rim_height=5.0, rim_inset=WALL,
               wall_thickness=WALL)
```

`lid()` builds a flat top panel with a hollow seating rim.  The rim outer width is
`length − 2 × rim_inset`, leaving a WALL-wide step that drops into the body opening.
`rim_inset=WALL` means the rim fits snugly inside a body whose walls are also WALL thick.

Vent slots and an LED hole are then subtracted:

```python
encl_lid = difference(encl_lid, lid_vents, led_lid)
```

Snap clips are created independently and positioned as a separate piece — they're not fused
into the lid geometry:

```python
_snap = snap_clip(length=12.0, width=4.0, hook_height=1.5, flex_arm_length=9.0)
snap_front = translate(_snap, dy=OUTER_W / 2 - WALL)
snap_back  = rotate(translate(_snap, dy=-(OUTER_W / 2 - WALL)),
                    axis=(0, 0, 1), angle_deg=180)
```

`snap_clip` returns a flexible arm with a latching hook.  Rotate the second one 180° so its
hook faces the opposing wall.

---

### §5 — NURBS surfaces  `[Tier 2 + Tier 15A]`

#### rounded_box  `[Tier 2]`

```python
rounded_ref = rounded_box(80, 60, 30, fillet_radius=4.0)
```

`rounded_box` pre-fillets all edges of a box in one call.  Equivalent to `fillet(box(...),
radius)` but more expressive when the shape is fundamentally "a rounded box".  Used here
as the reference solid for draft analysis (§6).

#### surface_from_points  `[Tier 15A]`

```python
dome_grid = [
    [(i * 8, j * 8, 8.0 * math.exp(-0.14 * ((i-2)**2 + (j-2)**2)))
     for j in range(5)]
    for i in range(5)
]
dome_surf = surface_from_points(dome_grid)
```

`surface_from_points` fits a `Part.BSplineSurface` through an m × n grid of `(x, y, z)`
tuples.  The result is a `PartikusShape` wrapping a `Part.Face` — compatible with the Tier
15D analysis tools.  Here the grid describes a Gaussian dome (peak 8 mm at the centre).

#### bspline_curve  `[Tier 15A]`

```python
cable_arc = bspline_curve([(-18, _ry, 0), (-9, _ry-7, 4), (0, _ry-9, 5), ...], degree=3)
```

`bspline_curve` produces a non-rational B-spline wire from control points.  The degree
controls smoothness: 1 = polyline, 3 = cubic (most common for smooth shapes).  The curve
can be used as a sweep path, a loft profile, or — as here — a reference sketch for a cable
routing arc.

---

### §6 — Surface analysis  `[Tier 15D]`

#### analyze_draft

```python
draft = analyze_draft(rounded_ref, pull_direction=(0, 0, 1))
# draft["min_draft_deg"]  — smallest face draft angle across the solid
# draft["mean_draft_deg"] — area-weighted mean
# draft["faces"]          — per-face breakdown: area, draft_angle_deg, ok
```

Draft angle = angle between a face's outward normal and the pull direction.  A face with
`draft_angle_deg < 1°` may stick in a straight-pull injection mould.

#### analyze_zebra

```python
zbr = analyze_zebra(dome_surf, stripe_count=10,
                    camera_direction=(0, 0, 1),
                    resolution=256,
                    output_path=zebra_path)
# zbr["continuity_hint"]  — "likely_G1" or "possible_G0"
# zbr["stripe_ids"]       — per-sample (u_frac, v_frac, stripe_id, normal)
```

The renderer samples the surface normal on a `resolution × resolution` UV grid, reflects a
virtual stripe environment off each normal, and maps the result to a PNG.  Stripe banding
that is smooth and continuous → surface is at least G1 (tangent-continuous).  Kinks or
breaks in the stripes indicate C0 discontinuities.

`analyze_zebra` requires a `PartikusShape` wrapping a single `Part.Face` with an underlying
`BSplineSurface` — the output of `surface_from_points`, `rebuild_surface`, etc.

---

### §7 — Assembly  `[Tier 14]`

```python
lid_seated = stack_on(encl_lid, body)
```

`stack_on(child, parent)` places the `BOTTOM` anchor of child exactly on the `TOP` anchor
of parent.  For the lid, this seats the rim inside the body opening.

Other Tier 14 functions used in the script:

| Function | Effect |
|---|---|
| `translate(shape, dx, dy, dz)` | Shift by an absolute offset vector |
| `rotate(shape, axis, angle_deg)` | Rotate around an arbitrary axis through origin |
| `stack_on(child, parent)` | Anchor-based vertical stacking |

For more precise anchor-to-anchor placement use `attach(child, parent, child_anchor,
parent_anchor)` — it aligns any two named anchors.

---

### §8 — Export  `[I/O]`

```python
to_step(body,  "rpi4_body.step")         # single shape → STEP
to_step(lid,   "rpi4_lid.step")

to_stl([(body, "Body"), (internals, "Internals"), (lid, "Lid")],
        "rpi4_enclosure.stl")             # labelled multi-body STL

save_fcstd([...], "rpi4_enclosure.FCStd") # FreeCAD native format
```

All three export functions accept:
- A single `PartikusShape`
- A list of `PartikusShape`
- A list of `(PartikusShape, label_string)` tuples

Import counterparts: `from_step()`, `from_brep()`, `from_stl()`.

---

### §9 — AI pipeline  `[AI]`

```python
from partikus.ai import generate_script

ai_script = generate_script(description_text,
                             hint="prefer hollow_box for the body",
                             export_step="ai_generated.step")
```

`generate_script` sends `description_text` to Claude, which:
1. Decomposes the description into a list of shapes + assembly operations
2. Generates a complete, runnable Partikus Python script

The returned string is valid Python that can be saved and executed under `freecadcmd`.

If you have an image of the object instead:
```python
ai_script = generate_script("/path/to/photo.jpg", hint="...")
```

The pipeline uses `ImageAnalyzer` (vision API) for image inputs and `analyze_text` for
text inputs.  Both require `ANTHROPIC_API_KEY` in the environment.

---

## Key design patterns

### Cutout-through-wall pattern

All connector openings follow the same pattern:

```
cutout = <tier7_or_tier8_function>(panel_thickness=CUT_D)
cutout = rotate(cutout, axis=<wall_normal_rotation>, angle_deg=<sign>90)
cutout = translate(cutout, d<wall_axis>=±OUTER_<dim>/2, dz=<connector_height>)
body   = difference(body, cutout)
```

`CUT_D = WALL * 6` ensures the cutout shape is always at least 3× the wall thickness,
eliminating any risk of the boolean failing due to near-tangent faces.

### Anchor-based positioning

Rather than tracking raw coordinates, use the shape's `anchors` dict:

```python
dz = target_surface_z - shape.anchors[BOTTOM].z
shape = translate(shape, dz=dz)
```

Every `PartikusShape` guarantees `CENTER`, `TOP`, `BOTTOM`, `FRONT`, `BACK`, `LEFT`,
`RIGHT`.  Box shapes additionally provide 8 corners and 12 edge midpoints.

### Centering convention

All shapes are bounding-box centred at the world origin when first created.  Assembly is
done by computing offsets from anchor positions, not from raw bounding box numbers.

---

## Parameters to experiment with

| Parameter | Default | Effect |
|---|---|---|
| `WALL` | 2.5 mm | Thicker = stronger; affects all cutout positioning |
| `OUTER_L / W / H` | 105 / 75 / 42 | Resize the entire enclosure |
| `STANDOFF_H` | 6 mm | PCB height above inner floor |
| `FILLET_R` | 3 mm | Outer corner rounding (cosmetic only) |
| `LID_RIM_H` | 5 mm | Rim depth; must be < body height |
| `CUT_D` | `WALL * 6` | Cutout depth; safe at any multiple ≥ 3 |
