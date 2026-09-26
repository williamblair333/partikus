"""
Attach — line one part up on another by named anchor, optionally welding them.

The GUI form of tier14 attach(): select two Partikus parts, pick which one
moves, which of its anchors meets which anchor on the other, and whether to
fuse the result into one solid.

attach_objects() holds all of the document logic and runs headless, so it is
what the tests exercise. The dialog and the command are thin shells over it.
"""

try:
    from PySide import QtWidgets
    import FreeCADGui
    HAS_GUI = True
except ImportError:
    # auto_dialog.py already reports a missing Qt binding; one warning is enough.
    HAS_GUI = False

from ..core.serialise import load_from_doc, save_to_doc, store_shape
from ..tier09_boolean import union
from ..tier14_assembly import attach


def is_partikus_object(obj):
    """True if *obj* is a document feature that carries Partikus anchors."""
    return obj is not None and "PartikusAnchors" in getattr(obj, "PropertiesList", ())


def anchor_names(obj):
    """Anchor names *obj* carries, in a stable order for a dropdown."""
    return sorted(obj.PartikusAnchors)


def _describe(obj):
    return obj.Label if obj.Label == obj.Name else f"{obj.Label} ({obj.Name})"


def _check_anchor(obj, name):
    names = anchor_names(obj)
    if name not in names:
        raise ValueError(f"{_describe(obj)} has no anchor {name!r}; "
                         f"it has: {', '.join(names)}")


def attach_objects(child_obj, parent_obj, child_anchor="BOTTOM", parent_anchor="TOP",
                   offset=0.0, rotation_deg=0.0, weld=False):
    """
    Move *child_obj* so its *child_anchor* sits on *parent_obj*'s *parent_anchor*.

    Both must be Partikus parts (created by the workbench or save_to_doc). Parts
    moved by hand beforehand are handled — anchors follow the part. The whole
    operation is one undo step, and a failure leaves the document untouched.

    Args:
        child_obj:     document object to move
        parent_obj:    document object that stays put
        child_anchor:  anchor on the moving part (default BOTTOM)
        parent_anchor: anchor on the fixed part (default TOP)
        offset:        gap between the two along the joining axis, mm
        rotation_deg:  spin of the moving part about the joining axis
        weld:          also fuse both into one new solid and hide the originals

    Returns:
        The new welded object when *weld* is True, otherwise *child_obj*.

    Raises:
        ValueError: an object is not a Partikus part, both arguments are the
                    same part, or an anchor name does not exist on its part.
    """
    for obj in (child_obj, parent_obj):
        if not is_partikus_object(obj):
            raise ValueError(f"{_describe(obj)} is not a Partikus part — it has no "
                             "anchors. Create parts from the Partikus menus.")
    if child_obj is parent_obj:
        raise ValueError("A part cannot be attached to itself; select two different parts.")
    _check_anchor(child_obj, child_anchor)
    _check_anchor(parent_obj, parent_anchor)

    child  = load_from_doc(child_obj)
    parent = load_from_doc(parent_obj)
    moved  = attach(child, parent, child_anchor=child_anchor, parent_anchor=parent_anchor,
                    offset=offset, rotation_deg=rotation_deg)

    doc = child_obj.Document
    doc.openTransaction("Attach")
    try:
        store_shape(child_obj, moved)
        result = child_obj
        if weld:
            result = save_to_doc(union(parent, moved), "Weld", doc)
            parent_obj.Visibility = False
            child_obj.Visibility = False
        doc.recompute()
    except Exception:
        doc.abortTransaction()
        raise
    doc.commitTransaction()
    return result


if HAS_GUI:

    class AttachDialog(QtWidgets.QDialog):
        """Pick the moving part, the two anchors, a gap, a spin and weld-or-not."""

        def __init__(self, first, second, parent=None):
            super().__init__(parent)
            self.setWindowTitle("Attach")
            self.setMinimumWidth(340)
            self._objs = [first, second]

            self.move_box   = QtWidgets.QComboBox()
            self.move_box.addItems([_describe(o) for o in self._objs])
            self.child_box  = QtWidgets.QComboBox()
            self.parent_box = QtWidgets.QComboBox()
            self.onto_label = QtWidgets.QLabel()
            self.gap        = QtWidgets.QDoubleSpinBox()
            self.gap.setRange(-1000.0, 1000.0)
            self.gap.setSuffix(" mm")
            self.spin       = QtWidgets.QDoubleSpinBox()
            self.spin.setRange(-360.0, 360.0)
            self.spin.setSuffix(" °")
            self.weld       = QtWidgets.QCheckBox("Weld into one solid")

            form = QtWidgets.QFormLayout()
            form.addRow("Move:", self.move_box)
            form.addRow("Its point:", self.child_box)
            form.addRow(self.onto_label, self.parent_box)
            form.addRow("Gap:", self.gap)
            form.addRow("Rotate:", self.spin)
            form.addRow("", self.weld)

            buttons = QtWidgets.QDialogButtonBox(
                QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
            buttons.accepted.connect(self.accept)
            buttons.rejected.connect(self.reject)

            layout = QtWidgets.QVBoxLayout()
            layout.addLayout(form)
            layout.addWidget(buttons)
            self.setLayout(layout)

            self.move_box.currentIndexChanged.connect(self._refresh)
            self._refresh()

        def _pair(self):
            i = self.move_box.currentIndex()
            return self._objs[i], self._objs[1 - i]

        @staticmethod
        def _fill(box, obj, preferred):
            box.clear()
            names = anchor_names(obj)
            box.addItems(names)
            if preferred in names:
                box.setCurrentText(preferred)

        def _refresh(self):
            child, parent = self._pair()
            self._fill(self.child_box, child, "BOTTOM")
            self._fill(self.parent_box, parent, "TOP")
            self.onto_label.setText(f"Onto point of {_describe(parent)}:")

        def values(self):
            child, parent = self._pair()
            return dict(child_obj=child, parent_obj=parent,
                        child_anchor=self.child_box.currentText(),
                        parent_anchor=self.parent_box.currentText(),
                        offset=self.gap.value(), rotation_deg=self.spin.value(),
                        weld=self.weld.isChecked())

    def run_attach_command():
        """Entry point for the workbench's Partikus_Attach command."""
        main = FreeCADGui.getMainWindow()
        selected = FreeCADGui.Selection.getSelection()
        parts = [o for o in selected if is_partikus_object(o)]
        if len(selected) != 2 or len(parts) != 2:
            QtWidgets.QMessageBox.information(
                main, "Attach",
                "Select exactly two Partikus parts (Ctrl+click in the 3D view or the "
                f"tree), then choose Attach.\n\nSelected now: {len(selected)} object(s), "
                f"{len(parts)} of them Partikus parts.")
            return
        dlg = AttachDialog(parts[0], parts[1], main)
        if dlg.exec() != QtWidgets.QDialog.Accepted:
            return
        try:
            attach_objects(**dlg.values())
        except ValueError as e:
            QtWidgets.QMessageBox.warning(main, "Attach", str(e))
