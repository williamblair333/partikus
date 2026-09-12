# Partikus — FreeCAD add-on loader, non-GUI half.
#
# DO NOT RENAME OR DELETE. FreeCAD scans every directory in its Mod path and
# executes the file literally named Init.py at the root of each one, in both
# console and GUI sessions. An add-on without it is skipped silently — no error,
# no entry in the workbench dropdown, nothing in the Report view.
#
# Nothing is needed here: the partikus package imports FreeCAD lazily and the
# headless API is used by importing it directly. The GUI half lives in
# InitGui.py beside this file. ./install.sh creates both and symlinks this
# directory into FreeCAD's user Mod directory.
