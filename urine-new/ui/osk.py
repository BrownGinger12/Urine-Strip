# ============================================================
# ui/osk.py — Launch Florence virtual keyboard (Linux/Pi)
# Install: sudo apt install florence
# ============================================================
import subprocess

_proc = None


def show():
    """Open Florence (non-blocking)."""
    global _proc
    if _proc is not None and _proc.poll() is None:
        return  # already open
    try:
        _proc = subprocess.Popen(["florence"])
    except FileNotFoundError:
        print("[osk] florence not found. Run: sudo apt install florence")


def hide():
    """Close Florence if we launched it."""
    global _proc
    if _proc is not None and _proc.poll() is None:
        _proc.terminate()
    _proc = None


def attach(entry):
    """Wire an Entry to show Florence on focus/click."""
    entry.bind("<FocusIn>",  lambda _e: show(), add="+")
    entry.bind("<Button-1>", lambda _e: show(), add="+")


def init(root):
    """Called by app.py on startup — nothing needed for Florence."""
    pass