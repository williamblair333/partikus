"""
Anchor-aware FreeCAD document serialisation for PartikusShape.

save_to_doc()   — stores a PartikusShape as Part::FeaturePython, persisting
                  anchors + orientations in App::PropertyPythonObject so they
                  survive .FCStd round-trips.

load_from_doc() — reconstructs a PartikusShape from such a feature.
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
        obj.Proxy = self

    def execute(self, obj):
        pass

    def __getstate__(self):
        return None

    def __setstate__(self, _state):
        pass


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

    obj = doc.addObject("Part::FeaturePython", label)
    _PartikusProxy(obj)
    obj.Shape               = shape.shape
    obj.PartikusAnchors      = {k: (v.x, v.y, v.z) for k, v in shape.anchors.items()}
    obj.PartikusOrientations = {k: (v.x, v.y, v.z) for k, v in shape.orientations.items()}
    doc.recompute()
    return obj


def load_from_doc(obj):
    """
    Reconstruct a PartikusShape from a feature created by save_to_doc().

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
    return PartikusShape(obj.Shape, anchors, orientations)
