#!/usr/bin/env python3
"""Pruebas de repo_profiles.py: perfiles de stack declarados por el repositorio consumidor."""

from __future__ import annotations

import json
from pathlib import Path
import re
import sys

import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
_SCRIPTS_DIR = _REPO_ROOT / "scripts" / "py"
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

import repo_profiles as rp  # noqa: E402

SYNC_SH = (
    "case x in\n"
    "  generic)\n    SKILLS=(base)\n    AGENTS=(planner.md)\n    ;;\n"
    "  go)\n    SKILLS=(golang base)\n    AGENTS=(go-reviewer.md planner.md)\n    ;;\n"
    "  python)\n    SKILLS=(py-patterns)\n    AGENTS=(py-reviewer.md)\n    ;;\n"
    "esac\n"
)


@pytest.fixture()
def aagy(tmp_path: Path) -> Path:
    root = tmp_path / "aagy"
    (root / "scripts" / "sh").mkdir(parents=True)
    (root / "scripts" / "sh" / "aagy-sync.sh").write_text(SYNC_SH, encoding="utf-8")
    for skill in ("base", "golang", "py-patterns"):
        (root / "skills" / skill).mkdir(parents=True)
        (root / "skills" / skill / "SKILL.md").write_text(f"# {skill}\n", encoding="utf-8")
    (root / "agents").mkdir()
    for agent in ("planner.md", "go-reviewer.md", "py-reviewer.md"):
        (root / "agents" / agent).write_text(f"# {agent}\n", encoding="utf-8")
    return root


def _repo(tmp_path: Path, profiles: object) -> Path:
    repo = tmp_path / "consumer"
    (repo / ".governance").mkdir(parents=True)
    (repo / ".governance" / "aagy-profiles.json").write_text(json.dumps({"profiles": profiles}), encoding="utf-8")
    return repo


def test_install_excludes_global_profile_and_writes_lock_and_gitignore(tmp_path: Path, aagy: Path) -> None:
    repo = _repo(tmp_path, ["go", "python"])
    selection, warnings = rp.install(repo, aagy)
    assert warnings == []
    assert selection.skills == ("golang", "py-patterns")
    assert selection.agents == ("go-reviewer.md", "py-reviewer.md")
    assert (repo / ".agents" / "skills" / "golang" / "SKILL.md").is_file()
    assert not (repo / ".agents" / "skills" / "base").exists()
    lock = json.loads((repo / ".agents" / rp.LOCK_FILE).read_text(encoding="utf-8"))
    assert lock["profiles"] == ["go", "python"]
    ignore = (repo / ".agents" / ".gitignore").read_text(encoding="utf-8")
    assert "/skills/golang/" in ignore and "/agents/py-reviewer.md" in ignore


def test_reinstall_prunes_removed_profile_and_keeps_own_items(tmp_path: Path, aagy: Path) -> None:
    repo = _repo(tmp_path, ["go", "python"])
    own = repo / ".agents" / "skills" / "golang-own"
    own.mkdir(parents=True)
    (repo / ".agents" / ".gitignore").write_text("own-entry\n", encoding="utf-8")
    rp.install(repo, aagy)
    (repo / ".governance" / "aagy-profiles.json").write_text(json.dumps({"profiles": ["go"]}), encoding="utf-8")
    selection, _ = rp.install(repo, aagy)
    assert selection.skills == ("golang",)
    assert not (repo / ".agents" / "skills" / "py-patterns").exists()
    assert own.is_dir()
    ignore = (repo / ".agents" / ".gitignore").read_text(encoding="utf-8")
    assert ignore.startswith("own-entry\n")
    assert ignore.count(rp.BLOCK_BEGIN) == 1 and "py-patterns" not in ignore


def test_unmanaged_item_with_same_name_is_not_overwritten(tmp_path: Path, aagy: Path) -> None:
    repo = _repo(tmp_path, ["go"])
    own = repo / ".agents" / "skills" / "golang"
    own.mkdir(parents=True)
    (own / "SKILL.md").write_text("propia\n", encoding="utf-8")
    selection, warnings = rp.install(repo, aagy)
    assert "golang" not in selection.skills
    assert warnings and (own / "SKILL.md").read_text(encoding="utf-8") == "propia\n"


@pytest.mark.parametrize("profiles", [["generic"], ["all"], ["unknown"], "go", [1]])
def test_invalid_declarations_are_rejected(tmp_path: Path, aagy: Path, profiles: object) -> None:
    repo = _repo(tmp_path, profiles)
    with pytest.raises(ValueError):
        rp.install(repo, aagy)


def test_missing_manifest_fails_with_exit_code(tmp_path: Path, aagy: Path) -> None:
    assert rp.main(["install", "--repo", str(tmp_path), "--aagy-root", str(aagy)]) == 1


STACK_CASES = {"status", "generic", "network-infra", "java-spring", "angular", "go", "python", "all", "infra", "*"}


def test_real_profiles_are_stack_named_and_agnostic() -> None:
    text = (_REPO_ROOT / "scripts" / "sh" / "aagy-sync.sh").read_text(encoding="utf-8")
    for profile in ("network-infra", "java-spring", "angular", "go", "python"):
        assert rp.expected_catalog(_REPO_ROOT, profile) is not None, profile
    cases = re.findall(r"^  ([a-z|-]+)\)$", text, re.MULTILINE)
    assert all(set(c.split("|")) <= STACK_CASES for c in cases), cases
