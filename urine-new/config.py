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
# Scaled up from original 240×160 design:
#   x_scale = 560/240 ≈ 2.33,  y_scale = 480/160 = 3.0
SQUARE_SIZE = 65
GAP         = 21
START_X     = 420
START_Y     = 24

PAD_ORDER = [
    "glucose",
    "ph",
    "specific_gravity",
    "protein",
]

# Derived ROIs: { param: (x, y, w, h) }
PAD_ROIS = {
    param: (START_X, START_Y + i * (SQUARE_SIZE + GAP), SQUARE_SIZE, SQUARE_SIZE)
    for i, param in enumerate(PAD_ORDER)
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
        "Trace":    [128, 112, 129],
        "+":        [ 79, 116, 143],
        "++":       [ 75, 121, 151],
        "+++":      [ 48, 133, 148],
        "++++":     [ 47, 139, 147],
    },
    "ph": {
        "5.0": [162, 132, 155],
        "6.0": [182, 133, 145],
        "6.5": [174, 129, 142],
        "7.0": [165, 125, 153],
        "7.5": [125, 121, 153],
        "8.0": [116, 118, 150],
        "8.5": [ 65, 114, 136],
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
        "Negative": [172, 124, 148],
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
