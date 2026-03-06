# ============================================================
# ui/osk.py — Full-width mobile-style on-screen keyboard
# ============================================================
import tkinter as tk
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from config import COLOR_HIGHLIGHT

BG_KB      = "#1a2b3c"
BG_KEY     = "#2e4057"
BG_SPECIAL = "#1e3048"
BG_SPACE   = "#2e4057"
FG_KEY     = "#ffffff"
FG_DIM     = "#aabbcc"
RADIUS     = 8
KEY_H      = 56
KEY_PAD    = 6

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


def _rounded_btn(parent, text, width, height, bg, fg, font, command):
    cv = tk.Canvas(parent, width=width, height=height,
                   bg=parent["bg"], highlightthickness=0, cursor="hand2")

    def _draw(color):
        cv.delete("all")
        r = min(RADIUS, width // 2, height // 2)
        x1, y1, x2, y2 = 1, 1, width - 1, height - 1
        cv.create_polygon(
            x1+r, y1, x2-r, y1, x2, y1+r,
            x2, y2-r, x2-r, y2, x1+r, y2,
            x1, y2-r, x1, y1+r,
            fill=color, smooth=True
        )
        cv.create_text(width // 2, height // 2,
                       text=text, fill=fg, font=font)

    _draw(bg)
    cv.bind("<ButtonPress-1>",   lambda e: _draw(COLOR_HIGHLIGHT))
    cv.bind("<ButtonRelease-1>", lambda e: (_draw(bg), command()))
    return cv


class _Keyboard(tk.Toplevel):
    def __init__(self, root: tk.Tk, target: tk.Entry):
        super().__init__(root)
        self._root   = root
        self._target = target
        self._upper  = False

        self.overrideredirect(True)
        self.attributes("-topmost", True)
        self.configure(bg=BG_KB)
        self.resizable(False, False)

        # Get screen width NOW — use it for all sizing
        self._sw = root.winfo_screenwidth()
        self._sh = root.winfo_screenheight()

        self._build()
        self.update_idletasks()
        self._place_bottom()

    def _key_width(self, row_len):
        """Calculate key width so the row fills the full screen width."""
        total_pad = KEY_PAD * (row_len + 1)
        return (self._sw - total_pad) // row_len

    def _build(self):
        for w in self.winfo_children():
            w.destroy()

        # ── Top bar ──
        top = tk.Frame(self, bg=BG_KB, width=self._sw)
        top.pack(fill=tk.X, padx=KEY_PAD, pady=(6, 2))

        tk.Label(top, text="Keyboard", font=("Helvetica", 9),
                 fg="#8899aa", bg=BG_KB).pack(side=tk.LEFT)

        _rounded_btn(
            top, "✕", 36, 26,
            bg="#c0392b", fg=FG_KEY,
            font=("Helvetica", 11, "bold"),
            command=self._close,
        ).pack(side=tk.RIGHT)

        # ── Letter rows ──
        rows = _ROWS_UPPER if self._upper else _ROWS_LOWER

        for row in rows:
            kw = self._key_width(len(row))
            rf = tk.Frame(self, bg=BG_KB, width=self._sw)
            rf.pack(fill=tk.X, pady=KEY_PAD // 2, padx=KEY_PAD)
            for key in row:
                if key in ("⇧", "⌫"):
                    bg   = BG_SPECIAL
                    font = ("Helvetica", 18)
                else:
                    bg   = BG_KEY
                    font = ("Helvetica", 16, "bold")

                _rounded_btn(
                    rf, key, kw, KEY_H,
                    bg=bg, fg=FG_KEY, font=font,
                    command=lambda k=key: self._press(k),
                ).pack(side=tk.LEFT, padx=KEY_PAD // 2)

        # ── Space row ──
        sr = tk.Frame(self, bg=BG_KB, width=self._sw)
        sr.pack(fill=tk.X, pady=(KEY_PAD // 2, KEY_PAD), padx=KEY_PAD)
        space_w = self._sw - KEY_PAD * 2
        _rounded_btn(
            sr, "space", space_w, KEY_H,
            bg=BG_SPACE, fg=FG_DIM,
            font=("Helvetica", 14),
            command=lambda: self._press("SPACE"),
        ).pack(side=tk.LEFT)

    def _place_bottom(self):
        self.update_idletasks()
        kh = self.winfo_reqheight()
        self.geometry(f"{self._sw}x{kh}+0+{self._sh - kh}")

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
            # Defer rebuild — we are inside a canvas event handler;
            # destroying widgets immediately causes a silent failure
            self._root.after(0, self._rebuild_shift)
            return
        else:
            t.insert(tk.INSERT, key)
        self._root.after(10, t.focus_set)

    def _rebuild_shift(self):
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