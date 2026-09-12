# Partikus — FreeCAD add-on loader, GUI half.
#
# DO NOT RENAME OR DELETE. FreeCAD executes the file literally named InitGui.py
# at the root of each Mod directory during GUI startup; that call is the only
# thing that ever runs partikus/gui/workbench.py, which is what puts "Partikus"
# in the workbench dropdown. Without this file the add-on loads and registers
# nothing, with no error anywhere. See Init.py for the console half.
#
# KEEP THIS FILE TRIVIAL, AND DO NOT REFERENCE __file__ HERE.
#
# FreeCAD does not import this as a module — it compiles the source and execs it
# in a fresh namespace that has no __file__ bound. The usual add-on first line,
#
#     _root = os.path.dirname(os.path.realpath(__file__))
#
# therefore raises NameError before reaching the import below, and the only
# symptom is one line of startup log that scrolls past:
#
#     During initialization the error "name '__file__' is not defined"
#     occurred in .../Mod/partikus/InitGui.py
#
# The workbench is then simply missing from the dropdown, which looks exactly
# like "not installed". tests/test_gui_loader.py guards this.
#
# There is no sys.path setup either, and none is needed: FreeCAD puts every Mod
# entry on sys.path before running this file. Adding the repo root would also
# let tests/ and examples/ shadow those top-level names for every other add-on
# in the process.
#
# Run ./install.sh to symlink the repo into FreeCAD's user Mod directory.

import partikus.gui.workbench  # noqa: F401  — importing it registers the workbench
