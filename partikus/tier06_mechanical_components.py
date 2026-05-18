"""
Tier 6 — Mechanical Components.

spur_gear uses a true involute profile (polyline approximation, 16 pts/flank).
All other shapes use geometric approximations suitable for layout and clearance
checking. All shapes centred at origin. All dimensions in mm.
"""

import math
import FreeCAD
import Part

from .core.shape_wrapper import PartikusShape
from .core.anchors import CENTER, TOP, BOTTOM, FRONT, BACK, LEFT, RIGHT


def _V(x, y, z):
    return FreeCAD.Vector(x, y, z)


def _bb_result(fc_shape):
    bb = fc_shape.BoundBox
    cx = (bb.XMin + bb.XMax) / 2
    cy = (bb.YMin + bb.YMax) / 2
    cz = (bb.ZMin + bb.ZMax) / 2
    return PartikusShape(
        fc_shape,
        {
            CENTER: _V(cx, cy, cz),
            TOP:    _V(cx, cy, bb.ZMax),
            BOTTOM: _V(cx, cy, bb.ZMin),
            FRONT:  _V(cx, bb.YMax, cz),
            BACK:   _V(cx, bb.YMin, cz),
            RIGHT:  _V(bb.XMax, cy, cz),
            LEFT:   _V(bb.XMin, cy, cz),
        },
        {
            TOP:   _V(0, 0, 1), BOTTOM: _V(0, 0, -1),
            FRONT: _V(0, 1, 0), BACK:   _V(0, -1, 0),
            RIGHT: _V(1, 0, 0), LEFT:   _V(-1, 0, 0),
        },
    )


def _center(fc_shape):
    bb = fc_shape.BoundBox
    cx = (bb.XMin + bb.XMax) / 2
    cy = (bb.YMin + bb.YMax) / 2
    cz = (bb.ZMin + bb.ZMax) / 2
    m = FreeCAD.Matrix()
    m.move(_V(-cx, -cy, -cz))
    s = fc_shape.copy()
    s.transformShape(m)
    return s


# ── Involute spur gear ────────────────────────────────────────────────────────

def _involute_point(rb, t):
    return (rb * (math.cos(t) + t * math.sin(t)),
            rb * (math.sin(t) - t * math.cos(t)))


def _rotate2d(x, y, angle):
    c, s = math.cos(angle), math.sin(angle)
    return (c * x - s * y, s * x + c * y)


