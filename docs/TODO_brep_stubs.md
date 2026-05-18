# BRep-Editing Stubs — Implementation Guide

**Audience:** Skilled CAD / OpenCASCADE developer picking this up cold.  
**Status:** Four functions in `partikus/tier15a_nurbs.py` raise `NotImplementedError`.  
**Priority:** Low — the rest of the toolkit (130+ functions) is fully working. These are
advanced Class-A surfacing operations that most users never reach. Read the context
section before deciding whether to implement.

---

## 1. Context — Why These Are Stuck

Partikus runs under FreeCAD 1.1.1 via `freecadcmd` (headless AppImage). The Python
layer wraps OpenCASCADE (OCC) but does not expose every OCC API. These four operations
exist in OCC's C++ core and work fine in FreeCAD's GUI — but the Python bindings were
never written for them.

**Critical architecture constraint:** every function must work headless — no display,
no GPU, no Qt. `FreeCADGui` is not importable under `freecadcmd`. Any implementation
must respect this.

The four stubs:

```python
# partikus/tier15a_nurbs.py
def untrim_surface(surface):          raise NotImplementedError(...)
def match_surfaces(surf_a, surf_b):   raise NotImplementedError(...)
def variable_fillet(shape, edge_radii): raise NotImplementedError(...)
def surface_chamfer(shape, edges, size): raise NotImplementedError(...)
```

---

## 2. What Each Function Does

### `untrim_surface(surface)`

A trimmed NURBS face is a mathematical surface (infinite, or at least larger than
what you see) clipped by a boundary curve. The visible face is only the region
inside that boundary. "Untrimming" discards the clip and returns the full underlying
surface as a new face spanning its natural parametric domain.

**Use case:** Reverse-engineering workflows, surface repair, feeding a raw surface
into a re-approximation pipeline. Rarely needed in normal modelling.

**What it should return:** A `PartikusShape` wrapping the untrimmed `Part.Face`.

---

### `match_surfaces(surf_a, surf_b, continuity="G1")`

Adjusts the boundary control points of `surf_b` so that it meets `surf_a` with
the requested continuity:

- **G0** — they touch (positional, no gap)
- **G1** — same tangent plane at the join (no visible crease)
- **G2** — same curvature at the join (required for Class-A automotive surfaces)

**Use case:** Patching multi-surface models where panels must flow smoothly into
each other. Critical in automotive, consumer electronics, jewellery.

**What it should return:** A modified copy of `surf_b` as a `PartikusShape`.

---

### `variable_fillet(shape, edge_radii)`

A standard fillet rounds an edge with a fixed radius. A variable fillet lets the
radius change along the edge length — you specify `[(param, radius), ...]` pairs
and the fillet interpolates between them.

**Use case:** Ergonomic product design. The curve where a thumb rests on a handle
is wider in the middle and tighter at the ends. Constant-radius fillets look
mechanical; variable fillets look organic.

**Current partial workaround:** The existing `fillet()` applies constant radius.
For many cases, subdividing the model and applying different radii to different
edge segments is an acceptable substitute.

**What it should return:** A `PartikusShape` with the filleted solid.

---

### `surface_chamfer(shape, edges, size)`

Same as `variable_fillet` but produces a flat bevel rather than a rounded one.
OCC's `BRepFilletAPI_MakeChamfer` is the underlying tool, and like the fillet
API, only the constant-size form is exposed in FreeCAD Python.

**Use case:** Machined parts where radius is impractical (tool geometry), optical
components, chamfered glass edges.

**What it should return:** A `PartikusShape` with the chamfered solid.

---

## 3. Implementation Paths

Three doors into the locked OCC layer. Not mutually exclusive — you could use
Door 1 for `match_surfaces` and Door 2 for the rest.

---

### Door 1 — BSplineSurface Pole Manipulation (already accessible)

FreeCAD does expose the control-point grid of a BSplineSurface directly:

```python
bss  = face.Surface           # Part.BSplineSurface
poles = bss.getPoles()        # list[list[FreeCAD.Vector]]  — (u_count × v_count)
bss.setPoles(new_poles)       # write back
knots_u = bss.getUKnots()     # list[float]
knots_v = bss.getVKnots()     # list[float]
mults_u = bss.getUMultiplicities()
mults_v = bss.getVMultiplicities()
degree_u = bss.UDegree
degree_v = bss.VDegree
```

**Applies to:** `match_surfaces` (G0 and G1 are achievable this way).

#### How G1 matching works via pole adjustment

