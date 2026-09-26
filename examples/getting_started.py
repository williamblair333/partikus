"""
The finished part from docs/getting-started.md — a parametric pillar mount.

    ./install.sh                                       # once
    squashfs-root/usr/bin/freecadcmd examples/getting_started.py

Writes examples/out/pillar_mount.step and .stl.

NOTE: docs/getting-started.md quotes this file section by section. If you
change the API this uses, change the tutorial too — they ship as a pair.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from partikus import (
    box, cylinder, attach, union, difference, to_step, to_stl,
    TOP, BOTTOM, CENTER,
)

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out")

# ── Parameters ────────────────────────────────────────────────────────────
# Change any of these and re-run. That is the whole point of the toolkit.
BASE_LENGTH = 60.0
BASE_WIDTH  = 40.0
BASE_THICK  = 6.0

PILLAR_DIA    = 20.0
PILLAR_HEIGHT = 30.0

BORE_DIA = 10.0

# ── Build ─────────────────────────────────────────────────────────────────
base   = box(BASE_LENGTH, BASE_WIDTH, BASE_THICK)
pillar = cylinder(diameter=PILLAR_DIA, height=PILLAR_HEIGHT)

# Seat the pillar's BOTTOM face onto the base's TOP face. No arithmetic.
seated = attach(pillar, base, child_anchor=BOTTOM, parent_anchor=TOP)

mount = union(base, seated)

# Bore straight down through pillar and base together.
#
# The cutter is centred on the origin like every other shape, so it grows in
# BOTH directions. To clear a part spanning -3..+33 mm it must be at least
# 2 x 33 mm tall, not 36. Undersize it and you silently get a blind hole.
bore_length = 2.0 * (BASE_THICK + PILLAR_HEIGHT + 2.0)
mount = difference(mount, cylinder(diameter=BORE_DIA, height=bore_length))

# ── Report ────────────────────────────────────────────────────────────────
print("pillar mount")
print("  base      : %.0f x %.0f x %.0f mm" % (BASE_LENGTH, BASE_WIDTH, BASE_THICK))
print("  pillar    : dia %.0f, height %.0f mm" % (PILLAR_DIA, PILLAR_HEIGHT))
print("  bore      : dia %.0f mm" % BORE_DIA)
print("  volume    : %.2f mm^3" % mount.shape.Volume)
print("  overall Z : %.1f mm" % (mount.anchors[TOP].z - mount.anchors[BOTTOM].z))

# ── Export ────────────────────────────────────────────────────────────────
if not os.path.isdir(OUT):
    os.makedirs(OUT)

step_path = os.path.join(OUT, "pillar_mount.step")
stl_path  = os.path.join(OUT, "pillar_mount.stl")

to_step(mount, step_path)
to_stl(mount, stl_path)

print()
print("wrote %s" % step_path)
print("wrote %s" % stl_path)
print("open the .step in FreeCAD, or the .stl in any slicer or mesh viewer.")