def _gear_profile_wire(teeth, module, pressure_angle_deg, n_pts=16):
    """
    Build a closed Part.Wire for a full spur gear profile in the XY plane.

    Uses a single Part.makePolygon call over all sampled points — no edge
    connectivity issues possible. Traversal order is CCW when viewed from +Z.

    Per-tooth sequence: left flank root→tip, tip arc interior, right flank
    tip→root, root arc interior. Left/right are relative to the tooth axis.
    """
    N = teeth
    m = module
    phi = math.radians(pressure_angle_deg)

    rp = m * N / 2           # pitch radius
    rb = rp * math.cos(phi)  # base radius
    ra = rp + m              # addendum (tip) radius
    rr = rp - 1.25 * m       # dedendum (root) radius

    # When root circle is inside base circle, approximate root as base circle.
    # The small undercut region is omitted (acceptable for cosmetic gears).
    rr_eff = max(rr, rb)

    t_tip   = math.sqrt(max((ra / rb) ** 2 - 1, 0))
    t_start = math.sqrt(max((rr_eff / rb) ** 2 - 1, 0))

    inv_phi    = math.tan(phi) - phi       # involute function at pressure angle
    tooth_half = math.pi / (2 * N)        # half tooth angular width at pitch circle
    rot_angle  = tooth_half - inv_phi     # rotate so tooth is centred at θ = 0

    # Right flank: n_pts points, index 0 = root, index -1 = tip
    right_base = []
    for i in range(n_pts):
        t = t_start + (t_tip - t_start) * i / (n_pts - 1)
        px, py = _involute_point(rb, t)
        right_base.append(_rotate2d(px, py, rot_angle))

    # Left flank: mirror of right in the tooth axis (y → −y), reversed so
    # index 0 = tip, index -1 = root (matches the CCW traversal order).
    left_base = [(x, -y) for x, y in reversed(right_base)]

    pitch_angle = 2 * math.pi / N
    n_arc = 6   # interior arc sample points per arc segment

    def rot_pts(pts, angle):
        c, s = math.cos(angle), math.sin(angle)
        return [(c * x - s * y, s * x + c * y) for x, y in pts]

    def ccw_end(a0, a1):
        """Return a1 adjusted so a1 > a0 (CCW / increasing-angle direction)."""
        while a1 <= a0:
            a1 += 2 * math.pi
        return a1

    all_pts = []

    for i in range(N):
        theta  = i * pitch_angle
        lf     = rot_pts(left_base, theta)            # [0]=tip, [-1]=root
        rf     = rot_pts(right_base, theta)           # [0]=root, [-1]=tip
        next_lf = rot_pts(left_base, theta + pitch_angle)

        # 1. Left flank: root (lf[-1]) → tip (lf[0])  — CCW, increasing radius
        for k in range(len(lf) - 1, -1, -1):
            all_pts.append(_V(lf[k][0], lf[k][1], 0))

        # 2. Tip arc interior: left tip → right tip, CCW short arc at ra
        a0 = math.atan2(lf[0][1], lf[0][0])
        a1 = ccw_end(a0, math.atan2(rf[-1][1], rf[-1][0]))
        for k in range(1, n_arc):
            a = a0 + (a1 - a0) * k / n_arc
            all_pts.append(_V(ra * math.cos(a), ra * math.sin(a), 0))

        # 3. Right flank: tip (rf[-1]) → root (rf[0])
        for k in range(len(rf) - 1, -1, -1):
            all_pts.append(_V(rf[k][0], rf[k][1], 0))

        # 4. Root arc interior: right root → next tooth's left root, CCW at rr_eff
        a0 = math.atan2(rf[0][1], rf[0][0])
        a1 = ccw_end(a0, math.atan2(next_lf[-1][1], next_lf[-1][0]))
        for k in range(1, n_arc):
            a = a0 + (a1 - a0) * k / n_arc
            all_pts.append(_V(rr_eff * math.cos(a), rr_eff * math.sin(a), 0))

    all_pts.append(all_pts[0])   # close
    return Part.makePolygon(all_pts)


def spur_gear(teeth=20, module=1.0, thickness=5.0, pressure_angle_deg=20):
    """
    Involute spur gear. Profile is a 16-point polyline approximation per flank
    (indistinguishable from exact at any practical module).

    Args:
        teeth:              number of teeth (>= 8 recommended)
        module:             gear module (mm) — pitch_diameter = module × teeth
        thickness:          gear face width / extrusion depth (mm)
        pressure_angle_deg: pressure angle (degrees); standard is 20

    Example:
        spur_gear(teeth=20, module=2, thickness=10)
    """
    if teeth < 5:
        raise ValueError("teeth must be >= 5")
    wire = _gear_profile_wire(teeth, module, pressure_angle_deg)
    face = Part.Face(wire)
    hh = thickness / 2
    raw = face.extrude(_V(0, 0, thickness))
    m = FreeCAD.Matrix()
    m.move(_V(0, 0, -hh))
    raw2 = raw.copy()
    raw2.transformShape(m)
    return _bb_result(raw2)


# ── Bevel gear (frustum approximation) ───────────────────────────────────────

