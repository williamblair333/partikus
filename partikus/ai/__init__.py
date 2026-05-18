"""
Partikus AI integration — image-to-script pipeline.

High-level usage::

    from partikus.ai import generate_script, run_script

    # From an image
    script = generate_script("photo.jpg", hint="a DIN rail bracket")

    # From a text description (no image needed)
    script = generate_script("a hex bolt M8 × 30mm")
    print(script)

    # Run it via freecadcmd
    out, err, rc = run_script(script)

Low-level usage::

    from partikus.ai import ImageAnalyzer, ScriptGenerator

    analysis = ImageAnalyzer().analyze("photo.jpg")
    script   = ScriptGenerator().generate(analysis, export_step="out.step")

Requires:
    ANTHROPIC_API_KEY environment variable with a valid Anthropic API key.
"""

from .pipeline  import analyze_image, analyze_text, generate_script, run_script
from .analyzer  import ImageAnalyzer
from .generator import ScriptGenerator, validate_syntax

__all__ = [
    "analyze_image",
    "analyze_text",
    "generate_script",
    "run_script",
    "ImageAnalyzer",
    "ScriptGenerator",
    "validate_syntax",
]
