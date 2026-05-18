"""
Tier 3 — 2D Profiles.

All functions return a closed Part.Wire in the XY plane (Z=0), centered at origin,
ready for use with extrude(), revolve(), sweep(), and loft().

For revolve around Z: position profiles in the XZ plane (Y=0) using polyline().
"""

import math
import FreeCAD
import Part


def _V(x, y, z=0.0):
    return FreeCAD.Vector(x, y, z)


def _close(pts):
    """Append first point to close a polygon."""
    return list(pts) + [pts[0]]


# ── Rectangle ─────────────────────────────────────────────────────────────────

def rectangle(length=10.0, width=10.0):
    """
    Closed rectangular wire centered at origin in the XY plane.

    Args:
        length: extent along X (mm)
        width:  extent along Y (mm)

    Example:
        extrude(rectangle(30, 20), height=10)
    """
    hl, hw = length / 2, width / 2
    pts = [_V(-hl, -hw), _V(hl, -hw), _V(hl, hw), _V(-hl, hw)]
    return Part.makePolygon(_close(pts))


def rounded_rectangle(length=10.0, width=10.0, fillet_radius=1.0):
    """
    Rectangle with quarter-circle corners.

    Args:
        length:        extent along X (mm)
        width:         extent along Y (mm)
        fillet_radius: corner radius (mm)

    Example:
        extrude(rounded_rectangle(30, 20, fillet_radius=3), height=8)
    """
    r = fillet_radius
    hl, hw = length / 2, width / 2
    if r * 2 > min(length, width):
        raise ValueError("fillet_radius too large for the given dimensions")

    def _arc(cx, cy, start_deg, end_deg):
        mid_deg = (start_deg + end_deg) / 2
        p0 = _V(cx + r * math.cos(math.radians(start_deg)),
                cy + r * math.sin(math.radians(start_deg)))
        pm = _V(cx + r * math.cos(math.radians(mid_deg)),
                cy + r * math.sin(math.radians(mid_deg)))
        p1 = _V(cx + r * math.cos(math.radians(end_deg)),
                cy + r * math.sin(math.radians(end_deg)))
        return Part.Arc(p0, pm, p1).toShape()

    def _seg(x0, y0, x1, y1):
        return Part.LineSegment(_V(x0, y0), _V(x1, y1)).toShape()

    edges = [
        _seg(-hl + r, -hw, hl - r, -hw),           # bottom
        _arc(hl - r, -hw + r, 270, 360),            # bottom-right corner
        _seg(hl, -hw + r, hl, hw - r),              # right
        _arc(hl - r, hw - r, 0, 90),               # top-right corner
        _seg(hl - r, hw, -hl + r, hw),             # top
        _arc(-hl + r, hw - r, 90, 180),            # top-left corner
        _seg(-hl, hw - r, -hl, -hw + r),           # left
        _arc(-hl + r, -hw + r, 180, 270),          # bottom-left corner
    ]
    return Part.Wire(edges)


def chamfered_rectangle(length=10.0, width=10.0, chamfer_size=1.0):
    """
    Rectangle with 45° corner cuts.

    Args:
        length:       extent along X (mm)
        width:        extent along Y (mm)
        chamfer_size: corner cut length (mm)

    Example:
        extrude(chamfered_rectangle(20, 15, chamfer_size=2), height=5)
    """
    c = chamfer_size
    hl, hw = length / 2, width / 2
    pts = [
        _V(-hl + c, -hw), _V(hl - c, -hw),
        _V(hl, -hw + c),  _V(hl, hw - c),
        _V(hl - c, hw),   _V(-hl + c, hw),
        _V(-hl, hw - c),  _V(-hl, -hw + c),
    ]
    return Part.makePolygon(_close(pts))


# ── Circle / Ellipse ──────────────────────────────────────────────────────────

def circle(diameter=10.0, *, radius=None):
    """
    Full-circle wire centered at origin.

    Args:
        diameter: diameter (mm)
        radius:   overrides diameter

    Example:
        extrude(circle(20), height=5)
    """
    r = radius if radius is not None else diameter / 2
    return Part.Wire([Part.makeCircle(r)])


def ellipse(major_diameter=20.0, minor_diameter=10.0):
    """
    Full-ellipse wire centered at origin. Major axis along X.

    Args:
        major_diameter: diameter along X (mm)
        minor_diameter: diameter along Y (mm)

    Example:
        extrude(ellipse(30, 15), height=8)
    """
    e = Part.Ellipse(FreeCAD.Vector(0, 0, 0), major_diameter / 2, minor_diameter / 2)
    return Part.Wire([e.toShape()])


# ── Polygon / Star ────────────────────────────────────────────────────────────

def regular_polygon(sides=6, diameter=10.0):
    """
    Regular n-sided polygon, vertices on a circle of *diameter*. Flat-to-flat
    alignment: first vertex at angle 0 (right).

    Args:
        sides:    number of sides (>= 3)
        diameter: circumscribed circle diameter (mm)

    Example:
        extrude(regular_polygon(sides=6, diameter=10), height=5)
    """
    if sides < 3:
        raise ValueError("sides must be >= 3")
    r = diameter / 2
    pts = [_V(r * math.cos(2 * math.pi * i / sides),
              r * math.sin(2 * math.pi * i / sides)) for i in range(sides)]
    return Part.makePolygon(_close(pts))


