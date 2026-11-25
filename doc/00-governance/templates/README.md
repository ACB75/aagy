# Plantillas del ciclo de vida (`00-governance/templates/`)

> **Flujo**: `1. Requisitos e impacto` -> `2. Plan y TDD` -> `3. Documentación y notas de versión` -> `4. Commits y PR`
> **Entradas flexibles**: ver [`MANUAL_WORKFLOW.md`](../MANUAL_WORKFLOW.md) (`IDEAS` | `REQ` | `PLAN` | `TODO`)

---

## 1. Plantilla base

Todas las plantillas heredan [`TEMPLATE_BASE.md`](TEMPLATE_BASE.md). Llevan la misma cabecera (ID de tarea, fecha, autor/rol, estado, ubicación) y estas secciones, en este orden:

1. `0. Estado actual`
2. `1. Contexto y objetivos`
3. el cuerpo propio del tipo
4. el marcador `<!-- aagy-extensions -->`
5. `Criterios de aceptación`
6. `Paridad aagy ↔ aagy-ecc`
7. `Preguntas abiertas`
8. `Referencias`

`python scripts/py/doc_templates.py check` comprueba el esqueleto y forma parte de `ci_local.py run`. Las plantillas no llevan nombres de proyectos, hosts, dominios ni usuarios.

La fase 3 va antes que la 4 para que la documentación viaje en el mismo squash que el código.

## 2. Índice

| Plantilla | Cuerpo propio |
| :--- | :--- |
| [`TEMPLATE_BASE.md`](TEMPLATE_BASE.md) | Esqueleto común. |
| [`01_TOMA_REQUISITOS_E_IMPACTO.md`](01_TOMA_REQUISITOS_E_IMPACTO.md) | Requisitos funcionales y no funcionales, impacto y retrocompatibilidad. |
| [`02_PLAN_ACCION_ARQUITECTURA.md`](02_PLAN_ACCION_ARQUITECTURA.md) | Diseño, pasos TDD, decisiones y costes, riesgos y rollback. |
| [`03_DOCUMENTACION_Y_RELEASE_NOTES.md`](03_DOCUMENTACION_Y_RELEASE_NOTES.md) | Notas de versión y espina documental. |
| [`04_PROPUESTA_COMMITS_PR.md`](04_PROPUESTA_COMMITS_PR.md) | Título y cuerpo del commit y la PR, revisión previa. |
| [`TEMPLATE_ADR.md`](TEMPLATE_ADR.md) | Opciones, decisión y consecuencias. |
| [`TEMPLATE_POSTMORTEM.md`](TEMPLATE_POSTMORTEM.md) | 5W, causa raíz y acciones (sin culpables). |

## 3. Puntos de extensión

Un repo consumidor añade sus propias secciones sin tocar el plugin. Las declara en `.governance/docs-map.json`:

```json
{
  "template_extensions": {
    "REQ": ["doc/00-governance/extensions/impact_matrix.md"],
    "*": ["doc/00-governance/extensions/common.md"]
  }
}
```

Al instanciar una plantilla, `new_lifecycle_task.py` inserta esos ficheros en el marcador `<!-- aagy-extensions -->`. Las claves son `REQ`, `PLAN`, `DOCS` y `REVIEW`, y `*` vale para todas. Las rutas que salen del repo se ignoran. [`extensions/EXAMPLE_impact_matrix.md`](extensions/EXAMPLE_impact_matrix.md) es un ejemplo genérico.

Si el repo no tiene una plantilla, se usa la del plugin. En `aagy-ecc` las plantillas están en `templates/lifecycle/`, copiadas por `sync_aagy_ecc.py`.

## 4. Uso

```bash
python scripts/py/new_lifecycle_task.py --task-id "feat/<proyecto>/<id>" --phase REQ
```

Tras implementar y validar con `python scripts/py/ci_local.py run`, cierra la tarea con `complete-task-pr`.
