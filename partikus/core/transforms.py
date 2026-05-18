"""Rotation and placement utilities used throughout the toolkit."""
import math

import FreeCAD


def rotation_from_to(from_vec, to_vec):
    """
    Return a FreeCAD.Rotation that maps from_vec → to_vec (both treated as unit vectors).
    Handles parallel and anti-parallel cases.
    """
    a = FreeCAD.Vector(from_vec).normalize()
    b = FreeCAD.Vector(to_vec).normalize()
    dot = max(-1.0, min(1.0, a.dot(b)))

    if dot > 0.9999:
        return FreeCAD.Rotation()          # identity

    if dot < -0.9999:
        # 180-degree rotation — pick any perpendicular axis
        perp = FreeCAD.Vector(1, 0, 0)
        if abs(a.dot(perp)) > 0.9:
            perp = FreeCAD.Vector(0, 1, 0)
        axis = a.cross(perp).normalize()
        return FreeCAD.Rotation(axis, 180)

    axis = a.cross(b)
    angle = math.degrees(math.acos(dot))
    return FreeCAD.Rotation(axis, angle)


def placement_for_rotation(rotation, center):
    """
    Return a FreeCAD.Placement that rotates vectors around *center*.
    For a point P: new_P = center + rotation * (P - center).
    """
    r_center = rotation.multVec(center)
    base = FreeCAD.Vector(
        center.x - r_center.x,
        center.y - r_center.y,
        center.z - r_center.z,
    )
    return FreeCAD.Placement(base, rotation)
