"""Generador e instanciador de artefactos del ciclo de vida de ingeniería (4 fases).

Soporta rutas parametrizadas vía `.governance/docs-map.json` (con fallback a `doc/` clásico),
puntos de entrada flexibles: `[IDEAS -> REQUISITOS -> PLAN -> TODO]` (`--phase`)
y vinculación directa con GitHub Issues (`--issue <N>` / `-Issue <N>`).
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import subprocess
import sys
from typing import Any, Dict, List, Optional, Sequence, Tuple

_SCRIPT_DIR = str(Path(__file__).resolve().parent)
if _SCRIPT_DIR not in sys.path:
    sys.path.insert(0, _SCRIPT_DIR)

import doc_templates  # noqa: E402
from docs_map import DocsMap, load_docs_map  # noqa: E402
from validate_branch import validate_branch_name  # noqa: E402

# Constantes SonarQube S1192
MSG_OK = "[PASS]"
MSG_WARN = "[WARN]"
MSG_DRY_RUN = "[DRY-RUN]"
DEFAULT_TEMPLATES_DIR = "doc/templates"
DEFAULT_OUTPUT_DIR = "doc/plan"
ACTIVE_ISSUE_REL = ".governance/active-issue.json"
ENCODING_UTF8 = "utf-8"
K_SUB_ISSUE = "sub_issue"

VALID_PHASES: Tuple[str, ...] = ("ALL", "IDEAS", "REQ", "PLAN", "TODO", "DOCS", "REVIEW")
BRANCH_TYPES: Tuple[str, ...] = ("feat", "fix", "refactor", "infra", "chore", "docs", "test")

PHASE_TEMPLATES: List[Tuple[str, str]] = [
    ("REQ", "01_TOMA_REQUISITOS_E_IMPACTO.md"),
    ("PLAN", "02_PLAN_ACCION_ARQUITECTURA.md"),
    ("DOCS", "03_DOCUMENTACION_Y_RELEASE_NOTES.md"),
    ("REVIEW", "04_PROPUESTA_COMMITS_PR.md"),
]

PHASE_SLICES: Dict[str, Tuple[str, ...]] = {
    "ALL": ("REQ", "PLAN", "DOCS", "REVIEW"),
    "REQ": ("REQ", "PLAN", "DOCS", "REVIEW"),
    "PLAN": ("PLAN", "DOCS", "REVIEW"),
    "DOCS": ("DOCS", "REVIEW"),
    "REVIEW": ("REVIEW",),
}

_ISSUE_TITLE_RE = re.compile(r"^\[(?P<type>[a-z]+)\]-\[(?P<projects>[^\]]+)\]:\s*(?P<desc>.+)$", re.IGNORECASE)


@dataclass(frozen=True)
class ScaffoldContext:
    """Contexto inmutable para la instanciación de artefactos de una tarea."""

    task_id: str
    slug: str
    date_str: str
    templates_dir: Path
    repo_root: Path
    output_dir: Path
    force: bool
    dry_run: bool


def slugify_task_id(task_id: str) -> str:
    """Convierte el ID o rama de tarea en un slug limpio para nombres de archivo."""
    cleaned = re.sub(r"^(feat|fix|refactor|infra|chore|docs|test)/", "", task_id)
    slug = re.sub(r"[^a-zA-Z0-9_\-]+", "_", cleaned).strip("_")
    return slug.replace("-", "_") if slug else "task"


def _infer_type_and_project(labels: Sequence[str]) -> Tuple[str, str]:
    lowered = {lbl.lower() for lbl in labels}
    b_type = "feat"
    if "bug" in lowered or "fix" in lowered:
        b_type = "fix"
    elif "area:infra" in lowered or "infra" in lowered:
        b_type = "infra"
    elif "documentation" in lowered or "area:docs" in lowered:
        b_type = "docs"

    project = "aagy"
    for lbl in sorted(lowered):
        if lbl.startswith("area:"):
            candidate = re.sub(r"[^a-z0-9-]+", "", lbl.split(":", 1)[1])
            if candidate:
                project = candidate
                break
    return b_type, project


def parse_issue_metadata(
    issue_number: int,
    title: str,
    labels: Sequence[str],
    url: str = "",
) -> Dict[str, Any]:
    """Construye metadatos y rama canónica <type>/<project>/gh-<N>-<slug> desde una GitHub Issue."""
    if issue_number <= 0:
        raise ValueError(f"Número de issue inválido: {issue_number}")

    b_type, project = _infer_type_and_project(labels)
    desc = title.strip()
    match = _ISSUE_TITLE_RE.match(desc)
    if match:
        raw_type = match.group("type").lower()
        if raw_type in BRANCH_TYPES:
            b_type = raw_type
        first_proj = match.group("projects").split(",")[0].strip().lower()
        clean_proj = re.sub(r"[^a-z0-9._-]+", "", first_proj)
        if clean_proj:
            project = clean_proj
        desc = match.group("desc").strip()

    raw_slug = re.sub(r"[^a-z0-9]+", "-", desc.lower()).strip("-")
    short_slug = raw_slug[:36].strip("-") or "issue"
    branch = f"{b_type}/{project}/gh-{issue_number}-{short_slug}"
    is_valid, err = validate_branch_name(branch)
    if not is_valid:
        raise ValueError(f"Rama generada inválida '{branch}': {err}")

    return {
        "issue": issue_number,
        "title": title.strip(),
        "branch": branch,
        "type": b_type,
        "project": project,
        "labels": list(labels),
        "url": url,
    }


def fetch_github_issue(issue_number: int, repo_root: Path) -> Dict[str, Any]:
    """Consulta una issue con `gh issue view` y devuelve sus metadatos normalizados."""
    proc = subprocess.run(
        ["gh", "issue", "view", str(issue_number), "--json", "number,title,labels,url"],
        cwd=str(repo_root),
        capture_output=True,
        text=True,
        encoding=ENCODING_UTF8,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"No se pudo leer la issue #{issue_number} con gh: {(proc.stderr or proc.stdout).strip()}")
    data = json.loads(proc.stdout)
    raw_labels = data.get("labels") or []
    labels = [
        str(item.get("name") if isinstance(item, dict) else item)
        for item in raw_labels
        if item
    ]
    return parse_issue_metadata(
        issue_number=int(data.get("number") or issue_number),
        title=str(data.get("title") or f"Issue {issue_number}"),
        labels=labels,
        url=str(data.get("url") or ""),
    )


def _checkout_issue_branch(repo_root: Path, branch: str) -> None:
    if not (repo_root / ".git").exists():
        return
    curr = subprocess.run(
        ["git", "branch", "--show-current"],
        cwd=str(repo_root),
        capture_output=True,
        text=True,
        encoding=ENCODING_UTF8,
        check=False,
    )
    if curr.returncode == 0 and curr.stdout.strip() == branch:
        return
    chk = subprocess.run(
        ["git", "checkout", "-b", branch],
        cwd=str(repo_root),
        capture_output=True,
        text=True,
        encoding=ENCODING_UTF8,
        check=False,
    )
    if chk.returncode != 0:
        subprocess.run(
            ["git", "checkout", branch],
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            encoding=ENCODING_UTF8,
            check=False,
        )


def bind_github_issue(
    issue_number: int,
    repo_root: Path,
    dry_run: bool = False,
    explicit_task_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Lee la issue, auto-asigna @me, crea la rama gh-<N> y registra .governance/active-issue.json."""
    meta = fetch_github_issue(issue_number, repo_root)
    if explicit_task_id and explicit_task_id.strip():
        custom_branch = explicit_task_id.strip()
        is_valid, err = validate_branch_name(custom_branch)
        if not is_valid:
            raise ValueError(f"Rama explícita inválida '{custom_branch}': {err}")
        meta["branch"] = custom_branch

    branch = str(meta["branch"])
    ref_path = repo_root / ACTIVE_ISSUE_REL
    if dry_run:
        print(f"{MSG_DRY_RUN} Asignaría @me a issue #{issue_number} y crearía rama '{branch}'")
        print(f"{MSG_DRY_RUN} Registraría referencia en: {ref_path}")
        return meta

    subprocess.run(
        ["gh", "issue", "edit", str(issue_number), "--add-assignee", "@me"],
        cwd=str(repo_root),
        capture_output=True,
        text=True,
        encoding=ENCODING_UTF8,
        check=False,
    )
    _checkout_issue_branch(repo_root, branch)
    ref_path.parent.mkdir(parents=True, exist_ok=True)
    ref_path.write_text(json.dumps(meta, indent=2, ensure_ascii=False) + "\n", encoding=ENCODING_UTF8)
    print(f"{MSG_OK} Issue #{issue_number} vinculada a rama '{branch}' ({ref_path})")
    return meta


