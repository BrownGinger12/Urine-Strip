# ============================================================
# ui/log_list.py — Patient scan-log browser
# ============================================================
import tkinter as tk
from tkinter import messagebox

import database as db
from config import (
    COLOR_BG, COLOR_PANEL, COLOR_ACCENT, COLOR_BORDER,
    COLOR_HIGHLIGHT, COLOR_SUCCESS, COLOR_DANGER,
    COLOR_TEXT, COLOR_SUBTEXT, COLOR_ROW_ALT,
    FONT_TITLE, FONT_BODY, FONT_SMALL, FONT_MONO,
)
from ui.widgets import make_topbar, make_button, ScrollFrame


class LogListScreen(tk.Frame):
    ROW_HEIGHT = 52

    def __init__(self, parent: tk.Widget, app, patient_id: int):
        super().__init__(parent, bg=COLOR_BG)
        self.app        = app
        self.patient_id = patient_id
        self.patient    = db.get_patient(patient_id)
        self._build_ui()
        self._load()

    # ── Layout ───────────────────────────────────────────

    def _build_ui(self):
        name = self.patient["name"] if self.patient else "—"

        scan_btn = make_button(
            self, "▶  New Scan",
            command=lambda: self.app.show_scan(self.patient_id),
            bg=COLOR_SUCCESS, pady=4,
        )
        make_topbar(
            self, f"Logs:  {name}",
            back_command=lambda: self.app.show_patient_list(),
            right_widget=scan_btn,
        )

        # Column headers — pixel widths must match _make_row cell() widths exactly
        col_bar = tk.Frame(self, bg=COLOR_PANEL, height=30)
        col_bar.pack(fill=tk.X)
        col_bar.pack_propagate(False)

        headers = [
            ("Date & Time",  160),
            ("Glucose",       90),
            ("pH",            60),
            ("Sp. Gravity",  105),
            ("Protein",       80),
            ("Actions",      165),
        ]
        for text, width in headers:
            f = tk.Frame(col_bar, bg=COLOR_PANEL, width=width)
            f.pack(side=tk.LEFT, fill=tk.Y)
            f.pack_propagate(False)
            tk.Label(f, text=text, fg=COLOR_SUBTEXT, bg=COLOR_PANEL,
                     font=FONT_SMALL, anchor="w").pack(side=tk.LEFT, padx=8, pady=4)

        self._scroll = ScrollFrame(self, bg=COLOR_BG)
        self._scroll.pack(fill=tk.BOTH, expand=True)

        self._count_var = tk.StringVar(value="")
        tk.Label(
            self, textvariable=self._count_var,
            font=FONT_SMALL, fg=COLOR_SUBTEXT, bg=COLOR_ACCENT,
            anchor="e", pady=4,
        ).pack(fill=tk.X, side=tk.BOTTOM)

    # ── Data loading ─────────────────────────────────────

    def _load(self):
        inner = self._scroll.inner
        for w in inner.winfo_children():
            w.destroy()

        scans = db.get_patient_scans(self.patient_id)
        self._count_var.set(f"  {len(scans)} record(s)  ")

        if not scans:
            tk.Label(
                inner,
                text='No scans recorded yet. Use "New Scan" to start.',
                fg=COLOR_SUBTEXT, bg=COLOR_BG, font=FONT_BODY,
            ).pack(pady=50)
            return

        for i, scan in enumerate(scans):
            self._make_row(inner, scan, i)

    def _make_row(self, parent: tk.Widget, scan: dict, idx: int):
        bg = COLOR_PANEL if idx % 2 == 0 else COLOR_ROW_ALT
        scan_id = scan["id"]

        row = tk.Frame(parent, bg=bg, height=self.ROW_HEIGHT)
        row.pack(fill=tk.X)
        row.pack_propagate(False)

        tk.Frame(row, bg=COLOR_BORDER, height=1).place(relx=0, rely=0, relwidth=1)

        # Fixed-width cells using Frame containers
        def cell(text, width, font=FONT_BODY, fg=COLOR_TEXT):
            f = tk.Frame(row, bg=bg, width=width)
            f.pack(side=tk.LEFT, fill=tk.Y)
            f.pack_propagate(False)
            tk.Label(f, text=text, fg=fg, bg=bg, font=font,
                     anchor="w").pack(side=tk.LEFT, padx=8, pady=0)

        cell(scan.get("scan_date", "—"),           160, font=FONT_MONO, fg=COLOR_SUBTEXT)
        cell(scan.get("glucose",   "---"),          90)
        cell(scan.get("ph",        "---"),          60)
        cell(scan.get("specific_gravity", "---"),  105)
        cell(scan.get("protein",   "---"),          80)

        # Action buttons in a fixed-width frame
        btn_frame = tk.Frame(row, bg=bg, width=165)
        btn_frame.pack(side=tk.LEFT, fill=tk.Y)
        btn_frame.pack_propagate(False)

        make_button(
            btn_frame, "🔍 QR",
            command=lambda sid=scan_id: self.app.show_qr(sid, self.patient_id),
            bg=COLOR_HIGHLIGHT, padx=8, pady=3, font=FONT_SMALL,
        ).pack(side=tk.LEFT, padx=(6, 4), pady=10)

        make_button(
            btn_frame, "🗑 Delete",
            command=lambda sid=scan_id: self._delete_scan(sid),
            bg=COLOR_DANGER, padx=8, pady=3, font=FONT_SMALL,
        ).pack(side=tk.LEFT, padx=(0, 6), pady=10)

    # ── Actions ──────────────────────────────────────────

    def _delete_scan(self, scan_id: int):
        if messagebox.askyesno(
            "Delete Scan",
            "Delete this scan record? This cannot be undone.",
            parent=self.app,
        ):
            db.delete_scan(scan_id)
            self._load()