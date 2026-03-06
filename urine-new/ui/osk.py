# ============================================================
# ui/osk.py — Mobile-style on-screen keyboard
# ============================================================
import tkinter as tk
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from config import COLOR_TEXT, COLOR_HIGHLIGHT

# ── Palette (iOS/Android inspired) ───────────────────────
BG_KB      = "#1a2b3c"   # keyboard background
BG_KEY     = "#2e4057"   # normal key
BG_SPECIAL = "#1e3048"   # shift, backspace
BG_SPACE   = "#2e4057"   # space bar
BG_ENTER   = "#3a7bd5"   # enter key
FG_KEY     = "#ffffff"
RADIUS     = 8           # corner radius (px) — drawn with Canvas

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

KEY_W  = 62   # normal key width
KEY_H  = 52   # normal key height
KEY_PAD = 5   # gap between keys

_kb_instance = None


# ── Rounded-rectangle key button ─────────────────────────

def _rounded_btn(parent, text, width, height, bg, fg, font, command):
    """A button drawn on a Canvas with rounded corners."""
    cv = tk.Canvas(parent, width=width, height=height,
                   bg=parent["bg"], highlightthickness=0, cursor="hand2")

    def _draw(color):
        cv.delete("all")
        r = RADIUS
        x1, y1, x2, y2 = 0, 0, width, height
        cv.create_polygon(
            x1+r, y1,
            x2-r, y1,
            x2,   y1+r,
            x2,   y2-r,
            x2-r, y2,
            x1+r, y2,
            x1,   y2-r,
            x1,   y1+r,
            fill=color, smooth=True
        )
        cv.create_text(width//2, height//2, text=text,
                       fill=fg, font=font)

    _draw(bg)
    cv.bind("<ButtonPress-1>",   lambda e: _draw(COLOR_HIGHLIGHT))
    cv.bind("<ButtonRelease-1>", lambda e: (_draw(bg), command()))
    return cv


# ── Keyboard Toplevel ─────────────────────────────────────

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

        self._build()
        self.update_idletasks()
        self._place_bottom()

    # ── Build ─────────────────────────────────────────────

    def _build(self):
        for w in self.winfo_children():
            w.destroy()

        # ── Top bar: title + close button ──
        top = tk.Frame(self, bg=BG_KB)
        top.pack(fill=tk.X, padx=8, pady=(6, 2))

        tk.Label(top, text="Keyboard", font=("Helvetica", 9),
                 fg="#8899aa", bg=BG_KB).pack(side=tk.LEFT)

        # Small close button top-right
        close_cv = _rounded_btn(
            top, "✕", 32, 24,
            bg="#c0392b", fg=FG_KEY,
            font=("Helvetica", 10, "bold"),
            command=self._close,
        )
        close_cv.pack(side=tk.RIGHT)

        rows = _ROWS_UPPER if self._upper else _ROWS_LOWER

        # ── Letter rows ──
        for row in rows:
            rf = tk.Frame(self, bg=BG_KB)
            rf.pack(pady=KEY_PAD//2, padx=8)

            for key in row:
                if key == "⇧":
                    w, bg, font = KEY_W + 14, BG_SPECIAL, ("Helvetica", 16)
                    label = "⇧"
                elif key == "⌫":
                    w, bg, font = KEY_W + 14, BG_SPECIAL, ("Helvetica", 14)
                    label = "⌫"
                else:
                    w, bg, font = KEY_W, BG_KEY, ("Helvetica", 16, "bold")
                    label = key

                btn = _rounded_btn(
                    rf, label, w, KEY_H,
                    bg=bg, fg=FG_KEY, font=font,
                    command=lambda k=key: self._press(k),
                )
                btn.pack(side=tk.LEFT, padx=KEY_PAD//2)

        # ── Bottom row: space + enter ──
        br = tk.Frame(self, bg=BG_KB)
        br.pack(pady=(KEY_PAD//2, 8), padx=8)

        # Total width calculation for space bar
        total = sum(KEY_W + KEY_PAD for _ in rows[0]) - KEY_PAD
        space_w = total - (KEY_W + 20) - KEY_PAD * 2

        _rounded_btn(br, "space", space_w, KEY_H,
                     bg=BG_SPACE, fg="#aabbcc",
                     font=("Helvetica", 14),
                     command=lambda: self._press("SPACE"),
                     ).pack(side=tk.LEFT, padx=KEY_PAD//2)

        _rounded_btn(br, "Enter", KEY_W + 20, KEY_H,
                     bg=BG_ENTER, fg=FG_KEY,
                     font=("Helvetica", 13, "bold"),
                     command=lambda: self._press("ENTER"),
                     ).pack(side=tk.LEFT, padx=KEY_PAD//2)

    # ── Position at screen bottom ─────────────────────────

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
        elif key == "ENTER":
            t.event_generate("<Return>")
        elif key == "⇧":
            self._upper = not self._upper
            self._build()
            self._place_bottom()
        else:
            t.insert(tk.INSERT, key)
        self._root.after(10, t.focus_set)

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