def _fetch_issue_node_id(issue_number: int, repo_root: Path) -> Optional[str]:
    proc = subprocess.run(
        ["gh", "issue", "view", str(issue_number), "--json", "id"],
        cwd=str(repo_root),
        capture_output=True,
        text=True,
        encoding=ENCODING_UTF8,
        check=False,
    )
    if proc.returncode != 0 or not proc.stdout.strip():
        return None
    try:
        data = json.loads(proc.stdout)
        return str(data.get("id") or "") or None
    except ValueError:
        return None


def create_sub_issue(
    parent_issue: int,
    title: str,
    body: str,
    repo_root: Path,
    labels: Sequence[str] = ("enhancement", "harness:both"),
    dry_run: bool = False,
) -> Dict[str, Any]:
    """Crea una sub-issue en GitHub y la enlaza a la issue padre mediante GraphQL addSubIssue."""
    if parent_issue <= 0:
        raise ValueError(f"Número de issue padre inválido: {parent_issue}")
    if dry_run:
        return {"parent_issue": parent_issue, K_SUB_ISSUE: 0, "url": "", "linked": False}

    label_arg = ",".join(labels) if labels else "enhancement,harness:both"
    full_body = f"Parent Issue: #{parent_issue}\n\n{body.strip()}".strip()
    create_proc = subprocess.run(
        ["gh", "issue", "create", "--title", title.strip(), "--body", full_body, "--label", label_arg],
        cwd=str(repo_root),
        capture_output=True,
        text=True,
        encoding=ENCODING_UTF8,
        check=False,
    )
    if create_proc.returncode != 0:
        raise RuntimeError(f"Error creando sub-issue: {(create_proc.stderr or create_proc.stdout).strip()}")

    url = create_proc.stdout.strip().splitlines()[-1].strip()
    match = re.search(r"/issues/(\d+)", url)
    if not match:
        raise RuntimeError(f"No se pudo extraer el número de sub-issue desde '{url}'")
    sub_num = int(match.group(1))

    parent_id = _fetch_issue_node_id(parent_issue, repo_root)
    child_id = _fetch_issue_node_id(sub_num, repo_root)
    linked = False
    if parent_id and child_id:
        mutation = (
            "mutation($parentId:ID!,$childId:ID!){"
            "addSubIssue(input:{issueId:$parentId,subIssueId:$childId}){"
            "issue{number}subIssue{number}}}"
        )
        gql_proc = subprocess.run(
            [
                "gh",
                "api",
                "graphql",
                "-H",
                "GraphQL-Features: sub_issues",
                "-f",
                f"query={mutation}",
                "-f",
                f"parentId={parent_id}",
                "-f",
                f"childId={child_id}",
            ],
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            encoding=ENCODING_UTF8,
            check=False,
        )
        linked = gql_proc.returncode == 0
    return {"parent_issue": parent_issue, K_SUB_ISSUE: sub_num, "url": url, "linked": linked}


