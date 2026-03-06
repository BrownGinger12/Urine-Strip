# ============================================================
# ui/osk.py — Built-in on-screen keyboard for touchscreen kiosk
# ============================================================
import tkinter as tk
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from config import (
    COLOR_PANEL, COLOR_ACCENT, COLOR_BORDER,
    COLOR_HIGHLIGHT, COLOR_DANGER, COLOR_TEXT, COLOR_SUBTEXT,
    FONT_SMALL,
)

_ROWS_LOWER = [
    ["1","2","3","4","5","6","7","8","9","0","⌫"],
    ["q","w","e","r","t","y","u","i","o","p"],
    ["a","s","d","f","g","h","j","k","l","."],
    ["z","x","c","v","b","n","m",",","-","⇧"],
    ["SPACE"],
]
_ROWS_UPPER = [
    ["1","2","3","4","5","6","7","8","9","0","⌫"],
    ["Q","W","E","R","T","Y","U","I","O","P"],
    ["A","S","D","F","G","H","J","K","L","."],
    ["Z","X","C","V","B","N","M",",","-","⇧"],
    ["SPACE"],
]

# Singleton
_kb_instance = None


class _Keyboard(tk.Toplevel):
    def __init__(self, root: tk.Tk, target: tk.Entry):
        super().__init__(root)
        self._root   = root
        self._target = target
        self._upper  = False

        self.overrideredirect(True)
        self.attributes("-topmost", True)
        self.configure(bg=COLOR_BORDER)
        self.resizable(False, False)

        self._build()
        self.update_idletasks()
        self._place_bottom()


    # ── Layout ────────────────────────────────────────────

    def _build(self):
        for w in self.winfo_children():
            w.destroy()

        rows = _ROWS_UPPER if self._upper else _ROWS_LOWER
        for row in rows:
            rf = tk.Frame(self, bg=COLOR_BORDER)
            rf.pack(fill=tk.X, pady=3, padx=6)

            for key in row:
                if key == "SPACE":
                    w, h, label = 32, 2, "SPACE"
                    bg = "#2d3748"
                elif key == "⌫":
                    w, h, label = 6, 2, "⌫"
                    bg = "#4a3728"
                elif key == "⇧":
                    w, h, label = 6, 2, "⇧  SHIFT"
                    bg = "#2d3748"
                else:
                    w, h, label = 4, 2, key
                    bg = COLOR_ACCENT

                tk.Button(
                    rf,
                    text=label,
                    font=("Helvetica", 12, "bold"),
                    fg=COLOR_TEXT, bg=bg,
                    activebackground=COLOR_HIGHLIGHT,
                    activeforeground=COLOR_TEXT,
                    relief=tk.FLAT,
                    width=w, height=h,
                    command=lambda k=key: self._press(k),
                ).pack(side=tk.LEFT, padx=2)

        # Close bar at bottom
        bar = tk.Frame(self, bg="#0d1117")
        bar.pack(fill=tk.X, pady=(4, 0))
        tk.Button(
            bar, text="✕  Close Keyboard",
            font=("Helvetica", 10),
            fg=COLOR_TEXT, bg=COLOR_DANGER,
            activebackground="#c0392b",
            relief=tk.FLAT, pady=5,
            command=self._close,
        ).pack(fill=tk.X)

    # ── Position at absolute screen bottom ───────────────

    def _place_bottom(self):
        self.update_idletasks()
        kw = self.winfo_reqwidth()
        kh = self.winfo_reqheight()
        sw = self._root.winfo_screenwidth()
        sh = self._root.winfo_screenheight()
        x  = (sw - kw) // 2
        y  = sh - kh
        self.geometry(f"{kw}x{kh}+{x}+{y}")

    # ── Key press ─────────────────────────────────────────

    def _press(self, key):
        t = self._target
        if t is None:
            return
        if key == "⌫":
            pos = t.index(tk.INSERT)
            if pos > 0:
                t.delete(pos - 1, pos)
        elif key == "SPACE":
            t.insert(tk.INSERT, " ")
        elif key == "⇧":
            self._upper = not self._upper
            self._build()
            self._place_bottom()
        else:
            t.insert(tk.INSERT, key)
        # Return focus to the entry after every keypress
        self._root.after(10, t.focus_set)


    def _close(self):
        global _kb_instance
        _kb_instance = None
        self.destroy()

    def set_target(self, entry: tk.Entry):
        self._target = entry


# ── Public API ────────────────────────────────────────────

def init(root):
    """Called by app.py — nothing to do, keyboard is lazy-created."""
    pass


def show(root: tk.Tk, entry: tk.Entry):
    """Show the keyboard targeting the given entry."""
    global _kb_instance
    if _kb_instance is not None:
        try:
            # Already open — just retarget it
            _kb_instance.set_target(entry)
            _kb_instance.lift()
            return
        except tk.TclError:
            _kb_instance = None
    _kb_instance = _Keyboard(root, entry)


def hide():
    global _kb_instance
    if _kb_instance is not None:
        try:
            _kb_instance.destroy()
        except Exception:
            pass
        _kb_instance = None


def attach(entry: tk.Entry, root: tk.Tk = None):
    """
    Wire an Entry to auto-show the keyboard on tap/focus.
    Pass root explicitly or it will be resolved from the entry.
    """
    def _show(_e=None):
        r = root or entry.winfo_toplevel()
        show(r, entry)

    entry.bind("<FocusIn>",  _show, add="+")
    entry.bind("<Button-1>", _show, add="+")