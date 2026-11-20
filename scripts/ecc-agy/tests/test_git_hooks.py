"""
Tests unitarios para la infraestructura de Git hooks (pre-commit, commit-msg, instalador).
"""
import os
from pathlib import Path
import subprocess
import sys


REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
HOOKS_DIR = REPO_ROOT / "scripts" / "ecc-agy" / "hooks"
SCRIPTS_BIN_DIR = REPO_ROOT / "scripts" / "bin" / "ecc-agy"


def test_hook_files_exist_and_executable():
    pre_commit = HOOKS_DIR / "pre-commit"
    commit_msg = HOOKS_DIR / "commit-msg"

    assert pre_commit.exists(), "Hook pre-commit debe existir en scripts/ecc-agy/hooks/"
    assert commit_msg.exists(), "Hook commit-msg debe existir en scripts/ecc-agy/hooks/"

    pre_content = pre_commit.read_text(encoding="utf-8")
    msg_content = commit_msg.read_text(encoding="utf-8")

    assert pre_content.startswith("#!/bin/sh"), "pre-commit debe ser un script POSIX sh"
    assert msg_content.startswith("#!/bin/sh"), "commit-msg debe ser un script POSIX sh"


def test_commit_msg_hook_validation(tmp_path):
    commit_msg = HOOKS_DIR / "commit-msg"
    format_commit = REPO_ROOT / "scripts" / "ecc-agy" / "format_commit.py"

    # Caso 1: Mensaje inválido (wip)
    invalid_file = tmp_path / "msg_invalid.txt"
    invalid_file.write_text("wip", encoding="utf-8")

    proc_invalid = subprocess.run(
        [sys.executable, str(format_commit), "--validate-file", str(invalid_file), "--strict"],
        capture_output=True,
        text=True,
    )
    assert proc_invalid.returncode != 0, "Mensaje 'wip' debe ser rechazado en modo strict"

    # Caso 2: Mensaje válido con cuerpo explicativo
    valid_file = tmp_path / "msg_valid.txt"
    valid_content = (
        "[feat]-[ecc]: implementacion de nueva funcionalidad\n\n"
        "Cuerpo explicativo detallado con mas de veinte caracteres para pasar el modo strict."
    )
    valid_file.write_text(valid_content, encoding="utf-8")

    proc_valid = subprocess.run(
        [sys.executable, str(format_commit), "--validate-file", str(valid_file), "--strict"],
        capture_output=True,
        text=True,
    )
    assert proc_valid.returncode == 0, f"Mensaje válido debe ser aceptado. Error: {proc_valid.stderr}"


def test_installer_scripts_exist():
    ps1_installer = SCRIPTS_BIN_DIR / "install-git-hooks.ps1"
    sh_installer = SCRIPTS_BIN_DIR / "install-git-hooks.sh"

    assert ps1_installer.exists(), "install-git-hooks.ps1 debe existir en scripts/bin/ecc-agy/"
    assert sh_installer.exists(), "install-git-hooks.sh debe existir en scripts/bin/ecc-agy/"


def test_hook_content_matches_requirements():
    pre_commit = HOOKS_DIR / "pre-commit"
    commit_msg = HOOKS_DIR / "commit-msg"

    pre_text = pre_commit.read_text(encoding="utf-8")
    msg_text = commit_msg.read_text(encoding="utf-8")

    assert "GIT_HOOKS_BYPASS" in pre_text, "pre-commit debe soportar variable GIT_HOOKS_BYPASS"
    assert "GIT_HOOKS_BYPASS" in msg_text, "commit-msg debe soportar variable GIT_HOOKS_BYPASS"
    assert "format_commit.py" in msg_text, "commit-msg debe invocar format_commit.py"
    assert "lint-markdown" in pre_text, "pre-commit debe invocar lint-markdown"

