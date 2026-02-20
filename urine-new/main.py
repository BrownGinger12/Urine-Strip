#!/usr/bin/env python3
# ============================================================
# main.py — Entry point for Urine Analyzer
# ============================================================
import sys
import os

# Ensure the project root is on the Python path when run directly
sys.path.insert(0, os.path.dirname(__file__))

from ui.app import App


def main():
    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()
