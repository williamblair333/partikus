"""
ImageAnalyzer — decompose an image into Partikus shape descriptions.

Sends the image to Claude's vision API and returns a structured analysis dict
that can be consumed by ScriptGenerator.
"""

import base64
import json
import os
import re

from . import _http

_MEDIA_TYPES = {
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "png": "image/png",
    "gif": "image/gif",
    "webp": "image/webp",
}

_SYSTEM_PROMPT = """You are a parametric CAD decomposition assistant for the Partikus toolkit.

Analyze the image and decompose the visible object into Partikus Python API calls.

## Partikus function reference (dimensions in mm)

**Primitives**
box(length, width, height)
cylinder(diameter, height)
sphere(diameter)
cone(diameter, height, top_diameter=0)
torus(outer_diameter, inner_diameter)

**Enhanced primitives**
rounded_box(length, width, height, fillet_radius)
tube(diameter, height, wall_thickness)
hollow_box(length, width, height, wall_thickness)
hemisphere(diameter)

**Boolean**
union(a, b)          — fuse shapes
difference(a, b)     — subtract b from a
intersection(a, b)   — common volume

**Modifiers**
fillet(shape, fillet_radius)
chamfer(shape, chamfer_size)
shell(shape, wall_thickness)   — hollow a solid

**Assembly**
translate(shape, dx=0, dy=0, dz=0)
rotate(shape, angle_deg, axis=(0,0,1))
stack_on(child, parent)        — place child on top of parent
attach(child, parent, child_anchor, parent_anchor)
place_beside(child, parent, direction="right", gap=0)

## Output format

Return ONLY a JSON object matching this schema — no markdown, no prose:

{
  "description": "one-line description of the object",
  "shapes": [
    {
      "id": "python_variable_name",
      "function": "partikus_function",
      "params": {"param": value},
      "note": "optional comment"
    }
  ],
  "assembly": [
    {
      "result": "variable_name",
      "op": "stack_on|attach|translate|rotate|union|difference|intersection|fillet|chamfer|shell",
      "args": ["shape_id_or_result_id", ...],
      "params": {}
    }
  ],
  "final": "variable_name_of_the_assembled_result",
  "estimated_dimensions_mm": {"x": 0, "y": 0, "z": 0}
}

Rules:
- Use simple primitives. Prefer box/cylinder over complex shapes.
- Estimate dimensions from visual proportions. If a reference is visible use it.
- If no scale reference, assume the object fits in a 100×100×100 mm bounding box.
- Omit assembly steps if the object is a single primitive.
- Every id must be a valid Python identifier (snake_case).
- Only use functions listed above.
"""


def _extract_json(text):
    """Return the first JSON object found in text, trying several heuristics."""
    # Strip ```json ... ``` fences
    fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if fenced:
        return json.loads(fenced.group(1))

    # Find first { ... } block
    start = text.find("{")
    if start == -1:
        raise ValueError("No JSON object found in response")
    depth = 0
    for i, ch in enumerate(text[start:], start):
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return json.loads(text[start : i + 1])
    raise ValueError("Unterminated JSON object in response")


class ImageAnalyzer:
    """
    Analyze an image and return a shape-decomposition dict.

    Usage::

        analyzer = ImageAnalyzer()
        analysis = analyzer.analyze("photo.jpg")
        # analysis["shapes"], analysis["assembly"], analysis["final"]
    """

    def __init__(self, model="claude-sonnet-4-6"):
        self.model = model

    def analyze(self, image_path, hint=""):
        """
        Decompose the image at *image_path* into Partikus shapes.

        Args:
            image_path: path to JPEG, PNG, GIF, or WEBP image
            hint:       optional text hint about the object (e.g. "a M8 hex bolt")

        Returns:
            dict with keys: description, shapes, assembly, final,
                            estimated_dimensions_mm

        Raises:
            FileNotFoundError: image not found
            RuntimeError:      API error or unparseable response
        """
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image not found: {image_path}")

        ext = os.path.splitext(image_path)[1].lstrip(".").lower()
        media_type = _MEDIA_TYPES.get(ext, "image/jpeg")

        with open(image_path, "rb") as f:
            img_b64 = base64.b64encode(f.read()).decode("ascii")

        user_text = "Decompose this object into Partikus CAD primitives."
        if hint:
            user_text += f" Hint: {hint}"
        user_text += "\n\nReturn only the JSON object."

        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": media_type,
                            "data": img_b64,
                        },
                    },
                    {"type": "text", "text": user_text},
                ],
            }
        ]

        resp = _http.call(messages, system=_SYSTEM_PROMPT, model=self.model)
        raw_text = _http.text_from(resp)

        try:
            analysis = _extract_json(raw_text)
        except (ValueError, json.JSONDecodeError) as e:
            raise RuntimeError(
                f"Could not parse JSON from model response: {e}\n\nRaw response:\n{raw_text}"
            ) from e

        _validate_analysis(analysis)
        return analysis

    def analyze_text(self, description, hint=""):
        """
        Decompose a text description (no image) into Partikus shapes.

        Useful for testing or when only a description is available.

        Args:
            description: text description of the object
            hint:        optional additional hint

        Returns:
            same dict structure as analyze()
        """
        text = f"Decompose this into Partikus CAD primitives: {description}"
        if hint:
            text += f" Hint: {hint}"
        text += "\n\nReturn only the JSON object."

        messages = [{"role": "user", "content": text}]
        resp = _http.call(messages, system=_SYSTEM_PROMPT, model=self.model)
        raw_text = _http.text_from(resp)

        try:
            analysis = _extract_json(raw_text)
        except (ValueError, json.JSONDecodeError) as e:
            raise RuntimeError(
                f"Could not parse JSON from model response: {e}\n\nRaw response:\n{raw_text}"
            ) from e

        _validate_analysis(analysis)
        return analysis


def _validate_analysis(d):
    """Raise ValueError if required keys are missing or malformed."""
    for key in ("description", "shapes", "final"):
        if key not in d:
            raise ValueError(f"Analysis missing required key: {key!r}")
    if not isinstance(d["shapes"], list) or len(d["shapes"]) == 0:
        raise ValueError("Analysis 'shapes' must be a non-empty list")
    for s in d["shapes"]:
        for k in ("id", "function", "params"):
            if k not in s:
                raise ValueError(f"Shape entry missing key {k!r}: {s}")
    d.setdefault("assembly", [])
    d.setdefault("estimated_dimensions_mm", {})
