"""
Partikus — parametric CAD toolkit.  Every part has its place.

Usage (inside FreeCAD / freecadcmd):

    from partikus import box, cylinder, difference, attach, TOP, BOTTOM
    body = box(40, 20, 10)
    hole = cylinder(diameter=8, height=15)
    part = difference(body, hole)

All dimensions are in mm unless a parameter name carries a suffix:
    _deg    → degrees
    _count  → dimensionless integer count
"""

# Coordinate / anchor constants
from .tier00_foundations import (
    UP, DOWN, NORTH, SOUTH, EAST, WEST,
    PLANE_XY, PLANE_XZ, PLANE_YZ,
    AXIS_X, AXIS_Y, AXIS_Z, ORIGIN,
)
from .core.anchors import (
    CENTER, TOP, BOTTOM, FRONT, BACK, LEFT, RIGHT,
    TOP_FRONT_LEFT, TOP_FRONT_RIGHT, TOP_BACK_LEFT, TOP_BACK_RIGHT,
    BOTTOM_FRONT_LEFT, BOTTOM_FRONT_RIGHT, BOTTOM_BACK_LEFT, BOTTOM_BACK_RIGHT,
    TOP_FRONT_EDGE, TOP_BACK_EDGE, TOP_LEFT_EDGE, TOP_RIGHT_EDGE,
    BOTTOM_FRONT_EDGE, BOTTOM_BACK_EDGE, BOTTOM_LEFT_EDGE, BOTTOM_RIGHT_EDGE,
    FRONT_LEFT_EDGE, FRONT_RIGHT_EDGE, BACK_LEFT_EDGE, BACK_RIGHT_EDGE,
    TOP_RIM, BOTTOM_RIM,
)

# Tier 1 — primitives
from .tier01_primitives import (
    box, cylinder, sphere, cone, torus, wedge, pyramid, disk, polyhedron,
)

# Tier 2 — enhanced primitives
from .tier02_enhanced import (
    rounded_box, chamfered_box, rounded_cylinder,
    tube, tube_by_wall, hollow_box,
    hemisphere, spherical_cap, frustum,
    prism, rounded_prism, stepped_cylinder,
)

# Tier 3 — 2D profiles
from .tier03_profiles_2d import (
    rectangle, rounded_rectangle, chamfered_rectangle,
    circle, ellipse, regular_polygon, star,
    slot, teardrop, arc, polyline,
)

# Tier 4 — mechanical features
from .tier04_mechanical import (
    boss, counterbore_hole, countersink_hole, slot_hole, keyway,
    rib, gusset, flange, lip, l_bracket, t_bracket, u_bracket,
    tab, slot_cutout, dovetail_pin, dovetail_slot, tongue, groove,
    living_hinge, snap_clip,
)

# Tier 5 — fasteners & standard parts
from .tier05_fasteners import (
    threaded_rod, tapped_hole,
    hex_bolt, socket_head_bolt, button_head_bolt, flat_head_bolt,
    hex_nut, flat_washer, lock_washer,
    heat_set_insert_pocket, clearance_hole, screw_size_preset,
    standoff, dowel_pin,
)

# Tier 6 — mechanical components
from .tier06_mechanical_components import (
    spur_gear, bevel_gear, rack, pulley_timing, sprocket,
    bearing_pocket, shaft_coupling,
)

# Tier 7 — enclosures
from .tier07_enclosures import (
    lid, snap_fit_box, hinged_box, magnetic_recess, battery_compartment,
    cable_channel, strain_relief, vent_slots, display_window, button_cutout,
)

# Tier 8 — electronics
from .tier08_electronics import (
    pcb_standoff, raspberry_pi_mount, arduino_mount, led_holder,
    usb_cutout, hdmi_cutout, barrel_jack_cutout, din_rail_clip,
    heatsink_fin_array,
)

# Tier 9 — booleans
from .tier09_boolean import (
    union, fuse,
    difference, cut,
    intersection, intersect,
)

# Tier 10 — modifiers
from .tier10_modifiers import (
    fillet, chamfer, shell, offset,
)

# Tier 11 — patterns
from .tier11_patterns import (
    linear_array, grid_array, polar_array, mirror,
)

# Tier 12 — sweep / loft
from .tier12_sweep_loft import (
    extrude, revolve, sweep, loft, pipe,
)

# Tier 13 — architectural
from .tier13_architectural import (
    wall, door, window, stairs, roof_gable, roof_hip, roof_shed,
    column, beam, slab, truss_simple,
)

# Tier 14 — assembly
from .tier14_assembly import (
    translate, rotate, scale, mirror_position,
    attach, stack_on, place_beside, align, coaxial,
)

# Tier 15A — NURBS curves (surfaces/editing stubbed)
from .tier15a_nurbs import (
    nurbs_curve, bspline_curve, bezier_curve, curve_through_points,
    helix_curve, conic_curve,
    loft_surface, network_surface, sweep_1rail, sweep_2rail,
    patch_fill, boundary_surface, surface_from_points,
    move_control_point, trim_surface, untrim_surface, split_surface,
    join_surfaces, rebuild_surface, offset_surface, match_surfaces,
    surface_fillet, variable_fillet, surface_chamfer,
)

# Tier 15B — SubD (all stubbed)
from .tier15b_subd import (
    subd_primitive, subd_push_pull, subd_insert_loop,
    subd_bevel_edge, subd_bevel_vertex, subd_bridge,
    subd_subdivide, subd_crease, subd_symmetry,
    subd_soft_select, subd_sculpt_brush,
)

# Tier 15C — conversion (stubbed)
from .tier15c_conversion import (
    subd_to_nurbs, nurbs_to_subd, mesh_to_subd, mesh_to_nurbs,
)