def star(points=5, outer_diameter=10.0, inner_diameter=4.0):
    """
    Star polygon with alternating outer and inner vertices.

    Args:
        points:         number of star points
        outer_diameter: tip circle diameter (mm)
        inner_diameter: valley circle diameter (mm)

    Example:
        extrude(star(points=5, outer_diameter=20, inner_diameter=8), height=3)
    """
    R = outer_diameter / 2
    r = inner_diameter / 2
    pts = []
    for i in range(points):
        a_out = 2 * math.pi * i / points - math.pi / 2
        a_in  = a_out + math.pi / points
        pts.append(_V(R * math.cos(a_out), R * math.sin(a_out)))
        pts.append(_V(r * math.cos(a_in),  r * math.sin(a_in)))
    return Part.makePolygon(_close(pts))


# ── Slot / Teardrop ───────────────────────────────────────────────────────────

def slot(length=20.0, width=8.0):
    """
    Rounded-end slot (stadium shape) centered at origin. Runs along X.

    Args:
        length: total length along X (mm); must be >= width
        width:  total width / diameter of end caps (mm)

    Example:
        extrude(slot(25, 8), height=3)
    """
    if length < width:
        raise ValueError("slot length must be >= width")
    r = width / 2
    straight = (length - width) / 2  # half the straight portion

    def _semicircle(cx, start_deg, end_deg):
        mid_deg = (start_deg + end_deg) / 2
        p0 = _V(cx + r * math.cos(math.radians(start_deg)),
                     r * math.sin(math.radians(start_deg)))
        pm = _V(cx + r * math.cos(math.radians(mid_deg)),
                     r * math.sin(math.radians(mid_deg)))
        p1 = _V(cx + r * math.cos(math.radians(end_deg)),
                     r * math.sin(math.radians(end_deg)))
        return Part.Arc(p0, pm, p1).toShape()

    if straight < 1e-6:
        # Length == width → pure circle
        return circle(width)

    edges = [
        Part.LineSegment(_V(-straight, -r), _V(straight, -r)).toShape(),
        _semicircle(straight, 270, 90),
        Part.LineSegment(_V(straight, r), _V(-straight, r)).toShape(),
        _semicircle(-straight, 90, 270),
    ]
    return Part.Wire(edges)


def teardrop(diameter=10.0, angle=45.0):
    """
    Teardrop profile for 3D-printable horizontal holes.
    Circle with a pointed top to prevent overhangs.

    Args:
        diameter: circle diameter at the base (mm)
        angle:    half-angle of the point from vertical (default 45°)

    Example:
        extrude(teardrop(8, angle=45), height=10)
    """
    r = diameter / 2
    a = math.radians(angle)
    # The point is at (0, r/cos(a)) from centre — straight above.
    # Two straight lines from the tangent points on the circle to the apex.
    # Tangent points: where the straight lines meet the circle at angle 'a'.
    # x_t = r * sin(a),  y_t = r * cos(a)  (mirror on both sides)
    xt = r * math.sin(a)
    yt = r * math.cos(a)
    apex_y = r / math.cos(a)

    # Arc from right tangent to left tangent, going around the bottom.
    # Start angle: 90° - angle (from X axis), going CCW to 90° + angle
    start_deg = 90 - math.degrees(a)
    end_deg   = 90 + math.degrees(a)
    # The arc goes from left tangent point, all the way around the bottom, to right tangent point.
    # Arc: from end_deg, going clockwise (negative direction) to start_deg + 360
    # Easier: arc from start_deg to start_deg - (360 - (end_deg - start_deg))
    arc_start = start_deg
    arc_end   = start_deg - (360 - (end_deg - start_deg))
    mid_deg   = (arc_start + arc_end) / 2

    p_right_tang = _V( xt, yt)
    p_left_tang  = _V(-xt, yt)
    p_mid_arc    = _V(r * math.cos(math.radians(mid_deg)),
                      r * math.sin(math.radians(mid_deg)))
    p_apex       = _V(0, apex_y)

    arc_edge = Part.Arc(p_right_tang, p_mid_arc, p_left_tang).toShape()
    line_l   = Part.LineSegment(p_left_tang, p_apex).toShape()
    line_r   = Part.LineSegment(p_apex, p_right_tang).toShape()
    return Part.Wire([arc_edge, line_l, line_r])


# ── Arc / Polyline ────────────────────────────────────────────────────────────

def arc(radius=5.0, start_angle_deg=0.0, end_angle_deg=180.0):
    """
    Open arc wire centered at origin in the XY plane.

    Args:
        radius:         arc radius (mm)
        start_angle_deg: start angle from +X axis
        end_angle_deg:   end angle from +X axis

    Example:
        arc(radius=10, start_angle_deg=0, end_angle_deg=180)
    """
    edge = Part.makeCircle(radius, _V(0, 0, 0), _V(0, 0, 1),
                           start_angle_deg, end_angle_deg)
    return Part.Wire([edge])


def polyline(points, closed=False):
    """
    Wire from an ordered list of 2D or 3D points.

    Args:
        points: list of (x, y) or (x, y, z) tuples
        closed: if True, connect last point back to first

    Example:
        # L-shaped bracket cross-section
        polyline([(0,0),(10,0),(10,3),(3,3),(3,10),(0,10)], closed=True)
    """
    verts = [_V(*p) if len(p) == 3 else _V(p[0], p[1]) for p in points]
    if closed:
        verts = verts + [verts[0]]
    return Part.makePolygon(verts)
