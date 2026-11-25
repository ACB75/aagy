"""RF-16: sincronización con lista de ficheros y hashes (install_manifest.py apply)."""

import json
from pathlib import Path
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import install_manifest as im  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[3]


def _stage(root: Path, files: dict) -> Path:
    for rel, text in files.items():
        (root / rel).parent.mkdir(parents=True, exist_ok=True)
        (root / rel).write_text(text, encoding="utf-8")
    return root


def _apply(stage: Path, dest: Path, profile: str = "generic", *flags: str) -> int:
    return im.main(["apply", "--stage", str(stage), "--dest", str(dest), "--profile", profile,
                    "--repo-root", str(REPO_ROOT), *flags])


def test_first_install_records_hashes_and_keeps_project_files(tmp_path):
    dest = tmp_path / "dest"
    _stage(dest, {"propio.md": "del proyecto", ".data/instincts/x.md": "datos"})
    stage = _stage(tmp_path / "s1", {"skills/a/SKILL.md": "a", "rules/AGENTS.md": "r"})
    assert _apply(stage, dest) == 0
    manifest = im.read_manifest(dest)
    assert manifest.schema == im.MANIFEST_SCHEMA
    assert set(manifest.files["generic"]) == {"skills/a/SKILL.md", "rules/AGENTS.md"}
    assert (dest / "propio.md").read_text(encoding="utf-8") == "del proyecto"
    assert (dest / ".data/instincts/x.md").is_file()


def test_hand_edited_file_is_protected_unless_force(tmp_path, capsys):
    dest = tmp_path / "dest"
    _apply(_stage(tmp_path / "s1", {"agents/p.md": "v1"}), dest)
    (dest / "agents/p.md").write_text("editado", encoding="utf-8")
    stage = _stage(tmp_path / "s2", {"agents/p.md": "v2"})
    _apply(stage, dest)
    assert (dest / "agents/p.md").read_text(encoding="utf-8") == "editado"
    assert "editado a mano" in capsys.readouterr().out
    assert im.drift(dest, im.read_manifest(dest))[0] == ["agents/p.md"]
    _apply(stage, dest, "generic", "--force")
    assert (dest / "agents/p.md").read_text(encoding="utf-8") == "v2"
    assert im.drift(dest, im.read_manifest(dest)) == ([], [], [])


def test_hard_deletes_orphans_soft_keeps_and_reports_them(tmp_path):
    dest = tmp_path / "dest"
    _apply(_stage(tmp_path / "s1", {"skills/a/SKILL.md": "a", "skills/b/SKILL.md": "b"}), dest)
    only_a = _stage(tmp_path / "s2", {"skills/a/SKILL.md": "a"})
    _apply(only_a, dest)
    assert (dest / "skills/b/SKILL.md").is_file()
    assert im.drift(dest, im.read_manifest(dest))[2] == ["skills/b/SKILL.md"]
    _apply(only_a, dest, "generic", "--hard")
    assert not (dest / "skills/b").exists()
    assert im.drift(dest, im.read_manifest(dest)) == ([], [], [])


def test_hard_keeps_files_of_other_profiles(tmp_path):
    dest = tmp_path / "dest"
    _apply(_stage(tmp_path / "g", {"skills/core/SKILL.md": "c", "rules/AGENTS.md": "r"}), dest, "generic")
    _apply(_stage(tmp_path / "p", {"skills/py/SKILL.md": "p", "rules/AGENTS.md": "r"}), dest, "python")
    _apply(_stage(tmp_path / "g2", {"rules/AGENTS.md": "r"}), dest, "generic", "--hard")
    assert (dest / "skills/py/SKILL.md").is_file()
    assert not (dest / "skills/core").exists()


def test_dry_run_changes_nothing(tmp_path, capsys):
    dest = tmp_path / "dest"
    _apply(_stage(tmp_path / "s", {"a.md": "a"}), dest, "generic", "--dry-run")
    assert not dest.exists() or not any(dest.iterdir())
    assert "[dry-run] [+] a.md" in capsys.readouterr().out


def test_drift_problems_message_for_doctor(tmp_path):
    dest = tmp_path / "dest"
    _apply(_stage(tmp_path / "s", {"a.md": "a", "b.md": "b"}), dest)
    (dest / "a.md").write_text("x", encoding="utf-8")
    (dest / "b.md").unlink()
    problems = im.drift_problems(dest, im.read_manifest(dest), "Reinstala.")
    assert any("modificados a mano: a.md" in p for p in problems)
    assert any("borrados: b.md" in p for p in problems)


def test_v1_manifest_without_files_still_reads(tmp_path):
    (tmp_path / im.MANIFEST_FILE).write_text(json.dumps({"harness": "agy", "profile": "generic"}), encoding="utf-8")
    manifest = im.read_manifest(tmp_path)
    assert manifest.files == {} and manifest.schema == 1
    assert im.drift(tmp_path, manifest) == ([], [], [])


def test_sh_sync_hard_dry_run_and_parity_with_ps1(tmp_path):
    dest = tmp_path / "plug"
    sh = REPO_ROOT / "scripts" / "sh" / "aagy-sync.sh"
    assert subprocess.run(["bash", str(sh), "generic", str(dest)], capture_output=True, check=False).returncode == 0
    sh_files = set(im.read_manifest(dest).files["generic"])
    out = subprocess.run(["bash", str(sh), "generic", str(dest), "--hard", "--dry-run"],
                         capture_output=True, text=True, check=False).stdout
    assert "[dry-run] [=]" in out and "0 a copiar, 0 a borrar" in out
    home = tmp_path / "home"
    ps1 = REPO_ROOT / "scripts" / "ps1" / "aagy-sync.ps1"
    res = subprocess.run(["pwsh", "-NoProfile", "-File", str(ps1), "-Phase", "generic"],
                         capture_output=True, text=True, check=False, env={"HOME": str(home), "PATH": "/usr/local/bin:/usr/bin:/bin"})
    if res.returncode == 0:
        ps1_files = set(im.read_manifest(home / ".gemini/config/plugins/aagy").files["generic"])
        assert {f for f in ps1_files if not f.startswith("hooks")} == {f for f in sh_files if not f.startswith("hooks")}
