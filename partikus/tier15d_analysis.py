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


def analyze_zebra(surface, stripe_count=8, camera_direction=(0, 0, 1), sample_grid=8):
    """
    Numerical zebra-stripe reflection analysis.

    Samples the surface on a grid, reflects a virtual stripe environment off
    each normal, and returns per-sample stripe IDs. Stripe-ID discontinuities
    between adjacent samples indicate C0 or G1 breaks.

    Args:
        surface:          PartikusShape wrapping a Part.Face (BSplineSurface)
        stripe_count:     number of alternating black/white stripes in the virtual
                          environment (higher = finer resolution)
        camera_direction: (x, y, z) unit vector representing the view direction
        sample_grid:      samples per axis (total = sample_grid²)

    Returns:
        dict with keys:
          stripe_ids      — list of (u_frac, v_frac, stripe_id, normal) per sample
          stripe_count    — stripe count used
          continuity_hint — "likely_G1" if no stripe ID jumps > 1 between neighbours,
                            "possible_G0" otherwise
          sample_count    — total samples

    Example:
        surf = surface_from_points(my_grid)
        z    = analyze_zebra(surf, stripe_count=10)
        print(z["continuity_hint"])
    """
    face = _unwrap_shape(surface)
    if not hasattr(face, "Surface"):
        raise TypeError("surface must wrap a Part.Face with an underlying BSplineSurface")

    bss     = face.Surface
    u0, u1, v0, v1 = face.ParameterRange
    n       = max(2, sample_grid)
    cam     = FreeCAD.Vector(*camera_direction)
    cam_len = math.sqrt(cam.x**2 + cam.y**2 + cam.z**2)
    if cam_len < 1e-10:
        raise ValueError("camera_direction must be a non-zero vector")
    cam = FreeCAD.Vector(cam.x / cam_len, cam.y / cam_len, cam.z / cam_len)

    samples = []
    for i in range(n):
        u_frac = i / (n - 1)
        u      = u0 + (u1 - u0) * u_frac
        for j in range(n):
            v_frac = j / (n - 1)
            v      = v0 + (v1 - v0) * v_frac
            try:
                normal = face.normalAt(u, v)
                # Reflect camera direction off the normal: R = D - 2(D·N)N
                dn     = cam.x * normal.x + cam.y * normal.y + cam.z * normal.z
                rx     = cam.x - 2 * dn * normal.x
                ry     = cam.y - 2 * dn * normal.y
                rz     = cam.z - 2 * dn * normal.z
                # Map reflected Z to a stripe ID (alternating black/white)
                angle  = math.atan2(math.sqrt(rx**2 + ry**2), rz)
                stripe = int(angle / math.pi * stripe_count) % stripe_count
                samples.append((u_frac, v_frac, stripe,
                                 (normal.x, normal.y, normal.z)))
            except Exception:
                pass

    # Heuristic continuity check: large stripe jumps between neighbours suggest G0
    continuity = "likely_G1"
    grid = {}
    for i_s, (uf, vf, sid, _) in enumerate(samples):
        ii = round(uf * (n - 1))
        jj = round(vf * (n - 1))
        grid[(ii, jj)] = sid

    for ii in range(n):
        for jj in range(n):
            sid = grid.get((ii, jj))
            for di, dj in ((1, 0), (0, 1)):
                nbr = grid.get((ii + di, jj + dj))
                if sid is not None and nbr is not None:
                    jump = abs(sid - nbr)
                    # Wrap-around jump
                    jump = min(jump, stripe_count - jump)
                    if jump > 1:
                        continuity = "possible_G0"

    return {
        "stripe_ids":      samples,
        "stripe_count":    stripe_count,
        "continuity_hint": continuity,
        "sample_count":    len(samples),
    }


def analyze_reflection(surface, environment_map=None, camera_direction=(0, 0, 1),
                       sample_grid=8):
    """
    Numerical reflection analysis — samples the surface and returns the
    reflected camera direction at each point.

    Useful for detecting surface tangency issues without a rendering pipeline:
    smooth reflection vectors indicate a G1 surface; discontinuous vectors
    indicate a G0 (positional-only) join.

    Args:
        surface:          PartikusShape wrapping a Part.Face
        environment_map:  reserved for future rendering pipeline support
        camera_direction: (x, y, z) incident view direction
        sample_grid:      samples per axis

    Returns:
        dict with keys:
          samples         — list of (u_frac, v_frac, (rx, ry, rz), (nx, ny, nz))
          mean_divergence — mean angular deviation between adjacent reflected vectors (rad)
          continuity_hint — "likely_G1" if mean_divergence < 0.1 rad, else "possible_G0"
          sample_count

    Example:
        surf = surface_from_points(my_grid)
        r    = analyze_reflection(surf)
        print(r["continuity_hint"])
    """
    face = _unwrap_shape(surface)
    if not hasattr(face, "Surface"):
        raise TypeError("surface must wrap a Part.Face with an underlying BSplineSurface")

    bss     = face.Surface
    u0, u1, v0, v1 = face.ParameterRange
    n       = max(2, sample_grid)
    cam     = FreeCAD.Vector(*camera_direction)
    cam_len = math.sqrt(cam.x**2 + cam.y**2 + cam.z**2)
    if cam_len < 1e-10:
        raise ValueError("camera_direction must be non-zero")
    cam = FreeCAD.Vector(cam.x / cam_len, cam.y / cam_len, cam.z / cam_len)

    samples = []
    grid    = {}
    for i in range(n):
        u_frac = i / (n - 1)
        u      = u0 + (u1 - u0) * u_frac
        for j in range(n):
            v_frac = j / (n - 1)
            v      = v0 + (v1 - v0) * v_frac
            try:
                normal = face.normalAt(u, v)
                dn     = cam.x * normal.x + cam.y * normal.y + cam.z * normal.z
                refl   = (cam.x - 2*dn*normal.x,
                           cam.y - 2*dn*normal.y,
                           cam.z - 2*dn*normal.z)
                entry  = (u_frac, v_frac, refl, (normal.x, normal.y, normal.z))
                samples.append(entry)
                grid[(i, j)] = refl
            except Exception:
                pass

    # Mean divergence between adjacent reflected vectors
    divergences = []
    for i in range(n):
        for j in range(n):
            r = grid.get((i, j))
            if r is None:
                continue
            for di, dj in ((1, 0), (0, 1)):
                nbr = grid.get((i + di, j + dj))
                if nbr is None:
                    continue
                dot = sum(r[c] * nbr[c] for c in range(3))
                dot = max(-1.0, min(1.0, dot))
                divergences.append(math.acos(dot))

    mean_div    = sum(divergences) / len(divergences) if divergences else 0.0
    continuity  = "likely_G1" if mean_div < 0.1 else "possible_G0"

    return {
        "samples":          samples,
        "mean_divergence":  mean_div,
        "continuity_hint":  continuity,
        "sample_count":     len(samples),
    }


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
