"""
examples/rpi4_enclosure.py — Parametric Raspberry Pi 4B enclosure

A single runnable script that demonstrates the full Partikus API:
  Tier 2   — rounded_box, hollow_box
  Tier 4   — boss, rib, snap_clip, gusset, slot_hole
  Tier 7   — lid, vent_slots, button_cutout
  Tier 8   — raspberry_pi_mount, usb_cutout, hdmi_cutout
  Tier 9   — union, difference
  Tier 10  — fillet, shell
  Tier 11  — grid_array, linear_array
  Tier 14  — translate, rotate, stack_on
  Tier 15A — bspline_curve, surface_from_points
  Tier 15D — analyze_draft, analyze_zebra
  I/O      — to_step, to_stl, save_fcstd
  AI       — generate_script  (requires ANTHROPIC_API_KEY)

Companion walkthrough: docs/rpi4_enclosure_walkthrough.md

Run headless (no display required):
    cd /opt/proj/partikus
    squashfs-root/usr/bin/freecadcmd examples/rpi4_enclosure.py

Run with live GUI (watch it build step-by-step):
    PARTIKUS_GUI=1 squashfs-root/AppRun freecad examples/rpi4_enclosure.py

View result after a headless run:
    squashfs-root/AppRun examples/out/rpi4_enclosure.FCStd

Output files land in  examples/out/ :
    rpi4_body.step          rpi4_lid.step
    rpi4_enclosure.stl      rpi4_enclosure.FCStd
    dome_zebra.png          (Tier 15D reflection map)
    ai_generated.py         (only when ANTHROPIC_API_KEY is set)
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ─── Imports ──────────────────────────────────────────────────────────────────
from partikus import (
    # Tier 1
    box,
    # Tier 2  — enhanced primitives
    rounded_box, hollow_box,
    # Tier 4  — mechanical features
    boss, rib, snap_clip, gusset, slot_hole,
    # Tier 7  — enclosure features
    lid, vent_slots, button_cutout,
    # Tier 8  — electronics
    raspberry_pi_mount, usb_cutout, hdmi_cutout,
    # Tier 9  — boolean operations
    union, difference,
    # Tier 10 — modifiers
    fillet, shell,
    # Tier 11 — patterns
    linear_array, grid_array,
    # Tier 14 — assembly
    translate, rotate, stack_on,
    # Tier 15A — NURBS / surfaces
    bspline_curve, surface_from_points,
    # Tier 15D — surface analysis
    analyze_draft, analyze_zebra,
    # Anchor constants
    TOP, BOTTOM, FRONT, BACK, LEFT, RIGHT, CENTER,
)
from partikus.io import to_step, to_stl, save_fcstd


def _log(msg):
    if GUI_MODE:
        try:
            import FreeCAD as _FC2
            _FC2.Console.PrintMessage(msg + "\n")
            return
        except Exception:
            pass
    sys.stderr.write(msg + "\n")


# ─── GUI mode ─────────────────────────────────────────────────────────────────
GUI_MODE = os.environ.get("PARTIKUS_GUI") == "1"
_fgui = None
_fdoc = None

if GUI_MODE:
    try:
        import FreeCADGui as _fgui
        import FreeCAD as _FC
        _fdoc = _FC.newDocument("rpi4_enclosure")
        _log("[gui] GUI mode active — shapes appear in FreeCAD as each step runs")
    except Exception as _e:
        _log(f"[gui] FreeCADGui unavailable ({_e})")
        _log("[gui] Tip: PARTIKUS_GUI=1 squashfs-root/AppRun freecad examples/rpi4_enclosure.py")
        GUI_MODE = False
        _fgui = None


def _gui_show(shape, label):
    """Add shape to the live FreeCAD document and refresh the 3-D view."""
    if not GUI_MODE or _fgui is None or _fdoc is None:
        return
    raw = shape.shape if hasattr(shape, "shape") else shape
    obj = _fdoc.addObject("Part::Feature", label.replace(" ", "_"))
    obj.Shape = raw
    _fdoc.recompute()
    _fgui.updateGui()
    try:
        _fgui.ActiveDocument.ActiveView.fitAll()
    except Exception:
        pass
    try:
        from PySide2.QtWidgets import QApplication
        QApplication.processEvents()
    except Exception:
        pass


# ─── Parameters  (edit these to resize the enclosure) ────────────────────────

WALL       = 2.5     # wall / floor thickness (mm)
OUTER_L    = 105.0   # enclosure X — 10 mm margin each side of 85 mm RPi 4B PCB
OUTER_W    = 75.0    # enclosure Y —  9.5 mm margin each side of 56 mm RPi 4B PCB
OUTER_H    = 42.0    # enclosure body height (Z)
FILLET_R   = 3.0     # outer corner rounding
LID_RIM_H  = 5.0     # lid seating rim height
STANDOFF_H = 6.0     # PCB standoff height above inner floor

# ─── Derived geometry constants ───────────────────────────────────────────────
_z_floor  = -OUTER_H / 2 + WALL            # Z of inner floor surface
_z_pcb    = _z_floor + STANDOFF_H + 1.6   # Z of the top PCB surface (floor + standoff + board)
CUT_D     = WALL * 6                       # cutout depth — safely punches through any wall

OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out")
if _fdoc is not None:
    _fdoc.FileName = os.path.join(OUT_DIR, "rpi4_enclosure_gui.FCStd")
os.makedirs(OUT_DIR, exist_ok=True)


# ══════════════════════════════════════════════════════════════════════════════
# 1.  BODY SHELL   [Tier 2 · Tier 10]
#
#   hollow_box   — Tier 2 convenience wrapper: creates a Tier 1 box then calls
#                  Tier 10's shell() to hollow it with a uniform wall.
#   shell        — Tier 10 direct usage: here builds a two-exit cable guide
#                  trough with FRONT and BACK faces removed.
# ══════════════════════════════════════════════════════════════════════════════
_log("1 · Body shell  [Tier 2 + Tier 10] …")

# Open-top enclosure body — WALL-thick floor, walls, no ceiling [Tier 2]
body_shell = hollow_box(OUTER_L, OUTER_W, OUTER_H,
                        wall_thickness=WALL, open_face=TOP)

# Cable guide trough attached to the inner left wall — Tier 10 shell() directly:
# open FRONT and BACK so cables thread straight through
_cg_l  = 22.0
_cg_w  = OUTER_W - WALL * 6      # 60 mm — spans most of the body width (Y)
_cg_h  = 14.0
cable_guide = shell(box(_cg_l, _cg_w, _cg_h), wall_thickness=1.5,
                    open_faces=[FRONT, BACK])
cable_guide = translate(cable_guide,
                        dx=-OUTER_L / 2 + WALL + _cg_l / 2 + 1,
                        dz=_z_floor + _cg_h / 2 + 1)

_log(f"   body  valid={body_shell.shape.isValid()}"
     f"  vol={round(body_shell.shape.Volume, 0)} mm³")
_log(f"   cable guide  valid={cable_guide.shape.isValid()}")
_gui_show(body_shell, "Body_Shell")
_gui_show(cable_guide, "Cable_Guide")


# ══════════════════════════════════════════════════════════════════════════════
# 2.  CONNECTOR OPENINGS   [Tier 7 · Tier 8 · Tier 9]
#
# Each cutout shape is born with its depth dimension along X (perpendicular to
# the YZ panel).  A single rotate() maps depth to the target wall direction,
# then translate() positions the centre on that wall.  CUT_D >> WALL so the
# cut always punches all the way through.
#
#   usb_cutout   — Tier 8: standard rectangular cutout for USB connectors
#   hdmi_cutout  — Tier 8: HDMI aperture sized to spec
#   display_window / vent_slots / button_cutout — Tier 7
#   slot_hole    — Tier 4: oblong slot for the GPIO ribbon cable
#   difference   — Tier 9: subtract all openings from the body in one call
# ══════════════════════════════════════════════════════════════════════════════
_log("2 · Connector cutouts  [Tier 7 + Tier 8 + Tier 9] …")

# ── FRONT wall (Y+): USB-C power, micro-HDMI × 2, 3.5 mm audio ───────────────
# Positions from official RPi 4B DXF (RP-0082); board centred at X=0, Y=0.
# enc_x = board_x_from_left_edge − 42.5   (board spans X: −42.5 → +42.5)
# usb_cutout / hdmi_cutout depth along X → rotate 90° about Z → depth along +Y.

usbc = usb_cutout("USB-C", panel_thickness=CUT_D, clearance=0.3)
usbc = rotate(usbc, axis=(0, 0, 1), angle_deg=90)
usbc = translate(usbc, dx=-31.3, dy=OUTER_W / 2, dz=_z_pcb + 2.4)   # 11.2 mm from left

mhdmi0 = hdmi_cutout("micro", panel_thickness=CUT_D, clearance=0.3)
mhdmi0 = rotate(mhdmi0, axis=(0, 0, 1), angle_deg=90)
mhdmi0 = translate(mhdmi0, dx=-16.5, dy=OUTER_W / 2, dz=_z_pcb + 2.0) # 26.0 mm from left

mhdmi1 = hdmi_cutout("micro", panel_thickness=CUT_D, clearance=0.3)
mhdmi1 = rotate(mhdmi1, axis=(0, 0, 1), angle_deg=90)
mhdmi1 = translate(mhdmi1, dx=-3.0,  dy=OUTER_W / 2, dz=_z_pcb + 2.0) # 39.5 mm from left

# 3.5 mm audio / composite jack — round Ø 7.5 mm aperture  [Tier 7]
# button_cutout depth along Z → rotate 90° about X → depth along +Y
av_jack = button_cutout(diameter=7.5, panel_thickness=CUT_D, shape="round")
av_jack = rotate(av_jack, axis=(1, 0, 0), angle_deg=90)
av_jack = translate(av_jack, dx=11.5, dy=OUTER_W / 2, dz=_z_pcb + 6.0) # 54.0 mm from left

# ── RIGHT wall (X+): USB 2.0 × 2, USB 3.0 × 2, Gigabit Ethernet ─────────────
# box(length, width, height): length=X, width=Y, height=Z.
# box() centred at origin; depth (X = CUT_D) punches through the right wall.

usb2_cut = box(CUT_D, 14.0, 15.6)
usb2_cut = translate(usb2_cut, dx=OUTER_L / 2, dy=19.4,   dz=_z_pcb + 7.8)

usb3_cut = box(CUT_D, 14.0, 15.6)
usb3_cut = translate(usb3_cut, dx=OUTER_L / 2, dy=0.7,    dz=_z_pcb + 7.8)

eth_cut  = box(CUT_D, 16.0, 16.0)
eth_cut  = translate(eth_cut,  dx=OUTER_L / 2, dy=-17.75, dz=_z_pcb + 6.75)

# ── BACK wall (Y-): GPIO 40-pin ribbon-cable slot  [Tier 4] ──────────────────
# slot_hole: length along X (52 mm), width along Y (9 mm cross-section), depth along Z.
# rotate 90° about X → depth along −Y (punches through the back wall).
gpio_slot = slot_hole(length=52, width=9, depth=CUT_D)
gpio_slot = rotate(gpio_slot, axis=(1, 0, 0), angle_deg=90)
gpio_slot = translate(gpio_slot, dx=-10.0, dy=-OUTER_W / 2, dz=_z_pcb + 4.5)

# ── LEFT wall (X-): ventilation slots  [Tier 7] ───────────────────────────────
# vent_slots depth along Z → rotate −90° about Y → depth along −X
side_vent = vent_slots(length=30, width=20, slot_count=4, slot_width=2.0,
                       depth=CUT_D, wall_thickness=1.0)
side_vent = rotate(side_vent, axis=(0, 1, 0), angle_deg=-90)
side_vent = translate(side_vent, dx=-OUTER_L / 2, dz=_z_floor + 14)

# ── Status LED on front wall  [Tier 7] ────────────────────────────────────────
led_wall = button_cutout(diameter=5.0, panel_thickness=CUT_D, shape="round")
led_wall = rotate(led_wall, axis=(1, 0, 0), angle_deg=90)
led_wall = translate(led_wall, dx=28.0, dy=OUTER_W / 2, dz=_z_pcb + 14)

# Subtract all openings at once  [Tier 9]
body = difference(body_shell,
                  usbc, mhdmi0, mhdmi1, av_jack,
                  usb2_cut, usb3_cut, eth_cut,
                  gpio_slot, side_vent, led_wall)

_log(f"   body after cuts  valid={body.shape.isValid()}"
     f"  vol={round(body.shape.Volume, 0)} mm³")
_gui_show(body, "Body_with_Cutouts")


# ══════════════════════════════════════════════════════════════════════════════
# 3.  INTERNAL FEATURES   [Tier 4 · Tier 8 · Tier 10 · Tier 11]
#
#   raspberry_pi_mount — Tier 8: mounting plate + M2.5 standoffs at the exact
#                        RPi 4B hole pattern (61.5 × 49 mm spacing)
#   boss + fillet      — Tier 4 + Tier 10: M3 corner posts, rim edges rounded
#   grid_array         — Tier 11: 2 × 2 layout positions the posts at corners
#   rib + linear_array — Tier 4 + Tier 11: two stability webs along the body
#   gusset             — Tier 4: triangular stiffeners at rib–floor junctions
# ══════════════════════════════════════════════════════════════════════════════
_log("3 · Internals  [Tier 4 + Tier 8 + Tier 10 + Tier 11] …")

# PCB mounting plate with standoffs  [Tier 8]
rpi_mount = raspberry_pi_mount(model="4B", standoff_height=STANDOFF_H)
# Anchor BOTTOM of mount to the inner floor
_dz_mount = _z_floor - rpi_mount.anchors[BOTTOM].z
rpi_mount = translate(rpi_mount, dz=_dz_mount)

# M3 corner boss posts — filleted top rim  [Tier 4 + Tier 10]
_boss_h   = OUTER_H - WALL * 2
boss_raw  = boss(diameter=6.0, height=_boss_h, hole_diameter=3.2)
boss_unit = fillet(boss_raw, radius=0.4)            # Tier 10: round the rim edge

# Place four corner bosses via 2 × 2 grid  [Tier 11]
_bsx = OUTER_L - 2 * (WALL + 5)          # 90 mm spacing along X
_bsy = OUTER_W - 2 * (WALL + 5)          # 60 mm spacing along Y
boss_corners = grid_array(boss_unit, count_x=2, count_y=2,
                          spacing_x=_bsx, spacing_y=_bsy)
boss_corners = translate(boss_corners, dz=_z_floor + _boss_h / 2)

# Structural webs — one rib unit, duplicated along X  [Tier 4 + Tier 11]
_rib_len  = OUTER_W - WALL * 6           # 60 mm, clears body inner walls
_rib_h    = STANDOFF_H - 1.0             # 5 mm, stays below PCB seating plane
rib_unit  = rib(length=_rib_len, height=_rib_h, thickness=2.5)
rib_unit  = translate(rib_unit, dz=_z_floor + _rib_h / 2)
rib_pair  = linear_array(rib_unit, count=2,
                         spacing=OUTER_L * 0.5, axis=(1, 0, 0))

# Gussets at rib-to-floor corners  [Tier 4 + Tier 11]
_gusset_unit = gusset(length=8.0, height=8.0, thickness=2.5)
_gusset_unit = translate(_gusset_unit, dz=_z_floor + 4)
gusset_corners = grid_array(_gusset_unit,
                             count_x=2, count_y=2,
                             spacing_x=OUTER_L - WALL * 6,
                             spacing_y=OUTER_W - WALL * 6)

internals = union(rpi_mount, boss_corners, rib_pair, gusset_corners, cable_guide)

_log(f"   internals  vol={round(internals.shape.Volume, 0)} mm³")
_gui_show(internals, "Internals")


# ══════════════════════════════════════════════════════════════════════════════
# 4.  LID   [Tier 7 · Tier 4 · Tier 9]
#
#   lid          — Tier 7: flat panel with a downward seating rim that nests
#                  inside the body opening
#   vent_slots   — Tier 7: ventilation grid cut into the lid panel
#   button_cutout— Tier 7: 5 mm status LED hole in the top-left corner
#   snap_clip    — Tier 4: latching tongue on the front and back rim edges
#   difference   — Tier 9: cut the vent grid and LED hole from the lid
# ══════════════════════════════════════════════════════════════════════════════
_log("4 · Lid  [Tier 7 + Tier 4 + Tier 9] …")

# Base lid panel + seating rim  [Tier 7]
encl_lid = lid(length=OUTER_L, width=OUTER_W,
               rim_height=LID_RIM_H, rim_inset=WALL,
               wall_thickness=WALL)

# Vent grid on top of lid panel  [Tier 7]
# Position centre at the lid panel midheight
_lid_top_z    = encl_lid.anchors[TOP].z        # ≈ (WALL + LID_RIM_H) / 2
_panel_mid_z  = _lid_top_z - WALL / 2
lid_vents = vent_slots(length=68, width=55, slot_count=7, slot_width=2.5,
                       depth=WALL * 2, wall_thickness=1.0)
lid_vents = translate(lid_vents, dz=_panel_mid_z)

# Status LED hole  [Tier 7]
led_lid = button_cutout(diameter=5.0, panel_thickness=WALL * 3, shape="round")
led_lid = translate(led_lid,
                    dx=-OUTER_L / 2 + 14,
                    dy=-OUTER_W / 2 + 14,
                    dz=_panel_mid_z)

# Cut both features from the lid panel  [Tier 9]
encl_lid = difference(encl_lid, lid_vents, led_lid)

# Snap-clip tabs on front and back rim — attach via translate/rotate  [Tier 4]
_snap    = snap_clip(length=12.0, width=4.0, hook_height=1.5, flex_arm_length=9.0)
snap_front = translate(_snap, dy=OUTER_W / 2 - WALL)
snap_back  = rotate(translate(_snap, dy=-(OUTER_W / 2 - WALL)),
                    axis=(0, 0, 1), angle_deg=180)
lid_snaps = union(snap_front, snap_back)

_log(f"   lid  valid={encl_lid.shape.isValid()}"
     f"  vol={round(encl_lid.shape.Volume, 0)} mm³")
_gui_show(encl_lid, "Lid")


# ══════════════════════════════════════════════════════════════════════════════
# 5.  NURBS SURFACES   [Tier 2 · Tier 15A]
#
#   rounded_box         — Tier 2: ergonomic rounded profile; used here as a
#                         reference solid for draft-angle analysis in §6
#   surface_from_points — Tier 15A: fits a BSplineSurface through a 2-D point
#                         grid; produces a Part.Face suitable for Tier 15D
#   bspline_curve       — Tier 15A: smooth B-spline from control points; used
#                         here to define a cable-routing arc on the rear wall
# ══════════════════════════════════════════════════════════════════════════════
_log("5 · NURBS surfaces  [Tier 2 + Tier 15A] …")

# Rounded reference solid — shows Tier 2 rounded_box independently of the body
rounded_ref = rounded_box(80, 60, 30, fillet_radius=4.0)    # Tier 2

# Gaussian dome surface: 5 × 5 point grid, peak of 8 mm at centre  [Tier 15A]
dome_grid = [
    [(i * 8, j * 8,
      8.0 * math.exp(-0.14 * ((i - 2) ** 2 + (j - 2) ** 2)))
     for j in range(5)]
    for i in range(5)
]
dome_surf = surface_from_points(dome_grid)   # → Part.Face wrapped as PartikusShape

# B-spline cable-routing arc sketched on the rear exterior wall  [Tier 15A]
_ry = -OUTER_W / 2
arc_ctrl = [
    (-18, _ry,     0), (-9, _ry - 7, 4),
    (  0, _ry - 9, 5),
    (  9, _ry - 7, 4), (18, _ry,     0),
]
cable_arc = bspline_curve(arc_ctrl, degree=3)

_log(f"   rounded_ref  valid={rounded_ref.shape.isValid()}")
_log(f"   dome surface valid={dome_surf.shape.isValid()}")
_log(f"   cable arc    valid={cable_arc.shape.isValid()}")
_gui_show(rounded_ref, "Rounded_Ref")
_gui_show(dome_surf,   "Dome_Surface")
_gui_show(cable_arc,   "Cable_Arc")


# ══════════════════════════════════════════════════════════════════════════════
# 6.  SURFACE ANALYSIS   [Tier 15D]
#
#   analyze_draft  — per-face draft-angle report; min_draft_deg < 1° means
#                    a face may stick in a straight-pull mould
#   analyze_zebra  — stripe reflection map written as a PNG; stripes that
#                    bend or break at seam lines reveal G1 discontinuities
# ══════════════════════════════════════════════════════════════════════════════
_log("6 · Surface analysis  [Tier 15D] …")

# Draft analysis on the rounded reference solid (pull along Z)
draft = analyze_draft(rounded_ref, pull_direction=(0, 0, 1))
_log(f"   draft  faces={len(draft['faces'])}"
     f"  min={round(draft['min_draft_deg'], 1)}°"
     f"  mean={round(draft['mean_draft_deg'], 1)}°")

# Zebra reflection map of the NURBS dome surface → PNG  [Tier 15D]
zebra_path = os.path.join(OUT_DIR, "dome_zebra.png")
zbr = analyze_zebra(
    dome_surf,
    stripe_count=10,
    camera_direction=(0, 0, 1),
    resolution=256,
    output_path=zebra_path,
)
_log(f"   zebra  continuity={zbr['continuity_hint']}"
     f"  samples={zbr['sample_count']}"
     f"  → {zebra_path}")


# ══════════════════════════════════════════════════════════════════════════════
# 7.  ASSEMBLY   [Tier 14]
#
#   stack_on  — places child BOTTOM anchor on parent TOP anchor;
#               seats the lid rim inside the body opening
#   translate — positions snap clips relative to the assembled body
# ══════════════════════════════════════════════════════════════════════════════
_log("7 · Assembly  [Tier 14] …")

# Seat lid on body
lid_seated = stack_on(encl_lid, body)

# Snap clips positioned on the exterior of the body at the lid seam
snaps_positioned = translate(lid_snaps,
                             dz=body.anchors[TOP].z)

_log(f"   body TOP     = {body.anchors[TOP]}")
_log(f"   lid  BOTTOM  = {lid_seated.anchors[BOTTOM]}")
_gui_show(lid_seated, "Assembly")


# ══════════════════════════════════════════════════════════════════════════════
# 8.  EXPORT   [I/O]
# ══════════════════════════════════════════════════════════════════════════════
_log("8 · Export  [I/O] …")

to_step(body,        os.path.join(OUT_DIR, "rpi4_body.step"))
to_step(lid_seated,  os.path.join(OUT_DIR, "rpi4_lid.step"))

to_stl(
    [(body, "Body"), (internals, "Internals"), (lid_seated, "Lid")],
    os.path.join(OUT_DIR, "rpi4_enclosure.stl"),
)
save_fcstd(
    [(body, "Body"), (internals, "Internals"), (lid_seated, "Lid")],
    os.path.join(OUT_DIR, "rpi4_enclosure.FCStd"),
)

_log(f"   STEP + STL + FCStd  → {OUT_DIR}/")


# ══════════════════════════════════════════════════════════════════════════════
# 9.  AI PIPELINE   [requires ANTHROPIC_API_KEY]
#
#   generate_script — send a text description to Claude; receive a complete
#                     runnable Partikus Python script in return; the output
#                     script can be edited, committed, and re-run independently
# ══════════════════════════════════════════════════════════════════════════════
_log("9 · AI pipeline …")

if not os.environ.get("ANTHROPIC_API_KEY"):
    _log("   ANTHROPIC_API_KEY not set — skipping AI demo.")
    _log("   Set it and re-run to see generate_script() produce a Partikus script.")
else:
    from partikus.ai import generate_script

    _desc = (
        "A compact rectangular enclosure for a Raspberry Pi 4B, "
        "105 mm × 75 mm × 42 mm outer dimensions, 2.5 mm walls, "
        "open top with a separate snap-fit lid.  Ventilation slots on the "
        "lid top face.  USB-C power inlet and micro-HDMI cutout on the front "
        "wall.  GPIO ribbon-cable slot on the right wall.  Internal standoffs "
        "at the RPi 4B mounting-hole pattern."
    )
    ai_script = generate_script(
        _desc,
        hint="prefer hollow_box for the body; use raspberry_pi_mount for standoffs",
        export_step=os.path.join(OUT_DIR, "ai_generated.step"),
    )
    ai_path = os.path.join(OUT_DIR, "ai_generated.py")
    with open(ai_path, "w") as _fh:
        _fh.write(ai_script)
    _log(f"   AI script  {len(ai_script)} chars  → {ai_path}")


# ─── Done ─────────────────────────────────────────────────────────────────────
_log("")
_log("═" * 52)
_log("  rpi4_enclosure.py — complete")
_log(f"  body  valid={body.shape.isValid()}"
     f"  vol={round(body.shape.Volume, 0)} mm³")
_log(f"  lid   valid={lid_seated.shape.isValid()}"
     f"  vol={round(lid_seated.shape.Volume, 0)} mm³")
_log(f"  out → {OUT_DIR}")
_log("═" * 52)
