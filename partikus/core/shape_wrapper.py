"""Anchor-aware wrapper around FreeCAD Part.Shape."""


class PartikusShape:
    """
    Wraps a Part.Shape with named anchor points and outward-facing orientation vectors.

    Attributes:
        shape       — the underlying Part.Shape in world coordinates
        anchors     — dict[str, FreeCAD.Vector] of named points on the shape
        orientations — dict[str, FreeCAD.Vector] of outward normals at each anchor
    """

    __slots__ = ("shape", "anchors", "orientations")

    def __init__(self, shape, anchors, orientations=None):
        self.shape = shape
        self.anchors = anchors
        self.orientations = orientations or {}

    # ------------------------------------------------------------------ repr

    def __repr__(self):
        anchors = list(self.anchors.keys())
        return (f"<PartikusShape volume={self.shape.Volume:.3f} "
                f"anchors={anchors}>")
