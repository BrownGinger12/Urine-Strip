import cv2
import numpy as np
import time
import tkinter as tk
from PIL import Image, ImageTk
import RPi.GPIO as GPIO
import threading

# ==============================
# GPIO CONFIGURATION
# ==============================
BUTTON_PIN = 26

def setup_gpio():
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

def cleanup_gpio():
    GPIO.cleanup()

# ==============================
# CONFIGURATION FOR 320x240 LCD
# ==============================
FRAME_WIDTH = 240
FRAME_HEIGHT = 160

SQUARE_SIZE = 35
START_X = 150
START_Y = 10
GAP = 8  # spacing between squares

PAD_ORDER = [
    "glucose",
    "ph",
    "specific_gravity",
    "protein"
]

PARAM_TIMES = {
    "glucose": 30,
    "specific_gravity": 45,
    "ph": 60,
    "protein": 60
}

DEFAULT_VALUE = "---"
DEFAULT_LAB_COLOR = np.array([230, 128, 128])  # gray
EMPTY_BOX_COLOR = np.array([50, 50, 50])      # dark gray for empty scan

# Generate square ROIs
PAD_ROIS = {}
for i, param in enumerate(PAD_ORDER):
    PAD_ROIS[param] = (
        START_X,
        START_Y + i * (SQUARE_SIZE + GAP),
        SQUARE_SIZE,
        SQUARE_SIZE
    )

# Sample legend (replace with calibrated LAB values)
LEGENDS = {
    "glucose": {
        "Negative": [165, 107, 115],
        "trace": [128, 112, 129],
        "+": [79, 116, 143],
        "++": [75, 121, 151],
        "+++": [48, 133, 148],
        "++++": [47, 139, 147]
    },
    "ph": {
        "5.0": [162, 132, 155],
        "6.0": [182, 133, 145],
        "6.5": [174, 129, 142],
        "7.0": [165, 125, 153],
        "7.5": [125, 121, 153],
        "8.0": [116, 118, 150],
        "8.5": [65, 114, 136],
    },
    "specific_gravity": {
        "1.000": [144, 128, 165],
        "1.05": [60, 114, 129],
        "1.01": [60, 115, 136],
        "1.015": [85, 119, 146],
        "1.020": [93, 121, 150],
        "1.025": [78, 129, 150],
        "1.030": [96, 132, 157]
    },
    "protein": {
        "Negative": [172, 124, 148],
        "Trace": [157, 119, 155],
        "+": [137, 117, 150],
        "++": [97, 114, 144],
        "+++": [58, 113, 132],
        "++++": [45, 112, 129]
    }
}

# ==============================
# FUNCTIONS
# ==============================
def preprocess(frame):
    frame = cv2.resize(frame, (FRAME_WIDTH, FRAME_HEIGHT))
    return cv2.GaussianBlur(frame, (3,3), 0)

def average_lab_color(square):
    lab = cv2.cvtColor(square, cv2.COLOR_BGR2LAB)
    return lab.reshape(-1,3).mean(axis=0)

def match_color(sample, legend):
    best_label = DEFAULT_VALUE
    min_dist = float("inf")
    for label, ref in legend.items():
        dist = np.linalg.norm(sample - np.array(ref))
        if dist < min_dist:
            min_dist = dist
            best_label = label
    return best_label

def fill_square(frame, lab_color, roi):
    try:
        x,y,w,h = roi
        # Ensure we don't go out of bounds
        if y+h > frame.shape[0] or x+w > frame.shape[1]:
            return
        lab_img = np.full((h,w,3), lab_color, dtype=np.uint8)
        bgr = cv2.cvtColor(lab_img, cv2.COLOR_LAB2BGR)
        frame[y:y+h, x:x+w] = bgr
    except Exception as e:
        print(f"Error filling square: {e}")

def draw_guides(frame):
    for param, roi in PAD_ROIS.items():
        x,y,w,h = roi
        cv2.rectangle(frame, (x,y), (x+w,y+h), (0,255,0), 1)

def draw_compact_info(frame, param, elapsed, wait_time, result, y_pos):
    remaining = max(0, wait_time - elapsed)
    # Shorten parameter names
    param_short = param[:3].upper()
    text = f"{param_short}:{remaining}s {result}"
    # White background for better visibility
    (w, h), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.35, 1)
    cv2.rectangle(frame, (3, y_pos - h - 2), (3 + w + 4, y_pos + 2), (0, 0, 0), -1)
    cv2.putText(frame, text, (5, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0,255,255), 1)

