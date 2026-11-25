"""RF-14: el repo no nombra a proyectos consumidores (consumer_refs.py)."""

import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import audit_plugin_parity  # noqa: E402
import consumer_refs as cr  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[3]


def _repo(tmp_path: Path, terms) -> Path:
    (tmp_path / ".git").mkdir()
    (tmp_path / ".governance").mkdir()
    (tmp_path / ".governance" / "aagy.json").write_text(json.dumps({"consumer_refs": terms}), encoding="utf-8")
    return tmp_path


def test_without_terms_it_skips(tmp_path, monkeypatch):
    monkeypatch.delenv("AAGY_ENV_DIR", raising=False)
    (tmp_path / ".git").mkdir()
    (tmp_path / "a.md").write_text("cualquier cosa", encoding="utf-8")
    assert cr.audit(tmp_path) == ((), [])
    assert cr.main(["--repo", str(tmp_path)]) == 0


def test_finds_terms_case_insensitive_and_skips_declaring_file(tmp_path, monkeypatch):
    monkeypatch.delenv("AAGY_ENV_DIR", raising=False)
    repo = _repo(tmp_path, ["MiProyecto"])
    (repo / "skills").mkdir()
    (repo / "skills" / "x.md").write_text("linea\nusa miproyecto aquí\n", encoding="utf-8")
    (repo / "bin.dat").write_bytes(b"\0miproyecto")
    terms, hits = cr.audit(repo)
    assert terms == ("MiProyecto",)
    assert [(h.path, h.line) for h in hits] == [("skills/x.md", 2)]
    assert cr.main(["--repo", str(repo)]) == 1


def test_env_layer_terms_are_added(tmp_path, monkeypatch):
    env_dir = tmp_path / "env"
    (env_dir / "aagy").mkdir(parents=True)
    (env_dir / "aagy" / "env.json").write_text(json.dumps({"consumer_refs": ["mi-host"]}), encoding="utf-8")
    monkeypatch.setenv("AAGY_ENV_DIR", str(env_dir))
    (tmp_path / "repo").mkdir()
    repo = _repo(tmp_path / "repo", ["a"])
    assert cr.declared_terms(repo) == ("a", "mi-host")


def test_parity_audit_flags_plugin_trees_only(tmp_path, monkeypatch):
    monkeypatch.delenv("AAGY_ENV_DIR", raising=False)
    repo = _repo(tmp_path, ["secreto"])
    (repo / "doc").mkdir()
    (repo / "doc" / "n.md").write_text("secreto", encoding="utf-8")
    (repo / "agents").mkdir()
    (repo / "agents" / "a.md").write_text("secreto", encoding="utf-8")
    found: list = []
    audit_plugin_parity._check_consumer_refs(repo, found)
    assert len(found) == 1 and "agents/a.md:1" in found[0]


def test_this_repo_declares_terms_and_has_no_hits():
    terms, hits = cr.audit(REPO_ROOT)
    assert terms, "el repo debe declarar consumer_refs en .governance/aagy.json"
    assert hits == [], hits[:5]


def test_windows_paths_match_either_separator(tmp_path):
    (tmp_path / "doc.md").write_text("ruta d:/RutaX/x\n", encoding="utf-8")
    hits = cr.scan(tmp_path, ["D:\\RutaX"])
    assert [h.term for h in hits] == ["D:\\RutaX"]
