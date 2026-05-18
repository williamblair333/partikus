"""
Partikus I/O — import and export shapes in standard CAD formats.

Export: to_step, to_stl, to_iges, to_brep, to_obj, save_fcstd
Import: from_step, from_brep, from_stl

All functions accept/return PartikusShape. Multi-shape exports accept a list
of PartikusShape or a list of (PartikusShape, label_str) tuples.

All dimensions in mm.
"""

import os
import FreeCAD
import Part

from .core.shape_wrapper import PartikusShape
from .core.anchors import CENTER, TOP, BOTTOM, FRONT, BACK, LEFT, RIGHT


def _V(x, y, z):
    return FreeCAD.Vector(x, y, z)


def _bb_result(fc_shape):
    bb = fc_shape.BoundBox
    cx = (bb.XMin + bb.XMax) / 2
    cy = (bb.YMin + bb.YMax) / 2
    cz = (bb.ZMin + bb.ZMax) / 2
    def V(x, y, z): return FreeCAD.Vector(x, y, z)
    return PartikusShape(
        fc_shape,
        {
            CENTER: V(cx, cy, cz),
            TOP:    V(cx, cy, bb.ZMax),
            BOTTOM: V(cx, cy, bb.ZMin),
            FRONT:  V(cx, bb.YMax, cz),
            BACK:   V(cx, bb.YMin, cz),
            RIGHT:  V(bb.XMax, cy, cz),
            LEFT:   V(bb.XMin, cy, cz),
        },
        {
            TOP:   V(0, 0, 1),  BOTTOM: V(0, 0, -1),
            FRONT: V(0, 1, 0),  BACK:   V(0, -1, 0),
            RIGHT: V(1, 0, 0),  LEFT:   V(-1, 0, 0),
        },
    )


def _normalise(shapes):
    """Return list of (raw_fc_shape, label) from flexible input."""
    if isinstance(shapes, PartikusShape):
        shapes = [shapes]
    result = []
    for i, item in enumerate(shapes):
        if isinstance(item, tuple):
            s, label = item
        else:
            s, label = item, f"Shape_{i}"
        raw = s.shape if isinstance(s, PartikusShape) else s
        result.append((raw, label))
    return result


def _require_dir(filename):
    d = os.path.dirname(os.path.abspath(filename))
    os.makedirs(d, exist_ok=True)


# ── Export ────────────────────────────────────────────────────────────────────

def to_step(shapes, filename):
    """
    Export one or more shapes to a STEP (.step / .stp) file.

    Single shapes use Part.Shape.exportStep() for maximum compatibility
    (readable back via from_step). Multi-shape exports use Part.export(),
    which produces a STEP assembly file.

    Args:
        shapes:   PartikusShape, or list of PartikusShape, or list of
                  (PartikusShape, label) tuples
        filename: output path (e.g. "output/part.step")

    Example:
        to_step(body, "exports/body.step")
        to_step([top, bottom], "exports/assembly.step")
        to_step([(top, "Lid"), (bottom, "Base")], "exports/asm.step")
    """
    _require_dir(filename)
    items = _normalise(shapes)
    if len(items) == 1:
        items[0][0].exportStep(filename)
    else:
        Part.export([r for r, _ in items], filename)
    return filename


def to_stl(shapes, filename, deflection=0.1):
    """
    Export shape(s) to an STL file (triangulated mesh).

    Multiple shapes are combined into a compound before meshing.

    Args:
        shapes:     PartikusShape or list of PartikusShape
        filename:   output path (e.g. "output/part.stl")
        deflection: mesh chord height in mm — smaller = finer mesh (default 0.1 mm)

    Example:
        to_stl(body, "exports/body.stl", deflection=0.05)
    """
    _require_dir(filename)
    import Mesh as _Mesh
    items = _normalise(shapes)
    if len(items) == 1:
        raw = items[0][0]
    else:
        raw = Part.makeCompound([r for r, _ in items])
    msh = _Mesh.Mesh(raw.tessellate(deflection))
    msh.write(filename)
    return filename


