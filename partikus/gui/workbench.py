"""
FreeCAD Workbench registration for Partikus — Tiers 1-8.

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
    from .. import (
        tier01_primitives          as _t01,
        tier02_enhanced            as _t02,
        tier03_profiles_2d         as _t03,
        tier04_mechanical          as _t04,
        tier05_fasteners           as _t05,
        tier06_mechanical_components as _t06,
        tier07_enclosures          as _t07,
        tier08_electronics         as _t08,
    )

    # ── Command factory ───────────────────────────────────────────────────────

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

    # ── Tier command tables ───────────────────────────────────────────────────

    _T1 = [
        ("Partikus_Box",             _t01.box),
        ("Partikus_Cylinder",        _t01.cylinder),
        ("Partikus_Sphere",          _t01.sphere),
        ("Partikus_Cone",            _t01.cone),
        ("Partikus_Torus",           _t01.torus),
        ("Partikus_Wedge",           _t01.wedge),
        ("Partikus_Pyramid",         _t01.pyramid),
        ("Partikus_Disk",            _t01.disk),
        ("Partikus_Polyhedron",      _t01.polyhedron),
    ]

    _T2 = [
        ("Partikus_RoundedBox",      _t02.rounded_box),
        ("Partikus_ChamferedBox",    _t02.chamfered_box),
        ("Partikus_RoundedCylinder", _t02.rounded_cylinder),
        ("Partikus_Tube",            _t02.tube),
        ("Partikus_TubeByWall",      _t02.tube_by_wall),
        ("Partikus_HollowBox",       _t02.hollow_box),
        ("Partikus_Hemisphere",      _t02.hemisphere),
        ("Partikus_SphericalCap",    _t02.spherical_cap),
        ("Partikus_Frustum",         _t02.frustum),
        ("Partikus_Prism",           _t02.prism),
        ("Partikus_RoundedPrism",    _t02.rounded_prism),
        ("Partikus_SteppedCylinder", _t02.stepped_cylinder),
    ]

    _T3 = [
        ("Partikus_Rectangle",           _t03.rectangle),
        ("Partikus_RoundedRectangle",    _t03.rounded_rectangle),
        ("Partikus_ChamferedRectangle",  _t03.chamfered_rectangle),
        ("Partikus_Circle",              _t03.circle),
        ("Partikus_Ellipse",             _t03.ellipse),
        ("Partikus_RegularPolygon",      _t03.regular_polygon),
        ("Partikus_Star",                _t03.star),
        ("Partikus_Slot",                _t03.slot),
        ("Partikus_Teardrop",            _t03.teardrop),
        ("Partikus_Arc",                 _t03.arc),
        ("Partikus_Polyline",            _t03.polyline),
    ]

    _T4 = [
        ("Partikus_Boss",            _t04.boss),
        ("Partikus_CounterboreHole", _t04.counterbore_hole),
        ("Partikus_CountersinkHole", _t04.countersink_hole),
        ("Partikus_SlotHole",        _t04.slot_hole),
        ("Partikus_Keyway",          _t04.keyway),
        ("Partikus_Rib",             _t04.rib),
        ("Partikus_Gusset",          _t04.gusset),
        ("Partikus_Flange",          _t04.flange),
        ("Partikus_Lip",             _t04.lip),
        ("Partikus_LBracket",        _t04.l_bracket),
        ("Partikus_TBracket",        _t04.t_bracket),
        ("Partikus_UBracket",        _t04.u_bracket),
        ("Partikus_Tab",             _t04.tab),
        ("Partikus_SlotCutout",      _t04.slot_cutout),
        ("Partikus_DovetailPin",     _t04.dovetail_pin),
        ("Partikus_DovetailSlot",    _t04.dovetail_slot),
        ("Partikus_Tongue",          _t04.tongue),
        ("Partikus_Groove",          _t04.groove),
        ("Partikus_LivingHinge",     _t04.living_hinge),
        ("Partikus_SnapClip",        _t04.snap_clip),
    ]

    _T5 = [
        ("Partikus_ThreadedRod",         _t05.threaded_rod),
        ("Partikus_TappedHole",          _t05.tapped_hole),
        ("Partikus_HexBolt",             _t05.hex_bolt),
        ("Partikus_SocketHeadBolt",      _t05.socket_head_bolt),
        ("Partikus_ButtonHeadBolt",      _t05.button_head_bolt),
        ("Partikus_FlatHeadBolt",        _t05.flat_head_bolt),
        ("Partikus_HexNut",              _t05.hex_nut),
        ("Partikus_FlatWasher",          _t05.flat_washer),
        ("Partikus_LockWasher",          _t05.lock_washer),
        ("Partikus_HeatSetInsertPocket", _t05.heat_set_insert_pocket),
        ("Partikus_ClearanceHole",       _t05.clearance_hole),
        ("Partikus_Standoff",            _t05.standoff),
        ("Partikus_DowelPin",            _t05.dowel_pin),
    ]

    _T6 = [
        ("Partikus_SpurGear",      _t06.spur_gear),
        ("Partikus_BevelGear",     _t06.bevel_gear),
        ("Partikus_Rack",          _t06.rack),
        ("Partikus_PulleyTiming",  _t06.pulley_timing),
        ("Partikus_Sprocket",      _t06.sprocket),
        ("Partikus_BearingPocket", _t06.bearing_pocket),
        ("Partikus_ShaftCoupling", _t06.shaft_coupling),
    ]

    _T7 = [
        ("Partikus_Lid",                _t07.lid),
        ("Partikus_SnapFitBox",         _t07.snap_fit_box),
        ("Partikus_HingedBox",          _t07.hinged_box),
        ("Partikus_MagneticRecess",     _t07.magnetic_recess),
        ("Partikus_BatteryCompartment", _t07.battery_compartment),
        ("Partikus_CableChannel",       _t07.cable_channel),
        ("Partikus_StrainRelief",       _t07.strain_relief),
        ("Partikus_VentSlots",          _t07.vent_slots),
        ("Partikus_DisplayWindow",      _t07.display_window),
        ("Partikus_ButtonCutout",       _t07.button_cutout),
    ]

    _T8 = [
        ("Partikus_PcbStandoff",       _t08.pcb_standoff),
        ("Partikus_RaspberryPiMount",  _t08.raspberry_pi_mount),
        ("Partikus_ArduinoMount",      _t08.arduino_mount),
        ("Partikus_LedHolder",         _t08.led_holder),
        ("Partikus_UsbCutout",         _t08.usb_cutout),
        ("Partikus_HdmiCutout",        _t08.hdmi_cutout),
        ("Partikus_BarrelJackCutout",  _t08.barrel_jack_cutout),
        ("Partikus_DinRailClip",       _t08.din_rail_clip),
        ("Partikus_HeatsinkFinArray",  _t08.heatsink_fin_array),
    ]

    _ALL_TIERS = [_T1, _T2, _T3, _T4, _T5, _T6, _T7, _T8]

    for _tier in _ALL_TIERS:
        for _name, _fn in _tier:
            _register(_name, _fn)

    # ── Workbench ─────────────────────────────────────────────────────────────

    class PartikusWorkbench(FreeCADGui.Workbench):
        MenuText = "Partikus"
        ToolTip  = "Parametric CAD toolkit — Every part has its place."
        Icon     = ""

        def Initialize(self):
            def _names(tier): return [n for n, _ in tier]

            # One toolbar per tier (user can show/hide individually)
            self.appendToolbar("Partikus — Primitives",  _names(_T1))
            self.appendToolbar("Partikus — Enhanced",    _names(_T2))
            self.appendToolbar("Partikus — Profiles 2D", _names(_T3))
            self.appendToolbar("Partikus — Mechanical",  _names(_T4))
            self.appendToolbar("Partikus — Fasteners",   _names(_T5))
            self.appendToolbar("Partikus — Components",  _names(_T6))
            self.appendToolbar("Partikus — Enclosures",  _names(_T7))
            self.appendToolbar("Partikus — Electronics", _names(_T8))

            # Menu tree under &Partikus
            base = ["&Partikus"]
            self.appendMenu(base + ["Primitives"],  _names(_T1))
            self.appendMenu(base + ["Enhanced"],    _names(_T2))
            self.appendMenu(base + ["Profiles 2D"], _names(_T3))
            self.appendMenu(base + ["Mechanical"],  _names(_T4))
            self.appendMenu(base + ["Fasteners"],   _names(_T5))
            self.appendMenu(base + ["Components"],  _names(_T6))
            self.appendMenu(base + ["Enclosures"],  _names(_T7))
            self.appendMenu(base + ["Electronics"], _names(_T8))

        def Activated(self):
            FreeCAD.Console.PrintMessage("Partikus workbench activated.\n")

        def Deactivated(self):
            pass

        def GetClassName(self):
            return "Gui::PythonWorkbench"

    FreeCADGui.addWorkbench(PartikusWorkbench())