Given two faces sharing a boundary edge, G1 requires that at every point along
the join:
1. The surfaces share the same position (G0 — usually already true).
2. The cross-boundary derivative of `surf_b` equals the cross-boundary derivative
   of `surf_a` (or is a positive scalar multiple of it).

The cross-boundary derivative at the join is controlled by the row of poles
immediately inside the boundary. The algorithm:

```
For each boundary pole p_boundary on surf_b:
  1. Find the corresponding point on surf_a (same parameter)
  2. Compute surf_a's cross-boundary tangent at that point:
       tangent_a = (pole_inner_a - pole_boundary_a) / knot_span_a
  3. Set the inner pole of surf_b to enforce the same tangent:
       pole_inner_b = pole_boundary_b + tangent_a * knot_span_b
```

For G2 you also match the second row of poles (curvature), which requires the
second derivative — same idea, one more row.

**Limitations:**
- Only works when both surfaces are BSplineSurface (not planar, cylindrical, etc.).
  Other surface types need converting first: `bss = face.Surface.toBSpline()`.
- Does not guarantee that the adjusted surface still passes through its original
  interior points. For precision work, a re-approximation step after pole
  adjustment is needed.
- No FreeCAD helper method computes the shared boundary — you have to find it
  yourself via edge topology or geometric proximity.

**Effort:** 1–2 days for G0/G1. G2 is harder (another 1–2 days).

---

### Door 2 — pythonocc Subprocess (the practical one)

`pythonocc-core` is a separate Python binding for OpenCASCADE, installable via pip
on the system Python (not inside the AppImage). It has full OCC access including
all the APIs FreeCAD's Python layer is missing.

**Install:** `pip install pythonocc-core`  
**System requirement:** System Python 3.x alongside the AppImage's bundled Python.

#### Exchange mechanism

BREP is OCC's native lossless geometry format. FreeCAD already reads and writes it:

```python
# Export from FreeCAD
shape.exportBrep("/tmp/partikus_in.brep")

# Run pythonocc script in system Python subprocess
import subprocess, sys
result = subprocess.run(
    ["/usr/bin/python3", "-c", pythonocc_script],
    capture_output=True, timeout=30
)

# Import result back into FreeCAD
import Part
result_shape = Part.read("/tmp/partikus_out.brep")
```

The subprocess approach means Partikus itself still has zero external runtime
dependencies. pythonocc becomes an optional system-level dependency, and functions
can check for it at call time:

```python
def _require_pythonocc():
    result = subprocess.run(["/usr/bin/python3", "-c", "import OCC"], 
                            capture_output=True)
    if result.returncode != 0:
        raise RuntimeError(
            "pythonocc-core is required for this function.\n"
            "Install it with: pip install pythonocc-core"
        )
```

#### `variable_fillet` via pythonocc

```python
_VARIABLE_FILLET_SCRIPT = """
import sys
from OCC.Core.BRep import BRep_Builder
from OCC.Core.BRepTools import breptools_Read, breptools_Write
from OCC.Core.TopoDS import TopoDS_Shape
from OCC.Core.BRepFilletAPI import BRepFilletAPI_MakeFillet
from OCC.Core.TopExp import TopExp_Explorer
from OCC.Core.TopAbs import TopAbs_EDGE
import json, ast

brep_in  = sys.argv[1]
brep_out = sys.argv[2]
# edge_radii: list of [param, radius] pairs per edge index
edge_radii_per_edge = json.loads(sys.argv[3])

builder = BRep_Builder()
shape   = TopoDS_Shape()
breptools_Read(shape, brep_in, builder)

fillet = BRepFilletAPI_MakeFillet(shape)
explorer = TopExp_Explorer(shape, TopAbs_EDGE)
edge_idx = 0
while explorer.More():
    edge = explorer.Current()
    if str(edge_idx) in edge_radii_per_edge:
        for param, radius in edge_radii_per_edge[str(edge_idx)]:
            fillet.Add(param, radius, edge)  # variable radius form
    explorer.Next()
    edge_idx += 1

fillet.Build()
breptools_Write(fillet.Shape(), brep_out)
"""
```

**OCC API used:** `BRepFilletAPI_MakeFillet.Add(r1, r2, edge)` — the two-radius
form linearly interpolates radius along the edge length. For more control,
`Add(param, radius, edge)` lets you specify radius at a specific curve parameter.

#### `surface_chamfer` via pythonocc

```python
from OCC.Core.BRepFilletAPI import BRepFilletAPI_MakeChamfer
# BRepFilletAPI_MakeChamfer.Add(size, edge) — constant
# BRepFilletAPI_MakeChamfer.Add(d1, d2, edge, face) — asymmetric
```

