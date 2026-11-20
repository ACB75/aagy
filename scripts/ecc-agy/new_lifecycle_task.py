"""Forwarding proxy towards canonical scripts/py/new_lifecycle_task.py"""
import sys
from pathlib import Path

_PY_DIR = str(Path(__file__).resolve().parent.parent / "py")
if _PY_DIR not in sys.path:
    sys.path.insert(0, _PY_DIR)

from new_lifecycle_task import *

if __name__ == "__main__":
    import runpy
    runpy.run_path(str(Path(_PY_DIR) / "new_lifecycle_task.py"), run_name="__main__")
