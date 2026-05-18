"""
Tier 15D — Continuity & Quality Analysis.

analyze_curvature, analyze_draft, and analyze_deviation are implemented.
analyze_zebra and analyze_reflection are stubbed (require rendering pipeline).
"""

import math
import FreeCAD
import Part

from .core.shape_wrapper import PartikusShape


def _unwrap_shape(s):
    if isinstance(s, PartikusShape):
        return s.shape
    return s


def analyze_curvature(surface, mode="gaussian"):
    """
    Curvature analysis on a NURBS surface face, sampled at a 5×5 grid.

    Args:
        surface: PartikusShape wrapping a Part.Face (BSplineSurface)
        mode:    "gaussian" | "mean" | "max" | "min"

    Returns:
        dict with keys: mode, min, max, mean, sample_count

    Example:
        surf = surface_from_points(grid)
        info = analyze_curvature(surf, mode="mean")
        print(info["mean"])
    """
    _MODES = {"gaussian": None, "mean": "Mean", "max": "Max", "min": "Min"}
    if mode not in _MODES:
        raise ValueError(f"mode must be one of {sorted(_MODES)}, got '{mode}'")

    face = _unwrap_shape(surface)
    if not hasattr(face, 'Surface'):
        raise TypeError("surface must wrap a Part.Face with an underlying BSplineSurface")
    bss = face.Surface
    u0, u1, v0, v1 = face.ParameterRange

    samples = 5
    values = []
    for i in range(samples):
        u = u0 + (u1 - u0) * i / (samples - 1)
        for j in range(samples):
            v = v0 + (v1 - v0) * j / (samples - 1)
            try:
                if mode == "gaussian":
                    k_max = bss.curvature(u, v, "Max")
                    k_min = bss.curvature(u, v, "Min")
                    values.append(k_max * k_min)
                else:
                    values.append(bss.curvature(u, v, _MODES[mode]))
            except Exception:
                pass

    if not values:
        raise RuntimeError("Could not sample curvature — surface may not be a BSplineSurface")

    return {
        "mode": mode,
        "min": min(values),
        "max": max(values),
        "mean": sum(values) / len(values),
        "sample_count": len(values),
        "unit": "1/mm^2" if mode == "gaussian" else "1/mm",
    }


def analyze_zebra(surface):
    """
    Zebra-stripe reflection continuity analysis.
    (Requires a rendering pipeline — Milestone 6)
    """
    raise NotImplementedError("analyze_zebra — planned for Milestone 6")


def analyze_reflection(surface, environment_map=None):
    """
    Reflection map analysis. (Milestone 6)
    """
    raise NotImplementedError("analyze_reflection — planned for Milestone 6")


def analyze_draft(shape, pull_direction=(0, 0, 1)):
    """
    Moldability draft-angle analysis — compute the angle between each face
    normal and the pull direction.

    Args:
        shape:          PartikusShape or Part.Shape (Solid or Shell)
        pull_direction: (x, y, z) unit vector — mold pull direction

    Returns:
        dict with keys:
          faces        — list of {"area_mm2", "draft_angle_deg", "ok"} per face
          min_draft_deg  — smallest draft angle across all faces
          max_draft_deg  — largest draft angle
          mean_draft_deg — area-weighted mean draft angle

    Example:
        box_shape = box(40, 30, 20)
        info = analyze_draft(box_shape, pull_direction=(0, 0, 1))
        print(info["min_draft_deg"])
    """
    raw = _unwrap_shape(shape)
    pull = FreeCAD.Vector(*pull_direction)
    pull_len = math.sqrt(pull.x**2 + pull.y**2 + pull.z**2)
    if pull_len < 1e-10:
        raise ValueError("pull_direction must be a non-zero vector")
    pull = FreeCAD.Vector(pull.x / pull_len, pull.y / pull_len, pull.z / pull_len)

    face_results = []
    for face in raw.Faces:
        try:
            u0, u1, v0, v1 = face.ParameterRange
            normal = face.normalAt((u0 + u1) / 2, (v0 + v1) / 2)
            dot = abs(normal.dot(pull))
            dot = max(-1.0, min(1.0, dot))
            # draft angle = 90° - angle_between_normal_and_pull
            # (0° = face perpendicular to pull; 90° = face parallel to pull)
            angle_deg = 90.0 - math.degrees(math.acos(dot))
            face_results.append({
                "area_mm2": face.Area,
                "draft_angle_deg": angle_deg,
                "ok": angle_deg >= 0.5,  # 0.5° is a typical minimum draft
            })
        except Exception:
            pass

    if not face_results:
        raise RuntimeError("No faces could be analyzed")

    total_area = sum(r["area_mm2"] for r in face_results)
    weighted_mean = (
        sum(r["area_mm2"] * r["draft_angle_deg"] for r in face_results) / total_area
        if total_area > 0 else 0.0
    )

    return {
        "faces": face_results,
        "min_draft_deg": min(r["draft_angle_deg"] for r in face_results),
        "max_draft_deg": max(r["draft_angle_deg"] for r in face_results),
        "mean_draft_deg": weighted_mean,
    }


def analyze_deviation(surface, reference, sample_count=10):
    """
    Compare a surface to a reference shape by sampling points on the surface
    and computing the minimum distance to the reference.

    Args:
        surface:      PartikusShape wrapping a Part.Face (source surface)
        reference:    PartikusShape or Part.Shape (target / nominal geometry)
        sample_count: number of samples per axis (total = sample_count²)

    Returns:
        dict with keys: min_deviation, max_deviation, mean_deviation,
                        rms_deviation, sample_count (total points sampled)

    Example:
        info = analyze_deviation(rebuilt_surf, original_surf)
        print(info["max_deviation"])
    """
    face = _unwrap_shape(surface)
    ref = _unwrap_shape(reference)

    if not hasattr(face, 'Surface'):
        raise TypeError("surface must wrap a Part.Face")

    bss = face.Surface
    u0, u1, v0, v1 = face.ParameterRange
    n = max(2, sample_count)

    deviations = []
    for i in range(n):
        u = u0 + (u1 - u0) * i / (n - 1)
        for j in range(n):
            v = v0 + (v1 - v0) * j / (n - 1)
            try:
                pt = bss.value(u, v)
                vertex = Part.Vertex(pt)
                dist, _, _ = vertex.distToShape(ref)
                deviations.append(dist)
            except Exception:
                pass

    if not deviations:
        raise RuntimeError("Could not compute deviations — check surface/reference types")

    mean = sum(deviations) / len(deviations)
    rms = math.sqrt(sum(d**2 for d in deviations) / len(deviations))

    return {
        "min_deviation": min(deviations),
        "max_deviation": max(deviations),
        "mean_deviation": mean,
        "rms_deviation": rms,
        "sample_count": len(deviations),
    }
