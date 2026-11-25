---
name: engineering-lifecycle
description: "Run the 4-phase lifecycle (requirements, plan, docs, PR) from the generic base templates."
metadata:
  origin: AAGY
---

# engineering-lifecycle

Ciclo de vida de 4 fases para cualquier cambio no trivial:
`1. Requisitos e impacto` -> `2. Plan y TDD` -> `3. Documentación y notas de versión` -> `4. Commits y PR`.

## Cuándo usarlo

- Una funcionalidad, un arreglo no trivial, una refactorización o un cambio de infraestructura.
- Un cambio que toca contratos compartidos, esquemas de datos o fronteras del sistema.
- Preparar una versión y sus notas.

## Uso

```bash
python <PLUGIN>/scripts/py/new_lifecycle_task.py --task-id "feat/<proyecto>/<id>" --phase REQ
python <PLUGIN>/scripts/py/new_lifecycle_task.py --issue <N> --phase REQ --attach-issue
python <PLUGIN>/scripts/py/new_lifecycle_task.py --task-id "feat/<proyecto>/<id>" --phase TODO   # sin ceremonia
```

Envoltorios: `<PLUGIN>/scripts/ps1/aagy.ps1 new-lifecycle-task` y `<PLUGIN>/scripts/sh/aagy.sh new-lifecycle-task`. Las rutas salen de `.governance/docs-map.json`.

## Qué hacer

1. **Requisitos** (`01_TOMA_REQUISITOS_E_IMPACTO.md`): RF, CA verificables (dado/cuando/entonces), impacto y retrocompatibilidad. Sin cambios que rompan contratos salvo aprobación.
2. **Plan** (`02_PLAN_ACCION_ARQUITECTURA.md`): reutiliza antes de escribir código nuevo, diseño, TDD (`RED` -> `GREEN` -> `REFACTOR` -> `VERIFY`) y rollback.
3. **Documentación** (`03_DOCUMENTACION_Y_RELEASE_NOTES.md`): notas de versión, ADR si la decisión es difícil de revertir, manuales, `STATUS.md`, `LOG.md` y postmortem en ramas `fix/*`. Va antes de la fase 4 para que viaje en el mismo squash.
4. **PR** (`04_PROPUESTA_COMMITS_PR.md`): rama `<tipo>/<proyecto>/<nombre>`, título `[type]-[projects]: <título>`, `python <PLUGIN>/scripts/py/ci_local.py run` en verde y `complete-task-pr`.

## Reglas

1. Todas las plantillas heredan `TEMPLATE_BASE.md` (`doc_templates.py check`).
2. Lo propio de un proyecto va en sus extensiones (`template_extensions` en `docs-map.json`), nunca en el plugin.
3. Sin auto-merge: la PR la fusiona una persona.

## Paridad

Claude Code: la skill se espeja en `aagy-ecc` y las plantillas viajan en `templates/lifecycle/`. Mismo motor (`new_lifecycle_task.py`).
