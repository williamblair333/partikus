"""
Example: rectangular hand-mirror frame (open rebated window + glass + preview).

    /path/to/freecadcmd examples/hand_mirror.py

Rectangular bezel 115 mm wide (X) x 100 mm long (Y), 10 mm thick. The front face
is opened into a viewing window with a rebate (recess cut from the BACK) so a
mirror pane drops in from behind and is retained by a 4 mm front lip. A grip
handle hangs off the bottom edge; a hang-hole sits at the top.

Outputs to examples/out/:
    hand_mirror_frame.step / .stl   — the frame alone
    hand_mirror_glass.stl           — the mirror pane
    hand_mirror_assembly.step       — frame + glass together
    hand_mirror_preview.png         — shaded orthographic front view
"""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import Part

from partikus import (
    box, rounded_box, cylinder,
    union, difference, translate,
    to_step, to_stl,
)
from partikus.core.render import write_png

def log(msg):
    sys.stderr.write(msg + "\n")

# ── Parameters (mm) ──────────────────────────────────────────────────────
FRAME_L   = 115.0   # X — width  ("115 mm wide")
FRAME_W   = 100.0   # Y — length ("100 mm long")
FRAME_T   = 10.0    # Z — thickness
CORNER_R  = 4.0     # frame corner rounding (2*R < FRAME_T)

FRONT_LIP = 4.0     # front wall that retains the glass
REBATE_D  = FRAME_T - FRONT_LIP     # pocket depth cut from the back (6 mm)

APER_L    = 87.0    # viewing window X (what you see through)
APER_W    = 72.0    # viewing window Y
LIP       = 4.0     # retaining lip width around the window
REBATE_L  = APER_L + 2 * LIP        # glass pocket X (95)
REBATE_W  = APER_W + 2 * LIP        # glass pocket Y (80)

GLASS_L   = REBATE_L - 1.0          # pane X (0.5 mm clearance/side)
GLASS_W   = REBATE_W - 1.0          # pane Y
GLASS_T   = 3.0                     # pane thickness (< REBATE_D)

HANDLE_L  = 26.0    # X — grip width
HANDLE_W  = 100.0   # Y — grip length
HANDLE_R  = 4.0     # grip corner rounding (2*R < FRAME_T)
OVERLAP   = 12.0    # how far the handle tucks into the frame

HOLE_D    = 8.0     # hang-hole diameter

FRONT_Z   = FRAME_T / 2             # +Z front face at +5
REBATE_BACK_OF_LIP = FRONT_Z - FRONT_LIP   # inner face of the lip at +1

# ── Frame: slab, then open the window (rebate from back + aperture through) ─
frame = rounded_box(FRAME_L, FRAME_W, FRAME_T, fillet_radius=CORNER_R)

rebate = box(REBATE_L, REBATE_W, REBATE_D)
rebate = translate(rebate, dz=-FRAME_T / 2 + REBATE_D / 2)   # occupy the back
aperture = box(APER_L, APER_W, FRAME_T * 3)                  # clean through-cut
frame = difference(frame, rebate, aperture)

# ── Handle off the bottom (-Y) edge ───────────────────────────────────────
handle = rounded_box(HANDLE_L, HANDLE_W, FRAME_T, fillet_radius=HANDLE_R)
handle_cy = -(FRAME_W / 2) - (HANDLE_W / 2) + OVERLAP
handle = translate(handle, dy=handle_cy)
frame = union(frame, handle)

# ── Hang-hole near the top (+Y) ──────────────────────────────────────────
hole = cylinder(diameter=HOLE_D, height=FRAME_T * 3)
hole = translate(hole, dy=FRAME_W / 2 - 12.0)
frame = difference(frame, hole)

# ── Mirror pane, seated in the rebate against the back of the lip ─────────
glass = box(GLASS_L, GLASS_W, GLASS_T)
glass = translate(glass, dz=REBATE_BACK_OF_LIP - GLASS_T / 2)   # rests on lip

# ── Verify the lip actually captures the glass ───────────────────────────
captured = (GLASS_L > APER_L and GLASS_W > APER_W and
            GLASS_L < REBATE_L and GLASS_W < REBATE_W)
log("frame  vol   : %.2f mm^3" % frame.shape.Volume)
log("glass  vol   : %.2f mm^3  (%.0fx%.0fx%.0f)" % (
    glass.shape.Volume, GLASS_L, GLASS_W, GLASS_T))
