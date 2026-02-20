# ============================================================
# analysis.py — Frame pre-processing and colour analysis
# ============================================================
import cv2
import numpy as np
from config import (
    CAM_WIDTH, CAM_HEIGHT,
    PAD_ROIS, LEGENDS,
    DEFAULT_VALUE, EMPTY_BOX_COLOR,
)


# ── Frame utilities ──────────────────────────────────────

def preprocess(frame: np.ndarray) -> np.ndarray:
    """Resize to processing resolution and apply a mild blur."""
    frame = cv2.resize(frame, (CAM_WIDTH, CAM_HEIGHT))
    return cv2.GaussianBlur(frame, (3, 3), 0)


def average_lab_color(square: np.ndarray) -> np.ndarray:
    """Return mean LAB colour of a BGR image patch."""
    lab = cv2.cvtColor(square, cv2.COLOR_BGR2LAB)
    return lab.reshape(-1, 3).mean(axis=0)


# ── Legend matching ──────────────────────────────────────

def match_color(sample: np.ndarray, legend: dict) -> str:
    """
    Find the closest legend entry by Euclidean distance in LAB space.
    Returns the label string.
    """
    best_label = DEFAULT_VALUE
    min_dist   = float("inf")
    for label, ref in legend.items():
        dist = np.linalg.norm(sample - np.array(ref, dtype=float))
        if dist < min_dist:
            min_dist   = dist
            best_label = label
    return best_label


# ── Per-parameter analysis ───────────────────────────────

def analyze_param(param: str, frame: np.ndarray) -> tuple[str, np.ndarray]:
    """
    Extract the ROI for *param* from *frame*, measure its colour,
    and return (result_label, avg_lab_color).
    Raises ValueError if the ROI is out of bounds or empty.
    """
    x, y, w, h = PAD_ROIS[param]
    if y + h > frame.shape[0] or x + w > frame.shape[1]:
        raise ValueError(
            f"ROI for '{param}' ({x},{y},{w},{h}) is outside "
            f"frame {frame.shape[1]}×{frame.shape[0]}"
        )
    square = frame[y : y + h, x : x + w]
    if square.size == 0:
        raise ValueError(f"Empty ROI for '{param}'")

    avg = average_lab_color(square)
    label = match_color(avg, LEGENDS[param])
    return label, avg


# ── Display helpers ──────────────────────────────────────

def draw_roi_guides(frame: np.ndarray) -> None:
    """Draw green guide rectangles for all pad ROIs (in-place)."""
    for x, y, w, h in PAD_ROIS.values():
        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)


def fill_roi_with_color(
    frame: np.ndarray, lab_color: np.ndarray, roi: tuple
) -> None:
    """Fill *roi* with a solid colour converted from LAB to BGR (in-place)."""
    x, y, w, h = roi
    if y + h > frame.shape[0] or x + w > frame.shape[1]:
        return
    lab_img = np.full((h, w, 3), lab_color.astype(np.uint8), dtype=np.uint8)
    bgr = cv2.cvtColor(lab_img, cv2.COLOR_LAB2BGR)
    frame[y : y + h, x : x + w] = bgr


def draw_param_overlay(
    frame: np.ndarray,
    param: str,
    elapsed: int,
    wait_time: int,
    result: str,
    y_pos: int,
) -> None:
    """Draw a compact status line on the camera frame (in-place)."""
    remaining = max(0, wait_time - elapsed)
    label = param[:3].upper()
    text  = f"{label}: {remaining}s  {result}"
    (tw, th), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
    cv2.rectangle(frame, (4, y_pos - th - 4), (4 + tw + 8, y_pos + 4), (0, 0, 0), -1)
    cv2.putText(
        frame, text, (8, y_pos),
        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1, cv2.LINE_AA,
    )
