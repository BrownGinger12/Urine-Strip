# ============================================================
# ui/app.py — Root Tk window + screen-navigation controller
# ============================================================
import tkinter as tk
import database as db
from config import SCREEN_WIDTH, SCREEN_HEIGHT, COLOR_BG


class App(tk.Tk):
    """
    Main application window.
    Owns the "stage" – a single Frame slot that is swapped when
    navigating between screens.  Each screen receives a reference
    to `self` so it can call navigation methods.
    """

    def __init__(self):
        super().__init__()
        self.title("Urine Analyzer")
        self.configure(bg=COLOR_BG)
        self.resizable(False, False)
        self.attributes("-fullscreen", True)

        # Initialise database schema
        db.init_db()


        # The active screen widget
        self._current: tk.Widget | None = None

        # Start on the patient list
        self.show_patient_list()

    # ── Navigation helpers ───────────────────────────────

    def _swap(self, widget: tk.Widget) -> None:
        """Destroy the current screen and install a new one."""
        if self._current is not None:
            # Give screens a chance to release resources (camera, etc.)
            if hasattr(self._current, "cleanup"):
                self._current.cleanup()
            self._current.destroy()
        self._current = widget
        self._current.pack(fill=tk.BOTH, expand=True)

    def show_patient_list(self) -> None:
        from ui.patient_list import PatientListScreen
        self._swap(PatientListScreen(self, self))

    def show_scan(self, patient_id: int) -> None:
        from ui.scan_screen import ScanScreen
        self._swap(ScanScreen(self, self, patient_id))

    def show_logs(self, patient_id: int) -> None:
        from ui.log_list import LogListScreen
        self._swap(LogListScreen(self, self, patient_id))

    def show_qr(self, scan_id: int, back_patient_id: int) -> None:
        from ui.qr_screen import QRScreen
        self._swap(QRScreen(self, self, scan_id, back_patient_id))