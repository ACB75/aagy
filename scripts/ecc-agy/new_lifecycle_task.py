"""Generador e instanciador de artefactos del ciclo de vida de ingeniería (4 fases).

Crea los archivos REQ, PLAN, DOCS y REVIEW a partir de las plantillas canónicas.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path
import re
import sys

# Constantes SonarQube S1192
MSG_OK = "[PASS]"
MSG_WARN = "[WARN]"
DEFAULT_TEMPLATES_DIR = "doc/templates"
DEFAULT_OUTPUT_DIR = "doc/plan"

PHASE_TEMPLATES = [
    ("REQ", "01_TOMA_REQUISITOS_E_IMPACTO.md"),
    ("PLAN", "02_PLAN_ACCION_ARQUITECTURA.md"),
    ("DOCS", "03_DOCUMENTACION_Y_RELEASE_NOTES.md"),
    ("REVIEW", "04_PROPUESTA_COMMITS_PR.md"),
]


def slugify_task_id(task_id: str) -> str:
    """Convierte el ID o rama de tarea en un slug limpio para nombres de archivo."""
    # Eliminar prefijos comunes de ramas
    cleaned = re.sub(r"^(feat|fix|refactor|infra|chore|docs|test)/", "", task_id)
    slug = re.sub(r"[^a-zA-Z0-9_\-]+", "_", cleaned).strip("_")
    return slug.replace("-", "_") if slug else "task"


def render_template_content(content: str, task_id: str, date_str: str) -> str:
    """Sustituye marcadores de posición en el contenido de la plantilla."""
    rendered = content.replace("<id_tarea>", task_id)
    rendered = rendered.replace("YYYY-MM-DD", date_str)
    return rendered


def scaffold_lifecycle_task(
    task_id: str,
    repo_root: Path,
    templates_rel: str = DEFAULT_TEMPLATES_DIR,
    output_rel: str = DEFAULT_OUTPUT_DIR,
    force: bool = False,
    dry_run: bool = False,
) -> list[Path]:
    """Genera los 4 artefactos del ciclo de vida para la tarea indicada."""
    slug = slugify_task_id(task_id)
    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    templates_dir = repo_root / templates_rel
    output_dir = repo_root / output_rel

    if not templates_dir.exists():
        raise FileNotFoundError(f"Directorio de plantillas no encontrado: {templates_dir}")

    if not dry_run:
        output_dir.mkdir(parents=True, exist_ok=True)

    created_files: list[Path] = []

    for prefix, tmpl_filename in PHASE_TEMPLATES:
        tmpl_path = templates_dir / tmpl_filename
        target_path = output_dir / f"{prefix}_{slug}.md"

        if not tmpl_path.exists():
            print(f"{MSG_WARN} Plantilla base no encontrada: {tmpl_path}", file=sys.stderr)
            continue

        if target_path.exists() and not force:
            print(f"{MSG_WARN} Archivo ya existente (omitido): {target_path}")
            continue

        content = tmpl_path.read_text(encoding="utf-8")
        rendered = render_template_content(content, task_id, date_str)

        if dry_run:
            print(f"[DRY-RUN] Generaría: {target_path} (de {tmpl_filename})")
        else:
            target_path.write_text(rendered, encoding="utf-8")
            print(f"{MSG_OK} Creado: {target_path}")

        created_files.append(target_path)

    return created_files


def main() -> int:
    """Punto de entrada CLI para la instanciación de tareas del ciclo de vida."""
    parser = argparse.ArgumentParser(
        description="Instancia las 4 plantillas del Engineering Lifecycle para una tarea."
    )
    parser.add_argument("--task-id", required=True, help="ID o rama de la tarea (ej. feat/kakebo/export-csv)")
    parser.add_argument("--repo-root", default=".", help="Ruta a la raíz del repositorio")
    parser.add_argument("--templates-dir", default=DEFAULT_TEMPLATES_DIR, help="Ruta a la carpeta de plantillas")
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR, help="Ruta destino para los planes")
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
        )
        print(f"\n[OK] Ciclo de vida instanciado con éxito ({len(created)} archivos).")
        return 0
    except Exception as exc:
        print(f"[ERROR] Error al instanciar ciclo de vida: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
