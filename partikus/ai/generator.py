"""
ScriptGenerator — convert an ImageAnalyzer analysis dict into a Partikus Python script.

The generated script is self-contained: it imports from partikus, defines
all shapes, assembles them, and (optionally) exports the result.
"""

import ast


# Every name here must be a callable export of `partikus` that returns a
# PartikusShape (a shape constructor) or transforms/combines shapes (an
# assembly op). generate() only *imports* names found in this set, so a
# function the model uses that is missing here produces a NameError at
# runtime. Deliberately excluded: analysis functions (analyze_*, which
# return dicts/PNGs, not shapes), SubD/mesh ops (subd_*, *_to_nurbs,
# mesh_to_*), 2D profiles (return wires), and the four Tier 15A stubs
# (untrim_surface, match_surfaces, variable_fillet, surface_chamfer).
_ALLOWED_FUNCTIONS = {
    # Tier 1 — primitives
    "box", "cylinder", "sphere", "cone", "torus", "wedge", "pyramid", "disk",
    # Tier 2 — enhanced primitives
    "rounded_box", "chamfered_box", "rounded_cylinder", "tube", "tube_by_wall",
    "hollow_box", "hemisphere", "spherical_cap", "frustum", "prism",
    "rounded_prism", "stepped_cylinder",
    # Tier 4 — mechanical features
    "boss", "counterbore_hole", "countersink_hole", "slot_hole", "keyway",
    "rib", "gusset", "flange", "lip", "l_bracket", "t_bracket", "u_bracket",
    "tab", "slot_cutout", "dovetail_pin", "dovetail_slot", "tongue", "groove",
    "living_hinge", "snap_clip",
    # Tier 5 — fasteners
    "threaded_rod", "tapped_hole", "hex_bolt", "socket_head_bolt",
    "button_head_bolt", "flat_head_bolt", "hex_nut", "flat_washer",
    "lock_washer", "heat_set_insert_pocket", "clearance_hole", "standoff",
    "dowel_pin",
    # Tier 6 — mechanical components
    "spur_gear", "bevel_gear", "rack", "pulley_timing", "sprocket",
    "bearing_pocket", "shaft_coupling",
    # Tier 7 — enclosures
    "lid", "snap_fit_box", "hinged_box", "magnetic_recess",
    "battery_compartment", "cable_channel", "strain_relief", "vent_slots",
    "display_window", "button_cutout",
    # Tier 8 — electronics
    "pcb_standoff", "raspberry_pi_mount", "arduino_mount", "led_holder",
    "usb_cutout", "hdmi_cutout", "barrel_jack_cutout", "din_rail_clip",
    "heatsink_fin_array",
    # Tier 9 — boolean
    "union", "difference", "intersection", "fuse", "cut", "intersect",
    # Tier 10 — modifiers
    "fillet", "chamfer", "shell", "offset",
    # Tier 11 — patterns
    "linear_array", "grid_array", "polar_array", "mirror",
    # Tier 12 — sweep / loft
    "extrude", "revolve", "sweep", "loft", "pipe",
    # Tier 13 — architectural
    "wall", "door", "window", "stairs", "roof_gable", "roof_hip", "roof_shed",
    "column", "beam", "slab", "truss_simple",
    # Tier 14 — assembly
    "translate", "rotate", "scale", "mirror_position",
    "attach", "stack_on", "place_beside", "align", "coaxial",
    # Tier 15 — NURBS curves + surfaces
    "nurbs_curve", "bspline_curve", "bezier_curve",
    "loft_surface", "sweep_1rail",
}

_ASSEMBLY_OPS = {
    "stack_on", "attach", "translate", "rotate", "scale",
    "union", "difference", "intersection",
    "fillet", "chamfer", "shell",
    "place_beside", "align", "coaxial", "mirror",
}


