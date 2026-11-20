"""Forwarding proxy towards canonical scripts/py/sync_ideas_todo.py"""
import sys
from pathlib import Path

_PY_DIR = str(Path(__file__).resolve().parent.parent / "py")
if _PY_DIR not in sys.path:
    sys.path.insert(0, _PY_DIR)

from sync_ideas_todo import *

if __name__ == "__main__":
    import runpy
    runpy.run_path(str(Path(_PY_DIR) / "sync_ideas_todo.py"), run_name="__main__")
