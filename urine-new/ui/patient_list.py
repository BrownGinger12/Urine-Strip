# ============================================================
# ui/patient_list.py — Patient directory screen
# ============================================================
import tkinter as tk

import database as db
from config import (
    COLOR_BG, COLOR_PANEL, COLOR_ACCENT, COLOR_BORDER,
    COLOR_HIGHLIGHT, COLOR_SUCCESS, COLOR_DANGER,
    COLOR_TEXT, COLOR_SUBTEXT, COLOR_ROW_ALT,
    FONT_TITLE, FONT_BODY, FONT_SMALL,
    SCREEN_WIDTH,
)
from ui.widgets import make_topbar, make_button, ModalDialog, ConfirmDialog, ScrollFrame
from ui import osk


class PatientListScreen(tk.Frame):
    """
    Main screen: searchable table of patients with
    [View Logs] and [New Scan] per row, plus [+ Add Patient].
    """

    ROW_HEIGHT = 48

    def __init__(self, parent: tk.Widget, app):
        super().__init__(parent, bg=COLOR_BG)
        self.app = app
        self._search_var = tk.StringVar()
        self._search_var.trace_add("write", lambda *_: self._load())
        self._build_ui()
        self._load()

    # ── Layout ───────────────────────────────────────────

    def _build_ui(self):
        # ── Top bar ──
        bar = make_topbar(self, "🔬  Urine Analyzer")

        # Search widget placed inside the bar after creation
        search_frame = tk.Frame(bar, bg=COLOR_ACCENT)
        search_frame.pack(side=tk.RIGHT, padx=14, pady=8)

        tk.Label(search_frame, text="Search:", fg=COLOR_SUBTEXT,
                 bg=COLOR_ACCENT, font=FONT_SMALL).pack(side=tk.LEFT, padx=(0, 4))
        search_entry = tk.Entry(
            search_frame, textvariable=self._search_var,
            font=FONT_BODY, width=20,
            bg=COLOR_PANEL, fg=COLOR_TEXT,
            insertbackground=COLOR_TEXT,
            relief=tk.FLAT, bd=4,
        )
        search_entry.pack(side=tk.LEFT)

        # ── Column header ──
        col_bar = tk.Frame(self, bg=COLOR_PANEL, height=30)
        col_bar.pack(fill=tk.X)
        col_bar.pack_propagate(False)

        for text, anchor, width in [
            ("Patient Name", "w", 34),
            ("Date Added",   "w", 18),
            ("Actions",      "w", 20),
        ]:
            tk.Label(
                col_bar, text=text, fg=COLOR_SUBTEXT, bg=COLOR_PANEL,
                font=FONT_SMALL, anchor=anchor, width=width,
            ).pack(side=tk.LEFT, padx=(14, 0), pady=4)

        # ── Scrollable list ──
        self._scroll = ScrollFrame(self, bg=COLOR_BG)
        self._scroll.pack(fill=tk.BOTH, expand=True)

        osk.attach(search_entry, self.app)

        # ── Footer ──
        footer = tk.Frame(self, bg=COLOR_ACCENT, height=54)
        footer.pack(fill=tk.X, side=tk.BOTTOM)
        footer.pack_propagate(False)

        make_button(
            footer, "+ Add New Patient", self._add_patient,
            bg=COLOR_HIGHLIGHT, pady=8,
        ).pack(pady=8)

    # ── Data loading ─────────────────────────────────────

    def _load(self):
        inner = self._scroll.inner
        for w in inner.winfo_children():
            w.destroy()

        patients = db.get_all_patients(self._search_var.get())

        if not patients:
            tk.Label(
                inner,
                text="No patients found.  Add a new patient to get started.",
                fg=COLOR_SUBTEXT, bg=COLOR_BG, font=FONT_BODY,
            ).pack(pady=50)
            return

        for i, p in enumerate(patients):
            self._make_row(inner, p, i)

    def _make_row(self, parent: tk.Widget, patient: dict, idx: int):
        bg = COLOR_PANEL if idx % 2 == 0 else COLOR_ROW_ALT

        row = tk.Frame(parent, bg=bg, height=self.ROW_HEIGHT)
        row.pack(fill=tk.X)
        row.pack_propagate(False)

        # Separator line
        tk.Frame(row, bg=COLOR_BORDER, height=1).place(
            relx=0, rely=0, relwidth=1
        )

        # Name
        tk.Label(
            row, text=patient["name"],
            fg=COLOR_TEXT, bg=bg, font=FONT_BODY,
            anchor="w", width=32,
        ).pack(side=tk.LEFT, padx=(14, 0), pady=10)

        # Date
        date_str = (patient.get("created_at") or "")[:10] or "—"
        tk.Label(
            row, text=date_str,
            fg=COLOR_SUBTEXT, bg=bg, font=FONT_SMALL,
            anchor="w", width=16,
        ).pack(side=tk.LEFT, pady=10)

        # Action buttons
        btns = tk.Frame(row, bg=bg)
        btns.pack(side=tk.LEFT, pady=8)

        pid = patient["id"]

        make_button(
            btns, "View Logs",
            lambda p=pid: self.app.show_logs(p),
            bg=COLOR_ACCENT, padx=10, pady=4, font=FONT_SMALL,
        ).pack(side=tk.LEFT, padx=4)

        make_button(
            btns, "▶  Scan",
            lambda p=pid: self.app.show_scan(p),
            bg=COLOR_SUCCESS, padx=10, pady=4, font=FONT_SMALL,
        ).pack(side=tk.LEFT, padx=4)

        make_button(
            btns, "✕",
            lambda p=pid, n=patient["name"]: self._delete_patient(p, n),
            bg=COLOR_DANGER, padx=8, pady=4, font=FONT_SMALL,
        ).pack(side=tk.LEFT, padx=4)

    # ── Actions ──────────────────────────────────────────

    def _add_patient(self):
        dlg = ModalDialog(self.app, "New Patient", "Enter patient's full name:")
        if not dlg.result:
            return
        name = dlg.result.strip()
        if not name:
            return
        if db.patient_exists(name):
            ConfirmDialog(self.app, "Duplicate",
                          f'A patient named "{name}" already exists.')
            return
        db.add_patient(name)
        self._load()

    def _delete_patient(self, patient_id: int, name: str):
        dlg = ConfirmDialog(self.app, "Delete Patient",
                            f'Delete "{name}" and all their scan records? This cannot be undone.')
        if dlg.result:
            db.delete_patient(patient_id)
            self._load()