"""Forwarding proxy towards canonical scripts/py/validate_ingress_routes.py"""
import sys
from pathlib import Path

_PY_DIR = str(Path(__file__).resolve().parent.parent / "py")
if _PY_DIR not in sys.path:
    sys.path.insert(0, _PY_DIR)

from validate_ingress_routes import *

if __name__ == "__main__":
    import runpy
    runpy.run_path(str(Path(_PY_DIR) / "validate_ingress_routes.py"), run_name="__main__")
