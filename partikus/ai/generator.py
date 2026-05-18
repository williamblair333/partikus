"""
ScriptGenerator — convert an ImageAnalyzer analysis dict into a Partikus Python script.

The generated script is self-contained: it imports from partikus, defines
all shapes, assembles them, and (optionally) exports the result.
"""

import ast


_ALLOWED_FUNCTIONS = {
    # Tier 1 — primitives
    "box", "cylinder", "sphere", "cone", "torus", "wedge", "pyramid", "disk",
    # Tier 2 — enhanced
    "rounded_box", "chamfered_box", "rounded_cylinder", "tube", "hollow_box",
    "hemisphere", "spherical_cap", "frustum", "prism", "rounded_prism",
    "stepped_cylinder",
    # Tier 9 — boolean
    "union", "difference", "intersection",
    # Tier 10 — modifiers
    "fillet", "chamfer", "shell", "offset",
    # Tier 12 — sweep / loft
    "extrude", "revolve", "sweep", "loft", "pipe",
    # Tier 14 — assembly
    "translate", "rotate", "scale", "mirror",
    "attach", "stack_on", "place_beside", "align", "coaxial",
    # Tier 15 — NURBS / surfaces
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
