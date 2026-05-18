"""
ISO metric screw dimension tables (coarse thread series).

Sources: ISO 261 (threads), ISO 4014 (hex bolts), ISO 4762 (socket head),
ISO 7380 (button head), ISO 10642 (flat head), ISO 4032 (hex nuts),
ISO 7089 (flat washers), ISO 7980 (lock washers), ISO 273 (clearance holes).
Heat-set insert dims approximate Ruthex/CJT standard for 3D printing.

Key    : nominal diameter in mm (int or float for M2.5)
pitch  : coarse-thread pitch (mm)
tap_drill: recommended tap drill diameter (mm), approx d - pitch
clearance: {'close','normal','loose'} hole diameters per ISO 273
heat_set : {'outer_diameter','length'} for 3D-printing heat-set inserts
"""

METRIC_COARSE = {
    2: {
        "pitch": 0.4,
        "tap_drill": 1.6,
        "hex_bolt":    {"across_flats": 4.0,  "head_height": 1.6},
        "socket_head": {"head_diameter": 3.8,  "head_height": 2.0},
        "button_head": None,
        "flat_head":   {"head_diameter": 4.7,  "head_angle": 90},
        "hex_nut":     {"across_flats": 4.0,  "height": 1.6},
        "flat_washer": {"inner_diameter": 2.2, "outer_diameter": 5.0,  "thickness": 0.3},
        "lock_washer": {"inner_diameter": 2.1, "outer_diameter": 4.4,  "thickness": 0.5},
        "clearance":   {"close": 2.2, "normal": 2.4, "loose": 2.6},
        "heat_set":    {"outer_diameter": 3.5, "length": 4.3},
    },
    2.5: {
        "pitch": 0.45,
        "tap_drill": 2.05,
        "hex_bolt":    {"across_flats": 5.0,  "head_height": 1.7},
        "socket_head": {"head_diameter": 4.5,  "head_height": 2.5},
        "button_head": None,
        "flat_head":   {"head_diameter": 5.6,  "head_angle": 90},
        "hex_nut":     {"across_flats": 5.0,  "height": 2.0},
        "flat_washer": {"inner_diameter": 2.7, "outer_diameter": 6.0,  "thickness": 0.5},
        "lock_washer": {"inner_diameter": 2.6, "outer_diameter": 5.1,  "thickness": 0.6},
        "clearance":   {"close": 2.7, "normal": 2.9, "loose": 3.1},
        "heat_set":    {"outer_diameter": 4.0, "length": 5.3},
    },
    3: {
        "pitch": 0.5,
        "tap_drill": 2.5,
        "hex_bolt":    {"across_flats": 5.5,  "head_height": 2.0},
        "socket_head": {"head_diameter": 5.5,  "head_height": 3.0},
        "button_head": {"head_diameter": 5.7,  "head_height": 1.65},
        "flat_head":   {"head_diameter": 6.72, "head_angle": 90},
        "hex_nut":     {"across_flats": 5.5,  "height": 2.4},
        "flat_washer": {"inner_diameter": 3.2, "outer_diameter": 7.0,  "thickness": 0.5},
        "lock_washer": {"inner_diameter": 3.1, "outer_diameter": 5.9,  "thickness": 0.9},
        "clearance":   {"close": 3.2, "normal": 3.4, "loose": 3.6},
        "heat_set":    {"outer_diameter": 4.5, "length": 5.7},
    },
    4: {
        "pitch": 0.7,
        "tap_drill": 3.3,
        "hex_bolt":    {"across_flats": 7.0,  "head_height": 2.8},
        "socket_head": {"head_diameter": 7.0,  "head_height": 4.0},
        "button_head": {"head_diameter": 7.6,  "head_height": 2.2},
        "flat_head":   {"head_diameter": 8.96, "head_angle": 90},
        "hex_nut":     {"across_flats": 7.0,  "height": 3.2},
        "flat_washer": {"inner_diameter": 4.3, "outer_diameter": 9.0,  "thickness": 0.8},
        "lock_washer": {"inner_diameter": 4.1, "outer_diameter": 7.6,  "thickness": 1.1},
        "clearance":   {"close": 4.3, "normal": 4.5, "loose": 4.8},
        "heat_set":    {"outer_diameter": 5.7, "length": 7.0},
    },
    5: {
        "pitch": 0.8,
        "tap_drill": 4.2,
        "hex_bolt":    {"across_flats": 8.0,  "head_height": 3.5},
        "socket_head": {"head_diameter": 8.5,  "head_height": 5.0},
        "button_head": {"head_diameter": 9.5,  "head_height": 2.75},
        "flat_head":   {"head_diameter": 11.2, "head_angle": 90},
        "hex_nut":     {"across_flats": 8.0,  "height": 4.0},
        "flat_washer": {"inner_diameter": 5.3, "outer_diameter": 10.0, "thickness": 1.0},
        "lock_washer": {"inner_diameter": 5.1, "outer_diameter": 9.2,  "thickness": 1.3},
        "clearance":   {"close": 5.3, "normal": 5.5, "loose": 5.8},
        "heat_set":    {"outer_diameter": 7.0, "length": 8.0},
    },
    6: {
        "pitch": 1.0,
        "tap_drill": 5.0,
        "hex_bolt":    {"across_flats": 10.0, "head_height": 4.0},
        "socket_head": {"head_diameter": 10.0, "head_height": 6.0},
        "button_head": {"head_diameter": 10.5, "head_height": 3.3},
        "flat_head":   {"head_diameter": 13.44,"head_angle": 90},
        "hex_nut":     {"across_flats": 10.0, "height": 5.0},
        "flat_washer": {"inner_diameter": 6.4, "outer_diameter": 12.0, "thickness": 1.6},
        "lock_washer": {"inner_diameter": 6.1, "outer_diameter": 11.0, "thickness": 1.6},
        "clearance":   {"close": 6.4, "normal": 6.6, "loose": 7.0},
        "heat_set":    {"outer_diameter": 9.0, "length": 10.0},
    },
    8: {
        "pitch": 1.25,
        "tap_drill": 6.75,
        "hex_bolt":    {"across_flats": 13.0, "head_height": 5.3},
        "socket_head": {"head_diameter": 13.0, "head_height": 8.0},
        "button_head": {"head_diameter": 14.0, "head_height": 4.4},
        "flat_head":   {"head_diameter": 17.92,"head_angle": 90},
        "hex_nut":     {"across_flats": 13.0, "height": 6.5},
        "flat_washer": {"inner_diameter": 8.4, "outer_diameter": 16.0, "thickness": 1.6},
        "lock_washer": {"inner_diameter": 8.1, "outer_diameter": 14.8, "thickness": 2.0},
        "clearance":   {"close": 8.4, "normal": 9.0, "loose": 10.0},
        "heat_set":    {"outer_diameter": 11.0, "length": 13.0},
    },
    10: {
        "pitch": 1.5,
        "tap_drill": 8.5,
        "hex_bolt":    {"across_flats": 16.0, "head_height": 6.4},
        "socket_head": {"head_diameter": 16.0, "head_height": 10.0},
        "button_head": {"head_diameter": 17.5, "head_height": 5.5},
        "flat_head":   {"head_diameter": 22.4, "head_angle": 90},
        "hex_nut":     {"across_flats": 16.0, "height": 8.0},
        "flat_washer": {"inner_diameter": 10.5,"outer_diameter": 20.0, "thickness": 2.0},
        "lock_washer": {"inner_diameter": 10.2,"outer_diameter": 18.1, "thickness": 2.5},
        "clearance":   {"close": 10.5, "normal": 11.0, "loose": 12.0},
        "heat_set":    {"outer_diameter": 14.0, "length": 16.0},
    },
    12: {
        "pitch": 1.75,
        "tap_drill": 10.2,
        "hex_bolt":    {"across_flats": 18.0, "head_height": 7.5},
        "socket_head": {"head_diameter": 18.0, "head_height": 12.0},
        "button_head": {"head_diameter": 21.0, "head_height": 6.6},
        "flat_head":   {"head_diameter": 26.88,"head_angle": 90},
        "hex_nut":     {"across_flats": 18.0, "height": 10.0},
        "flat_washer": {"inner_diameter": 13.0,"outer_diameter": 24.0, "thickness": 2.5},
        "lock_washer": {"inner_diameter": 12.2,"outer_diameter": 21.1, "thickness": 3.0},
        "clearance":   {"close": 13.0, "normal": 13.5, "loose": 14.5},
        "heat_set":    {"outer_diameter": 16.0, "length": 18.0},
    },
    16: {
        "pitch": 2.0,
        "tap_drill": 14.0,
        "hex_bolt":    {"across_flats": 24.0, "head_height": 10.0},
        "socket_head": {"head_diameter": 24.0, "head_height": 16.0},
        "button_head": None,
        "flat_head":   None,
        "hex_nut":     {"across_flats": 24.0, "height": 13.0},
        "flat_washer": {"inner_diameter": 17.0,"outer_diameter": 30.0, "thickness": 3.0},
        "lock_washer": {"inner_diameter": 16.2,"outer_diameter": 27.4, "thickness": 3.5},
        "clearance":   {"close": 17.0, "normal": 17.5, "loose": 18.5},
        "heat_set":    None,
    },
    20: {
        "pitch": 2.5,
        "tap_drill": 17.5,
        "hex_bolt":    {"across_flats": 30.0, "head_height": 12.5},
        "socket_head": {"head_diameter": 30.0, "head_height": 20.0},
        "button_head": None,
        "flat_head":   None,
        "hex_nut":     {"across_flats": 30.0, "height": 16.0},
        "flat_washer": {"inner_diameter": 21.0,"outer_diameter": 37.0, "thickness": 3.0},
        "lock_washer": {"inner_diameter": 20.2,"outer_diameter": 33.6, "thickness": 4.0},
        "clearance":   {"close": 21.0, "normal": 22.0, "loose": 24.0},
        "heat_set":    None,
    },
}


def _to_key(diameter):
    d = float(diameter)
    return int(d) if d == int(d) else d


def parse_size(name):
    """Parse 'M6' or 'M6x1.0' → (diameter_key, pitch_or_None)."""
    s = str(name).upper().strip().lstrip("M")
    if "X" in s:
        parts = s.split("X", 1)
        return _to_key(parts[0]), float(parts[1])
    return _to_key(s), None


def lookup(diameter):
    """Return the METRIC_COARSE entry for the given nominal diameter (mm)."""
    key = _to_key(diameter)
    if key not in METRIC_COARSE:
        raise ValueError(
            f"No ISO data for M{key}. "
            f"Supported: {sorted(METRIC_COARSE)}"
        )
    return METRIC_COARSE[key]
