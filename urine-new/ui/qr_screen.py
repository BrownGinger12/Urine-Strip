# ============================================================
# ui/qr_screen.py — QR code display for a single scan
# ============================================================
import tkinter as tk
from PIL import ImageTk

import database as db
from qr_utils import build_qr_text, generate_qr_image
from config import (
    COLOR_BG, COLOR_PANEL, COLOR_ACCENT, COLOR_BORDER,
    COLOR_HIGHLIGHT, COLOR_SUCCESS,
    COLOR_TEXT, COLOR_SUBTEXT,
    FONT_TITLE, FONT_BODY, FONT_SMALL, FONT_MONO,
    SCREEN_WIDTH, SCREEN_HEIGHT,
)
from ui.widgets import make_topbar, make_button


class QRScreen(tk.Frame):
    QR_SIZE = 340

    def __init__(self, parent: tk.Widget, app, scan_id: int, back_patient_id: int):
        super().__init__(parent, bg=COLOR_BG)
        self.app             = app
        self.scan_id         = scan_id
        self.back_patient_id = back_patient_id
        self.scan            = db.get_scan(scan_id)
        self._imgtk          = None
        self._build_ui()

    def _build_ui(self):
        if not self.scan:
            make_topbar(self, "QR Code", back_command=self._go_back)
            tk.Label(self, text="Record not found.",
                     fg=COLOR_SUBTEXT, bg=COLOR_BG, font=FONT_BODY).pack(pady=60)
            return

        patient_name = self.scan.get("patient_name", "Unknown")
        make_topbar(self, f"QR Code  -  {patient_name}", back_command=self._go_back)

        body = tk.Frame(self, bg=COLOR_BG)
        body.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Left: QR image
        left = tk.Frame(body, bg=COLOR_BG)
        left.pack(side=tk.LEFT, padx=(0, 20))
        self._qr_label = tk.Label(left, bg=COLOR_BG)
        self._qr_label.pack()
        self._render_qr()

        # Separator
        tk.Frame(body, bg=COLOR_BORDER, width=1).pack(side=tk.LEFT, fill=tk.Y)

        # Right: details
        right = tk.Frame(body, bg=COLOR_BG)
        right.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=20)
        self._build_details(right)

    def _build_details(self, parent):
        scan = self.scan
        tk.Label(parent, text="Scan Summary",
                 font=FONT_TITLE, fg=COLOR_TEXT, bg=COLOR_BG).pack(anchor="w", pady=(4, 12))

        details = [
            ("Patient",     scan.get("patient_name",      "—")),
            ("Date",        scan.get("scan_date",          "—")),
            ("",            ""),
            ("Glucose",     scan.get("glucose",            "---")),
            ("pH",          scan.get("ph",                 "---")),
            ("Sp. Gravity", scan.get("specific_gravity",   "---")),
            ("Protein",     scan.get("protein",            "---")),
        ]

        for label, value in details:
            if not label:
                tk.Frame(parent, bg=COLOR_BORDER, height=1).pack(fill=tk.X, pady=6)
                continue
            row = tk.Frame(parent, bg=COLOR_BG)
            row.pack(fill=tk.X, pady=3)
            tk.Label(row, text=f"{label}:", font=FONT_SMALL,
                     fg=COLOR_SUBTEXT, bg=COLOR_BG, anchor="w", width=12).pack(side=tk.LEFT)
            tk.Label(row, text=value, font=FONT_MONO,
                     fg=COLOR_TEXT, bg=COLOR_BG, anchor="w").pack(side=tk.LEFT)

        # Payload preview
        tk.Frame(parent, bg=COLOR_BORDER, height=1).pack(fill=tk.X, pady=(16, 6))
        tk.Label(parent, text="QR Payload:", font=FONT_SMALL,
                 fg=COLOR_SUBTEXT, bg=COLOR_BG, anchor="w").pack(anchor="w")

        payload = self._make_payload()
        tk.Label(parent, text=payload, font=("Courier", 9),
                 fg=COLOR_SUCCESS, bg=COLOR_BG,
                 justify="left", anchor="w").pack(anchor="w", padx=4)

    def _make_payload(self):
        scan = self.scan
        return build_qr_text(
            patient_name=scan.get("patient_name",      "—"),
            scan_date=scan.get("scan_date",             "—"),
            glucose=scan.get("glucose",                 "---"),
            ph=scan.get("ph",                           "---"),
            specific_gravity=scan.get("specific_gravity", "---"),
            protein=scan.get("protein",                 "---"),
        )

    def _render_qr(self):
        qr_img = generate_qr_image(self._make_payload())
        qr_img = qr_img.resize((self.QR_SIZE, self.QR_SIZE), resample=0)
        self._imgtk = ImageTk.PhotoImage(image=qr_img)
        self._qr_label.configure(image=self._imgtk)

    def _go_back(self):
        self.app.show_logs(self.back_patient_id)