def bevel_gear(teeth=20, module=1.0, cone_angle_deg=45, thickness=10.0):
    """
    Bevel gear: truncated-cone approximation at the pitch cone geometry.

    Full spherical-involute tooth geometry is not modelled. The frustum
    represents the correct overall envelope for clearance and layout.

    Args:
        teeth:          number of teeth
        module:         gear module (mm)
        cone_angle_deg: pitch-cone half-angle (degrees); 45° = miter gear
        thickness:      face width along the cone surface (mm)

    Example:
        bevel_gear(teeth=20, module=2, cone_angle_deg=45, thickness=10)
    """
    cone_rad = math.radians(cone_angle_deg)
    rp_large = module * teeth / 2                       # pitch radius at large end
    rp_small = rp_large - thickness * math.sin(cone_rad) # pitch radius at small end
    h = thickness * math.cos(cone_rad)

    hh = h / 2
    raw = Part.makeCone(max(rp_small, 0.01), rp_large, h, _V(0, 0, -hh))
    return _bb_result(raw)


# ── Rack ──────────────────────────────────────────────────────────────────────

def rack(teeth=10, module=1.0, length=None, height=None):
    """
    Gear rack: flat bar with trapezoidal teeth on top (20° pressure angle).

    Args:
        teeth:  number of teeth
        module: gear module (mm)
        length: total rack length (mm); default = teeth × π × module
        height: rack height below the pitch line (mm); default = 2 × module

    Example:
        rack(teeth=12, module=2)
    """
    cp = math.pi * module           # circular pitch
    addendum = module
    dedendum = 1.25 * module
    phi = math.radians(20)

    L = length if length is not None else teeth * cp
    H = height if height is not None else 2.5 * module  # full tooth height below datum

    hh_h = H / 2
    half_L = L / 2

    # Build the 2D profile of one tooth (trapezoidal, symmetric about x=0)
    # tooth at the datum line (y=0): half-width = cp/4 at datum, narrows toward tip
    tooth_hw_root = cp / 4 + dedendum * math.tan(phi)  # half-width at root
    tooth_hw_tip  = cp / 4 - addendum * math.tan(phi)  # half-width at tip

    tooth_hw_tip = max(tooth_hw_tip, 0.05 * module)    # avoid degenerate tip

    # Build rack body + teeth as a compound of box + N tooth prisms
    body = Part.makeBox(L, 1.0, H, _V(-half_L, -0.5, -H - addendum))

    # We'll use a 2D profile + extrude in Y to make a full rack solid
    # Profile in XZ plane at y=0, closed:
    # Bottom of rack at z = -(H + addendum), top of teeth at z = addendum
    # Build one period, then array
    tooth_shapes = []
    for i in range(teeth):
        cx = -half_L + cp / 2 + i * cp   # centre of this tooth
        pts_xz = [
            (cx - tooth_hw_root, -dedendum),
            (cx + tooth_hw_root, -dedendum),
            (cx + tooth_hw_tip,   addendum),
            (cx - tooth_hw_tip,   addendum),
            (cx - tooth_hw_root, -dedendum),
        ]
        pts = [_V(x, 0, z) for (x, z) in pts_xz]
        wire = Part.makePolygon(pts)
        face = Part.Face(wire)
        tooth_shapes.append(face.extrude(_V(0, 1.0, 0)))

    # Rack body (rectangular base) goes from z=-(H+addendum) to z=-dedendum
    base_h = H - dedendum
    if base_h > 0:
        base = Part.makeBox(L, 1.0, base_h,
                            _V(-half_L, -0.5, -(H + addendum)))
        all_shapes = [base] + tooth_shapes
    else:
        all_shapes = tooth_shapes

    raw = all_shapes[0]
    for s in all_shapes[1:]:
        raw = raw.fuse(s)

    return _bb_result(_center(raw))


# ── Timing pulley ─────────────────────────────────────────────────────────────

