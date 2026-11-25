"""Paridad de hooks entre plugins con un solo motor Python (#96, CA-07)."""

import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import audit_plugin_parity as parity  # noqa: E402
import hook_post_write  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[3]


def test_real_hooks_are_in_parity():
    discrepancies = []
    parity._check_hook_parity(REPO_ROOT, discrepancies)
    assert discrepancies == []
    agy, ecc = parity.hook_coverage(REPO_ROOT)
    assert set(ecc) - set(agy) == parity.HOOK_ASYMMETRY_EVENTS


def test_every_hook_engine_exists_in_both_plugins():
    agy, ecc = parity.hook_coverage(REPO_ROOT)
    for script in set().union(*agy.values(), *ecc.values()):
        assert (REPO_ROOT / "scripts" / "py" / script).is_file(), script
        assert (REPO_ROOT / "aagy-ecc" / "scripts" / "py" / script).is_file(), script


def _write_hooks(root: Path, agy: dict, ecc: dict) -> None:
    (root / "aagy-ecc" / "hooks").mkdir(parents=True)
    (root / "hooks.json").write_text(json.dumps(agy), encoding="utf-8")
    (root / "aagy-ecc" / "hooks" / "hooks.json").write_text(json.dumps({"hooks": ecc}), encoding="utf-8")


def _cmd(script: str, root: str = "${AAGY_PLUGIN_ROOT}/") -> list:
    return [{"matcher": "*", "hooks": [{"command": f'python "{root}scripts/py/{script}"'}]}]


def test_detects_different_engines_undeclared_events_and_relative_paths(tmp_path):
    ecc = {"Stop": _cmd("backlog.py", "${CLAUDE_PLUGIN_ROOT}/"), "Notification": _cmd("x.py", "${CLAUDE_PLUGIN_ROOT}/")}
    _write_hooks(tmp_path, {"g": {"Stop": _cmd("self_improve.py"), "PreToolUse": _cmd("hook_safety.py", "")}}, ecc)
    discrepancies = []
    parity._check_hook_parity(tmp_path, discrepancies)
    text = " ".join(discrepancies)
    assert "Eventos de hooks distintos" in text and "motores distintos" in text and "rutas relativas" in text


def test_post_write_extracts_agy_and_claude_paths(tmp_path):
    agy = {"toolCall": {"args": {"TargetFile": "doc/a.md"}}, "cwd": str(tmp_path)}
    assert hook_post_write.extract_path(agy, "agy") == tmp_path / "doc" / "a.md"
    claude = {"tool_input": {"file_path": str(tmp_path / "b.md")}}
    assert hook_post_write.extract_path(claude, "claude") == tmp_path / "b.md"
    assert hook_post_write.extract_path({}, "agy") is None
