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
SQUARE_SIZE = 48

PAD_ORDER = [
    "glucose",
    "ph",
    "specific_gravity",
    "protein",
]

# Individual box positions (x, y) — adjust each pad independently
PAD_POSITIONS = {
    "glucose":          (222, 169),
    "ph":               (225, 250),
    "specific_gravity": (225, 329),
    "protein":          (225, 410),
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
        "Negative": [165, 107, 115],
        "Trace":    [202, 113, 128],
        "+":        [187, 117, 142],
        "++":       [172, 122, 157],
        "+++":      [ 146, 134, 148],
        "++++":     [ 118, 144, 142],
    },
    "ph": {
        "5.0": [207, 132, 166],
        "6.0": [214, 130, 152],
        "6.5": [212, 128, 144],
        "7.0": [199, 123, 159],
        "7.5": [194, 119, 151],
        "8.0": [183, 114, 156],
        "8.5": [ 163, 110, 145],
    },
    "specific_gravity": {
        "1.000": [144, 128, 165],
        "1.005": [ 60, 114, 129],
        "1.010": [ 60, 115, 136],
        "1.015": [ 85, 119, 146],
        "1.020": [ 93, 121, 150],
        "1.025": [ 78, 129, 150],
        "1.030": [ 96, 132, 157],
    },
    "protein": {
        "Negative": [200, 118, 143],
        "Trace":    [157, 119, 155],
        "+":        [137, 117, 150],
        "++":       [ 97, 114, 144],
        "+++":      [ 58, 113, 132],
        "++++":     [ 45, 112, 129],
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