def _extract_criteria_and_mermaid(artifacts: Sequence[Path]) -> Tuple[List[str], List[str]]:
    criteria: List[str] = []
    mermaids: List[str] = []
    mermaid_re = re.compile(r"```mermaid\s+.*?```", re.DOTALL)
    for path in artifacts:
        if not path.is_file():
            continue
        text = path.read_text(encoding=ENCODING_UTF8)
        for line in text.splitlines():
            stripped = line.strip()
            if stripped.startswith(("- [ ]", "- [x]", "* [ ]", "* [x]")) and len(criteria) < 12:
                criteria.append(stripped)
        for block in mermaid_re.findall(text):
            if len(mermaids) < 3:
                mermaids.append(block.strip())
    return criteria, mermaids


def format_lifecycle_artifacts_comment(
    task_id: str,
    artifacts: Sequence[Path],
    repo_root: Path,
) -> str:
    """Construye un comentario Markdown con enlaces a REQ/PLAN, criterios de aceptación y diagramas Mermaid."""
    lines = [
        f"## Artefactos del Ciclo de Vida (`{task_id}`)",
        "",
        "### Documentos Generados",
        "",
    ]
    for path in artifacts:
        try:
            rel = path.resolve().relative_to(repo_root.resolve()).as_posix()
        except ValueError:
            rel = path.name
        lines.append(f"- `{rel}`")

    criteria, mermaids = _extract_criteria_and_mermaid(artifacts)
    if criteria:
        lines.extend(["", "### Criterios de Aceptación y Checklist", ""] + criteria)
    if mermaids:
        lines.extend(["", "### Diagramas de Arquitectura (Mermaid)", ""] + mermaids)
    return "\n".join(lines) + "\n"


