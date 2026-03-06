# ============================================================
# ui/scan_screen.py — Live camera scan screen
# ============================================================
import tkinter as tk
import threading
import time

import cv2
import numpy as np
from PIL import Image, ImageTk

import database as db
from analysis import preprocess, analyze_param, draw_roi_guides, fill_roi_with_color
from config import (
    CAM_WIDTH, CAM_HEIGHT, PANEL_WIDTH,
    PAD_ORDER, PAD_ROIS, PARAM_TIMES, MAX_SCAN_TIME,
    DEFAULT_VALUE, EMPTY_BOX_COLOR,
    COLOR_BG, COLOR_PANEL, COLOR_ACCENT, COLOR_BORDER,
    COLOR_HIGHLIGHT, COLOR_SUCCESS, COLOR_WARNING, COLOR_DANGER,
    COLOR_TEXT, COLOR_SUBTEXT,
    FONT_TITLE, FONT_BODY, FONT_SMALL, FONT_MONO,
    SCREEN_HEIGHT,
)
from ui.widgets import make_topbar, make_button

try:
    import RPi.GPIO as GPIO
    _GPIO_AVAILABLE = True
except (ImportError, RuntimeError, ModuleNotFoundError):
    GPIO = None
    _GPIO_AVAILABLE = False

BUTTON_PIN = 26

# Friendly display names for parameters
PARAM_LABELS = {
    "glucose":          "Glucose",
    "ph":               "pH",
    "specific_gravity": "Sp. Gravity",
    "protein":          "Protein",
}

# Status machine states
STATE_IDLE     = "idle"
STATE_SCANNING = "scanning"
STATE_DONE     = "done"
STATE_SAVED    = "saved"


