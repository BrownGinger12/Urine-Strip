# ============================================================
# config.py — Central configuration for Urine Analyzer
# ============================================================

# ── Screen (7-inch LCD) ──────────────────────────────────
SCREEN_WIDTH  = 800
SCREEN_HEIGHT = 480

# ── Camera / Processing Frame ────────────────────────────
# The frame is processed AND displayed at this size.
# The right panel (PANEL_WIDTH) sits beside the camera feed.
PANEL_WIDTH   = 240
CAM_WIDTH     = SCREEN_WIDTH - PANEL_WIDTH   # 560
CAM_HEIGHT    = SCREEN_HEIGHT                # 480

# ── Reagent Pad ROIs (in processing-frame coordinates) ───
SQUARE_SIZE = 56

PAD_ORDER = [
    "glucose",
    "ph",
    "specific_gravity",
    "protein",
]

# Individual box positions (x, y) — adjust each pad independently
PAD_POSITIONS = {
    "glucose":          (88, 167),
    "ph":               (199, 159),
    "specific_gravity": (311, 151),
    "protein":          (424, 141),
}

# Derived ROIs: { param: (x, y, w, h) }
PAD_ROIS = {
    param: (x, y, SQUARE_SIZE, SQUARE_SIZE)
    for param, (x, y) in PAD_POSITIONS.items()
}



# ── Timing (seconds after scan starts) ──────────────────
PARAM_TIMES = {
    "glucose":          30,
    "specific_gravity": 45,
    "ph":               60,
    "protein":          60,
}

MAX_SCAN_TIME = max(PARAM_TIMES.values())   # 60 s

# ── Default / placeholder values ────────────────────────
DEFAULT_VALUE     = "---"
EMPTY_BOX_COLOR   = [50, 50, 50]    # dark gray (LAB)
DEFAULT_LAB_COLOR = [230, 128, 128] # light gray (LAB)

# ── Reference colour legends (LAB) ──────────────────────
LEGENDS = {
    "glucose": {
        "Negative": [144, 111, 113],
        "Trace":    [119, 113, 134],
        "+":        [105, 117, 144],
        "++":       [ 88, 124, 156],
        "+++":      [ 75, 132, 149],
        "++++":     [ 55, 139, 139],
    },
    "ph": {
        "5.0": [132, 133, 167],
        "6.0": [141, 130, 160],
        "6.5": [137, 126, 158],
        "7.0": [127, 121, 168],
        "7.5": [125, 117, 162],
        "8.0": [106, 116, 158],
        "8.5": [ 81, 117, 145],
    },
    "specific_gravity": {
        "1.000": [ 75, 122, 111],
        "1.005": [ 82, 117, 136],
        "1.010": [ 84, 120, 140],
        "1.015": [ 93, 118, 149],
        "1.020": [ 98, 121, 154],
        "1.025": [112, 125, 160],
        "1.030": [128, 126, 166],
    },
    "protein": {
        "Negative": [139, 122, 153],
        "Trace":    [133, 120, 164],
        "+":        [123, 119, 159],
        "++":       [112, 116, 151],    
        "+++":      [107, 110, 142],
        "++++":     [100, 111, 137],
    },
}

# ── UI colour palette (dark medical theme) ───────────────
COLOR_BG        = "#0d1117"
COLOR_PANEL     = "#161b22"
COLOR_ACCENT    = "#1f2937"
COLOR_BORDER    = "#30363d"
COLOR_HIGHLIGHT = "#3b82f6"   # blue
COLOR_SUCCESS   = "#22c55e"   # green
COLOR_WARNING   = "#f59e0b"   # amber
COLOR_DANGER    = "#ef4444"   # red
COLOR_TEXT      = "#f0f6fc"
COLOR_SUBTEXT   = "#8b949e"
COLOR_ROW_ALT   = "#0e1318"

# ── Fonts ────────────────────────────────────────────────
FONT_TITLE  = ("Helvetica", 14, "bold")
FONT_BODY   = ("Helvetica", 11)
FONT_SMALL  = ("Helvetica",  9)
FONT_MONO   = ("Courier",   10)
