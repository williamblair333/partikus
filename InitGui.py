# Partikus — FreeCAD add-on loader, GUI half.
#
# DO NOT RENAME OR DELETE. FreeCAD executes the file literally named InitGui.py
# at the root of each Mod directory during GUI startup; that call is the only
# thing that ever runs partikus/gui/workbench.py, which is what puts "Partikus"
# in the workbench dropdown. Without this file the add-on loads and registers
# nothing, with no error anywhere. See Init.py for the console half.
#
# Run ./install.sh to create this file and symlink the repo into FreeCAD's user
# Mod directory (App.getUserAppDataDir()/Mod/partikus).

import os
import sys

_root = os.path.dirname(os.path.realpath(__file__))

# FreeCAD already puts each Mod entry on sys.path before running this file, so
# this is a fallback for unusual load paths. Append rather than insert: the repo
# root also contains tests/, examples/ and docs/, and putting it first would let
# those shadow same-named top-level modules for every other add-on in the process.
if _root not in sys.path:
    sys.path.append(_root)

import partikus.gui.workbench  # noqa: F401,E402  — registers the workbench