class ScanScreen(tk.Frame):
    """
    Full-screen scan view.

    Layout (800×480):
    ┌──────────────────────────────────┬────────────────────┐
    │  [← Back]   Scanning: <name>    │                    │
    │                                  │   RESULTS PANEL    │
    │        Camera Feed (560×480)     │   (240px wide)     │
    │                                  │                    │
    │   SPACE — start  |  Q — quit    │                    │
    └──────────────────────────────────┴────────────────────┘
    """

    POLL_MS   = 33    # ~30 fps
    SAVE_DELAY = 2000  # ms after scan completes before auto-returning

    def __init__(self, parent: tk.Widget, app, patient_id: int):
        super().__init__(parent, bg=COLOR_BG)
        self.app        = app
        self.patient_id = patient_id
        self.patient    = db.get_patient(patient_id)

        # Camera
        self._cap: cv2.VideoCapture | None = None
        self._cam_running = False

        # Scan state
        self._state      = STATE_IDLE
        self._start_time: float | None = None
        self._analyzing  = False           # guard: only one thread at a time

        self._results   = {p: DEFAULT_VALUE for p in PAD_ORDER}
        self._done      = {p: False         for p in PAD_ORDER}
        self._pad_colors = {p: np.array(EMPTY_BOX_COLOR, dtype=np.uint8)
                            for p in PAD_ORDER}

        # Tk image reference (prevents GC)
        self._imgtk: ImageTk.PhotoImage | None = None

        self._build_ui()
        self._open_camera()
        self._bind_keys()
        self._poll()   # start camera loop

    # ── Layout ───────────────────────────────────────────

    def _build_ui(self):
        name = self.patient["name"] if self.patient else "Unknown"
        make_topbar(self, f"Scanning:  {name}",
                    back_command=self._go_back)

        # Main body below the top bar
        body = tk.Frame(self, bg=COLOR_BG)
        body.pack(fill=tk.BOTH, expand=True)

        # Camera canvas (left)
        self._cam_canvas = tk.Canvas(
            body, width=CAM_WIDTH, height=CAM_HEIGHT,
            bg="black", highlightthickness=0,
        )
        self._cam_canvas.pack(side=tk.LEFT)

        # Results panel (right, fixed width)
        self._panel = tk.Frame(body, bg=COLOR_PANEL,
                               width=PANEL_WIDTH, height=CAM_HEIGHT)
        self._panel.pack(side=tk.LEFT, fill=tk.Y)
        self._panel.pack_propagate(False)

        self._build_panel()

    def _build_panel(self):
        p = self._panel

        tk.Label(p, text="RESULTS", font=FONT_SMALL,
                 fg=COLOR_SUBTEXT, bg=COLOR_PANEL).pack(pady=(16, 4))

        tk.Frame(p, bg=COLOR_BORDER, height=1).pack(fill=tk.X, padx=10)

        # One label per parameter
        self._result_labels: dict[str, tk.Label] = {}
        self._timer_labels:  dict[str, tk.Label] = {}

        for param in PAD_ORDER:
            row = tk.Frame(p, bg=COLOR_PANEL)
            row.pack(fill=tk.X, padx=10, pady=6)

            tk.Label(row, text=PARAM_LABELS[param],
                     font=FONT_SMALL, fg=COLOR_SUBTEXT, bg=COLOR_PANEL,
                     anchor="w", width=11).pack(side=tk.LEFT)

            val_lbl = tk.Label(row, text=DEFAULT_VALUE,
                               font=FONT_MONO, fg=COLOR_TEXT,
                               bg=COLOR_PANEL, anchor="e")
            val_lbl.pack(side=tk.RIGHT)
            self._result_labels[param] = val_lbl

            # Timer / countdown below param name
            timer_lbl = tk.Label(p, text="",
                                 font=("Helvetica", 8), fg=COLOR_SUBTEXT,
                                 bg=COLOR_PANEL)
            timer_lbl.pack(anchor="w", padx=12)
            self._timer_labels[param] = timer_lbl

        tk.Frame(p, bg=COLOR_BORDER, height=1).pack(fill=tk.X, padx=10, pady=8)

        # Status message
        self._status_var = tk.StringVar(value="Press Button to Scan")
        self._status_lbl = tk.Label(
            p, textvariable=self._status_var,
            font=FONT_SMALL, fg=COLOR_WARNING, bg=COLOR_PANEL,
            wraplength=PANEL_WIDTH - 20, justify="center",
        )
        self._status_lbl.pack(padx=10, pady=4)

        # Keyboard hint
        tk.Label(p, text="[SPACE] Start",
                 font=("Helvetica", 8), fg=COLOR_SUBTEXT,
                 bg=COLOR_PANEL).pack(pady=4)

        # Save / progress indicator (appears when scan completes)
        self._save_lbl = tk.Label(
            p, text="", font=FONT_SMALL, fg=COLOR_SUCCESS,
            bg=COLOR_PANEL, wraplength=PANEL_WIDTH - 20, justify="center",
        )
        self._save_lbl.pack(pady=4)

    # ── Camera ───────────────────────────────────────────

    def _open_camera(self):
        self._cap = cv2.VideoCapture(0)
        if not self._cap.isOpened():
            self._status_var.set("⚠ Camera not found.\nPress SPACE when ready.")
        self._cam_running = True

    def _read_frame(self) -> np.ndarray | None:
        if not self._cap or not self._cap.isOpened():
            return None
        ret, frame = self._cap.read()
        return preprocess(frame) if ret else None

    # ── Main poll loop ───────────────────────────────────

    def _poll(self):
        frame = self._read_frame()

        if frame is not None:
            display = frame.copy()
            draw_roi_guides(display)

            elapsed = int(time.time() - self._start_time) if self._start_time else 0

            if self._state == STATE_SCANNING:
                self._tick_analysis(frame, elapsed)
                self._update_panel(elapsed)

            # Fill measured pads with their detected colour
            for param in PAD_ORDER:
                if self._done[param]:
                    fill_roi_with_color(display, self._pad_colors[param],
                                        PAD_ROIS[param])

            # Render to canvas
            img = cv2.cvtColor(display, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(img)
            self._imgtk = ImageTk.PhotoImage(image=img)
            self._cam_canvas.delete("all")
            self._cam_canvas.create_image(0, 0, anchor=tk.NW, image=self._imgtk)
        else:
            # No camera: show placeholder
            self._cam_canvas.delete("all")
            self._cam_canvas.create_rectangle(
                0, 0, CAM_WIDTH, CAM_HEIGHT, fill="#0a0a0a", outline=""
            )
            self._cam_canvas.create_text(
                CAM_WIDTH // 2, CAM_HEIGHT // 2,
                text="No camera signal", fill=COLOR_SUBTEXT,
                font=FONT_BODY,
            )

        if self._cam_running:
            self.after(self.POLL_MS, self._poll)

    # ── Analysis ticking ─────────────────────────────────

    def _tick_analysis(self, frame: np.ndarray, elapsed: int):
        for param in PAD_ORDER:
            if (
                elapsed >= PARAM_TIMES[param]
                and not self._done[param]
                and not self._analyzing
            ):
                self._analyzing = True
                t = threading.Thread(
                    target=self._run_analysis,
                    args=(param, frame.copy()),
                    daemon=True,
                )
                t.start()
                break  # one param at a time

        # Check if all done
        if all(self._done[p] for p in PAD_ORDER) and self._state == STATE_SCANNING:
            self._state = STATE_DONE
            self._on_scan_complete()

    def _run_analysis(self, param: str, frame: np.ndarray):
        try:
            label, avg_color = analyze_param(param, frame)
            self._results[param]    = label
            self._pad_colors[param] = avg_color
            self._done[param]       = True
        except Exception as exc:
            print(f"[analysis] {param}: {exc}")
            self._results[param] = "ERR"
            self._done[param]    = True
        finally:
            self._analyzing = False

    # ── Panel updates ─────────────────────────────────────

    def _update_panel(self, elapsed: int):
        for param in PAD_ORDER:
            wait = PARAM_TIMES[param]
            lbl  = self._result_labels[param]
            tlbl = self._timer_labels[param]

            if self._done[param]:
                lbl.configure(text=self._results[param], fg=COLOR_SUCCESS)
                tlbl.configure(text="✔  done")
            else:
                remaining = max(0, wait - elapsed)
                lbl.configure(text=DEFAULT_VALUE, fg=COLOR_TEXT)
                tlbl.configure(text=f"⏱  {remaining}s")

    # ── Scan lifecycle ────────────────────────────────────

    def _start_scan(self):
        if self._state == STATE_SCANNING:
            return  # already running
        self._state      = STATE_SCANNING
        self._start_time = time.time()
        self._analyzing  = False

        for p in PAD_ORDER:
            self._done[p]       = False
            self._results[p]    = DEFAULT_VALUE
            self._pad_colors[p] = np.array(EMPTY_BOX_COLOR, dtype=np.uint8)
            self._result_labels[p].configure(text=DEFAULT_VALUE, fg=COLOR_TEXT)
            self._timer_labels[p].configure(text="")

        self._status_lbl.configure(fg=COLOR_HIGHLIGHT)
        self._status_var.set("Analysing… please hold strip steady")
        self._save_lbl.configure(text="")

    def _on_scan_complete(self):
        self._status_lbl.configure(fg=COLOR_SUCCESS)
        self._status_var.set("Scan complete!  Saving…")

        # Save to database
        try:
            db.add_scan(self.patient_id, self._results)
            self._save_lbl.configure(
                text="✔ Saved to patient record.\nReturning…",
                fg=COLOR_SUCCESS,
            )
        except Exception as exc:
            self._save_lbl.configure(
                text=f"⚠ Save failed: {exc}", fg=COLOR_DANGER
            )

        # Return to patient log after a brief delay
        self.after(self.SAVE_DELAY, lambda: self.app.show_logs(self.patient_id))

    # ── Button / key bindings ────────────────────────────

    def _bind_keys(self):
        if _GPIO_AVAILABLE:
            try:
                GPIO.setmode(GPIO.BCM)
                GPIO.setup(BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
                # Remove any existing event detect before adding a new one
                try:
                    GPIO.remove_event_detect(BUTTON_PIN)
                except Exception:
                    pass
                GPIO.add_event_detect(
                    BUTTON_PIN, GPIO.FALLING,
                    callback=lambda _: self.after(0, self._on_button),
                    bouncetime=300,
                )
            except Exception as e:
                print(f"[GPIO] setup failed: {e}")
        else:
            # Fallback: spacebar for PC testing
            self.app.bind("<space>", self._on_button)

    def _unbind_keys(self):
        if _GPIO_AVAILABLE:
            try:
                GPIO.remove_event_detect(BUTTON_PIN)
                GPIO.cleanup(BUTTON_PIN)
            except Exception:
                pass
        else:
            try:
                self.app.unbind("<space>")
            except Exception:
                pass

    def _on_button(self, _event=None):
        if self._state in (STATE_IDLE, STATE_DONE):
            self._start_scan()

    # ── Navigation ────────────────────────────────────────

    def _go_back(self):
        self.cleanup()
        self.app.show_patient_list()

    # ── Cleanup ───────────────────────────────────────────

    def cleanup(self):
        """Release camera and bindings. Called by App._swap before destroy."""
        self._cam_running = False
        self._unbind_keys()
        if self._cap and self._cap.isOpened():
            self._cap.release()
            self._cap = None