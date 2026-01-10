import cv2
import numpy as np
import time

# =====================
# ROI SETTINGS
# =====================
SQUARE_SIZE = 80
ROI_X = 280
ROI_Y = 180

# =====================
# CAMERA SETUP
# =====================
cap = cv2.VideoCapture(1)

# Optional: stabilize camera
cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 0)
cap.set(cv2.CAP_PROP_AUTO_WB, 0)

print("INSTRUCTIONS:")
print("1. Place color inside the square")
print("2. Press 'C' to capture LAB value and preview")
print("3. Press 'Q' to quit\n")

while True:
    ret, frame = cap.read()
    if not ret:
        break

    display = frame.copy()

    # Draw square
    cv2.rectangle(
        display,
        (ROI_X, ROI_Y),
        (ROI_X + SQUARE_SIZE, ROI_Y + SQUARE_SIZE),
        (0, 255, 0),
        2
    )

    cv2.putText(
        display,
        "Press C to capture LAB",
        (ROI_X - 40, ROI_Y - 10),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.6,
        (0, 255, 0),
        2
    )

    cv2.imshow("LAB Calibration", display)

    key = cv2.waitKey(1) & 0xFF

    # =====================
    # CAPTURE LAB VALUE
    # =====================
    if key == ord('c'):
        roi = frame[ROI_Y:ROI_Y + SQUARE_SIZE,
                    ROI_X:ROI_X + SQUARE_SIZE]

        # Convert to LAB and compute average
        lab = cv2.cvtColor(roi, cv2.COLOR_BGR2LAB)
        avg_lab = np.mean(lab.reshape(-1, 3), axis=0)
        print("Captured LAB:", avg_lab.astype(int))

        # Fill square with captured color for 1 second
        fill_color = np.full((SQUARE_SIZE, SQUARE_SIZE, 3),
                             avg_lab.astype(np.uint8),
                             dtype=np.uint8)
        fill_color_bgr = cv2.cvtColor(fill_color, cv2.COLOR_LAB2BGR)

        temp_frame = display.copy()
        temp_frame[ROI_Y:ROI_Y + SQUARE_SIZE, ROI_X:ROI_X + SQUARE_SIZE] = fill_color_bgr

        cv2.imshow("LAB Calibration", temp_frame)
        cv2.waitKey(1000)  # show for 1 second

    elif key == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