log("pane > window: %s  (glass %gx%g vs aperture %gx%g)" % (
    GLASS_L > APER_L and GLASS_W > APER_W, GLASS_L, GLASS_W, APER_L, APER_W))
log("pane fits rebate: %s" % captured)
log("=> lip retains glass: %s" % captured)

# ── Export solids ─────────────────────────────────────────────────────────
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out")
os.makedirs(OUT, exist_ok=True)
to_step(frame, os.path.join(OUT, "hand_mirror_frame.step"))
to_stl(frame, os.path.join(OUT, "hand_mirror_frame.stl"), deflection=0.1)
to_stl(glass, os.path.join(OUT, "hand_mirror_glass.stl"), deflection=0.1)
# NOTE: to_step([...]) multi-shape path is broken in this build (Part.export
# expects document objects, not raw shapes -> empty file). Export a compound.
Part.Compound([frame.shape, glass.shape]).exportStep(
    os.path.join(OUT, "hand_mirror_assembly.step"))
log("Wrote frame .step/.stl, glass .stl, assembly .step")

# ── Software-rendered front preview (orthographic, +Z toward viewer) ──────
def _tris(shape, base_rgb, ambient=0.30):
    """Tessellate -> front-facing shaded triangles as (v0, v1, v2, rgb)."""
    verts, facets = shape.shape.tessellate(0.15)
    out = []
    for f in facets:
        a, b, c = verts[f[0]], verts[f[1]], verts[f[2]]
        nx = (b.y - a.y) * (c.z - a.z) - (b.z - a.z) * (c.y - a.y)
        ny = (b.z - a.z) * (c.x - a.x) - (b.x - a.x) * (c.z - a.z)
        nz = (b.x - a.x) * (c.y - a.y) - (b.y - a.y) * (c.x - a.x)
        n = math.sqrt(nx * nx + ny * ny + nz * nz) or 1.0
        nzn = nz / n
        if nzn <= 0.0:                      # cull back faces (light = viewer)
            continue
        sh = ambient + (1.0 - ambient) * nzn
        rgb = tuple(min(255, int(ch * sh)) for ch in base_rgb)
        out.append((a, b, c, rgb))
    return out

tris = _tris(frame, (198, 198, 205)) + _tris(glass, (150, 195, 230), ambient=0.55)

# Shared bounds over both parts so they stay registered.
allv = [v for t in tris for v in t[:3]]
minx = min(v.x for v in allv); maxx = max(v.x for v in allv)
miny = min(v.y for v in allv); maxy = max(v.y for v in allv)
PAD = 24
TARGET_W = 480
scale = (TARGET_W - 2 * PAD) / (maxx - minx)
W = TARGET_W
H = int((maxy - miny) * scale + 2 * PAD)

def _proj(v):
    px = PAD + (v.x - minx) * scale
    py = PAD + (maxy - v.y) * scale         # flip Y so +Y points up
    return px, py, v.z

fb = [(22, 22, 26)] * (W * H)
zb = [-1e18] * (W * H)
for a, b, c, rgb in tris:
    x0, y0, z0 = _proj(a); x1, y1, z1 = _proj(b); x2, y2, z2 = _proj(c)
    minpx = max(0, int(min(x0, x1, x2)));      maxpx = min(W - 1, int(max(x0, x1, x2)) + 1)
    minpy = max(0, int(min(y0, y1, y2)));      maxpy = min(H - 1, int(max(y0, y1, y2)) + 1)
    denom = (y1 - y2) * (x0 - x2) + (x2 - x1) * (y0 - y2)
    if abs(denom) < 1e-9:
        continue
    for py in range(minpy, maxpy + 1):
        for px in range(minpx, maxpx + 1):
            fx = px + 0.5; fy = py + 0.5
            w0 = ((y1 - y2) * (fx - x2) + (x2 - x1) * (fy - y2)) / denom
            w1 = ((y2 - y0) * (fx - x2) + (x0 - x2) * (fy - y2)) / denom
            w2 = 1.0 - w0 - w1
            if w0 < 0 or w1 < 0 or w2 < 0:
                continue
            z = w0 * z0 + w1 * z1 + w2 * z2
            idx = py * W + px
            if z > zb[idx]:
                zb[idx] = z
                fb[idx] = rgb

png = write_png(W, H, fb)
preview_path = os.path.join(OUT, "hand_mirror_preview.png")
with open(preview_path, "wb") as fh:
    fh.write(png)
log("Wrote %s (%dx%d)" % (preview_path, W, H))