# ==============================
# TKINTER GUI
# ==============================
class UrineAnalyzerApp:
    def __init__(self, root):
        self.root = root
        
        # Setup GPIO
        setup_gpio()
        
        # Fullscreen for LCD
        root.overrideredirect(True)
        root.geometry("320x240+0+0")
        root.configure(bg="black")

        # Camera
        self.cap = cv2.VideoCapture(0)
        self.start_time = None
        self.analysis_done = {p: False for p in PAD_ORDER}
        self.results = {p: DEFAULT_VALUE for p in PAD_ORDER}
        self.pad_colors = {p: EMPTY_BOX_COLOR.copy() for p in PAD_ORDER}

        # Button state tracking
        self.button_pressed = False
        
        # Analysis lock to prevent freezing
        self.analyzing = False
        self.current_frame = None

        # Persistent reference for Tkinter image
        self.imgtk = None

        # Main canvas (full screen)
        self.video_canvas = tk.Canvas(root, width=320, height=240, bg="black", highlightthickness=0)
        self.video_canvas.pack(fill=tk.BOTH, expand=True)

        # Instructions at bottom
        self.info_label = tk.Label(root, text="Press Button to Start", 
                                   font=("Arial", 8), fg="white", bg="black")
        self.info_label.place(x=80, y=220)

        # Bind keys for testing
        root.bind("<s>", self.start_analysis)
        root.bind("<q>", lambda e: self.quit_app())

        # Start updating frames
        self.check_button()
        self.update_frame()

    def check_button(self):
        """Check if button is pressed (active LOW)"""
        if GPIO.input(BUTTON_PIN) == GPIO.LOW and not self.button_pressed:
            self.button_pressed = True
            self.start_analysis()
        elif GPIO.input(BUTTON_PIN) == GPIO.HIGH:
            self.button_pressed = False
        
        # Check button every 100ms
        self.root.after(100, self.check_button)

    def analyze_parameter(self, param, frame):
        """Analyze a single parameter in background thread"""
        try:
            x, y, w, h = PAD_ROIS[param]
            # Ensure ROI is within frame bounds
            if y+h > frame.shape[0] or x+w > frame.shape[1]:
                print(f"ROI out of bounds for {param}")
                self.analyzing = False
                return
            
            square = frame[y:y+h, x:x+w]
            if square.size > 0 and square.shape[0] == h and square.shape[1] == w:
                avg_color = average_lab_color(square)
                self.pad_colors[param] = avg_color
                result = match_color(avg_color, LEGENDS[param])
                self.results[param] = result
                self.analysis_done[param] = True
                print(f"{param}: {result}")
            else:
                print(f"Invalid square shape for {param}: {square.shape}")
        except Exception as e:
            print(f"Error analyzing {param}: {e}")
        finally:
            self.analyzing = False
    def start_analysis(self, event=None):
        """Start a new scan: reset everything"""
        # Prevent starting a new scan while one is running
        if self.start_time is not None:
            elapsed = int(time.time() - self.start_time)
            if elapsed < max(PARAM_TIMES.values()):
                return  # Scan still in progress
        
        self.start_time = time.time()
        self.analyzing = False
        for p in PAD_ORDER:
            self.analysis_done[p] = False
            self.results[p] = DEFAULT_VALUE
            self.pad_colors[p] = EMPTY_BOX_COLOR.copy()
        print("Scan started!")

    def quit_app(self):
        self.cap.release()
        cleanup_gpio()
        self.root.destroy()

    def update_frame(self):
        ret, frame = self.cap.read()
        if not ret:
            print("Camera read failed, retrying...")
            self.cap.release()
            time.sleep(0.1)
            self.cap = cv2.VideoCapture(0)
            self.root.after(100, self.update_frame)
            return
        
        try:
            frame = preprocess(frame)
            display = frame.copy()

            # Draw guides
            draw_guides(display)

            # Analyze each parameter after timer
            if self.start_time:
                elapsed = int(time.time() - self.start_time)
                
                # Check and start analysis in background thread
                for param in PAD_ORDER:
                    if elapsed >= PARAM_TIMES[param] and not self.analysis_done[param] and not self.analyzing:
                        self.analyzing = True
                        # Run analysis in separate thread to prevent UI freeze
                        thread = threading.Thread(target=self.analyze_parameter, args=(param, frame.copy()))
                        thread.daemon = True
                        thread.start()
                        break  # Only analyze one at a time
                
                # Draw all info
                y_text = 15
                for param in PAD_ORDER:
                    draw_compact_info(display, param, elapsed, PARAM_TIMES[param], 
                                     self.results[param], y_text)
                    y_text += 12

            # Fill squares with detected colors
            for param, roi in PAD_ROIS.items():
                if self.analysis_done[param]:
                    fill_square(display, self.pad_colors[param], roi)

            # Convert to Tk image
            img = cv2.cvtColor(display, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(img)
            # Resize to fit 320x240 screen
            img = img.resize((320, 213), Image.Resampling.LANCZOS)
            self.imgtk = ImageTk.PhotoImage(image=img)
            self.video_canvas.delete("all")
            self.video_canvas.create_image(0, 0, anchor=tk.NW, image=self.imgtk)
        
        except Exception as e:
            print(f"Error in update_frame: {e}")

        self.root.after(10, self.update_frame)

# ==============================
# RUN APP
# ==============================
if __name__ == "__main__":
    root = tk.Tk()
    app = UrineAnalyzerApp(root)
    root.mainloop()