# Tier 15D — analysis (stubbed)
from .tier15d_analysis import (
    analyze_curvature, analyze_zebra, analyze_reflection,
    analyze_draft, analyze_deviation,
)

# I/O — export and import
from .io import (
    to_step, to_stl, to_iges, to_brep, to_obj, save_fcstd,
    from_step, from_brep, from_stl,
)

# AI integration — available as partikus.ai (lazy import; not re-exported here
# to avoid pulling in AI deps when not needed)
# Usage: from partikus.ai import generate_script, analyze_image

# Core type
from .core.shape_wrapper import PartikusShape

__all__ = [
    # foundations
    "UP", "DOWN", "NORTH", "SOUTH", "EAST", "WEST",
    "PLANE_XY", "PLANE_XZ", "PLANE_YZ",
    "AXIS_X", "AXIS_Y", "AXIS_Z", "ORIGIN",
    # anchors
    "CENTER", "TOP", "BOTTOM", "FRONT", "BACK", "LEFT", "RIGHT",
    "TOP_FRONT_LEFT", "TOP_FRONT_RIGHT", "TOP_BACK_LEFT", "TOP_BACK_RIGHT",
    "BOTTOM_FRONT_LEFT", "BOTTOM_FRONT_RIGHT", "BOTTOM_BACK_LEFT", "BOTTOM_BACK_RIGHT",
    "TOP_FRONT_EDGE", "TOP_BACK_EDGE", "TOP_LEFT_EDGE", "TOP_RIGHT_EDGE",
    "BOTTOM_FRONT_EDGE", "BOTTOM_BACK_EDGE", "BOTTOM_LEFT_EDGE", "BOTTOM_RIGHT_EDGE",
    "FRONT_LEFT_EDGE", "FRONT_RIGHT_EDGE", "BACK_LEFT_EDGE", "BACK_RIGHT_EDGE",
    "TOP_RIM", "BOTTOM_RIM",
    # tier 1
    "box", "cylinder", "sphere", "cone", "torus", "wedge", "pyramid", "disk", "polyhedron",
    # tier 2
    "rounded_box", "chamfered_box", "rounded_cylinder",
    "tube", "tube_by_wall", "hollow_box",
    "hemisphere", "spherical_cap", "frustum",
    "prism", "rounded_prism", "stepped_cylinder",
    # tier 3
    "rectangle", "rounded_rectangle", "chamfered_rectangle",
    "circle", "ellipse", "regular_polygon", "star",
    "slot", "teardrop", "arc", "polyline",
    # tier 4
    "boss", "counterbore_hole", "countersink_hole", "slot_hole", "keyway",
    "rib", "gusset", "flange", "lip", "l_bracket", "t_bracket", "u_bracket",
    "tab", "slot_cutout", "dovetail_pin", "dovetail_slot", "tongue", "groove",
    "living_hinge", "snap_clip",
    # tier 5
    "threaded_rod", "tapped_hole",
    "hex_bolt", "socket_head_bolt", "button_head_bolt", "flat_head_bolt",
    "hex_nut", "flat_washer", "lock_washer",
    "heat_set_insert_pocket", "clearance_hole", "screw_size_preset",
    "standoff", "dowel_pin",
    # tier 6
    "spur_gear", "bevel_gear", "rack", "pulley_timing", "sprocket",
    "bearing_pocket", "shaft_coupling",
    # tier 7
    "lid", "snap_fit_box", "hinged_box", "magnetic_recess", "battery_compartment",
    "cable_channel", "strain_relief", "vent_slots", "display_window", "button_cutout",
    # tier 8
    "pcb_standoff", "raspberry_pi_mount", "arduino_mount", "led_holder",
    "usb_cutout", "hdmi_cutout", "barrel_jack_cutout", "din_rail_clip",
    "heatsink_fin_array",
    # tier 9
    "union", "fuse", "difference", "cut", "intersection", "intersect",
    # tier 10
    "fillet", "chamfer", "shell", "offset",
    # tier 11
    "linear_array", "grid_array", "polar_array", "mirror",
    # tier 12
    "extrude", "revolve", "sweep", "loft", "pipe",
    # tier 13
    "wall", "door", "window", "stairs", "roof_gable", "roof_hip", "roof_shed",
    "column", "beam", "slab", "truss_simple",
    # tier 14
    "translate", "rotate", "scale", "mirror_position",
    "attach", "stack_on", "place_beside", "align", "coaxial",
    # tier 15a
    "nurbs_curve", "bspline_curve", "bezier_curve", "curve_through_points",
    "helix_curve", "conic_curve",
    "loft_surface", "network_surface", "sweep_1rail", "sweep_2rail",
    "patch_fill", "boundary_surface", "surface_from_points",
    "move_control_point", "trim_surface", "untrim_surface", "split_surface",
    "join_surfaces", "rebuild_surface", "offset_surface", "match_surfaces",
    "surface_fillet", "variable_fillet", "surface_chamfer",
    # tier 15b
    "subd_primitive", "subd_push_pull", "subd_insert_loop",
    "subd_bevel_edge", "subd_bevel_vertex", "subd_bridge",
    "subd_subdivide", "subd_crease", "subd_symmetry",
    "subd_soft_select", "subd_sculpt_brush",
    # tier 15c
    "subd_to_nurbs", "nurbs_to_subd", "mesh_to_subd", "mesh_to_nurbs",
    # tier 15d
    "analyze_curvature", "analyze_zebra", "analyze_reflection",
    "analyze_draft", "analyze_deviation",
    # I/O
    "to_step", "to_stl", "to_iges", "to_brep", "to_obj", "save_fcstd",
    "from_step", "from_brep", "from_stl",
    # core
    "PartikusShape",
]
