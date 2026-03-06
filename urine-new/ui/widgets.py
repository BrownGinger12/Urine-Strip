# ============================================================
# ui/widgets.py — Reusable Tkinter widget helpers
# ============================================================
import tkinter as tk
from config import (
    COLOR_BG, COLOR_PANEL, COLOR_ACCENT, COLOR_BORDER,
    COLOR_HIGHLIGHT, COLOR_DANGER, COLOR_SUCCESS,
    COLOR_TEXT, COLOR_SUBTEXT,
    FONT_TITLE, FONT_BODY, FONT_SMALL,
)
from ui import osk


# ── Top bar ──────────────────────────────────────────────

def make_topbar(
    parent: tk.Widget,
    title: str,
    back_command=None,
    right_widget: tk.Widget | None = None,
    height: int = 48,
) -> tk.Frame:
    bar = tk.Frame(parent, bg=COLOR_ACCENT, height=height)
    bar.pack(fill=tk.X)
    bar.pack_propagate(False)

    if back_command:
        btn = tk.Button(
            bar, text="◀  Back",
            font=FONT_SMALL, fg=COLOR_TEXT, bg=COLOR_ACCENT,
            activebackground=COLOR_PANEL, activeforeground=COLOR_TEXT,
            relief=tk.FLAT, cursor="hand2", padx=12,
            command=back_command,
        )
        btn.pack(side=tk.LEFT, pady=6)

    tk.Label(
        bar, text=title,
        font=FONT_TITLE, fg=COLOR_TEXT, bg=COLOR_ACCENT,
    ).pack(side=tk.LEFT, padx=8, pady=6)

    if right_widget:
        right_widget.pack(side=tk.RIGHT, padx=10, pady=6)

    return bar


# ── Styled button ────────────────────────────────────────

def make_button(
    parent: tk.Widget,
    text: str,
    command,
    bg: str = COLOR_HIGHLIGHT,
    fg: str = COLOR_TEXT,
    font=FONT_BODY,
    padx: int = 18,
    pady: int = 6,
    width: int | None = None,
) -> tk.Button:
    kw = dict(
        text=text, command=command,
        font=font, fg=fg, bg=bg,
        activebackground=bg, activeforeground=fg,
        relief=tk.FLAT, cursor="hand2",
        padx=padx, pady=pady,
    )
    if width:
        kw["width"] = width
    return tk.Button(parent, **kw)


# ── Input dialog ─────────────────────────────────────────

class ModalDialog(tk.Toplevel):
    """
    Dark-themed blocking text-input dialog.
    Usage:
        dlg = ModalDialog(root, "New Patient", "Enter full name:")
        if dlg.result:
            ...
    """

    def __init__(self, parent: tk.Widget, title: str, prompt: str):
        super().__init__(parent)
        self.result: str | None = None

        self.title(title)
        self.configure(bg=COLOR_PANEL)
        self.resizable(False, False)
        self.transient(parent)

        # Centre over screen
        w, h = 380, 180
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        self.geometry(f"{w}x{h}+{(sw - w)//2}+{sh // 6}")

        # Prompt
        tk.Label(self, text=prompt, font=FONT_BODY,
                 fg=COLOR_TEXT, bg=COLOR_PANEL).pack(pady=(24, 8))

        # Entry
        self._var = tk.StringVar()
        entry = tk.Entry(
            self, textvariable=self._var,
            font=FONT_BODY, width=28,
            bg=COLOR_ACCENT, fg=COLOR_TEXT,
            insertbackground=COLOR_TEXT,
            relief=tk.FLAT, bd=6,
        )
        entry.pack(padx=20)
        entry.bind("<Return>",  lambda _e: self._ok())
        entry.bind("<Escape>",  lambda _e: self._cancel())

        # Buttons
        btn_row = tk.Frame(self, bg=COLOR_PANEL)
        btn_row.pack(pady=14)
        make_button(btn_row, "Add",    self._ok,     bg=COLOR_HIGHLIGHT).pack(side=tk.LEFT, padx=6)
        make_button(btn_row, "Cancel", self._cancel, bg=COLOR_DANGER).pack(side=tk.LEFT, padx=6)

        # Must grab + raise AFTER geometry is set
        osk.attach(entry, self)

        self.update_idletasks()
        self.grab_set()
        entry.focus_set()

        self.wait_window(self)

    def _ok(self):
        v = self._var.get().strip()
        if v:
            self.result = v
            self.destroy()

    def _cancel(self):
        self.destroy()


# ── Confirm dialog (replaces messagebox.askyesno) ────────

class ConfirmDialog(tk.Toplevel):
    """
    Dark-themed Yes/No confirmation dialog.
    Usage:
        dlg = ConfirmDialog(root, "Delete?", "Are you sure?")
        if dlg.result:
            ...
    """

    def __init__(self, parent: tk.Widget, title: str, message: str):
        super().__init__(parent)
        self.result: bool = False

        self.title(title)
        self.configure(bg=COLOR_PANEL)
        self.resizable(False, False)
        self.transient(parent)

        w, h = 380, 160
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        self.geometry(f"{w}x{h}+{(sw - w)//2}+{sh // 6}")

        # Message
        tk.Label(self, text=message, font=FONT_BODY,
                 fg=COLOR_TEXT, bg=COLOR_PANEL,
                 wraplength=340, justify="center").pack(pady=(24, 12))

        # Buttons
        btn_row = tk.Frame(self, bg=COLOR_PANEL)
        btn_row.pack()
        make_button(btn_row, "Yes", self._yes, bg=COLOR_DANGER).pack(side=tk.LEFT, padx=8)
        make_button(btn_row, "No",  self._no,  bg=COLOR_ACCENT).pack(side=tk.LEFT, padx=8)

        self.update_idletasks()
        self.grab_set()
        self.focus_set()
        self.bind("<Return>", lambda _e: self._yes())
        self.bind("<Escape>", lambda _e: self._no())

        self.wait_window(self)

    def _yes(self):
        self.result = True
        self.destroy()

    def _no(self):
        self.destroy()


# ── Scrollable frame ─────────────────────────────────────

class ScrollFrame(tk.Frame):
    """A Frame with a vertical scrollbar and an inner Frame for children."""

    def __init__(self, parent: tk.Widget, bg: str = COLOR_BG, **kw):
        super().__init__(parent, bg=bg, **kw)

        self._canvas = tk.Canvas(self, bg=bg, highlightthickness=0)
        scrollbar = tk.Scrollbar(self, orient="vertical",
                                  command=self._canvas.yview)
        self.inner = tk.Frame(self._canvas, bg=bg)

        self.inner.bind(
            "<Configure>",
            lambda _e: self._canvas.configure(
                scrollregion=self._canvas.bbox("all")
            ),
        )

        self._window_id = self._canvas.create_window(
            (0, 0), window=self.inner, anchor="nw"
        )
        self._canvas.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self._canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self._canvas.bind(
            "<Configure>",
            lambda e: self._canvas.itemconfig(
                self._window_id, width=e.width
            ),
        )

        self._canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        self._canvas.bind_all("<Button-4>",   self._on_mousewheel)
        self._canvas.bind_all("<Button-5>",   self._on_mousewheel)

    def _on_mousewheel(self, event):
        if event.num == 4:
            self._canvas.yview_scroll(-1, "units")
        elif event.num == 5:
            self._canvas.yview_scroll(1, "units")
        else:
            self._canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def scroll_to_top(self):
        self._canvas.yview_moveto(0)