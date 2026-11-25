from __future__ import annotations

from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
SH_DIR = REPO_ROOT / "scripts" / "sh"

EXPECTED_SH_SCRIPTS = [
    "aagy.sh",
    "aagy-sync.sh",
    "git-flow-helper.sh",
    "install-git-hooks.sh",
    "lint-markdown.sh",
]


def test_sh_scripts_exist():
    assert SH_DIR.is_dir(), f"scripts/sh directory must exist at {SH_DIR}"
    for script_name in EXPECTED_SH_SCRIPTS:
        script_path = SH_DIR / script_name
        assert script_path.is_file(), f"Expected sh script missing: {script_name}"


def test_sh_scripts_have_shebang_and_lf():
    for script_name in EXPECTED_SH_SCRIPTS:
        script_path = SH_DIR / script_name
        raw = script_path.read_bytes()
        assert len(raw) > 0, f"Script {script_name} must not be empty"
        assert raw.startswith(b"#!/"), f"Script {script_name} must begin with shebang #!/"
        assert b"\r\n" not in raw, f"Script {script_name} must use strict LF line endings"


def test_launcher_is_agnostic_and_forwards_to_python():
    import subprocess
    launcher = SH_DIR / "aagy.sh"
    content = launcher.read_text(encoding="utf-8")
    assert not [w for w in _consumer_terms() if w in content.lower()]
    assert "../py" in content
    cmd = ['bash'] + [str(launcher)]
    listed = subprocess.run(cmd + ["help"], capture_output=True, text=True, check=False)
    assert listed.returncode == 0 and "complete-task-pr" in listed.stdout
    ran = subprocess.run(cmd + ["validate-branch", "--branch", "feat/app/x"], capture_output=True, text=True, check=False)
    assert ran.returncode == 0 and "PASS" in ran.stdout
    unknown = subprocess.run(cmd + ["no-existe"], capture_output=True, text=True, check=False)
    assert unknown.returncode == 2


def _consumer_terms():
    """Términos de consumer_refs del repo (.governance/aagy.json): el plugin no los conoce."""
    import json
    cfg = Path(__file__).resolve().parents[3] / ".governance" / "aagy.json"
    data = json.loads(cfg.read_text(encoding="utf-8")) if cfg.is_file() else {}
    return [str(t).lower() for t in data.get("consumer_refs", [])]
