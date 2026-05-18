"""
End-to-end AI pipeline integration tests.

Requires ANTHROPIC_API_KEY. Exits 1 immediately if the key is absent.

Usage:
    cd /opt/proj/partikus
    ANTHROPIC_API_KEY=sk-ant-... \\
        squashfs-root/usr/bin/freecadcmd tests/run_integration_tests.py
"""

import sys, os, time, traceback

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _ROOT)


def _say(msg):
    try:
        import FreeCAD
        FreeCAD.Console.PrintMessage(msg + "\n")
    except Exception:
        pass
    sys.stderr.write(msg + "\n")
    sys.stderr.flush()


def _check_key():
    key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    if not key:
        _say("ERROR: ANTHROPIC_API_KEY not set.")
        _say("  ANTHROPIC_API_KEY=sk-ant-... squashfs-root/usr/bin/freecadcmd tests/run_integration_tests.py")
        sys.exit(1)
    _say(f"  key: {'*' * 10}{key[-4:]}")


def _run(name, fn):
    t0 = time.time()
    try:
        fn()
        _say(f"  PASS  {name}  ({time.time() - t0:.1f}s)")
        return True
    except Exception as e:
        _say(f"  FAIL  {name}  ({time.time() - t0:.1f}s): {e}")
        _say(traceback.format_exc())
        return False


# ── Test functions ─────────────────────────────────────────────────────────────

def test_analyze_text_box():
    from partikus.ai import analyze_text
    result = analyze_text("a simple rectangular box 80mm x 50mm x 30mm")
    assert "shapes" in result and len(result["shapes"]) >= 1, \
        f"Expected at least one shape, got: {result}"
    fns = [s["function"] for s in result["shapes"]]
    assert any("box" in fn for fn in fns), f"Expected box function, got: {fns}"


def test_analyze_text_cylinder():
    from partikus.ai import analyze_text
    result = analyze_text("a solid cylinder 30mm diameter, 50mm tall")
    assert "shapes" in result and len(result["shapes"]) >= 1
    fns = [s["function"] for s in result["shapes"]]
    assert any("cylinder" in fn for fn in fns), f"Expected cylinder, got: {fns}"


def test_generate_script_syntax():
    from partikus.ai import generate_script
    from partikus.ai.generator import validate_syntax
    script = generate_script("a cylinder with diameter 30mm and height 50mm")
    ok, err = validate_syntax(script)
    assert ok, f"SyntaxError in generated script: {err}\n\nScript:\n{script}"
    assert "cylinder" in script, "Expected 'cylinder' in script"


def test_script_runs_cube():
    from partikus.ai import generate_script, run_script
    script = generate_script("a 40mm cube")
    out, err, rc = run_script(script)
    assert rc == 0, f"Script failed (rc={rc}):\nstderr: {err}\nscript:\n{script}"


def test_analyze_multipart_assembly():
    from partikus.ai import analyze_text
    result = analyze_text(
        "a cylinder mounted on top of a square base: "
        "base is 60mm x 60mm x 10mm, cylinder is 30mm diameter 40mm tall"
    )
    assert len(result["shapes"]) >= 2, \
        f"Expected >=2 shapes for two-part assembly, got: {result['shapes']}"
    assert len(result.get("assembly", [])) >= 1, \
        "Expected at least one assembly operation"


def test_generate_and_run_assembly():
    from partikus.ai import generate_script, run_script
    from partikus.ai.generator import validate_syntax
    script = generate_script(
        "a hollow box 80mm x 60mm x 40mm with 3mm walls and an open top"
    )
    ok, err = validate_syntax(script)
    assert ok, f"SyntaxError: {err}\nScript:\n{script}"
    out, stderr, rc = run_script(script)
    assert rc == 0, f"Assembly script failed (rc={rc}):\n{stderr}\nscript:\n{script}"


def test_generate_with_step_export():
    import tempfile
    from partikus.ai import generate_script, run_script
    from partikus.ai.generator import validate_syntax, ScriptGenerator
    from partikus.ai.analyzer import _validate_analysis
    from partikus.ai import analyze_text

    analysis = analyze_text("a solid sphere diameter 25mm")
    with tempfile.NamedTemporaryFile(suffix=".step", delete=False) as f:
        path = f.name
    try:
        gen = ScriptGenerator()
        script = gen.generate(analysis, export_step=path)
        ok, err = validate_syntax(script)
        assert ok, f"SyntaxError: {err}"
        out, stderr, rc = run_script(script)
        assert rc == 0, f"Script failed (rc={rc}):\n{stderr}\nscript:\n{script}"
        assert os.path.exists(path) and os.path.getsize(path) > 0, \
            f"STEP file not created at {path}"
    finally:
        try:
            os.unlink(path)
        except Exception:
            pass


# ── Runner ────────────────────────────────────────────────────────────────────

_TESTS = [
    ("analyze_text_box",           test_analyze_text_box),
    ("analyze_text_cylinder",      test_analyze_text_cylinder),
    ("generate_script_syntax",     test_generate_script_syntax),
    ("script_runs_cube",           test_script_runs_cube),
    ("analyze_multipart_assembly", test_analyze_multipart_assembly),
    ("generate_and_run_assembly",  test_generate_and_run_assembly),
    ("generate_with_step_export",  test_generate_with_step_export),
]


def main():
    _say("\n=== Partikus AI Integration Tests ===")
    _check_key()
    _say("")

    passed = failed = 0
    for name, fn in _TESTS:
        if _run(name, fn):
            passed += 1
        else:
            failed += 1

    _say(f"\n{'=' * 44}")
    _say(f"  {passed} passed  |  {failed} failed")
    _say("")
    sys.exit(1 if failed else 0)


main()
