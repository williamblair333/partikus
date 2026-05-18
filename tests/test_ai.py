"""
Tests for partikus.ai — AI integration module.

Most tests use mock data so they run without an ANTHROPIC_API_KEY.
Integration tests (test_integration_*) are skipped when the key is absent.
"""
import sys, os, json, tempfile
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from partikus.ai.generator import ScriptGenerator, validate_syntax, _safe_id, _format_params
from partikus.ai.analyzer  import _extract_json, _validate_analysis, ImageAnalyzer

# ── Helpers ────────────────────────────────────────────────────────────────────

def _make_analysis(description="a box", shapes=None, assembly=None, final="body"):
    return {
        "description": description,
        "shapes": shapes or [
            {"id": "body", "function": "box", "params": {"length": 80, "width": 50, "height": 30}}
        ],
        "assembly": assembly or [],
        "final": final,
        "estimated_dimensions_mm": {"x": 80, "y": 50, "z": 30},
    }


# ── _safe_id ───────────────────────────────────────────────────────────────────

def test_safe_id_normal():
    assert _safe_id("body") == "body"

def test_safe_id_hyphen():
    assert _safe_id("top-cap") == "top_cap"

def test_safe_id_space():
    assert _safe_id("main body") == "main_body"

def test_safe_id_leading_digit():
    s = _safe_id("1part")
    assert s[0] == "_"
    assert "1" in s

def test_safe_id_empty():
    assert _safe_id("") == "shape"


# ── _format_params ─────────────────────────────────────────────────────────────

def test_format_params_int():
    assert "length=80" in _format_params({"length": 80})

def test_format_params_float():
    s = _format_params({"diameter": 10.5})
    assert "10.5" in s

def test_format_params_string():
    s = _format_params({"fit": "close"})
    assert "'close'" in s or '"close"' in s

def test_format_params_tuple():
    s = _format_params({"axis": [0, 0, 1]})
    assert "0" in s and "1" in s

def test_format_params_empty():
    assert _format_params({}) == ""


# ── ScriptGenerator ────────────────────────────────────────────────────────────

def test_generate_single_shape():
    script = ScriptGenerator().generate(_make_analysis())
    assert "box(" in script
    assert "length=80" in script

def test_generate_imports_function():
    analysis = _make_analysis(shapes=[
        {"id": "c", "function": "cylinder", "params": {"diameter": 20, "height": 40}}
    ], final="c")
    script = ScriptGenerator().generate(analysis)
    assert "cylinder" in script

def test_generate_valid_python():
    script = ScriptGenerator().generate(_make_analysis())
    ok, err = validate_syntax(script)
    assert ok, f"SyntaxError: {err}"

def test_generate_with_assembly():
    analysis = _make_analysis(
        shapes=[
            {"id": "body", "function": "box", "params": {"length": 80, "width": 50, "height": 30}},
            {"id": "cap",  "function": "box", "params": {"length": 80, "width": 50, "height": 5}},
        ],
        assembly=[
            {"result": "asm", "op": "stack_on", "args": ["cap", "body"], "params": {}}
        ],
        final="asm",
    )
    script = ScriptGenerator().generate(analysis)
    assert "stack_on" in script
    ok, err = validate_syntax(script)
    assert ok, err

def test_generate_with_export_step():
    script = ScriptGenerator().generate(
        _make_analysis(), export_step="/tmp/out.step"
    )
    assert "to_step" in script
    assert "/tmp/out.step" in script
    ok, _ = validate_syntax(script)
    assert ok

def test_generate_with_export_stl():
    script = ScriptGenerator().generate(
        _make_analysis(), export_stl="/tmp/out.stl"
    )
    assert "to_stl" in script
    ok, _ = validate_syntax(script)
    assert ok

def test_generate_contains_description():
    analysis = _make_analysis(description="a hex bolt M8")
    script = ScriptGenerator().generate(analysis)
    assert "hex bolt M8" in script

def test_generate_contains_final():
    analysis = _make_analysis(final="body")
    script = ScriptGenerator().generate(analysis)
    assert "result = body" in script

def test_generate_with_note():
    analysis = _make_analysis(shapes=[
        {"id": "b", "function": "box", "params": {"length": 10, "width": 10, "height": 10}, "note": "main body"}
    ], final="b")
    script = ScriptGenerator().generate(analysis)
    assert "main body" in script

def test_generate_boolean_op():
    analysis = _make_analysis(
        shapes=[
            {"id": "outer", "function": "box", "params": {"length": 40, "width": 40, "height": 40}},
            {"id": "inner", "function": "box", "params": {"length": 36, "width": 36, "height": 36}},
        ],
        assembly=[
            {"result": "shell_box", "op": "difference", "args": ["outer", "inner"], "params": {}}
        ],
        final="shell_box",
    )
    script = ScriptGenerator().generate(analysis)
    assert "difference" in script
    ok, err = validate_syntax(script)
    assert ok, err

