"""
ISO metric ball bearing dimension tables.

Sources: ISO 15 (radial ball bearings), manufacturers' catalogues.

Key: bearing designation string (e.g. "608", "6004")
  id   : bore diameter (mm)
  od   : outer diameter (mm)
  width: bearing width (mm)
"""

BEARINGS = {
    # 600-series — miniature / instrument
    "606":  {"id":  6, "od": 17, "width":  6},
    "607":  {"id":  7, "od": 19, "width":  6},
    "608":  {"id":  8, "od": 22, "width":  7},
    "609":  {"id":  9, "od": 24, "width":  7},
    "6000": {"id": 10, "od": 26, "width":  8},
    "6001": {"id": 12, "od": 28, "width":  8},
    "6002": {"id": 15, "od": 32, "width":  9},
    "6003": {"id": 17, "od": 35, "width": 10},
    "6004": {"id": 20, "od": 42, "width": 12},
    "6005": {"id": 25, "od": 47, "width": 12},
    "6006": {"id": 30, "od": 55, "width": 13},
    "6007": {"id": 35, "od": 62, "width": 14},
    "6008": {"id": 40, "od": 68, "width": 15},
    # 620-series — light
    "6200": {"id": 10, "od": 30, "width":  9},
    "6201": {"id": 12, "od": 32, "width": 10},
    "6202": {"id": 15, "od": 35, "width": 11},
    "6203": {"id": 17, "od": 40, "width": 12},
    "6204": {"id": 20, "od": 47, "width": 14},
    "6205": {"id": 25, "od": 52, "width": 15},
    "6206": {"id": 30, "od": 62, "width": 16},
    "6207": {"id": 35, "od": 72, "width": 17},
    "6208": {"id": 40, "od": 80, "width": 18},
    # 630-series — medium
    "6300": {"id": 10, "od": 35, "width": 11},
    "6301": {"id": 12, "od": 37, "width": 12},
    "6302": {"id": 15, "od": 42, "width": 13},
    "6303": {"id": 17, "od": 47, "width": 14},
    "6304": {"id": 20, "od": 52, "width": 15},
    "6305": {"id": 25, "od": 62, "width": 17},
    "6306": {"id": 30, "od": 72, "width": 19},
    "6307": {"id": 35, "od": 80, "width": 21},
    "6308": {"id": 40, "od": 90, "width": 23},
}


def lookup_bearing(designation):
    """Return dims dict for the given bearing designation string."""
    key = str(designation).strip()
    if key not in BEARINGS:
        raise ValueError(
            f"No data for bearing {key!r}. "
            f"Supported: {sorted(BEARINGS)}"
        )
    return BEARINGS[key]
