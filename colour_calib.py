import cv2
import numpy as np
import re

CONFIG_PATH = r"C:\Users\miles\OneDrive\Desktop\Urine-Strip\urine-new\config.py"

# Scan-screen pad labels (must match PAD_ORDER in config.py)
PAD_LABELS = ["glucose", "ph", "specific_gravity", "protein"]

# ── Load initial positions from config.py ─────────────────
def load_positions():
    with open(CONFIG_PATH, "r") as f:
        src = f.read()
    boxes = []
    for label in PAD_LABELS:
        m = re.search(
            rf'"{label}"\s*:\s*\((\d+)\s*,\s*(\d+)\)',
            src
        )
        if m:
            boxes.append([int(m.group(1)), int(m.group(2))])
        else:
            boxes.append([100, 100])
    # Size comes from SQUARE_SIZE
    m = re.search(r'SQUARE_SIZE\s*=\s*(\d+)', src)
    size = int(m.group(1)) if m else 48
    return boxes, size

# ── Save positions back to config.py ──────────────────────
def save_positions(boxes, size):
    with open(CONFIG_PATH, "r") as f:
        src = f.read()

    # Update SQUARE_SIZE
    src = re.sub(r'(SQUARE_SIZE\s*=\s*)\d+', rf'\g<1>{size}', src)

    # Update each pad position
    for i, label in enumerate(PAD_LABELS):
        x, y = boxes[i]
        src = re.sub(
            rf'("{label}"\s*:\s*\()\d+\s*,\s*\d+(\))',
            rf'\g<1>{x}, {y}\2',
            src
        )

    with open(CONFIG_PATH, "w") as f:
        f.write(src)
    print(f"Saved positions to {CONFIG_PATH}")

# ── Init ──────────────────────────────────────────────────
positions, sq_size = load_positions()
# boxes: [x, y, size] per pad
boxes = [[x, y, sq_size] for x, y in positions]

selected = 0
STEP     = 2

# =====================
# CAMERA SETUP
# =====================
cap = cv2.VideoCapture(1)
cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 0)
cap.set(cv2.CAP_PROP_AUTO_WB, 0)

print("CONTROLS:")
print("  1 2 3 4  — select box")
print("  W A S D  — move selected box")
print("  E / Q    — grow / shrink selected box")
print("  C        — capture LAB from all boxes")
print("  P        — print current positions")
print("  ESC      — save to config.py and quit\n")

while True:
    ret, frame = cap.read()
    if not ret:
        break

    display = frame.copy()

    for i, (x, y, sz) in enumerate(boxes):
        color     = (0, 255, 255) if i == selected else (0, 255, 0)
        thickness = 2             if i == selected else 1
        cv2.rectangle(display, (x, y), (x + sz, y + sz), color, thickness)
        label_y = y - 6 if y > 14 else y + sz + 14
        cv2.putText(display, f"{i+1}:{PAD_LABELS[i]}",
                    (x, label_y),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.38, color, 1)

    cv2.putText(display,
                f"box {selected+1} ({PAD_LABELS[selected]})  "
                f"pos:({boxes[selected][0]},{boxes[selected][1]})  "
                f"size:{boxes[selected][2]}",
                (8, display.shape[0] - 8),
                cv2.FONT_HERSHEY_SIMPLEX, 0.38, (200, 200, 200), 1)

    cv2.imshow("LAB Calibration", display)
    key = cv2.waitKey(16) & 0xFF

    # ── Box selection ──────────────────────────────────────
    if   key == ord('1'): selected = 0
    elif key == ord('2'): selected = 1
    elif key == ord('3'): selected = 2
    elif key == ord('4'): selected = 3

    # ── Move ──────────────────────────────────────────────
    elif key == ord('a'): boxes[selected][0] -= STEP
    elif key == ord('d'): boxes[selected][0] += STEP
    elif key == ord('w'): boxes[selected][1] -= STEP
    elif key == ord('s'): boxes[selected][1] += STEP

    # ── Resize (E = grow, Q = shrink) ─────────────────────
    elif key == ord('e'): boxes[selected][2] = max(5, boxes[selected][2] + 2)
    elif key == ord('q'): boxes[selected][2] = max(5, boxes[selected][2] - 2)

    # ── Print ─────────────────────────────────────────────
    elif key == ord('p'):
        print("Current box positions:")
        for i, (bx, by, bsz) in enumerate(boxes):
            print(f"  {PAD_LABELS[i]:16s}: x={bx}, y={by}, size={bsz}")
        print()

    # ── Capture LAB ───────────────────────────────────────
    elif key == ord('c'):
        temp = display.copy()
        print("--- Captured LAB values ---")
        for i, (bx, by, bsz) in enumerate(boxes):
            roi = frame[by:by + bsz, bx:bx + bsz]
            if roi.size == 0:
                print(f"  # {PAD_LABELS[i]}: out of frame, skipped")
                continue
            lab = cv2.cvtColor(roi, cv2.COLOR_BGR2LAB)
            avg = np.mean(lab.reshape(-1, 3), axis=0).astype(int)
            L, A, B = avg
            print(f'        "{PAD_LABELS[i]}": [{L:3d}, {A:3d}, {B:3d}],')
            fill = np.full((bsz, bsz, 3), avg.astype(np.uint8), dtype=np.uint8)
            temp[by:by + bsz, bx:bx + bsz] = cv2.cvtColor(fill, cv2.COLOR_LAB2BGR)
        print()
        cv2.imshow("LAB Calibration", temp)
        cv2.waitKey(1500)

    # ── Save & quit ───────────────────────────────────────
    elif key == 27:  # ESC
        save_positions(boxes, boxes[0][2])
        break

cap.release()
cv2.destroyAllWindows()
