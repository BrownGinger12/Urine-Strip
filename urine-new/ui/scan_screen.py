# ============================================================
# ui/scan_screen.py — Live camera scan screen
# ============================================================
import re
import tkinter as tk
import threading
import time
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageTk

import database as db
from analysis import preprocess, analyze_param, draw_roi_guides, fill_roi_with_color
from config import (
    CAM_WIDTH, CAM_HEIGHT, PANEL_WIDTH,
    PAD_ORDER, PAD_ROIS, PAD_POSITIONS, SQUARE_SIZE, PARAM_TIMES, MAX_SCAN_TIME,
    DEFAULT_VALUE, EMPTY_BOX_COLOR,
    COLOR_BG, COLOR_PANEL, COLOR_ACCENT, COLOR_BORDER,
    COLOR_HIGHLIGHT, COLOR_SUCCESS, COLOR_WARNING, COLOR_DANGER,
    COLOR_TEXT, COLOR_SUBTEXT,
    FONT_TITLE, FONT_BODY, FONT_SMALL, FONT_MONO,
    SCREEN_HEIGHT,
)

CONFIG_PATH = Path(__file__).parent.parent / "config.py"
from ui.widgets import make_topbar, make_button

try:
    import RPi.GPIO as GPIO
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(26, GPIO.IN, pull_up_down=GPIO.PUD_UP)
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
        self._button_pressed = False         # GPIO debounce flag

        self._results   = {p: DEFAULT_VALUE for p in PAD_ORDER}
        self._done      = {p: False         for p in PAD_ORDER}
        self._pad_colors = {p: np.array(EMPTY_BOX_COLOR, dtype=np.uint8)
                            for p in PAD_ORDER}

        # Tk image reference (prevents GC)
        self._imgtk: ImageTk.PhotoImage | None = None

        # Calibration mode
        self._calib_mode     = False
        self._calib_selected = 0
        self._calib_boxes    = {p: list(PAD_POSITIONS[p]) + [SQUARE_SIZE]
                                for p in PAD_ORDER}  # {param: [x, y, size]}
        self._calib_step     = 2

        self._build_ui()
        self._open_camera()
        self._bind_keys()
        self._poll()   # start camera loop

    # ── Layout ───────────────────────────────────────────

    def _build_ui(self):
        name = self.patient["name"] if self.patient else "Unknown"
        make_topbar(self, f"Scanning:  {name}",
                    back_command=self._go_back, height=50)

        # Main body below the top bar
        body = tk.Frame(self, bg=COLOR_BG)
        body.pack(fill=tk.BOTH, expand=True)

        TOPBAR_H = 50
        view_h = SCREEN_HEIGHT - TOPBAR_H
        self._view_h = view_h

        # Camera canvas (left)
        self._cam_canvas = tk.Canvas(
            body, width=CAM_WIDTH, height=view_h,
            bg="black", highlightthickness=0,
        )
        self._cam_canvas.pack(side=tk.LEFT)

        # Results panel (right, fixed width)
        self._panel = tk.Frame(body, bg=COLOR_PANEL,
                               width=PANEL_WIDTH, height=view_h)
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
        self._cap = cv2.VideoCapture(1)
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

            if self._calib_mode:
                self._draw_calib_overlay(display)
            else:
                draw_roi_guides(display)

            elapsed = int(time.time() - self._start_time) if self._start_time else 0

            if self._state == STATE_SCANNING and not self._calib_mode:
                self._tick_analysis(frame, elapsed)
                self._update_panel(elapsed)

            # Fill measured pads with their detected colour
            for param in PAD_ORDER:
                if self._done[param] and not self._calib_mode:
                    fill_roi_with_color(display, self._pad_colors[param],
                                        PAD_ROIS[param])

            # Render to canvas — scale to fit the available view height
            img = cv2.cvtColor(display, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(img)
            img = img.resize((CAM_WIDTH, self._view_h), Image.BILINEAR)
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

    # ── Button polling (GPIO) / key binding (PC) ─────────

    def _bind_keys(self):
        if _GPIO_AVAILABLE:
            self._check_button()
        else:
            self.app.bind("<space>", self._on_button)

        a = self.app
        a.bind("<Tab>",    self._toggle_calib)
        a.bind("<Return>", self._calib_save)
        a.bind("1", lambda e: self._calib_select(0))
        a.bind("2", lambda e: self._calib_select(1))
        a.bind("3", lambda e: self._calib_select(2))
        a.bind("4", lambda e: self._calib_select(3))
        s = self._calib_step
        a.bind("w", lambda e: self._calib_move( 0, -s))
        a.bind("s", lambda e: self._calib_move( 0,  s))
        a.bind("a", lambda e: self._calib_move(-s,  0))
        a.bind("d", lambda e: self._calib_move( s,  0))
        a.bind("q", lambda e: self._calib_resize(-2))
        a.bind("e", lambda e: self._calib_resize( 2))

    def _unbind_keys(self):
        if not _GPIO_AVAILABLE:
            try:
                self.app.unbind("<space>")
            except Exception:
                pass
        for key in ("<Tab>", "<Return>", "1", "2", "3", "4",
                    "w", "a", "s", "d", "q", "e"):
            try:
                self.app.unbind(key)
            except Exception:
                pass

    def _check_button(self):
        """Poll GPIO pin 26 every 100ms — same logic as original."""
        if not self._cam_running:
            return
        try:
            if GPIO.input(BUTTON_PIN) == GPIO.LOW and not self._button_pressed:
                self._button_pressed = True
                self._on_button()
            elif GPIO.input(BUTTON_PIN) == GPIO.HIGH:
                self._button_pressed = False
        except Exception:
            pass
        self.after(100, self._check_button)

    def _on_button(self, _event=None):
        if self._state in (STATE_IDLE, STATE_DONE):
            self._start_scan()

    # ── Calibration mode ──────────────────────────────────

    def _toggle_calib(self, _event=None):
        self._calib_mode = not self._calib_mode
        if self._calib_mode:
            self._status_lbl.configure(fg=COLOR_HIGHLIGHT)
            self._status_var.set(
                "CALIB  1-4:select  WASD:move  Q/E:size  Enter:save  Tab:exit"
            )
        else:
            self._status_lbl.configure(fg=COLOR_WARNING)
            self._status_var.set("Press Button to Scan")

    def _draw_calib_overlay(self, display: np.ndarray):
        for i, param in enumerate(PAD_ORDER):
            x, y, sz = self._calib_boxes[param]
            color     = (0, 255, 255) if i == self._calib_selected else (0, 255, 0)
            thick     = 2             if i == self._calib_selected else 1
            cv2.rectangle(display, (x, y), (x + sz, y + sz), color, thick)
            label_y = y - 6 if y > 14 else y + sz + 14
            cv2.putText(display, f"{i+1}:{param}",
                        (x, label_y), cv2.FONT_HERSHEY_SIMPLEX, 0.4, color, 1)

        bx, by, bsz = self._calib_boxes[PAD_ORDER[self._calib_selected]]
        cv2.putText(display,
                    f"pos:({bx},{by}) size:{bsz}",
                    (6, display.shape[0] - 6),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.4, (200, 200, 200), 1)

    def _calib_select(self, idx: int):
        if self._calib_mode:
            self._calib_selected = idx

    def _calib_move(self, dx: int, dy: int):
        if not self._calib_mode:
            return
        param = PAD_ORDER[self._calib_selected]
        self._calib_boxes[param][0] += dx
        self._calib_boxes[param][1] += dy

    def _calib_resize(self, delta: int):
        if not self._calib_mode:
            return
        param = PAD_ORDER[self._calib_selected]
        self._calib_boxes[param][2] = max(5, self._calib_boxes[param][2] + delta)

    def _calib_save(self, _event=None):
        if not self._calib_mode:
            return
        src = CONFIG_PATH.read_text()

        # Update SQUARE_SIZE
        sz = self._calib_boxes[PAD_ORDER[self._calib_selected]][2]
        src = re.sub(r'SQUARE_SIZE\s*=\s*\d+', f'SQUARE_SIZE = {sz}', src)

        # Replace the entire PAD_POSITIONS block
        lines = ["PAD_POSITIONS = {\n"]
        for param in PAD_ORDER:
            x, y, _ = self._calib_boxes[param]
            lines.append(f'    "{param}": ({x}, {y}),\n')
        lines.append("}\n")
        new_block = "".join(lines)

        src = re.sub(
            r'PAD_POSITIONS\s*=\s*\{[^}]*\}',
            new_block.rstrip("\n"),
            src,
            flags=re.DOTALL,
        )

        CONFIG_PATH.write_text(src)

        # Also update PAD_ROIS in memory so analysis uses new positions immediately
        for param in PAD_ORDER:
            x, y, s = self._calib_boxes[param]
            PAD_ROIS[param] = (x, y, s, s)

        self._status_var.set("Saved to config.py")
        self.after(1500, lambda: self._status_var.set(
            "CALIB  1-4:select  WASD:move  Q/E:size  Enter:save  Tab:exit"
        ))

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