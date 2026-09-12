"""
Auto-generated Qt dialog from function signatures.

Requires a FreeCAD GUI session.  Qt comes in through FreeCAD's own `PySide`
shim rather than PySide2 or PySide6 directly: the shim forwards to whichever
binding the running FreeCAD was built against (PySide6 on FreeCAD 1.x), so this
module keeps working across the Qt5 -> Qt6 change.
"""

import inspect
from typing import get_type_hints, Literal, get_args, get_origin

try:
    from PySide import QtWidgets, QtCore
    import FreeCAD
    import FreeCADGui
    HAS_GUI = True
except ImportError as _e:
    # Say so. A silent HAS_GUI = False here imports cleanly, registers nothing,
    # and is indistinguishable from "Partikus is not installed" — which is how
    # a stale `from PySide2 import ...` went unnoticed through all of FreeCAD 1.x.
    HAS_GUI = False
    try:
        import FreeCAD as _FC
        _FC.Console.PrintWarning(
            f"Partikus: GUI dialogs disabled — {type(_e).__name__}: {_e}\n")
    except Exception:
        import sys as _sys
        _sys.stderr.write(f"Partikus: GUI dialogs disabled — {_e}\n")


def auto_dialog(fn):
    """
    Show a modal dialog for *fn* built from its signature.
    On accept, calls fn(**kwargs) and adds the result to the active document.

    Returns:
        The PartikusShape produced by fn, or None if the dialog was cancelled.
    """
    if not HAS_GUI:
        raise RuntimeError(
            "auto_dialog requires a FreeCAD GUI session — Qt (PySide) or "
            "FreeCADGui could not be imported; see the Report view for the reason")

    dlg = _build_dialog(fn)
    if dlg.exec() == QtWidgets.QDialog.Accepted:
        result = fn(**dlg.get_values())
        _add_to_doc(fn.__name__, result)
        return result
    return None


# ── Dialog builder ────────────────────────────────────────────────────────────

def _build_dialog(fn):
    sig = inspect.signature(fn)
    try:
        hints = get_type_hints(fn)
    except Exception:
        hints = {}

    dlg = QtWidgets.QDialog()
    dlg.setWindowTitle(_humanize(fn.__name__))
    dlg.setMinimumWidth(320)

    form = QtWidgets.QFormLayout()
    widgets = {}

    for name, param in sig.parameters.items():
        if name in ("self", "cls"):
            continue
        if param.kind in (inspect.Parameter.VAR_POSITIONAL,
                          inspect.Parameter.VAR_KEYWORD):
            continue

        annotation = hints.get(name)
        default    = param.default if param.default is not inspect.Parameter.empty else None
        widget     = _make_widget(annotation, default)
        form.addRow(_humanize(name) + ":", widget)
        widgets[name] = widget

    buttons = QtWidgets.QDialogButtonBox(
        QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel
    )
    buttons.accepted.connect(dlg.accept)
    buttons.rejected.connect(dlg.reject)

    layout = QtWidgets.QVBoxLayout()
    layout.addLayout(form)
    layout.addWidget(buttons)
    dlg.setLayout(layout)

    def get_values():
        out = {}
        for name, w in widgets.items():
            if isinstance(w, QtWidgets.QDoubleSpinBox):
                out[name] = w.value()
            elif isinstance(w, QtWidgets.QSpinBox):
                out[name] = w.value()
            elif isinstance(w, QtWidgets.QCheckBox):
                out[name] = w.isChecked()
            elif isinstance(w, QtWidgets.QComboBox):
                out[name] = w.currentText()
            else:
                out[name] = w.text()
        return out

    dlg.get_values = get_values
    return dlg


def _make_widget(annotation, default):
    # Literal["a", "b"] → QComboBox
    if annotation is not None and get_origin(annotation) is Literal:
        choices = list(get_args(annotation))
        w = QtWidgets.QComboBox()
        for c in choices:
            w.addItem(str(c))
        if default is not None:
            idx = next((i for i, c in enumerate(choices) if str(c) == str(default)), 0)
            w.setCurrentIndex(idx)
        return w

    # str → QComboBox for face anchors, QLineEdit otherwise.
    #
    # Without this branch a string parameter fell through to the QDoubleSpinBox
    # below and get_values() returned 0.0 for it, so every command carrying one
    # (open_face, hinge_side, battery_type, connector_type, model, ...) died
    # inside the geometry call with an unrelated-looking error.
    #
    # The face list is a heuristic and only covers the four anchor parameters.
    # The real fix is a Literal[...] annotation on each constrained string
    # parameter, which the branch above already turns into a validated combo
    # box; 28 exported functions still need one. Until then those get free text.
    if annotation is str or isinstance(default, str):
        faces = ["TOP", "BOTTOM", "FRONT", "BACK", "LEFT", "RIGHT"]
        if default in faces:
            w = QtWidgets.QComboBox()
            w.addItems(faces)
            w.setCurrentIndex(faces.index(default))
            return w
        w = QtWidgets.QLineEdit()
        w.setText(str(default) if default is not None else "")
        return w

    # bool → QCheckBox
    if annotation is bool or (default is not None and isinstance(default, bool)):
        w = QtWidgets.QCheckBox()
        if default is not None:
            w.setChecked(bool(default))
        return w

    # int → QSpinBox
    if annotation is int or (
        default is not None
        and isinstance(default, int)
        and not isinstance(default, bool)
    ):
        w = QtWidgets.QSpinBox()
        w.setRange(-100_000, 100_000)
        if default is not None:
            w.setValue(int(default))
        return w

    # Default: float → QDoubleSpinBox (mm)
    w = QtWidgets.QDoubleSpinBox()
    w.setRange(-100_000.0, 100_000.0)
    w.setDecimals(3)
    w.setSuffix(" mm")
    w.setSingleStep(0.5)
    if default is not None and isinstance(default, (int, float)):
        w.setValue(float(default))
    return w


def _humanize(name):
    return name.replace("_", " ").title()


def _add_to_doc(label, partikus_shape):
    from ..core.serialise import save_to_doc
    doc = FreeCAD.ActiveDocument
    if doc is None:
        doc = FreeCAD.newDocument("Partikus")
    save_to_doc(partikus_shape, label, doc)
    try:
        FreeCADGui.SendMsgToActiveView("ViewFit")
    except Exception:
        pass
