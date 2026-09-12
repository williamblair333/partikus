"""
Tests for the FreeCAD add-on loaders, Init.py and InitGui.py.

These two files are the only thing standing between a working install and a
workbench that is silently absent from the dropdown, and nothing else in the
suite touches them. They are also the one place in the project whose execution
environment is not a normal Python import: FreeCAD compiles each loader and
execs it in a fresh namespace during startup, and that namespace **has no
`__file__`**. A loader written like an ordinary module — `os.path.dirname(
os.path.realpath(__file__))` is the usual first line — raises NameError before
it reaches its first import, and all the user sees is one line of startup log
that scrolls past:

    During initialization the error "name '__file__' is not defined"
    occurred in .../Mod/partikus/InitGui.py

Every assertion here exists because that failure is invisible from inside
FreeCAD and from every other test in this suite.

The real `partikus.gui.workbench` cannot be imported under freecadcmd —
FreeCADGui exists there but is a stub without `addCommand`, so registration
raises. It is stubbed out; what is under test is the loader, not the workbench.
"""
import os
import sys
import types

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _ROOT)


def _loader_source(name):
    with open(os.path.join(_ROOT, name)) as fh:
        return fh.read()


def _exec_like_freecad(name):
    """
    Run a loader the way FreeCAD's add-on startup does: compiled, exec'd in a
    fresh namespace with no __file__ bound, with the workbench import stubbed.

    Returns the namespace. Raises whatever the loader raises.
    """
    saved = {k: sys.modules.get(k) for k in
             ("partikus", "partikus.gui", "partikus.gui.workbench")}
    try:
        pkg = types.ModuleType("partikus")
        pkg.__path__ = []
        gui = types.ModuleType("partikus.gui")
        gui.__path__ = []
        wb = types.ModuleType("partikus.gui.workbench")
        pkg.gui = gui
        gui.workbench = wb
        sys.modules["partikus"] = pkg
        sys.modules["partikus.gui"] = gui
        sys.modules["partikus.gui.workbench"] = wb

        path = os.path.join(_ROOT, name)
        # No "__file__" key — this is the whole point of the test.
        ns = {"__name__": "__main__", "__builtins__": __builtins__}
        exec(compile(_loader_source(name), path, "exec"), ns)
        return ns
    finally:
        for k, v in saved.items():
            if v is None:
                sys.modules.pop(k, None)
            else:
                sys.modules[k] = v


# ── The loaders exist at all ─────────────────────────────────────────────────

def test_both_loaders_exist_at_the_repo_root():
    # FreeCAD looks for these exact filenames at the root of each Mod entry and
    # skips the directory in silence when they are missing.
    for name in ("Init.py", "InitGui.py"):
        assert os.path.isfile(os.path.join(_ROOT, name)), f"{name} is missing"


# ── They survive FreeCAD's execution environment ─────────────────────────────

def test_init_runs_without_a_file_global():
    _exec_like_freecad("Init.py")


def test_initgui_runs_without_a_file_global():
    # The regression: any __file__ reference here raises NameError under FreeCAD
    # and the workbench never registers.
    _exec_like_freecad("InitGui.py")


def test_neither_loader_references_dunder_file():
    # Belt and braces: the exec test above only catches a reference on a line
    # that actually runs. This catches one parked inside a function or branch.
    for name in ("Init.py", "InitGui.py"):
        src = _loader_source(name)
        code = "\n".join(line for line in src.splitlines()
                         if not line.lstrip().startswith("#"))
        assert "__file__" not in code, (
            f"{name} references __file__, which FreeCAD does not define when it "
            f"execs the loader — the workbench will not register")


# ── InitGui does the one thing it is for ─────────────────────────────────────

def test_initgui_imports_the_workbench():
    # If this import ever goes away, the add-on loads and registers nothing —
    # exactly the state the dropdown showed before 2026-09-12.
    src = _loader_source("InitGui.py")
    assert "partikus.gui.workbench" in src


def test_initgui_does_not_touch_sys_path():
    # FreeCAD puts each Mod entry on sys.path before running the loader, so this
    # is unnecessary; doing it needs __file__, which is what broke registration.
    # The repo root also holds tests/ and examples/, which would shadow those
    # top-level names for every other add-on in the process.
    src = _loader_source("InitGui.py")
    code = "\n".join(line for line in src.splitlines()
                     if not line.lstrip().startswith("#"))
    assert "sys.path" not in code, "InitGui.py should not manipulate sys.path"
