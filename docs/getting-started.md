# Getting Started with Partikus

**A 20-minute lesson. You will end up with a real 3-D part on disk that you can open and look at.**

This is a tutorial, not a reference. Every line here is meant to be typed and run,
in order. It does not cover most of what Partikus can do — the
[Tier Reference](../README.md#tier-reference) does that, and it will make far more
sense after you have finished this page.

---

## What you are going to build

A **pillar mount**: a rectangular base plate with a cylindrical pillar standing on
it, bored straight through so a shaft or bolt can pass down the middle.

```
        ┌────┐          bore, Ø10, straight through
        │ ██ │  ◄─┐
        │ ██ │    │     pillar, Ø20 × 30 mm
        │ ██ │    │
   ┌────┴────┴────┴────┐
   │        ██         │  base, 60 × 40 × 6 mm
   └───────────────────┘
```

Nothing about this part is impressive. It was chosen because building it uses the
four ideas you need before anything else in Partikus makes sense: **solids**,
**booleans**, **anchors**, and **parameters**.

The finished program is about 30 lines.

---

## Before you start

You need:

- **Linux** with a shell.
- **FreeCAD 1.1 or newer.** Either a system install with `freecadcmd` on your
  `PATH`, or the Linux AppImage from [freecad.org](https://www.freecad.org/downloads.php)
  saved into the project root. The AppImage is not committed to the repository —
  it is ~800 MB — so on a fresh clone you download it yourself. Step 1 unpacks it.
- **Python 3.11.** Comes bundled inside FreeCAD. You do not install it separately,
  and you do not use your system `python3` to run Partikus.

That last point is the single most common source of confusion, so it is worth
saying plainly:

> **You never run Partikus with `python`.** You run it with `freecadcmd`, the
> command-line FreeCAD interpreter. Partikus is built on FreeCAD's geometry
> kernel, and that kernel only exists inside FreeCAD's own Python. Typing
> `python3 my_script.py` will fail at the first `import`.

---

## Step 1 — Install, and find your `freecadcmd`

From the project root:

```bash
./install.sh
```

The script looks for a system FreeCAD first, then an already-unpacked AppImage,
then falls back to extracting a `FreeCAD*.AppImage` it finds in the project root.
Extraction takes a minute or so the first time and produces a `squashfs-root/`
directory. If it finds none of the three, it stops and tells you so — download
the AppImage into the project root and re-run it.

When it finishes it prints the path it resolved, and the commands to use it:

```
Setup complete

  Run examples (headless):
    /opt/proj/partikus/squashfs-root/usr/bin/freecadcmd examples/capped_cylinder.py
```

**Copy that `freecadcmd` path.** Every command for the rest of this tutorial uses
it. On a normal checkout it will be:

```
squashfs-root/usr/bin/freecadcmd
```

but if you had FreeCAD installed system-wide already, `install.sh` will have
picked that instead, and yours may just be `freecadcmd`. Use whatever it printed.

From here on this tutorial writes `freecadcmd` and means *your* path.

---

## Step 2 — Make one solid and get it out of the computer

Create a file called `mount.py` in the project root:

```python
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from partikus import box, to_step, to_stl

part = box(60, 40, 6)

to_step(part, "examples/out/mount.step")
to_stl(part, "examples/out/mount.stl")

print("volume:", part.shape.Volume)
```

Run it:

```bash
freecadcmd mount.py
```

Expect a **wall of output**. FreeCAD's STEP writer prints a banner about transfer
statistics, and the STL writer prints a percentage counter that runs 0 % to 99 %.
None of that is an error. Buried in it you will find:

```
volume: 14400.0
```

Now look at what you made:

```bash
ls -la examples/out/mount.step examples/out/mount.stl
```

Open `mount.step` in FreeCAD, or drag `mount.stl` into any slicer, mesh viewer, or
[the online viewer of your choice](https://www.viewstl.com/). **It is a real
60 × 40 × 6 box.**

This step exists for one reason. Partikus builds geometry in memory and does
nothing visible unless you ask it to export. A script that builds a beautiful
assembly and never calls `to_step` or `to_stl` produces no output and looks
completely broken. Get the export line in early and you always have something to
look at.

### The two lines worth remembering

| Call | Gives you | Use it for |
|---|---|---|
| `to_step(shape, path)` | Exact CAD geometry (curves stay curves) | Opening in FreeCAD/Fusion/SolidWorks, further CAD work |
| `to_stl(shape, path)` | Triangle mesh approximation | 3-D printing, quick visual check |

Other formats — IGES, OBJ, BREP, native `.FCStd` — live in
[`partikus/io.py`](../partikus/io.py) and work the same way.

---

## Step 3 — Cut a hole

Replace the body of `mount.py`:

```python
from partikus import box, cylinder, difference, to_step, to_stl

base = box(60, 40, 6)
drill = cylinder(diameter=10, height=100)

base = difference(base, drill)

to_step(base, "examples/out/mount.step")
print("volume:", base.shape.Volume)
```

Run it again. The volume drops from `14400.0` to roughly `13928.7`.

Two things just happened that you need to understand before going further.

**Every shape is centred on the origin.** `box(60, 40, 6)` does not have a corner
at `(0,0,0)`. Its *centre* is at `(0,0,0)`, so it spans −30…+30 in X, −20…+20 in
Y, and −3…+3 in Z. Same for the cylinder. That is why the drill landed exactly in
the middle of the plate without you positioning it — both are centred, so they
already overlap.

**`difference` is subtraction, and order matters.** `difference(a, b)` means
"`a` with `b` removed." Swapping the arguments gives you the drill rod with a
plate-shaped notch in it, which is not what anyone wants. Its siblings are
`union` (fuse together) and `intersection` (keep only the overlap); all three are
in [Tier 9](../README.md#tier-9--boolean-operations).

The drill was made 100 mm tall against a 6 mm plate on purpose. When cutting
through something, always overshoot. A cutter exactly as tall as the wall it
passes through leaves coincident faces, and coincident faces are where CAD kernels
produce zero-thickness slivers and strange results.

And because the cutter is centred on the origin like everything else, it grows in
**both** directions — 100 mm tall means −50 to +50, not 0 to 100. Sizing a cutter
by the depth you want to cut rather than the span you need to clear is the single
easiest way to end up with a blind hole and no error message. There is a worked
example of getting this wrong in Step 5.

---

## Step 4 — Anchors, which is why Partikus exists

Now stand a pillar on the plate. Here is the version you would write in any
scripting CAD tool:

```python
from partikus import box, cylinder, translate

BASE_THICK    = 6.0
PILLAR_HEIGHT = 30.0

base   = box(60, 40, BASE_THICK)
pillar = cylinder(diameter=20, height=PILLAR_HEIGHT)

pillar = translate(pillar, dz=(BASE_THICK / 2) + (PILLAR_HEIGHT / 2))
```

That `dz` expression is correct. Work through it: the base's top face is half the
base thickness above the origin; the pillar's centre must sit half the pillar
height above that face. Hence `3 + 15 = 18`.

It is also exactly the kind of arithmetic that silently breaks the moment you
change `BASE_THICK`, flip the part over, or nest an assembly three levels deep.

Partikus's answer is that **every shape carries named points on its surface**, and
you position parts by naming the points that should touch:

```python
from partikus import box, cylinder, attach, TOP, BOTTOM

base   = box(60, 40, 6)
pillar = cylinder(diameter=20, height=30)

pillar = attach(pillar, base, child_anchor=BOTTOM, parent_anchor=TOP)
```

Read it aloud: *put the pillar's bottom on the base's top.* No arithmetic, and
nothing to update when the base thickness changes.

Both versions place the pillar's centre at exactly `(0, 0, 18)` — the second one
just does not care what 18 is.

### Seeing the anchors

Anchors are a plain dictionary on the shape. Print them:

```python
base = box(60, 40, 6)
for name, point in base.anchors.items():
    print(name, point)
```

A box gives you 27 anchors: the six faces, the eight corners, the twelve edge
midpoints, and the centre.

```
CENTER (0.0, 0.0, 0.0)
TOP (0.0, 0.0, 3.0)
BOTTOM (0.0, 0.0, -3.0)
FRONT (0.0, 20.0, 0.0)
...
TOP_FRONT_RIGHT (30.0, 20.0, 3.0)
TOP_LEFT_EDGE (-30.0, 0.0, 3.0)
```

Different primitives carry different sets. A cylinder has five — `CENTER`, `TOP`,
`BOTTOM`, `TOP_RIM`, `BOTTOM_RIM` — because corners and edge midpoints mean
nothing on a round body. The three names you can count on everywhere —
including on the result of a boolean — are `CENTER`, `TOP` and `BOTTOM`. Anchor
names are importable constants, so use `TOP` rather than the string `"TOP"` and
let Python catch your typos.

`attach()` also takes an `offset` (leave a deliberate gap along the joining axis)
and `rotation_deg` (spin the child in place). Full behaviour is documented in the
[Anchor System](../README.md#anchor-system) section.

> **One gotcha, and it will bite you.** Booleans do not preserve the full anchor
> set. Union or subtract two shapes and the result comes back with only `CENTER`,
> `TOP` and `BOTTOM`, recomputed from the new bounding box. So do your
> **positioning first, while the rich anchors still exist**, and combine
> afterwards. The next step is written in that order for exactly this reason.

---

## Step 5 — The finished part

Put it together. Position, then combine, then cut:

```python
base   = box(60, 40, 6)
pillar = cylinder(diameter=20, height=30)

seated = attach(pillar, base, child_anchor=BOTTOM, parent_anchor=TOP)

mount = union(base, seated)
mount = difference(mount, cylinder(diameter=10, height=38))
```

Now, how tall does that bore need to be? The assembled part runs from −3 mm (the
underside of the base) to +33 mm (the top of the pillar). That is 36 mm of
material, so 38 looks like a sensible overshoot.

**It is wrong, and it fails silently.** The cutter is centred on the origin, so
38 mm tall means it spans −19 to +19. It bores from the bottom of the base up to
+19 and stops — leaving 14 mm of solid pillar above it. You get a blind hole, no
warning, and a STEP file that looks fine until you section it.

The give-away is the volume. A Ø10 bore through 36 mm of material should remove
`π × 5² × 36 ≈ 2827 mm³`. Measure what the 38 mm cutter actually removed and you
get about 1728 mm³ — 22 mm of cutting, not 36.

To clear a part that reaches 33 mm above the origin, the cutter needs a
**half**-length of at least 33:

```python
bore_length = 2.0 * (BASE_THICK + PILLAR_HEIGHT + 2.0)
mount = difference(mount, cylinder(diameter=BORE_DIA, height=bore_length))
```

The complete, runnable program — with that fix in it — is committed as
[`examples/getting_started.py`](../examples/getting_started.py). Run it:

```bash
freecadcmd examples/getting_started.py
```

```
pillar mount
  base      : 60 x 40 x 6 mm
  pillar    : dia 20, height 30 mm
  bore      : dia 10 mm
  volume    : 20997.34 mm^3
  overall Z : 36.0 mm

wrote /opt/proj/partikus/examples/out/pillar_mount.step
wrote /opt/proj/partikus/examples/out/pillar_mount.stl
```

`23824.78` of solid, minus `2827.43` of bore, is `20997.34`. The arithmetic
reconciles, so the hole really does go through.

Open `examples/out/pillar_mount.step`. That is your part.

> Get in the habit of sanity-checking `shape.Volume` against a number you worked
> out by hand. It is the cheapest bug detector available in a headless workflow,
> and it is how the mistake above was caught.

---

## Step 6 — Change a number

This is the step that explains the word *parametric*, and it is the reason to use
a toolkit like this instead of drawing the part by hand.

Open `examples/getting_started.py` and find the parameter block near the top:

```python
PILLAR_DIA    = 20.0
PILLAR_HEIGHT = 30.0
```

Change the diameter to `28.0`. Re-run the same command:

```bash
freecadcmd examples/getting_started.py
```

```
  pillar    : dia 28, height 30 mm
  volume    : 30045.13 mm^3
```

The pillar got fatter, the bore stayed centred through it, the pillar stayed
seated on the plate, and the STEP file was rewritten. **You did not reposition
anything.** The bore is centred because both shapes are centred; the pillar stays
seated because `attach` recomputes from the anchors every run.

Change `BASE_THICK` to `10.0` and re-run — the pillar rides up with it, because
nothing in your code ever wrote down where the top of the base was.

That is the whole idea. Set `PILLAR_DIA` back to `20.0` when you are done.

---

## What you now know

- Partikus scripts run under **`freecadcmd`**, never plain `python`.
- Shapes are **centred on the origin** and are inert until you **export** them.
- `union`, `difference` and `intersection` combine solids; overshoot your cutters,
  and remember they overshoot in **both** directions from the origin.
- Check `shape.Volume` against hand arithmetic. Bad booleans do not raise.
- **Anchors** are named points on a shape; `attach()` positions parts by naming
  which points meet, so nothing breaks when dimensions change.
- Booleans **collapse the anchor set** — position first, combine second.

That is roughly Tier 0 through Tier 9 of a fifteen-tier toolkit.

## Where to go next

| If you want to… | Go to |
|---|---|
| See the whole API, tier by tier | [Tier Reference](../README.md#tier-reference) |
| Read a real, non-toy part | [`examples/rpi4_enclosure.py`](../examples/rpi4_enclosure.py) and its [walkthrough](rpi4_enclosure_walkthrough.md) |
| Round edges, shell out a box, add ribs | [Tier 7](../README.md#tier-7--container--enclosure-features), [Tier 10](../README.md#tier-10--edge--surface-modifiers) |
| Mount a PCB, add standoffs and vents | [Tier 8](../README.md#tier-8--electronics-mounting) |
| Sweep, loft, or work with NURBS | [Tier 12](../README.md#tier-12--sweep--loft), [Tier 15A](../README.md#tier-15a--nurbs-curves--surfaces) |
| Understand `attach()` fully | [Anchor System](../README.md#anchor-system) |
| Keep the shape in a FreeCAD document | [Document Serialisation](../README.md#document-serialisation) |
| Generate parts from a description or photo | [AI Integration](../README.md#ai-integration) |

### If something went wrong

| Symptom | Cause |
|---|---|
| `ModuleNotFoundError: No module named 'FreeCAD'` | You ran it with `python`. Use `freecadcmd`. |
| `ModuleNotFoundError: No module named 'partikus'` | The `sys.path.insert` line is missing, or you ran from outside the project root. |
| Script runs, prints numbers, produces nothing | No `to_step`/`to_stl` call. Geometry stays in memory otherwise. |
| `KeyError: 'TOP_FRONT_RIGHT'` after a boolean | Booleans keep only `CENTER`/`TOP`/`BOTTOM`. Position before combining. |
| Boolean gives an empty or bizarre solid | Coincident faces. Make cutters longer than the material they pass through. |
| Hole does not go all the way through | The cutter is centred on the origin and grows both ways. Its half-length must exceed the part's reach, not its total thickness. |
| Screens of transfer statistics and `(47 %)` | Normal. That is FreeCAD's exporter, not a failure. |