def attach_lifecycle_artifacts(
    issue_number: int,
    task_id: str,
    artifacts: Sequence[Path],
    repo_root: Path,
    dry_run: bool = False,
) -> str:
    """Publica el resumen de artefactos del lifecycle (REQ, PLAN, Mermaid, criterios) en la GitHub Issue."""
    comment = format_lifecycle_artifacts_comment(task_id, artifacts, repo_root)
    if dry_run:
        print(f"{MSG_DRY_RUN} Adjuntaría resumen de {len(artifacts)} artefactos en issue #{issue_number}")
        return comment

    subprocess.run(
        ["gh", "issue", "comment", str(issue_number), "--body", comment],
        cwd=str(repo_root),
        capture_output=True,
        text=True,
        encoding=ENCODING_UTF8,
        check=False,
    )
    print(f"{MSG_OK} Artefactos adjuntados en GitHub Issue #{issue_number}")
    return comment


def render_template_content(content: str, task_id: str, date_str: str) -> str:
    """Sustituye marcadores de posición en el contenido de la plantilla."""
    rendered = content.replace("<id_tarea>", task_id)
    return rendered.replace("YYYY-MM-DD", date_str)


def _scaffold_idea_entry(task_id: str, slug: str, dmap: DocsMap, dry_run: bool) -> List[Path]:
    """Registra una nueva entrada estructurada en IDEAS.md desde el punto de entrada IDEAS."""
    ideas_path = dmap.resolve("ideas")
    existing = ideas_path.read_text(encoding=ENCODING_UTF8) if ideas_path.is_file() else "# Catálogo de Propuestas e Ideas de Ingeniería (`IDEAS.md`)\n"
    idea_header = f"## Idea {slug}: {task_id}"

    if idea_header in existing:
        print(f"{MSG_WARN} Idea ya existente (omitida): {ideas_path}")
        return []

    block = (
        f"\n{idea_header}\n\n"
        f"- Status: Approved\n"
        f"- Sector: Universal Engineering & Architecture\n"
        f"- DataType: Code / Markdown Artifacts\n"
        f"- Objective: Diseñar e implementar {task_id}\n"
        f"- Description: Propuesta registrada desde el punto de entrada IDEAS para '{task_id}'.\n"
    )

    if dry_run:
        print(f"{MSG_DRY_RUN} Registraría idea en: {ideas_path}")
    else:
        ideas_path.parent.mkdir(parents=True, exist_ok=True)
        updated = existing.rstrip() + "\n" + block
        ideas_path.write_text(updated, encoding=ENCODING_UTF8)
        print(f"{MSG_OK} Idea registrada en: {ideas_path}")

    return [ideas_path]


def _backlog_id(slug: str) -> str:
    """Id válido para backlog.py (minúsculas, cifras y guiones)."""
    return re.sub(r"[^a-z0-9]+", "-", slug.lower()).strip("-") or "task"


