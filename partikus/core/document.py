"""FreeCAD document management utilities."""

try:
    import FreeCAD as _FC
    _HAS_FREECAD = True
except ImportError:
    _HAS_FREECAD = False


def active_doc(name="Partikus"):
    """Return the active FreeCAD document, creating one named *name* if needed."""
    if not _HAS_FREECAD:
        raise RuntimeError("FreeCAD not available")
    doc = _FC.ActiveDocument
    if doc is None:
        doc = _FC.newDocument(name)
    return doc


def add_shape(partikus_shape, label="Shape", doc=None):
    """Add a PartikusShape to the FreeCAD document as a Part::Feature."""
    if not _HAS_FREECAD:
        raise RuntimeError("FreeCAD not available")
    if doc is None:
        doc = active_doc()
    feature = doc.addObject("Part::Feature", label)
    feature.Shape = partikus_shape.shape
    doc.recompute()
    return feature
