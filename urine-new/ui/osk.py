# ============================================================
# ui/osk.py — Full-width on-screen keyboard
# ============================================================
import tkinter as tk
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from config import COLOR_HIGHLIGHT

BG_KB      = "#1a2b3c"
BG_KEY     = "#2e4057"
BG_SPECIAL = "#1e3048"
FG_KEY     = "#ffffff"
FG_DIM     = "#aabbcc"
KEY_H      = 48
KEY_PAD    = 5

_ROWS_LOWER = [
    ["q","w","e","r","t","y","u","i","o","p"],
    ["a","s","d","f","g","h","j","k","l"],
    ["⇧","z","x","c","v","b","n","m","⌫"],
]
_ROWS_UPPER = [
    ["Q","W","E","R","T","Y","U","I","O","P"],
    ["A","S","D","F","G","H","J","K","L"],
    ["⇧","Z","X","C","V","B","N","M","⌫"],
]

_kb_instance = None


class _Keyboard(tk.Toplevel):
    def __init__(self, root: tk.Tk, target: tk.Entry):
        super().__init__(root)
        self._app   = root
        self._target = target
        self._upper  = False

        self.overrideredirect(True)
        self.attributes("-topmost", True)
        self.configure(bg=BG_KB)
        self.resizable(False, False)

        self._sw = root.winfo_screenwidth()
        self._sh = root.winfo_screenheight()

        self._build()
        self.update_idletasks()
        self._place_bottom()

    # ── Build all keys ────────────────────────────────────

    def _build(self):
        for w in self.winfo_children():
            w.destroy()

        rows = _ROWS_UPPER if self._upper else _ROWS_LOWER

        # Top bar
        top = tk.Frame(self, bg=BG_KB)
        top.pack(fill=tk.X, padx=KEY_PAD, pady=(4, 2))
        tk.Label(top, text="Keyboard", font=("Helvetica", 9),
                 fg="#8899aa", bg=BG_KB).pack(side=tk.LEFT)
        tk.Button(
            top, text="✕ Close",
            font=("Helvetica", 10, "bold"),
            fg=FG_KEY, bg="#c0392b",
            activebackground="#e74c3c",
            relief=tk.FLAT, padx=10, pady=4,
            command=self._close,
        ).pack(side=tk.RIGHT)

        # Letter rows
        for row in rows:
            kw = (self._sw - KEY_PAD * (len(row) + 1)) // len(row)
            rf = tk.Frame(self, bg=BG_KB)
            rf.pack(fill=tk.X, pady=KEY_PAD // 2, padx=KEY_PAD)
            for key in row:
                bg   = BG_SPECIAL if key in ("⇧", "⌫") else BG_KEY
                font = ("Helvetica", 15) if key in ("⇧", "⌫") else ("Helvetica", 15, "bold")
                k = key
                cell = tk.Frame(rf, width=kw, height=KEY_H, bg=bg)
                cell.pack_propagate(False)
                cell.pack(side=tk.LEFT, padx=KEY_PAD // 2)
                tk.Button(
                    cell, text=key,
                    font=font, fg=FG_KEY, bg=bg,
                    activebackground=COLOR_HIGHLIGHT,
                    activeforeground=FG_KEY,
                    relief=tk.FLAT, bd=0,
                    command=lambda _k=k: self._press(_k),
                ).place(relwidth=1, relheight=1)

        # Space bar
        sr = tk.Frame(self, bg=BG_KB)
        sr.pack(fill=tk.X, pady=(KEY_PAD // 2, KEY_PAD), padx=KEY_PAD)
        tk.Button(
            sr, text="space",
            font=("Helvetica", 14), fg=FG_DIM, bg=BG_KEY,
            activebackground=COLOR_HIGHLIGHT,
            activeforeground=FG_KEY,
            relief=tk.FLAT, bd=0,
            command=lambda: self._press("SPACE"),
        ).pack(fill=tk.X)

    # ── Position at screen bottom ─────────────────────────

    def _place_bottom(self):
        self.update_idletasks()
        kh = self.winfo_reqheight()
        self.geometry(f"{self._sw}x{kh}+0+{self._sh - kh}")

    # ── Key press ─────────────────────────────────────────

    def _press(self, key):
        if key == "⇧":
            self._upper = not self._upper
            # Use after(1) so the button click event fully completes
            # before we destroy and recreate all widgets
            self.after(1, self._rebuild)
            return

        t = self._target
        if t is None:
            return
        if key == "⌫":
            pos = t.index(tk.INSERT)
            if pos > 0:
                t.delete(pos - 1, pos)
        elif key == "SPACE":
            t.insert(tk.INSERT, " ")
        else:
            t.insert(tk.INSERT, key)
        self._app.after(10, t.focus_set)

    def _rebuild(self):
        self._build()
        self._place_bottom()

    def _close(self):
        global _kb_instance
        _kb_instance = None
        try:
            self.destroy()
        except Exception:
            pass

    def set_target(self, entry: tk.Entry):
        self._target = entry


# ── Public API ────────────────────────────────────────────

def init(root):
    pass


def show(root: tk.Tk, entry: tk.Entry):
    global _kb_instance
    if _kb_instance is not None:
        try:
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
    def _show(_e=None):
        r = root or entry.winfo_toplevel()
        show(r, entry)
    entry.bind("<FocusIn>",  _show, add="+")
    entry.bind("<Button-1>", _show, add="+")