def _scaffold_todo_quick_entry(
    ctx: ScaffoldContext,
    dmap: DocsMap,
) -> List[Path]:
    """Registra la tarea en TODO.md y crea la nota QUICK_<slug>.md con las secciones comunes."""
    todo_path = dmap.resolve("todo")
    quick_dir = dmap.resolve("quick")
    quick_path = quick_dir / f"QUICK_{ctx.slug}.md"
    created: List[Path] = []

    existing_todo = todo_path.read_text(encoding=ENCODING_UTF8) if todo_path.is_file() else "# PROTOCOLO DE EJECUCIÓN Y BACKLOG MAESTRO\n"
    task_marker = f"**{ctx.task_id}**"
    if task_marker not in existing_todo:
        task_block = (
            f"\n- [ ] {task_marker}\n"
            f"  <!-- aagy-task: id={_backlog_id(ctx.slug)} -->\n"
            f"  Nota: `{quick_path.name}` (Motivación, Criterios de aceptación, Paridad, Artefactos).\n"
        )
        if ctx.dry_run:
            print(f"{MSG_DRY_RUN} Añadiría tarea en: {todo_path}")
        else:
            todo_path.parent.mkdir(parents=True, exist_ok=True)
            todo_path.write_text(existing_todo.rstrip() + "\n" + task_block, encoding=ENCODING_UTF8)
            print(f"{MSG_OK} Tarea añadida a: {todo_path}")
        created.append(todo_path)

    if not quick_path.exists() or ctx.force:
        quick_body = (
            f"# Tarea rápida: {ctx.task_id}\n\n"
            f"> **Fecha**: `{ctx.date_str}` | **Entrada**: `TODO` (sin REQ ni PLAN)\n\n"
            f"<!-- Mismas secciones que las issues y la PR (#93). -->\n\n"
            f"## 1. Motivación\n\nQué se hace y por qué.\n\n"
            f"## 2. Criterios de aceptación\n\n"
            f"- [ ] Tests en verde y `python scripts/py/ci_local.py run` en verde.\n\n"
            f"## 3. Paridad aagy ↔ aagy-ecc\n\n- [ ] Igual en los dos plugins o asimetría declarada.\n\n"
            f"## 4. Artefactos\n\n- `<rutas>`; cierre con `complete-task-pr`.\n"
        )
        if ctx.dry_run:
            print(f"{MSG_DRY_RUN} Generaría: {quick_path}")
        else:
            quick_dir.mkdir(parents=True, exist_ok=True)
            quick_path.write_text(quick_body, encoding=ENCODING_UTF8)
            print(f"{MSG_OK} Creado: {quick_path}")
        created.append(quick_path)

    return created


def _scaffold_phase_templates(ctx: ScaffoldContext, phase_key: str) -> List[Path]:
    """Instancia las plantillas de las fases seleccionadas hacia `output_dir`."""
    if not ctx.templates_dir.exists() and not any(d.is_dir() for d in doc_templates.PLUGIN_TEMPLATE_DIRS):
        raise FileNotFoundError(f"Directorio de plantillas no encontrado: {ctx.templates_dir}")

    if not ctx.dry_run:
        ctx.output_dir.mkdir(parents=True, exist_ok=True)

    selected_prefixes = PHASE_SLICES[phase_key]
    created_files: List[Path] = []

    for prefix, tmpl_filename in PHASE_TEMPLATES:
        if prefix not in selected_prefixes:
            continue
        tmpl_path = doc_templates.find_template(tmpl_filename, ctx.templates_dir)
        target_path = ctx.output_dir / f"{prefix}_{ctx.slug}.md"

        if tmpl_path is None:
            print(f"{MSG_WARN} Plantilla base no encontrada: {ctx.templates_dir / tmpl_filename}", file=sys.stderr)
            continue

        if target_path.exists() and not ctx.force:
            print(f"{MSG_WARN} Archivo ya existente (omitido): {target_path}")
            continue

        content = tmpl_path.read_text(encoding=ENCODING_UTF8)
        rendered = doc_templates.apply_extensions(
            render_template_content(content, ctx.task_id, ctx.date_str), prefix, ctx.repo_root)

        if ctx.dry_run:
            print(f"{MSG_DRY_RUN} Generaría: {target_path} (de {tmpl_filename})")
        else:
            target_path.write_text(rendered, encoding=ENCODING_UTF8)
            print(f"{MSG_OK} Creado: {target_path}")

        created_files.append(target_path)

    return created_files


