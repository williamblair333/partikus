"""
High-level pipeline functions: image → Partikus script (→ optional run).

These are the entry points for the AI integration. For finer control,
use ImageAnalyzer and ScriptGenerator directly.
"""

import os
import subprocess
import sys
import tempfile

from .analyzer import ImageAnalyzer
from .generator import ScriptGenerator, validate_syntax


def analyze_image(image_path, hint="", model="claude-sonnet-4-6"):
    """
    Analyze an image and return a structured shape-decomposition dict.

    Args:
        image_path: path to image (JPEG/PNG/GIF/WEBP)
        hint:       optional text hint (e.g. "a DIN rail mounting bracket")
        model:      Claude model to use (default claude-sonnet-4-6)

    Returns:
        dict with keys: description, shapes, assembly, final,
                        estimated_dimensions_mm

    Requires:
        ANTHROPIC_API_KEY environment variable
    """
    return ImageAnalyzer(model=model).analyze(image_path, hint=hint)


def analyze_text(description, hint="", model="claude-sonnet-4-6"):
    """
    Decompose a text description into a shape-decomposition dict (no image).

    Useful for testing or quick prototyping without a photo.

    Args:
        description: text description of the object
        hint:        optional additional hint
        model:       Claude model to use

    Returns:
        same dict structure as analyze_image()

    Requires:
        ANTHROPIC_API_KEY environment variable
    """
    return ImageAnalyzer(model=model).analyze_text(description, hint=hint)


def generate_script(
    source,
    hint="",
    model="claude-sonnet-4-6",
    export_step=None,
    export_stl=None,
):
    """
    Analyze *source* (image path or text description) and return a Partikus script.

    If *source* is a path to an existing image file, it is analyzed with vision.
    Otherwise it is treated as a text description.

    Args:
        source:      image path or text description of the object
        hint:        optional text hint
        model:       Claude model to use
        export_step: if given, append to_step() export to the script
        export_stl:  if given, append to_stl() export to the script

    Returns:
        str — a complete, runnable Partikus Python script

    Requires:
        ANTHROPIC_API_KEY environment variable
    """
    analyzer = ImageAnalyzer(model=model)
    if os.path.isfile(source):
        analysis = analyzer.analyze(source, hint=hint)
    else:
        analysis = analyzer.analyze_text(source, hint=hint)

    gen = ScriptGenerator()
    script = gen.generate(analysis, export_step=export_step, export_stl=export_stl)
    return script


def run_script(script, freecadcmd=None, timeout=120):
    """
    Execute a Partikus script via freecadcmd and return (stdout, stderr, returncode).

    Args:
        script:      Python source code string (from generate_script)
        freecadcmd:  path to freecadcmd; auto-detected if None
        timeout:     maximum execution time in seconds (default 120)

    Returns:
        (stdout: str, stderr: str, returncode: int)

    Example::

        script = generate_script("a hex bolt M8×30")
        out, err, rc = run_script(script)
        if rc == 0:
            print("Success")
    """
    if freecadcmd is None:
        freecadcmd = _find_freecadcmd()

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".py", prefix="partikus_ai_", delete=False
    ) as f:
        f.write(script)
        tmp_path = f.name

    try:
        proc = subprocess.run(
            [freecadcmd, tmp_path],
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return proc.stdout, proc.stderr, proc.returncode
    except subprocess.TimeoutExpired:
        return "", "Script execution timed out", 1
    finally:
        os.unlink(tmp_path)


def _find_freecadcmd():
    """Locate freecadcmd relative to the project root or on PATH."""
    # Check relative path (project convention)
    project_root = os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    )
    candidate = os.path.join(project_root, "squashfs-root", "usr", "bin", "freecadcmd")
    if os.path.exists(candidate):
        return candidate

    # Fall back to PATH
    import shutil
    cmd = shutil.which("freecadcmd")
    if cmd:
        return cmd

    raise RuntimeError(
        "freecadcmd not found. Pass freecadcmd= explicitly or ensure it is on PATH."
    )
