"""
Anchor-aware FreeCAD document serialisation for PartikusShape.

save_to_doc()   — stores a PartikusShape as Part::FeaturePython, persisting
                  anchors + orientations in App::PropertyPythonObject so they
                  survive .FCStd round-trips.

load_from_doc() — reconstructs a PartikusShape from such a feature.

store_shape()   — replaces the shape and anchors of an existing feature.
"""

import FreeCAD
from .shape_wrapper import PartikusShape


class _PartikusProxy:
    """FeaturePython proxy that owns the two anchor storage properties."""

    def __init__(self, obj):
        obj.addProperty(
            "App::PropertyPythonObject",
            "PartikusAnchors",
            "Partikus",
            "Named anchor points (name -> (x, y, z))",
        ).PartikusAnchors = {}
        obj.addProperty(
            "App::PropertyPythonObject",
            "PartikusOrientations",
            "Partikus",
            "Anchor outward normals (name -> (x, y, z))",
        ).PartikusOrientations = {}
        _ensure_placement_property(obj)
        obj.Proxy = self

    def execute(self, obj):
        pass

    def __getstate__(self):
        return None

    def __setstate__(self, _state):
        pass


def _ensure_placement_property(obj):
    # The anchors are stored in the frame the shape had when it was written.
    # This records that frame, so a part moved by hand afterwards (Placement,
    # Edit -> Transform) can have its anchors moved to match on load. Objects
    # saved before this existed lack it and load exactly as they always did.
    if "PartikusPlacement" not in obj.PropertiesList:
        obj.addProperty(
            "App::PropertyPlacement",
            "PartikusPlacement",
            "Partikus",
            "Placement the anchors were stored in (internal)",
        )
        obj.setEditorMode("PartikusPlacement", 2)    # hidden: not user-editable


def store_shape(obj, shape):
    """
    Write *shape* and its anchors into an existing Partikus feature *obj*.

    save_to_doc() uses this for new features; the GUI Attach command uses it to
    replace a part in place. Anchors and the frame they are expressed in are
    always written together, so they cannot drift apart.
    """
    obj.Shape                = shape.shape
    obj.PartikusAnchors      = {k: (v.x, v.y, v.z) for k, v in shape.anchors.items()}
    obj.PartikusOrientations = {k: (v.x, v.y, v.z) for k, v in shape.orientations.items()}
    _ensure_placement_property(obj)
    obj.PartikusPlacement    = obj.Placement      # the Shape assignment set it


def _warn_if_degenerate(label, raw):
    """
    Say something when a shape that cannot be seen or printed enters a document.

    Nothing in FreeCAD objects to an empty solid. It adds cleanly, renders as
    nothing, and to_stl() will happily tessellate it — so a bad parameter
    surfaces as an empty viewport, with no exception and no log line, and gets
    diagnosed from a screenshot. An audit on 2026-09-12 found 18 exported
    functions reaching exactly that state through the GUI dialog.

    This does not raise. A caller may legitimately want a degenerate shape, and
    a warning that blocks work is worse than no warning. It only removes the
    silence.
    """
    problems = []
    try:
        if not raw.isValid():
            problems.append("not a valid shape")
        # Zero volume is only wrong for something that claims to be a solid —
        # Tier 3 profiles are wires and correctly have none.
        if raw.Solids and raw.Volume < 1e-9:
            problems.append("zero volume")
        if not raw.Solids and not raw.Faces and not raw.Wires:
            problems.append("empty — no solids, faces or wires")
    except Exception as e:                      # pragma: no cover - defensive
        problems.append(f"could not be inspected ({type(e).__name__})")

    if not problems:
        return
    msg = (f"Partikus: '{label}' is {'; '.join(problems)}. It will be invisible "
           f"in the 3D view and unusable in a boolean or an export. Check for a "
           f"zero or missing dimension.\n")
    try:
        FreeCAD.Console.PrintWarning(msg)
    except Exception:                           # pragma: no cover - defensive
        import sys
        sys.stderr.write(msg)


def save_to_doc(shape, label, doc=None):
    """
    Add *shape* to *doc* as a Part::FeaturePython feature named *label*.

    Anchors and orientations are stored in App::PropertyPythonObject
    properties and survive .FCStd save/load round-trips.

    Args:
        shape: PartikusShape to store
        label: feature name; FreeCAD may append a suffix if the name exists
        doc:   FreeCAD.Document; defaults to FreeCAD.ActiveDocument; a new
               document is created when none exists

    Returns:
        The created FreeCAD.DocumentObject

    Example:
        body = box(40, 30, 20)
        obj  = save_to_doc(body, "body")
    """
    if doc is None:
        doc = FreeCAD.ActiveDocument
    if doc is None:
        doc = FreeCAD.newDocument("Partikus")

    _warn_if_degenerate(label, shape.shape)

    obj = doc.addObject("Part::FeaturePython", label)
    _PartikusProxy(obj)
    store_shape(obj, shape)

    # DO NOT REMOVE — this line is what makes the shape visible.
    #
    # A Part::FeaturePython gets FreeCAD's ViewProviderPartExt, but that view
    # provider asks a Python proxy which display mode to use. With no proxy on
    # the ViewObject it picks none, and the result is an object that is valid,
    # visible, listed in the tree, and draws absolutely nothing. Measured on
    # FreeCAD 1.1.3:
    #
    #     no proxy   -> DisplayMode None          -> nothing rendered
    #     Proxy = 0  -> DisplayMode 'Flat Lines'  -> rendered
    #
    # (listDisplayModes() reports all four modes in both cases — availability is
    # not the problem, selection is.) Assigning 0 is the FreeCAD convention for
    # "no Python view provider, use the C++ default", and it matches what a
    # plain Part::Feature does.
    #
    # There is no error to catch here: FreeCAD considers an unrendered object a
    # perfectly good object, which is why this reached a user before a test.
    if obj.ViewObject is not None:        # None under freecadcmd — no GUI
        obj.ViewObject.Proxy = 0

    doc.recompute()
    return obj


def load_from_doc(obj):
    """
    Reconstruct a PartikusShape from a feature created by save_to_doc().

    Anchors follow the part: if it was moved or rotated by hand after it was
    saved, the returned anchors and normals are moved the same way.

    Args:
        obj: FreeCAD.DocumentObject with PartikusAnchors and
             PartikusOrientations properties

    Returns:
        PartikusShape

    Raises:
        AttributeError: if *obj* is not a Partikus feature

    Example:
        loaded = load_from_doc(doc.getObject("body"))
    """
    anchors      = {k: FreeCAD.Vector(*v) for k, v in obj.PartikusAnchors.items()}
    orientations = {k: FreeCAD.Vector(*v) for k, v in obj.PartikusOrientations.items()}
    if "PartikusPlacement" in obj.PropertiesList:
        # How far the part has been moved since its anchors were stored.
        moved = obj.Placement.multiply(obj.PartikusPlacement.inverse())
        anchors      = {k: moved.multVec(v)          for k, v in anchors.items()}
        orientations = {k: moved.Rotation.multVec(v) for k, v in orientations.items()}
    return PartikusShape(obj.Shape, anchors, orientations)
