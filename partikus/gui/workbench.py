"""
FreeCAD Workbench registration for Partikus.

Drop this file (or the entire partikus package) into FreeCAD's Mod directory,
or add the parent of the partikus/ package to sys.path in user.cfg / InitGui.py.

This module imports PySide2 and FreeCADGui — it is a no-op when loaded outside
a FreeCAD GUI session.
"""

try:
    import FreeCAD
    import FreeCADGui
    from PySide2 import QtGui
    _HAS_GUI = True
except ImportError:
    _HAS_GUI = False

if _HAS_GUI:
    from .auto_dialog import auto_dialog
    from .. import tier01_primitives as _t01
    from .. import tier09_boolean    as _t09

    # ── Command registry ──────────────────────────────────────────────────────

    _COMMANDS = []   # list of (command_name, fn) registered with FreeCADGui

    def _register(cmd_name, fn):
        """Create and register a one-shot dialog command for *fn*."""
        class _Cmd:
            def GetResources(self):
                return {
                    "MenuText": fn.__name__.replace("_", " ").title(),
                    "ToolTip":  (fn.__doc__ or "").strip().split("\n")[0],
                    "Pixmap":   "",
                }
            def Activated(self):
                auto_dialog(fn)
            def IsActive(self):
                return FreeCAD.ActiveDocument is not None

        FreeCADGui.addCommand(cmd_name, _Cmd())
        _COMMANDS.append(cmd_name)

    # Tier 1 primitives
    _T1 = [
        ("Partikus_Box",        _t01.box),
        ("Partikus_Cylinder",   _t01.cylinder),
        ("Partikus_Sphere",     _t01.sphere),
        ("Partikus_Cone",       _t01.cone),
        ("Partikus_Torus",      _t01.torus),
        ("Partikus_Wedge",      _t01.wedge),
        ("Partikus_Pyramid",    _t01.pyramid),
        ("Partikus_Disk",       _t01.disk),
    ]
    for _name, _fn in _T1:
        _register(_name, _fn)

    # ── Workbench ─────────────────────────────────────────────────────────────

    class PartikusWorkbench(FreeCADGui.Workbench):
        MenuText = "Partikus"
        ToolTip  = "Parametric CAD toolkit — Every part has its place."
        Icon     = ""

        def Initialize(self):
            t1_names = [n for n, _ in _T1]
            self.appendToolbar("Partikus Primitives", t1_names)
            self.appendMenu(["&Partikus", "Primitives"], t1_names)

        def Activated(self):
            FreeCAD.Console.PrintMessage("Partikus workbench activated.\n")

        def Deactivated(self):
            pass

        def GetClassName(self):
            return "Gui::PythonWorkbench"

    FreeCADGui.addWorkbench(PartikusWorkbench())
