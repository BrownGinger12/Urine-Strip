# ============================================================
# ui/osk.py — Launch onboard on-screen keyboard (Linux/Pi)
# ============================================================
import subprocess

_proc = None


def show():
    """Open onboard (non-blocking). Install: sudo apt install onboard"""
    global _proc
    if _proc is not None and _proc.poll() is None:
        return  # already open
    try:
        _proc = subprocess.Popen(["onboard"])
    except FileNotFoundError:
        print("[osk] onboard not found. Run: sudo apt install onboard")


def hide():
    """Close onboard if we launched it."""
    global _proc
    if _proc is not None and _proc.poll() is None:
        _proc.terminate()
    _proc = None


def attach(entry):
    """Wire up an Entry to show onboard on focus/click."""
    entry.bind("<FocusIn>",  lambda _e: show(), add="+")
    entry.bind("<Button-1>", lambda _e: show(), add="+")