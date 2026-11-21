"""Generador e instanciador de artefactos del ciclo de vida de ingeniería (4 fases).

Soporta rutas parametrizadas vía `.governance/docs-map.json` (con fallback a `doc/` clásico)
y puntos de entrada flexibles: `[IDEAS -> REQUISITOS -> PLAN -> TODO]` (`--phase`).
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
import re
import sys
from typing import Dict, List, Optional, Tuple

_SCRIPT_DIR = str(Path(__file__).resolve().parent)
if _SCRIPT_DIR not in sys.path:
    sys.path.insert(0, _SCRIPT_DIR)

from docs_map import DocsMap, load_docs_map

# Constantes SonarQube S1192
MSG_OK = "[PASS]"
MSG_WARN = "[WARN]"
MSG_DRY_RUN = "[DRY-RUN]"
DEFAULT_TEMPLATES_DIR = "doc/templates"
DEFAULT_OUTPUT_DIR = "doc/plan"

VALID_PHASES: Tuple[str, ...] = ("ALL", "IDEAS", "REQ", "PLAN", "TODO", "DOCS", "REVIEW")

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


@dataclass(frozen=True)
class ScaffoldContext:
    """Contexto inmutable para la instanciación de artefactos de una tarea."""

    task_id: str
    slug: str
    date_str: str
    templates_dir: Path
    output_dir: Path
    force: bool
    dry_run: bool


def slugify_task_id(task_id: str) -> str:
    """Convierte el ID o rama de tarea en un slug limpio para nombres de archivo."""
    cleaned = re.sub(r"^(feat|fix|refactor|infra|chore|docs|test)/", "", task_id)
    slug = re.sub(r"[^a-zA-Z0-9_\-]+", "_", cleaned).strip("_")
    return slug.replace("-", "_") if slug else "task"


def render_template_content(content: str, task_id: str, date_str: str) -> str:
    """Sustituye marcadores de posición en el contenido de la plantilla."""
    rendered = content.replace("<id_tarea>", task_id)
    return rendered.replace("YYYY-MM-DD", date_str)


def _scaffold_idea_entry(task_id: str, slug: str, dmap: DocsMap, dry_run: bool) -> List[Path]:
    """Registra una nueva entrada estructurada en IDEAS.md desde el punto de entrada IDEAS."""
    ideas_path = dmap.resolve("ideas")
    existing = ideas_path.read_text(encoding="utf-8") if ideas_path.is_file() else "# Catálogo de Propuestas e Ideas de Ingeniería (`IDEAS.md`)\n"
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
        ideas_path.write_text(updated, encoding="utf-8")
        print(f"{MSG_OK} Idea registrada en: {ideas_path}")

    return [ideas_path]


def _scaffold_todo_quick_entry(
    ctx: ScaffoldContext,
    dmap: DocsMap,
) -> List[Path]:
    """Registra tarea 7-fases en TODO.md y crea nota rápida QUICK_<slug>.md."""
    todo_path = dmap.resolve("todo")
    quick_dir = dmap.resolve("quick")
    quick_path = quick_dir / f"QUICK_{ctx.slug}.md"
    created: List[Path] = []

    existing_todo = todo_path.read_text(encoding="utf-8") if todo_path.is_file() else "# PROTOCOLO DE EJECUCIÓN Y BACKLOG MAESTRO\n"
    task_marker = f"**Tarea: {ctx.task_id}**"
    if task_marker not in existing_todo:
        task_block = (
            f"\n- [ ] {task_marker}\n"
            f"  - **01 - ROLE:** Principal Software & Automation Architect.\n"
            f"  - **02 - CONTEXT:** `[Objective: Implementar {ctx.task_id}]` `[Quick Note: {quick_path.name}]`.\n"
            f"  - **03 - PHASE 1 (ANALYSIS):** Revisar activos reutilizables (DRY) y contratos impactados.\n"
            f"  - **04 - PHASE 2 (STRATEGY):** Evaluar 3 alternativas antes de implementar.\n"
            f"  - **05 - PHASE 3 (EXECUTION):** Ejecutar ciclo TDD RED -> GREEN -> REFACTOR.\n"
            f"  - **06 - PHASE 4 (CRITIC):** Verificar cobertura >= 80%, SonarQube Rating A y markdownlint.\n"
            f"  - **07 - PHASE 5 (FORMAT):** Cierre atómico con complete-task-pr.\n"
        )
        if ctx.dry_run:
            print(f"{MSG_DRY_RUN} Añadiría tarea en: {todo_path}")
        else:
            todo_path.parent.mkdir(parents=True, exist_ok=True)
            todo_path.write_text(existing_todo.rstrip() + "\n" + task_block, encoding="utf-8")
            print(f"{MSG_OK} Tarea añadida a: {todo_path}")
        created.append(todo_path)

    if not quick_path.exists() or ctx.force:
        quick_body = (
            f"# Quick Task: {ctx.task_id}\n\n"
            f"> **Fecha**: `{ctx.date_str}` | **Modo**: Entrada directa `TODO` (sin ceremonia previa)\n\n"
            f"## Checklist Operativo\n\n"
            f"- [ ] Tests unitarios TDD en verde (`pytest` >= 80%)\n"
            f"- [ ] Linter Markdown (`lint-markdown`) y SonarQube Rating A\n"
            f"- [ ] Integración vía `complete-task-pr`\n"
        )
        if ctx.dry_run:
            print(f"{MSG_DRY_RUN} Generaría: {quick_path}")
        else:
            quick_dir.mkdir(parents=True, exist_ok=True)
            quick_path.write_text(quick_body, encoding="utf-8")
            print(f"{MSG_OK} Creado: {quick_path}")
        created.append(quick_path)

    return created


def _scaffold_phase_templates(ctx: ScaffoldContext, phase_key: str) -> List[Path]:
    """Instancia las plantillas de las fases seleccionadas hacia `output_dir`."""
    if not ctx.templates_dir.exists():
        raise FileNotFoundError(f"Directorio de plantillas no encontrado: {ctx.templates_dir}")

    if not ctx.dry_run:
        ctx.output_dir.mkdir(parents=True, exist_ok=True)

    selected_prefixes = PHASE_SLICES[phase_key]
    created_files: List[Path] = []

    for prefix, tmpl_filename in PHASE_TEMPLATES:
        if prefix not in selected_prefixes:
            continue
        tmpl_path = ctx.templates_dir / tmpl_filename
        target_path = ctx.output_dir / f"{prefix}_{ctx.slug}.md"

        if not tmpl_path.exists():
            print(f"{MSG_WARN} Plantilla base no encontrada: {tmpl_path}", file=sys.stderr)
            continue

        if target_path.exists() and not ctx.force:
            print(f"{MSG_WARN} Archivo ya existente (omitido): {target_path}")
            continue

        content = tmpl_path.read_text(encoding="utf-8")
        rendered = render_template_content(content, ctx.task_id, ctx.date_str)

        if ctx.dry_run:
            print(f"{MSG_DRY_RUN} Generaría: {target_path} (de {tmpl_filename})")
        else:
            target_path.write_text(rendered, encoding="utf-8")
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
        output_dir=resolved_output,
        force=force,
        dry_run=dry_run,
    )

    if phase_key == "TODO":
        return _scaffold_todo_quick_entry(ctx, dmap)

    return _scaffold_phase_templates(ctx, phase_key)


def main() -> int:
    """Punto de entrada CLI para la instanciación de tareas del ciclo de vida."""
    parser = argparse.ArgumentParser(
        description="Instancia artefactos del Engineering Lifecycle desde cualquier punto de entrada (IDEAS, REQ, PLAN, TODO, ALL)."
    )
    parser.add_argument("--task-id", required=True, help="ID o rama de la tarea (ej. feat/kakebo/export-csv)")
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

    args = parser.parse_args()
    root = Path(args.repo_root).resolve()

    try:
        created = scaffold_lifecycle_task(
            task_id=args.task_id,
            repo_root=root,
            templates_rel=args.templates_dir,
            output_rel=args.output_dir,
            force=args.force,
            dry_run=args.dry_run,
            phase=args.phase,
        )
        print(f"\n[OK] Ciclo de vida ({args.phase}) instanciado con éxito ({len(created)} artefactos).")
        return 0
    except Exception as exc:
        print(f"[ERROR] Error al instanciar ciclo de vida: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