Same subprocess pattern as variable_fillet.

#### `untrim_surface` via pythonocc

```python
from OCC.Core.BRep import BRep_Tool
from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_MakeFace
from OCC.Core.TopAbs import TopAbs_FACE
from OCC.Core.TopExp import TopExp_Explorer

# Get the underlying geometry stripped of trim bounds
explorer = TopExp_Explorer(shape, TopAbs_FACE)
face = explorer.Current()
surface, u0, u1, v0, v1 = BRep_Tool.Surface(face)  # returns Handle + natural bounds
untrimmed = BRepBuilderAPI_MakeFace(surface, u0, u1, v0, v1, 1e-6).Face()
```

This is the most straightforward of the four — OCC's `BRep_Tool.Surface()` is
literally what "untrim" means at the API level.

#### `match_surfaces` via pythonocc

```python
from OCC.Core.ShapeAnalysis import ShapeAnalysis_Surface
from OCC.Core.GeomAPI import GeomAPI_PointsToBSplineSurface
from OCC.Core.ShapeCustom import ShapeCustom_BSplineRestriction
# Or via BRepOffsetAPI_ThruSections for guided matching
```

This one is harder than the others. OCC does not have a single
"match these two surfaces to G1" call. The standard approach is:
1. Use `ShapeAnalysis_Surface` to find the shared boundary parameters.
2. Sample derivative vectors along that boundary on `surf_a`.
3. Use `GeomLProp_SLProps` to evaluate the tangent plane at each sample.
4. Adjust the boundary poles of `surf_b` to match (same maths as Door 1, but
   via pythonocc's more complete API).

Alternatively, OCC's `BRepFill_Filling` (the N-sided patch filler) can rebuild
`surf_b` constrained to be G1 with `surf_a` at the shared edge — effectively
a "refit within constraints" approach. This loses the original interior shape
of `surf_b` but guarantees continuity.

**Effort (all four via pythonocc):** 3–5 days including subprocess wrappers,
error handling, BREP exchange plumbing, and tests.

---

### Door 3 — Compiled FreeCAD Extension (the proper long-term solution)

Write a native FreeCAD Python extension module in C++ that wraps the missing
OCC calls. FreeCAD loads `.so` modules from its module search path at startup.

**Build requirements:**
- OpenCASCADE development headers (same version as bundled in the AppImage — extract
  from `squashfs-root/usr/include/opencascade/`)
- FreeCAD development headers (from the AppImage or source)
- `pybind11` (header-only, no install needed)
- A C++ compiler (g++ or clang++)

#### Module skeleton

```cpp
// partikus_brep.cpp
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <BRepFilletAPI_MakeFillet.hxx>
#include <BRepFilletAPI_MakeChamfer.hxx>
#include <BRep_Tool.hxx>
#include <BRepBuilderAPI_MakeFace.hxx>
#include <TopExp_Explorer.hxx>
#include <TopAbs_ShapeEnum.hxx>

namespace py = pybind11;

// FreeCAD exposes TopoDS_Shape pointers via a CObject capsule.
// Extract it from a Part.Shape Python object:
TopoDS_Shape shape_from_part(py::object part_shape) {
    // FreeCAD's Part.Shape holds a pointer accessible via __getstate__
    // or through the internal "_Shape" attribute — check FreeCAD source
    // src/Mod/Part/App/TopoShapePy.cpp for the exact capsule name.
    py::object capsule = part_shape.attr("_Shape");
    return *static_cast<TopoDS_Shape*>(
        PyCapsule_GetPointer(capsule.ptr(), "TopoDS_Shape"));
}

py::object variable_fillet_impl(py::object shape_obj,
                                  py::list edge_radius_pairs) {
    TopoDS_Shape shape = shape_from_part(shape_obj);
    BRepFilletAPI_MakeFillet fillet(shape);
    // ... iterate edges, call fillet.Add(param, radius, edge) ...
    fillet.Build();
    // Wrap result back into Part.Shape via FreeCAD's Python API
    // ...
}

PYBIND11_MODULE(partikus_brep, m) {
    m.def("variable_fillet", &variable_fillet_impl);
    m.def("untrim_surface",  &untrim_surface_impl);
    m.def("match_surfaces",  &match_surfaces_impl);
    m.def("surface_chamfer", &surface_chamfer_impl);
}
```

**The hard part:** Bridging FreeCAD's Python `Part.Shape` objects to OCC's
`TopoDS_Shape` C++ objects. FreeCAD does this internally but the bridge is not
a public API. The cleanest documented approach is to use FreeCAD's `Part.Shape`
import/export — but that defeats the purpose of a native extension.

The undocumented-but-working approach (used by several FreeCAD community
extensions): access the `_Shape` attribute via ctypes to retrieve the raw
`TopoDS_Shape*` pointer. This is fragile across FreeCAD versions.

A safer alternative: pass geometry as BREP strings (not files — as Python
`bytes` objects) through the pybind11 boundary. Less elegant than direct pointer
sharing but version-stable.

**Effort:** 1–2 weeks including figuring out the Part.Shape bridge, build system
setup, and testing. Worth it if the functions will be called frequently in
performance-sensitive loops.

---

## 4. Recommendation Per Function

| Function | Recommended path | Rationale |
|---|---|---|
| `match_surfaces` | Door 1 (pole manipulation) | G0/G1 is achievable with existing API; no subprocess overhead |
| `untrim_surface` | Door 2 (pythonocc) | One-liner in OCC; not worth Door 3 for a rarely-used utility |
| `variable_fillet` | Door 2 (pythonocc) | The most-wanted of the four; subprocess cost is acceptable |
| `surface_chamfer` | Door 2 (pythonocc) | Same pattern as variable_fillet; implement together |

If pythonocc subprocess is implemented, build a shared `_brep_subprocess.py`
helper that handles the BREP exchange boilerplate once, then each function is
just a different pythonocc script string.

---

## 5. Architecture Constraints to Respect

1. **Headless always.** No `FreeCADGui`, no Qt, no OpenGL. Every function must
   work under `squashfs-root/usr/bin/freecadcmd`.

2. **`freecadcmd` captures stdout.** All debug output must go to `sys.stderr` or
   `FreeCAD.Console.PrintMessage()`. Never `print()`.

3. **`__name__` is the script filename.** Never put bare code under
   `if __name__ == "__main__":` — use a plain `main()` call.

4. **Every function returns `PartikusShape`.** Never return a raw `Part.Shape`.
   Use `_bb_result(fc_shape)` for new shapes or `_preserve(src, new_fc_shape)`
   to carry anchors forward.

5. **Parameter naming is non-negotiable.** See `HANDOFF.md §11`. The AI
   downstream guesses parameter names from natural language — no abbreviations.

6. **External dependencies must be optional.** If pythonocc is not installed,
   raise a helpful `RuntimeError` explaining how to install it. Don't crash on
   import.

---

## 6. Testing Approach

The test runner is hand-rolled (no pytest — it's not bundled in the AppImage).
Add tests to `tests/test_tier15.py` following the existing pattern.

Minimum test set per function:

```python
def test_variable_fillet_produces_valid_shape():
    # Apply variable fillet, check isValid() and Volume > 0

def test_variable_fillet_volume_less_than_original():
    # Filleting removes material — result volume < input volume

def test_variable_fillet_missing_pythonocc_raises():
    # Patch PATH so pythonocc not found; assert RuntimeError with install hint

def test_variable_fillet_invalid_input_raises():
    # Pass None or wrong type; assert TypeError
```

Run with:
```bash
cd /opt/proj/partikus
squashfs-root/usr/bin/freecadcmd tests/run_tests.py 2>&1 | tail -5
```

Expected after full implementation: 4 stub tests removed, replaced by real tests.
Net test count should increase by ~15–20.

---

## 7. Files to Touch

| File | Change |
|---|---|
| `partikus/tier15a_nurbs.py` | Replace `raise NotImplementedError` bodies |
| `partikus/_brep_subprocess.py` | New — BREP exchange helper (if Door 2) |
| `partikus/core/render.py` | No change needed |
| `partikus/__init__.py` | No change needed — functions already exported |
| `tests/test_tier15.py` | Add real tests, remove stub-verification stubs |
| `CHANGELOG.md` | Add milestone entry |
| `HANDOFF.md` | Update stub table |

---

## 8. Effort Summary

| Path | Functions covered | Estimated effort |
|---|---|---|
| Door 1 alone (pole math) | `match_surfaces` G0/G1 | 1–2 days |
| Door 2 alone (pythonocc) | All four | 3–5 days |
| Door 1 + Door 2 | All four, `match_surfaces` more robust | 4–6 days |
| Door 3 (compiled extension) | All four, production-grade | 1–2 weeks |

For a one-person sprint, Door 1 + Door 2 is the sweet spot. Door 3 is worth it
only if these functions end up in hot paths (automated surface repair pipelines,
batch processing), which the current use cases don't suggest.
