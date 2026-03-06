# ============================================================
# ui/osk.py — Launch matchbox-keyboard virtual keyboard (Linux/Pi)
# Install: sudo apt install matchbox-keyboard
# ============================================================
import subprocess

_proc = None


def show():
    """Open matchbox-keyboard (non-blocking)."""
    global _proc
    if _proc is not None and _proc.poll() is None:
        return  # already open
    try:
        _proc = subprocess.Popen(["matchbox-keyboard"])
    except FileNotFoundError:
        print("[osk] matchbox-keyboard not found. Run: sudo apt install matchbox-keyboard")


def hide():
    """Close matchbox-keyboard if we launched it."""
    global _proc
    if _proc is not None and _proc.poll() is None:
        _proc.terminate()
    _proc = None


def attach(entry):
    """Wire an Entry to show matchbox-keyboard on focus/click."""
    entry.bind("<FocusIn>",  lambda _e: show(), add="+")
    entry.bind("<Button-1>", lambda _e: show(), add="+")


def init(root):
    """Called by app.py on startup — nothing needed for matchbox-keyboard."""
    pass