class ScriptGenerator:
    """
    Convert an analysis dict (from ImageAnalyzer) into a Partikus Python script.

    Usage::

        gen = ScriptGenerator()
        script = gen.generate(analysis, export_step="output/part.step")
        print(script)
    """

    def generate(self, analysis, export_step=None, export_stl=None):
        """
        Generate a Partikus Python script from an analysis dict.

        Args:
            analysis:    dict returned by ImageAnalyzer.analyze()
            export_step: optional path — appends to_step() call if given
            export_stl:  optional path — appends to_stl() call if given

        Returns:
            str — valid Python source code
        """
        lines = []
        imports = {"box"}  # minimal default; expanded below

        # Collect all referenced functions
        for s in analysis.get("shapes", []):
            fn = s.get("function", "")
            if fn in _ALLOWED_FUNCTIONS:
                imports.add(fn)
        for step in analysis.get("assembly", []):
            op = step.get("op", "")
            if op in _ALLOWED_FUNCTIONS:
                imports.add(op)

        io_imports = []
        if export_step:
            io_imports.append("to_step")
        if export_stl:
            io_imports.append("to_stl")

        # Header
        lines.append('"""')
        lines.append(f'Partikus script — {analysis.get("description", "generated shape")}')
        dims = analysis.get("estimated_dimensions_mm", {})
        if dims:
            lines.append(
                f'Estimated size: {dims.get("x", "?")} × {dims.get("y", "?")} × {dims.get("z", "?")} mm'
            )
        lines.append('"""')
        lines.append("from partikus import (")
        for fn in sorted(imports):
            lines.append(f"    {fn},")
        if io_imports:
            for fn in io_imports:
                lines.append(f"    {fn},")
        lines.append(")")
        lines.append("")

        # Shape definitions
        lines.append("# --- Shapes ---")
        for s in analysis.get("shapes", []):
            var   = _safe_id(s["id"])
            fn    = s.get("function", "box")
            params = s.get("params", {})
            note  = s.get("note", "")
            param_str = _format_params(params)
            comment = f"  # {note}" if note else ""
            lines.append(f"{var} = {fn}({param_str}){comment}")

        # Assembly steps
        assembly = analysis.get("assembly", [])
        if assembly:
            lines.append("")
            lines.append("# --- Assembly ---")
            for step in assembly:
                result = _safe_id(step.get("result", "result"))
                op     = step.get("op", "union")
                args   = [_safe_id(a) for a in step.get("args", [])]
                params = step.get("params", {})
                all_args = args + ([_format_params(params)] if params else [])
                lines.append(f"{result} = {op}({', '.join(all_args)})")

        # Final result
        final = _safe_id(analysis.get("final", "result"))
        lines.append("")
        lines.append(f"result = {final}")

        # Exports
        if export_step or export_stl:
            lines.append("")
            lines.append("# --- Export ---")
        if export_step:
            lines.append(f'to_step(result, {export_step!r})')
        if export_stl:
            lines.append(f'to_stl(result, {export_stl!r})')

        return "\n".join(lines) + "\n"


def validate_syntax(script):
    """
    Check that *script* is syntactically valid Python.

    Returns:
        (True, None) if valid
        (False, error_message) if invalid
    """
    try:
        ast.parse(script)
        return True, None
    except SyntaxError as e:
        return False, f"SyntaxError at line {e.lineno}: {e.msg}"


def _safe_id(name):
    """Return a safe Python identifier (replace hyphens, spaces, etc.)."""
    import re
    s = re.sub(r"[^a-zA-Z0-9_]", "_", str(name))
    if s and s[0].isdigit():
        s = "_" + s
    return s or "shape"


def _format_params(params):
    """Format a params dict as keyword arguments string."""
    parts = []
    for k, v in params.items():
        if isinstance(v, str):
            parts.append(f"{k}={v!r}")
        elif isinstance(v, (list, tuple)):
            parts.append(f"{k}={tuple(v)!r}")
        else:
            parts.append(f"{k}={v}")
    return ", ".join(parts)
