# ============================================================
# ui/osk.py — Launch the OS built-in on-screen keyboard
# ============================================================
import subprocess
import sys
import os

_proc = None  # track the process so we don't open duplicates


def show():
    """Open the OS on-screen keyboard (non-blocking)."""
    global _proc

    # Already open
    if _proc is not None and _proc.poll() is None:
        return

    if sys.platform == "win32":
        # Windows — built-in On-Screen Keyboard
        _proc = subprocess.Popen(["osk.exe"])

    else:
        # Raspberry Pi / Linux — try common soft keyboards in order
        for cmd in ["onboard", "matchbox-keyboard", "florence"]:
            if _which(cmd):
                _proc = subprocess.Popen([cmd])
                return
        print("[osk] No on-screen keyboard found. "
              "Install one with:  sudo apt install onboard")


def hide():
    """Close the on-screen keyboard if we launched it."""
    global _proc
    if _proc is not None and _proc.poll() is None:
        _proc.terminate()
    _proc = None


def attach(entry):
    """
    Bind show/hide to an Entry widget.
    Call once per Entry:  osk.attach(my_entry)
    """
    entry.bind("<FocusIn>",  lambda _e: show(), add="+")
    entry.bind("<Button-1>", lambda _e: show(), add="+")
    entry.bind("<FocusOut>", lambda _e: hide(), add="+")


def _which(cmd: str) -> bool:
    """Return True if cmd exists on PATH."""
    return any(
        os.path.isfile(os.path.join(p, cmd))
        for p in os.environ.get("PATH", "").split(os.pathsep)
    )