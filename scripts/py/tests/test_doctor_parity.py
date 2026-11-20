#!/usr/bin/env python3
"""Pruebas de la paridad 1:1 entre /aagy-doctor y /aagy-ecc-doctor y de la exclusión del espejo."""

from __future__ import annotations

from pathlib import Path
import shutil
import sys

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
_SCRIPTS_DIR = _REPO_ROOT / "scripts" / "py"
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from audit_plugin_parity import _check_doctor_parity, audit_parity  # noqa: E402
from sync_aagy_ecc import compare, sync  # noqa: E402

DOCTOR_FILES = (
    Path("scripts/py/doctor_core.py"),
    Path("scripts/py/aagy_doctor.py"),
    Path("aagy-ecc/scripts/py/aagy_ecc_doctor.py"),
)


def _copy_doctors(dest: Path) -> None:
    for rel in DOCTOR_FILES:
        (dest / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(_REPO_ROOT / rel, dest / rel)


def test_real_repo_parity_passes():
    result = audit_parity(_REPO_ROOT)
    assert result.is_valid, result.discrepancies


def test_doctor_parity_ok_and_skipped_without_doctors(tmp_path: Path):
    problems: list = []
    _check_doctor_parity(tmp_path, problems)
    assert problems == []
    _copy_doctors(tmp_path)
    _check_doctor_parity(tmp_path, problems)
    assert problems == []


def test_doctor_parity_requires_both_doctors(tmp_path: Path):
    _copy_doctors(tmp_path)
    (tmp_path / "aagy-ecc" / "scripts" / "py" / "aagy_ecc_doctor.py").unlink()
    problems: list = []
    _check_doctor_parity(tmp_path, problems)
    assert problems and "aagy_ecc_doctor.py" in problems[0]


def test_doctor_parity_detects_divergent_ids(tmp_path: Path):
    _copy_doctors(tmp_path)
    ecc = tmp_path / "aagy-ecc" / "scripts" / "py" / "aagy_ecc_doctor.py"
    ecc.write_text(ecc.read_text(encoding="utf-8").replace('    "DOC-14": check_repo,\n', ""), encoding="utf-8")
    problems: list = []
    _check_doctor_parity(tmp_path, problems)
    assert any("checks distintos" in p for p in problems)
    assert any("aagy_ecc_doctor.py" in p and "catálogo" in p for p in problems)


def test_aagy_doctor_skill_is_not_mirrored(tmp_path: Path):
    for name in ("tdd-workflow", "aagy-doctor"):
        (tmp_path / "skills" / name).mkdir(parents=True)
        (tmp_path / "skills" / name / "SKILL.md").write_text(f"# {name}\n", encoding="utf-8")
    (tmp_path / "aagy-ecc").mkdir()
    sync(tmp_path)
    assert (tmp_path / "aagy-ecc" / "skills" / "tdd-workflow" / "SKILL.md").is_file()
    assert not (tmp_path / "aagy-ecc" / "skills" / "aagy-doctor").exists()
    assert compare(tmp_path).in_sync
    stray = tmp_path / "aagy-ecc" / "skills" / "aagy-doctor"
    stray.mkdir()
    (stray / "SKILL.md").write_text("# no debe estar\n", encoding="utf-8")
    assert compare(tmp_path).extra == ("skills/aagy-doctor/SKILL.md",)
