import json
import subprocess
import sys
import tempfile
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from generate_postmortem import (
    slugify_branch_name,
    format_postmortem_markdown,
    generate_postmortem_file,
    PostMortemMetadata
)

def test_slugify_branch_name():
    assert slugify_branch_name("fix/SEC-001") == "fix_sec_001"
    assert slugify_branch_name("fix/kakebo/issue-102") == "fix_kakebo_issue_102"
    assert slugify_branch_name("fix/cluster/timeout_p99") == "fix_cluster_timeout_p99"

def test_format_postmortem_markdown():
    meta = PostMortemMetadata(
        branch_name="fix/auth-leak",
        author="SRE Engineer",
        timestamp_utc="2026-11-07T22:00:00Z",
        affected_files=["services/auth/login.go"],
        diff_summary="1 file changed, 2 insertions(+), 1 deletion(-)",
        environment="SANDBOX"
    )
    template = """# Post-Mortem 5W: {{BRANCH}}
- **Fecha UTC:** {{TIMESTAMP_UTC}}
- **Autor:** {{AUTHOR}}
- **Entorno:** {{ENVIRONMENT}}
- **Diff:** {{DIFF_SUMMARY}}
"""
    result = format_postmortem_markdown(meta, template)
    assert "Post-Mortem 5W: fix/auth-leak" in result
    assert "2026-11-07T22:00:00Z" in result
    assert "SRE Engineer" in result
    assert "SANDBOX" in result

def test_generate_postmortem_file_creates_file_in_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        out_dir = Path(tmpdir) / "post-mortem"
        out_dir.mkdir()
        tpl = out_dir / "TEMPLATE.md"
        tpl.write_text("# Template {{BRANCH}} - {{AUTHOR}}", encoding="utf-8")

        created_file = generate_postmortem_file(
            output_dir=out_dir,
            template_path=tpl,
            branch_name="fix/kakebo/jwt-leak",
            author="DevOps",
            diff_stat="1 file changed"
        )

        assert created_file.is_file()
        assert created_file.name.startswith("PM_fix_kakebo_jwt_leak_")
        assert created_file.name.endswith(".md")

        content = created_file.read_text(encoding="utf-8")
        assert "fix/kakebo/jwt-leak" in content
        assert "DevOps" in content


def test_default_template_path():
    from generate_postmortem import DEFAULT_TEMPLATE
    assert DEFAULT_TEMPLATE == Path("doc/post-mortem/TEMPLATE_POSTMORTEM.md")


def test_cli_postmortem_resolves_v2_and_legacy_fallback(tmp_path: Path):
    """CLI de generate_postmortem.py resuelve rutas v2 y fallback clásico en ramas fix/*."""
    script_path = Path(__file__).resolve().parent.parent / "generate_postmortem.py"

    # 1. Caso v2 con docs-map.json
    v2_root = tmp_path / "v2"
    (v2_root / ".governance").mkdir(parents=True)
    (v2_root / "doc" / "00-governance" / "templates").mkdir(parents=True)
    (v2_root / "doc" / "05-post-mortems").mkdir(parents=True)
    (v2_root / "doc" / "00-governance" / "templates" / "TEMPLATE_POSTMORTEM.md").write_text(
        "# V2 PM {{BRANCH}}", encoding="utf-8"
    )
    (v2_root / ".governance" / "docs-map.json").write_text(
        json.dumps(
            {
                "schema_version": 2,
                "paths": {
                    "postmortems": "doc/05-post-mortems",
                    "postmortem_template": "doc/00-governance/templates/TEMPLATE_POSTMORTEM.md",
                },
            }
        ),
        encoding="utf-8",
    )

    res_v2 = subprocess.run(
        [sys.executable, str(script_path), "--repo-root", str(v2_root), "--branch", "fix/v2-case"],
        capture_output=True,
        text=True,
    )
    assert res_v2.returncode == 0
    pm_v2 = list((v2_root / "doc" / "05-post-mortems").glob("PM_fix_v2_case_*.md"))
    assert len(pm_v2) == 1
    assert "V2 PM fix/v2-case" in pm_v2[0].read_text(encoding="utf-8")

    # 2. Caso clásico sin docs-map.json
    legacy_root = tmp_path / "legacy"
    (legacy_root / "doc" / "post-mortem").mkdir(parents=True)
    (legacy_root / "doc" / "post-mortem" / "TEMPLATE_POSTMORTEM.md").write_text(
        "# Legacy PM {{BRANCH}}", encoding="utf-8"
    )

    res_leg = subprocess.run(
        [sys.executable, str(script_path), "--repo-root", str(legacy_root), "--branch", "fix/legacy-case"],
        capture_output=True,
        text=True,
    )
    assert res_leg.returncode == 0
    pm_leg = list((legacy_root / "doc" / "post-mortem").glob("PM_fix_legacy_case_*.md"))
    assert len(pm_leg) == 1
    assert "Legacy PM fix/legacy-case" in pm_leg[0].read_text(encoding="utf-8")


