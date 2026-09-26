"""
Example: hollow cylinder with a flat cap.

    /path/to/freecadcmd examples/capped_cylinder.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from partikus import (
    cylinder, disk, difference, union, stack_on, translate,
    to_step, to_stl, TOP, BOTTOM
)

# Outer shell
outer = cylinder(diameter=30, height=50)

# Bore (slightly shorter so the cap has a ledge to rest on)
bore = cylinder(diameter=26, height=46)

# Hollow body
body = difference(outer, translate(bore, dz=-2))

# Cap: a solid disk that sits on top
cap = disk(diameter=30, thickness=4)
capped = stack_on(cap, body)

print("Body volume :", round(body.shape.Volume, 2))
print("Cap  volume :", round(cap.shape.Volume, 2))
print("Cap TOP anchor:", capped.anchors[TOP])
print("Cap BOT anchor:", capped.anchors[BOTTOM])

# Export, so there is something to actually look at.
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out")
if not os.path.isdir(OUT):
    os.makedirs(OUT)

assembly = union(body, capped)
step_path = os.path.join(OUT, "capped_cylinder.step")
stl_path = os.path.join(OUT, "capped_cylinder.stl")
to_step(assembly, step_path)
to_stl(assembly, stl_path)

print()
print("wrote", step_path)
print("wrote", stl_path)
print("Open the .step in FreeCAD, or the .stl in any mesh viewer.")
print()
print("To load it into a live FreeCAD document instead:")
print("  from partikus.core.document import add_shape")
print("  add_shape(body, 'Body')")
print("  add_shape(capped, 'Cap')")