def test_generate_complex_assembly():
    analysis = _make_analysis(
        description="flanged cylinder",
        shapes=[
            {"id": "shaft",  "function": "cylinder", "params": {"diameter": 20, "height": 60}},
            {"id": "flange", "function": "cylinder", "params": {"diameter": 40, "height": 8}},
            {"id": "bore",   "function": "cylinder", "params": {"diameter": 16, "height": 62}},
        ],
        assembly=[
            {"result": "body",   "op": "stack_on",   "args": ["shaft", "flange"],  "params": {}},
            {"result": "result", "op": "difference",  "args": ["body", "bore"],    "params": {}},
        ],
        final="result",
    )
    script = ScriptGenerator().generate(analysis)
    ok, err = validate_syntax(script)
    assert ok, err
    assert "cylinder" in script
    assert "difference" in script


# ── validate_syntax ────────────────────────────────────────────────────────────

def test_validate_syntax_good():
    ok, err = validate_syntax("x = 1 + 2\n")
    assert ok
    assert err is None

def test_validate_syntax_bad():
    ok, err = validate_syntax("x = (1 +\n")
    assert not ok
    assert err is not None


# ── _extract_json ──────────────────────────────────────────────────────────────

_SAMPLE_ANALYSIS = {
    "description": "a simple box",
    "shapes": [{"id": "body", "function": "box", "params": {"length": 50}}],
    "assembly": [],
    "final": "body",
    "estimated_dimensions_mm": {"x": 50, "y": 30, "z": 20},
}

def test_extract_json_bare():
    text = json.dumps(_SAMPLE_ANALYSIS)
    result = _extract_json(text)
    assert result["description"] == "a simple box"

def test_extract_json_fenced():
    text = "Here is the JSON:\n```json\n" + json.dumps(_SAMPLE_ANALYSIS) + "\n```"
    result = _extract_json(text)
    assert result["final"] == "body"

def test_extract_json_with_preamble():
    text = "Sure! Here you go: " + json.dumps(_SAMPLE_ANALYSIS) + " Hope that helps!"
    result = _extract_json(text)
    assert result["shapes"][0]["function"] == "box"

def test_extract_json_no_json():
    try:
        _extract_json("There is no JSON here at all.")
        assert False, "Expected ValueError"
    except ValueError:
        pass


# ── _validate_analysis ────────────────────────────────────────────────────────

def test_validate_analysis_good():
    d = _make_analysis()
    _validate_analysis(d)  # should not raise

def test_validate_analysis_missing_description():
    d = _make_analysis()
    del d["description"]
    try:
        _validate_analysis(d)
        assert False
    except ValueError:
        pass

def test_validate_analysis_missing_shapes():
    d = _make_analysis()
    del d["shapes"]
    try:
        _validate_analysis(d)
        assert False
    except ValueError:
        pass

def test_validate_analysis_empty_shapes():
    d = _make_analysis()
    d["shapes"] = []
    try:
        _validate_analysis(d)
        assert False
    except ValueError:
        pass

def test_validate_analysis_shape_missing_id():
    d = _make_analysis()
    del d["shapes"][0]["id"]
    try:
        _validate_analysis(d)
        assert False
    except ValueError:
        pass

def test_validate_analysis_sets_defaults():
    d = _make_analysis()
    del d["assembly"]
    _validate_analysis(d)
    assert "assembly" in d  # default set


# ── Integration tests (skip without API key) ───────────────────────────────────

def _has_api_key():
    return bool(os.environ.get("ANTHROPIC_API_KEY"))

def test_integration_analyze_text_box():
    if not _has_api_key():
        return  # skip
    from partikus.ai import analyze_text
    result = analyze_text("a simple rectangular box 80mm × 50mm × 30mm")
    assert "shapes" in result
    assert len(result["shapes"]) >= 1
    # Should identify box as the primary shape
    fns = [s["function"] for s in result["shapes"]]
    assert any("box" in fn for fn in fns)

def test_integration_generate_script_text():
    if not _has_api_key():
        return  # skip
    from partikus.ai import generate_script
    script = generate_script("a cylinder with diameter 30mm and height 50mm")
    ok, err = validate_syntax(script)
    assert ok, err
    assert "cylinder" in script

def test_integration_script_runs():
    if not _has_api_key():
        return  # skip
    from partikus.ai import generate_script, run_script
    script = generate_script("a 40mm cube")
    out, err, rc = run_script(script)
    assert rc == 0, f"Script failed:\n{err}"
