# ============================================================
# ui/osk.py — Built-in on-screen keyboard
# ============================================================
import tkinter as tk
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

_instance = None


class OnScreenKeyboard(tk.Frame):
    """
    Inline on-screen keyboard rendered as a Frame — no Toplevel,
    no focus stealing. Embed it in the screen layout and call
    show(entry) / hide() to activate it.
    """

    def __init__(self, parent, **kw):
        super().__init__(parent, bg=COLOR_BORDER, **kw)
        self._target = None
        self._upper  = False
        self._build()

    # ── Build ─────────────────────────────────────────────

    def _build(self):
        for w in self.winfo_children():
            w.destroy()

        rows = _ROWS_UPPER if self._upper else _ROWS_LOWER

        for row in rows:
            rf = tk.Frame(self, bg=COLOR_BORDER)
            rf.pack(pady=2, padx=4)

            for key in row:
                if key == "SPACE":
                    w, pad = 28, 4
                elif key in ("⌫", "⇧"):
                    w, pad = 5, 2
                else:
                    w, pad = 3, 2

                bg = COLOR_PANEL if key in ("⌫", "⇧", "SPACE") else COLOR_ACCENT
                label = "Space" if key == "SPACE" else key

                tk.Button(
                    rf,
                    text=label,
                    font=FONT_SMALL,
                    fg=COLOR_TEXT, bg=bg,
                    activebackground=COLOR_HIGHLIGHT,
                    activeforeground=COLOR_TEXT,
                    relief=tk.FLAT,
                    width=w, pady=6, padx=pad,
                    command=lambda k=key: self._press(k),
                ).pack(side=tk.LEFT, padx=2)

    # ── Key press ─────────────────────────────────────────

    def _press(self, key):
        if self._target is None:
            return

        t = self._target
        if key == "⌫":
            pos = t.index(tk.INSERT)
            if pos > 0:
                t.delete(pos - 1, pos)
        elif key == "SPACE":
            t.insert(tk.INSERT, " ")
        elif key == "⇧":
            self._upper = not self._upper
            self._build()
        else:
            t.insert(tk.INSERT, key)

    # ── Show / hide ───────────────────────────────────────

    def show(self, entry: tk.Entry):
        self._target = entry
        self.pack(side=tk.BOTTOM, fill=tk.X, pady=(4, 0))

    def hide(self):
        self._target = None
        self.pack_forget()


# ── Module-level helpers ──────────────────────────────────

def create(parent) -> OnScreenKeyboard:
    """Create and return an OnScreenKeyboard Frame (hidden by default)."""
    kb = OnScreenKeyboard(parent)
    kb.pack_forget()
    return kb


def attach(kb: OnScreenKeyboard, entry: tk.Entry):
    """Bind an Entry to show/hide the keyboard on focus."""
    entry.bind("<FocusIn>",  lambda _e: kb.show(entry), add="+")
    entry.bind("<Button-1>", lambda _e: kb.show(entry), add="+")
    entry.bind("<FocusOut>", lambda _e: _on_focus_out(kb, entry), add="+")


def _on_focus_out(kb: OnScreenKeyboard, entry: tk.Entry):
    # Delay check so clicking a key doesn't instantly hide the keyboard
    entry.after(150, lambda: _check_hide(kb, entry))


def _check_hide(kb: OnScreenKeyboard, entry: tk.Entry):
    try:
        focused = entry.focus_get()
    except Exception:
        focused = None

    # Hide only if focus left both the entry and the keyboard itself
    if focused is None or focused == entry:
        return
    focused_str = str(focused)
    if focused_str.startswith(str(kb)):
        return
    kb.hide()