def to_iges(shapes, filename):
    """
    Export one or more shapes to an IGES (.igs / .iges) file.

    Args:
        shapes:   PartikusShape, list of PartikusShape, or list of
                  (PartikusShape, label) tuples
        filename: output path

    Example:
        to_iges(surface, "exports/surface.igs")
    """
    _require_dir(filename)
    items = _normalise(shapes)
    raw_shapes = [r for r, _ in items]
    if len(raw_shapes) == 1:
        raw_shapes[0].exportIges(filename)
    else:
        compound = Part.makeCompound(raw_shapes)
        compound.exportIges(filename)
    return filename


def to_brep(shape, filename):
    """
    Export a shape to an OpenCASCADE BREP file (lossless round-trip format).

    Args:
        shape:    PartikusShape
        filename: output path

    Example:
        to_brep(body, "exports/body.brep")
    """
    _require_dir(filename)
    raw = shape.shape if isinstance(shape, PartikusShape) else shape
    raw.exportBrep(filename)
    return filename


def to_obj(shapes, filename, deflection=0.1):
    """
    Export shape(s) to a Wavefront OBJ file via mesh tessellation.

    Args:
        shapes:     PartikusShape or list of PartikusShape
        filename:   output path (e.g. "exports/part.obj")
        deflection: mesh quality in mm (default 0.1)

    Example:
        to_obj(body, "exports/body.obj")
    """
    _require_dir(filename)
    import Mesh as _Mesh
    items = _normalise(shapes)
    if len(items) == 1:
        raw = items[0][0]
    else:
        raw = Part.makeCompound([r for r, _ in items])
    msh = _Mesh.Mesh(raw.tessellate(deflection))
    msh.write(filename)
    return filename


def save_fcstd(shapes, filename, doc_name="Partikus"):
    """
    Save shape(s) to a FreeCAD .FCStd project file.

    Each shape is added as a Part::Feature with its label. The file can be
    opened directly in the FreeCAD GUI.

    Args:
        shapes:   PartikusShape, list of PartikusShape, or list of
                  (PartikusShape, label) tuples
        filename: output path ending in .FCStd
        doc_name: FreeCAD document name (default "Partikus")

    Example:
        save_fcstd([(body, "Body"), (cap, "Cap")], "project.FCStd")
    """
    _require_dir(filename)
    items = _normalise(shapes)
    doc = FreeCAD.newDocument(doc_name)
    for raw, label in items:
        feat = doc.addObject("Part::Feature", label)
        feat.Shape = raw
    doc.recompute()
    doc.saveAs(os.path.abspath(filename))
    return filename


# ── Import ────────────────────────────────────────────────────────────────────

def from_step(filename):
    """
    Import a STEP file and return a PartikusShape.

    The imported shape is bounding-box centred at origin.

    Args:
        filename: path to .step / .stp file

    Returns:
        PartikusShape wrapping the imported Part.Shape

    Example:
        part = from_step("vendor/flange.step")
    """
    if not os.path.exists(filename):
        raise FileNotFoundError(f"STEP file not found: {filename}")
    shape = Part.read(filename)
    if not shape.isValid():
        raise RuntimeError(f"Imported STEP shape is invalid: {filename}")
    return _bb_result(shape)


def from_brep(filename):
    """
    Import a BREP file and return a PartikusShape.

    Args:
        filename: path to .brep file

    Returns:
        PartikusShape wrapping the imported Part.Shape

    Example:
        part = from_brep("cache/body.brep")
    """
    if not os.path.exists(filename):
        raise FileNotFoundError(f"BREP file not found: {filename}")
    shape = Part.read(filename)
    if not shape.isValid():
        raise RuntimeError(f"Imported BREP shape is invalid: {filename}")
    return _bb_result(shape)


def from_stl(filename, tolerance=0.1):
    """
    Import an STL file and return a PartikusShape (as a Shell).

    The mesh is converted to a BREP shell via makeShapeFromMesh.

    Args:
        filename:  path to .stl file
        tolerance: stitching tolerance in mm (default 0.1)

    Returns:
        PartikusShape wrapping the imported Part.Shape

    Example:
        scan = from_stl("scan/printed_part.stl", tolerance=0.05)
    """
    if not os.path.exists(filename):
        raise FileNotFoundError(f"STL file not found: {filename}")
    import Mesh as _Mesh
    msh = _Mesh.read(filename)
    shape = Part.Shape()
    shape.makeShapeFromMesh(msh.Topology, tolerance)
    if not shape.isValid():
        raise RuntimeError(f"STL-to-shape conversion failed: {filename}")
    return _bb_result(shape)
