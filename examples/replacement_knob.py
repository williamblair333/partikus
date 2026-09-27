"""
examples/replacement_knob.py — a replacement knob for a D-shaft

The knob on your stove, oven, washer, dryer, fan or amplifier broke, and the
model is old enough that nobody sells that knob any more. The "universal" knobs
that do exist rarely match the shaft, the depth, or the look of the panel. This
builds one from five caliper readings.

Measuring your shaft (calipers, not a ruler):

    SHAFT_DIA     across the round part of the shaft
    SHAFT_FLAT    from the flat face straight across to the far side
                  (for a double-D shaft: flat to flat)
    SHAFT_FLATS   1 for a D shaft, 2 for a double-D
    SHAFT_ENGAGE  how far the old knob sat down onto the shaft
    POINTER_DEG   where the knob's pointer sits relative to the flat, measured
                  counter-clockwise looking down on the knob. 0 = the pointer
                  is on the same side as the flat, which is the usual layout.
                  Check it against your old knob or the panel markings.

The most common stove/range valve shaft is 1/4 in (6.35 mm) with a flat at
about 4.6-4.8 mm, which is what the defaults below describe.

Print the FIT COUPON first. It is a 5 mm ring with exactly the knob's bore —
push it onto the shaft. Too tight: raise FIT_CLEARANCE by 0.05. Loose or it
turns on the shaft: lower it. Then print the knob. Five minutes of coupon saves
an hour of knob.

Safety — read this if the knob is for a cooker:
    * Print in PETG or ASA. PLA softens around 60 C and a range knob sits next
      to a burner.
    * After fitting, turn the valve to its OFF detent and check that the
      pointer reads OFF. A pointer that lies is worse than no knob.
    * The knob does not make a gas valve safe — the valve's own push-to-turn
      does. If the old knob had a spring clip or a metal insert, keep it.

Run headless:
    squashfs-root/usr/bin/freecadcmd examples/replacement_knob.py

Output files land in examples/out/:
    replacement_knob.stl              print this — already upside down, so the
                                      bore and the hollow underside open
                                      upward and nothing needs support
    replacement_knob_fit_coupon.stl   print this FIRST
    replacement_knob.step             the knob as fitted, for CAD
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from partikus import (
    cylinder, box, rounded_cylinder,
    union, difference, intersection,
    polar_array,
    translate, rotate, attach,
    TOP, BOTTOM,
)
from partikus.io import to_step, to_stl


# ─── Parameters — your measurements go here ──────────────────────────────────

SHAFT_DIA     = 6.35    # round diameter of the shaft
SHAFT_FLAT    = 4.75    # flat to far side (double-D: flat to flat)
SHAFT_FLATS   = 1       # 1 = D shaft, 2 = double-D
SHAFT_ENGAGE  = 13.0    # how deep the shaft goes into the knob
FIT_CLEARANCE = 0.15    # per side; tune with the fit coupon

KNOB_DIA      = 40.0
KNOB_HEIGHT   = 24.0
TOP_FILLET    = 3.0     # rounding on the top edge

POINTER_DEG   = 0.0     # pointer angle from the flat, counter-clockwise
POINTER_WIDTH = 1.6
POINTER_DEPTH = 1.0

# Grip. Real knurling would be nicer, but partikus knurl() is still a stub, so
# the grip is a ring of scallops cut into the rim instead.
GRIP_FLUTES   = 20
FLUTE_DIA     = 4.0
FLUTE_BITE    = 1.0     # how far each scallop cuts into the rim

# Underside. The knob is a shell around a central boss, not a solid puck —
# faster to print, less plastic, and it will not warp on the bed.
WALL          = 2.4
TOP_THICK     = 4.0
BOSS_DIA      = 12.0

COUPON_HEIGHT = 5.0

OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out")

_EPS = 0.5          # cutters overshoot the faces they open through by this
_MIN_BOSS_WALL = 1.2
_MIN_CEILING = 1.0  # plastic left between the bore and the pointer groove


# ─── Geometry ────────────────────────────────────────────────────────────────

def d_shaft(dia, across_flat, flats, height, z0=0.0):
    """
    A D (or double-D) shaft section standing on *z0*.

    The flat faces +Y. Used for the appliance shaft in the tests and, grown by
    the fit clearance, as the cutter for the knob's bore.
    """
    r = dia / 2.0
    tall = height + 2.0
    if flats == 1:
        flat_y = across_flat - r               # distance from axis to the flat
        lo = -r - 1.0
        keep = translate(box(dia + 2.0, flat_y - lo, tall), dy=(flat_y + lo) / 2.0)
    else:
        keep = box(dia + 2.0, across_flat, tall)
    section = intersection(cylinder(diameter=dia, height=height), keep)
    return translate(section, dz=z0 + height / 2.0)


def sink(cutter, body, face, depth):
    """
    Seat *cutter* so it reaches *depth* into *body* through *face* (TOP or
    BOTTOM) and pokes _EPS out past that face.

    The trick is a NEGATIVE offset. attach() puts the cutter against the face
    and offset moves it along the face's outward normal, so offset=-depth
    pushes it in. Cutter height must be depth + _EPS for the overshoot.
    """
    child = BOTTOM if face == TOP else TOP
    return attach(cutter, body, child_anchor=child, parent_anchor=face, offset=-depth)


def check(shaft_dia, shaft_flat, flats, engage, clearance, knob_dia, knob_height,
          top_fillet, top_thick, wall, boss_dia, flute_bite, pointer_depth):
    """Refuse measurements that cannot make a working knob, and say why."""
    if flats not in (1, 2):
        raise ValueError(f"SHAFT_FLATS must be 1 (D) or 2 (double-D), got {flats}")
    # A D's flat is measured to the far round side, so below half the diameter
    # it has cut past the axis. A double-D is symmetric, so any width works
    # geometrically; the floor there only catches a misread (a quarter of the
    # diameter is thinner than any real shaft).
    lowest = shaft_dia / 2.0 if flats == 1 else shaft_dia / 4.0
    if not lowest < shaft_flat < shaft_dia:
        how = ("from the flat face straight across to the far side, not the depth "
               "of the flat" if flats == 1 else "from one flat straight across to the other")
        raise ValueError(
            f"SHAFT_FLAT {shaft_flat} must be between {lowest:.2f} and SHAFT_DIA "
            f"{shaft_dia:.2f}. Measure {how}.")
    if top_thick >= knob_height - 2.0:
        raise ValueError(f"TOP_THICK {top_thick} leaves no skirt under a "
                         f"{knob_height} mm tall knob")
    deepest = knob_height - pointer_depth - _MIN_CEILING
    if engage > deepest:
        raise ValueError(
            f"SHAFT_ENGAGE {engage} is too deep for a {knob_height} mm knob — the bore "
            f"would break into the pointer groove. Max {deepest:.1f}, or raise KNOB_HEIGHT.")
    if flute_bite >= wall:
        raise ValueError(f"FLUTE_BITE {flute_bite} would cut through the {wall} mm WALL")
    if boss_dia >= knob_dia - 2 * wall - 1.0:
        raise ValueError(f"BOSS_DIA {boss_dia} fills the skirt of a {knob_dia} mm knob "
                         f"with {wall} mm WALL")
    thinnest = shaft_dia + 2 * clearance + 2 * _MIN_BOSS_WALL
    if boss_dia < thinnest:
        raise ValueError(f"BOSS_DIA {boss_dia} leaves under {_MIN_BOSS_WALL} mm of "
                         f"plastic around the bore — use at least {thinnest:.1f}")
    if not 0 < top_fillet < min(top_thick, knob_dia / 4):
        raise ValueError(f"TOP_FILLET {top_fillet} must be above 0 and below TOP_THICK")


def build_knob(shaft_dia=SHAFT_DIA, shaft_flat=SHAFT_FLAT, flats=SHAFT_FLATS,
               engage=SHAFT_ENGAGE, clearance=FIT_CLEARANCE,
               knob_dia=KNOB_DIA, knob_height=KNOB_HEIGHT, top_fillet=TOP_FILLET,
               pointer_deg=POINTER_DEG, pointer_width=POINTER_WIDTH,
               pointer_depth=POINTER_DEPTH,
               flutes=GRIP_FLUTES, flute_dia=FLUTE_DIA, flute_bite=FLUTE_BITE,
               wall=WALL, top_thick=TOP_THICK, boss_dia=BOSS_DIA):
    """The knob as fitted: underside on z=0, shaft entering from below."""
    check(shaft_dia, shaft_flat, flats, engage, clearance, knob_dia, knob_height,
          top_fillet, top_thick, wall, boss_dia, flute_bite, pointer_depth)

    body = rounded_cylinder(diameter=knob_dia, height=knob_height,
                            fillet_radius=top_fillet, ends="TOP")
    body = translate(body, dz=knob_height / 2.0)

    # Hollow underside: an annular cutter leaves the central boss standing.
    skirt_depth = knob_height - top_thick
    annulus = difference(cylinder(diameter=knob_dia - 2 * wall, height=skirt_depth + _EPS),
                         cylinder(diameter=boss_dia, height=skirt_depth + 2 * _EPS))
    skirt = sink(annulus, body, BOTTOM, skirt_depth)

    # The bore: the shaft itself, grown by the clearance, sunk up from below.
    bore = d_shaft(shaft_dia + 2 * clearance, shaft_flat + 2 * clearance, flats,
                   engage + _EPS, z0=-_EPS)

    # Grip scallops, offset half a step so none lands under the pointer.
    step = 360.0 / flutes
    flute = translate(cylinder(diameter=flute_dia, height=knob_height + 2 * _EPS),
                      dz=knob_height / 2.0)
    grip = polar_array(flute, count=flutes,
                       radius=knob_dia / 2.0 + flute_dia / 2.0 - flute_bite)
    grip = rotate(grip, axis=(0, 0, 1), angle_deg=step / 2.0)

    # Pointer groove on the top, from near the centre out through the rim,
    # on the flat's side (+Y) and then turned to POINTER_DEG.
    reach = knob_dia / 2.0 + _EPS
    start = 3.0
    groove = sink(box(pointer_width, reach - start, pointer_depth + _EPS),
                  body, TOP, pointer_depth)
    groove = translate(groove, dy=(start + reach) / 2.0)
    groove = rotate(groove, axis=(0, 0, 1), angle_deg=pointer_deg)

    return difference(body, skirt, bore, grip, groove)


def build_fit_coupon(shaft_dia=SHAFT_DIA, shaft_flat=SHAFT_FLAT, flats=SHAFT_FLATS,
                     clearance=FIT_CLEARANCE, height=COUPON_HEIGHT, boss_dia=BOSS_DIA):
    """
    A thin ring carrying exactly the knob's bore, to test the fit in minutes.
    A notch in the rim marks the flat's side.
    """
    ring = translate(cylinder(diameter=boss_dia + 6.0, height=height), dz=height / 2.0)
    bore = d_shaft(shaft_dia + 2 * clearance, shaft_flat + 2 * clearance, flats,
                   height + 2 * _EPS, z0=-_EPS)
    notch = translate(box(1.6, 4.0, height + 2 * _EPS),
                      dy=(boss_dia + 6.0) / 2.0, dz=height / 2.0)
    return difference(ring, bore, notch)


def print_oriented(knob):
    """Flip the knob onto its top face so the bore and skirt open upward."""
    h = knob.shape.BoundBox.ZMax
    return translate(rotate(knob, axis=(1, 0, 0), angle_deg=180), dz=h)


def verify(shape, name):
    """
    Fail loudly on a boolean that produced a degenerate result, before export.

    to_stl() tessellates whatever it is handed, so a bad cut would otherwise
    only show up in the slicer — or on the stove.
    """
    raw = shape.shape
    if not raw.isValid():
        raise ValueError(f"{name}: boolean produced an invalid shape — do not print it")
    if len(raw.Solids) != 1:
        raise ValueError(f"{name}: expected 1 solid, got {len(raw.Solids)}")
    return shape


# ─── Build ───────────────────────────────────────────────────────────────────

def main():
    knob = verify(build_knob(), "knob")
    coupon = verify(build_fit_coupon(), "fit coupon")

    kind = "double-D" if SHAFT_FLATS == 2 else "D"
    sys.stderr.write(
        f"replacement knob\n"
        f"  shaft   : {kind} {SHAFT_DIA} mm, flat {SHAFT_FLAT} mm, {SHAFT_ENGAGE} mm deep\n"
        f"  bore    : +{FIT_CLEARANCE} mm per side\n"
        f"  knob    : dia {KNOB_DIA} x {KNOB_HEIGHT} mm, {GRIP_FLUTES} grip flutes, "
        f"pointer at {POINTER_DEG} deg from the flat\n"
        f"  plastic : {knob.shape.Volume / 1000:.1f} cm^3\n")

    os.makedirs(OUT_DIR, exist_ok=True)
    to_stl(print_oriented(knob), os.path.join(OUT_DIR, "replacement_knob.stl"))
    to_stl(coupon, os.path.join(OUT_DIR, "replacement_knob_fit_coupon.stl"))
    to_step(knob, os.path.join(OUT_DIR, "replacement_knob.step"))
    sys.stderr.write(f"wrote replacement_knob.stl, replacement_knob_fit_coupon.stl and "
                     f"replacement_knob.step to {OUT_DIR}\n"
                     f"print the fit coupon first.\n")


# freecadcmd execs a script with __name__ set to its basename, not "__main__".
# Matching on the basename lets tests/test_replacement_knob.py load this module
# under another name without building and exporting.
if __name__ == "replacement_knob":
    main()