def pulley_timing(teeth=20, belt_type="GT2", width=7.0):
    """
    Timing pulley: smooth cylinder at the correct pitch diameter.

    Tooth profile geometry is not modelled (belt-type-specific tooling data
    varies by manufacturer). The OD is the pitch-circle diameter, which is
    the correct spatial envelope for assembly layout.

    Args:
        teeth:     number of teeth
        belt_type: "GT2" (2 mm pitch) or "HTD" (5 mm pitch)
        width:     pulley belt-contact width (mm)

    Example:
        pulley_timing(teeth=20, belt_type="GT2", width=7)
    """
    pitches = {"GT2": 2.0, "HTD": 5.0}
    if belt_type not in pitches:
        raise ValueError(f"belt_type must be 'GT2' or 'HTD'; got {belt_type!r}")
    belt_pitch = pitches[belt_type]
    pd = (teeth * belt_pitch) / math.pi   # pitch diameter
    hh = width / 2
    raw = Part.makeCylinder(pd / 2, width, _V(0, 0, -hh))
    return _bb_result(raw)


# ── Sprocket ──────────────────────────────────────────────────────────────────

def sprocket(teeth=16, chain_pitch=12.7, thickness=5.0):
    """
    Roller-chain sprocket: involute-like profile approximated as a spur gear
    at the correct pitch diameter for layout. Roller seats are not modelled.

    Args:
        teeth:       number of teeth
        chain_pitch: chain pitch (mm); e.g. 12.7 = #40 / #25 chain
        thickness:   sprocket thickness (mm)

    Example:
        sprocket(teeth=16, chain_pitch=12.7, thickness=6)
    """
    pd = (teeth * chain_pitch) / math.pi  # pitch diameter
    module = pd / teeth                    # equivalent module for profile shape
    # Use spur_gear profile — visually correct at this scale
    wire = _gear_profile_wire(teeth, module, pressure_angle_deg=25, n_pts=12)
    face = Part.Face(wire)
    hh = thickness / 2
    raw = face.extrude(_V(0, 0, thickness))
    m_mat = FreeCAD.Matrix()
    m_mat.move(_V(0, 0, -hh))
    raw2 = raw.copy()
    raw2.transformShape(m_mat)
    return _bb_result(raw2)


# ── Bearing pocket ────────────────────────────────────────────────────────────

def bearing_pocket(bearing_id="608", depth=None):
    """
    Cylindrical pocket to receive a standard ball bearing.

    Args:
        bearing_id: ISO bearing designation, e.g. "608", "6004"
        depth:      pocket depth (mm); defaults to bearing width

    Example:
        bearing_pocket("608")          # 8mm bore, 22mm OD, 7mm wide
        bearing_pocket("6004", depth=10)
    """
    from .presets.bearings import lookup_bearing
    dims = lookup_bearing(bearing_id)
    od = dims["od"]
    d = depth if depth is not None else dims["width"]
    hh = d / 2
    raw = Part.makeCylinder(od / 2, d, _V(0, 0, -hh))
    return _bb_result(raw)


# ── Shaft coupling ────────────────────────────────────────────────────────────

def shaft_coupling(shaft1_diameter=6.0, shaft2_diameter=6.0, length=25.0):
    """
    Rigid shaft coupling: cylindrical body sized to fit both shaft ends.

    The OD is 2.5× the larger shaft diameter (common rule of thumb).

    Args:
        shaft1_diameter: diameter of the first shaft (mm)
        shaft2_diameter: diameter of the second shaft (mm)
        length:          coupling total length (mm)

    Example:
        shaft_coupling(shaft1_diameter=6, shaft2_diameter=8, length=30)
    """
    od = 2.5 * max(shaft1_diameter, shaft2_diameter)
    hh = length / 2
    body = Part.makeCylinder(od / 2, length, _V(0, 0, -hh))

    # Bore each half for the respective shaft
    bore1 = Part.makeCylinder(shaft1_diameter / 2, length / 2 * 1.01,
                              _V(0, 0, -hh * 1.005))
    bore2 = Part.makeCylinder(shaft2_diameter / 2, length / 2 * 1.01,
                              _V(0, 0, 0))
    raw = body.cut(bore1).cut(bore2)
    return _bb_result(raw)