def scaffold_lifecycle_task(
    task_id: str,
    repo_root: Path,
    templates_rel: Optional[str] = None,
    output_rel: Optional[str] = None,
    force: bool = False,
    dry_run: bool = False,
    phase: str = "ALL",
) -> List[Path]:
    """Genera los artefactos del ciclo de vida según el punto de entrada `phase`."""
    phase_key = phase.strip().upper()
    if phase_key not in VALID_PHASES:
        raise ValueError(f"Fase inválida '{phase}'. Permitidas: {', '.join(VALID_PHASES)}")

    dmap = load_docs_map(repo_root)
    slug = slugify_task_id(task_id)
    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    if phase_key == "IDEAS":
        return _scaffold_idea_entry(task_id, slug, dmap, dry_run)

    resolved_templates = repo_root / templates_rel if templates_rel else dmap.resolve("templates")
    resolved_output = repo_root / output_rel if output_rel else dmap.resolve("plans")

    ctx = ScaffoldContext(
        task_id=task_id,
        slug=slug,
        date_str=date_str,
        templates_dir=resolved_templates,
        repo_root=repo_root,
        output_dir=resolved_output,
        force=force,
        dry_run=dry_run,
    )

    if phase_key == "TODO":
        return _scaffold_todo_quick_entry(ctx, dmap)

    return _scaffold_phase_templates(ctx, phase_key)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Instancia artefactos del Engineering Lifecycle desde cualquier punto de entrada (IDEAS, REQ, PLAN, TODO, ALL)."
    )
    parser.add_argument("--task-id", default=None, help="ID o rama de la tarea (ej. feat/app/export-csv)")
    parser.add_argument("--issue", type=int, default=None, help="Número de GitHub Issue para auto-asignar y crear rama gh-<N>")
    parser.add_argument("--parent-issue", type=int, default=None, help="Crea una sub-issue nativa bajo la issue padre #<N>")
    parser.add_argument("--attach-issue", action="store_true", help="Adjunta resumen de artefactos REQ/PLAN/Mermaid a la issue")
    parser.add_argument("--repo-root", default=".", help="Ruta a la raíz del repositorio")
    parser.add_argument("--templates-dir", default=None, help="Ruta a plantillas (opcional, lee docs-map.json)")
    parser.add_argument("--output-dir", default=None, help="Ruta destino para planes (opcional, lee docs-map.json)")
    parser.add_argument(
        "--phase",
        default="ALL",
        choices=list(VALID_PHASES),
        help="Punto de entrada del flujo flexible (ALL, IDEAS, REQ, PLAN, TODO, DOCS, REVIEW).",
    )
    parser.add_argument("--force", action="store_true", help="Sobrescribir archivos existentes")
    parser.add_argument("--dry-run", action="store_true", help="Simular sin modificar archivos")
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    """Punto de entrada CLI para la instanciación de tareas del ciclo de vida."""
    parser = build_parser()
    args = parser.parse_args(argv)
    root = Path(args.repo_root).resolve()

    if not args.task_id and not args.issue and not args.parent_issue:
        print("[ERROR] Debe especificar --task-id, --issue <N> o --parent-issue <N>.", file=sys.stderr)
        return 1

    try:
        target_issue = args.issue
        if args.parent_issue is not None and target_issue is None:
            sub_title = args.task_id or f"[feat]-[aagy]: sub-issue de #{args.parent_issue}"
            sub_res = create_sub_issue(
                parent_issue=args.parent_issue,
                title=sub_title,
                body=f"Sub-issue generada desde `new_lifecycle_task.py` para `#{args.parent_issue}`.",
                repo_root=root,
                dry_run=args.dry_run,
            )
            target_issue = int(sub_res[K_SUB_ISSUE]) if sub_res.get(K_SUB_ISSUE) else None

        effective_task_id = args.task_id
        if target_issue is not None:
            meta = bind_github_issue(
                issue_number=target_issue,
                repo_root=root,
                dry_run=args.dry_run,
                explicit_task_id=args.task_id,
            )
            effective_task_id = str(meta["branch"])

        created = scaffold_lifecycle_task(
            task_id=str(effective_task_id),
            repo_root=root,
            templates_rel=args.templates_dir,
            output_rel=args.output_dir,
            force=args.force,
            dry_run=args.dry_run,
            phase=args.phase,
        )
        if args.attach_issue and target_issue is not None and created:
            attach_lifecycle_artifacts(
                issue_number=target_issue,
                task_id=str(effective_task_id),
                artifacts=created,
                repo_root=root,
                dry_run=args.dry_run,
            )
        print(f"\n[OK] Ciclo de vida ({args.phase}) instanciado con éxito ({len(created)} artefactos).")
        return 0
    except Exception as exc:
        print(f"[ERROR] Error al instanciar ciclo de vida: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
