"""
Example: hollow cylinder with a flat cap.

    /path/to/freecadcmd examples/capped_cylinder.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from partikus import (
    cylinder, disk, difference, stack_on, translate, TOP, BOTTOM
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
print()
print("Done — import into a FreeCAD document with:")
print("  from partikus.core.document import add_shape")
print("  add_shape(body, 'Body')")
print("  add_shape(capped, 'Cap')")
