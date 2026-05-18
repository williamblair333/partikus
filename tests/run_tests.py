"""
Test runner for Partikus.

Usage:
    /path/to/squashfs-root/usr/bin/freecadcmd tests/run_tests.py

freecadcmd captures stdout, so we use FreeCAD.Console (which routes to stderr /
the terminal) and write a summary to stdout at the very end via sys.stderr.
"""
import sys
import os
import traceback
import importlib

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _ROOT)

_MODULES = [
    "tests.test_core",
    "tests.test_tier01",
    "tests.test_tier09",
    "tests.test_tier14",
    "tests.test_tier10",
    "tests.test_tier11",
    "tests.test_tier03",
    "tests.test_tier02",
    "tests.test_tier12",
    "tests.test_tier04",
    "tests.test_tier05",
    "tests.test_tier06",
    "tests.test_tier07",
    "tests.test_tier08",
    "tests.test_tier13",
    "tests.test_tier15",
    "tests.test_io",
    "tests.test_ai",
    "tests.test_serialise",
    "tests.test_subd",
]


def _say(msg):
    """Print via FreeCAD console (visible in terminal) and stderr."""
    try:
        import FreeCAD
        FreeCAD.Console.PrintMessage(msg + "\n")
    except Exception:
        pass
    sys.stderr.write(msg + "\n")
    sys.stderr.flush()


def _collect(module):
    return [(k, v) for k, v in vars(module).items()
            if k.startswith("test_") and callable(v)]


def main():
    passed = failed = 0
    errors = []

    for mod_name in _MODULES:
        try:
            mod = importlib.import_module(mod_name)
        except Exception as e:
            _say(f"\nERROR importing {mod_name}: {e}")
            _say(traceback.format_exc())
            failed += 1
            continue

        _say(f"\n{mod_name}")
        for name, fn in _collect(mod):
            full = f"{mod_name}.{name}"
            try:
                fn()
                _say(f"  PASS  {name}")
                passed += 1
            except Exception as e:
                _say(f"  FAIL  {name}: {e}")
                _say(traceback.format_exc())
                errors.append(full)
                failed += 1

    _say(f"\n{'=' * 60}")
    _say(f"  {passed} passed  |  {failed} failed")
    if errors:
        _say("\nFailed tests:")
        for e in errors:
            _say(f"  {e}")
    _say("")

    sys.exit(1 if failed else 0)


main()
