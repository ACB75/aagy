# ADR-0003: Arquitectura Documental `/doc` v2, `.governance/docs-map.json` Parametrizado y Paridad Manual

- **Estado**: `accepted`
- **Fecha**: `2026-11-20`
- **Decisores**: `Documentation Governance & Developer Experience Architect`

---

## 1. Contexto

La estructura clásica de `doc/` acumulaba documentos vivos, guías de referencia sueltas (`README.md` duplicado con `INDEX.md`, `STACK_MODERNO_GOOGLE.md`, `the-security-guide.md`), planes históricos sin vigencia en `doc/plan/` y acoplamiento rígido de rutas en los scripts de automatización (`doc/TODO.md`, `doc/TODO_DONE/`, `doc/post-mortem/`). Además, repositorios externos como `home-lab` aún operan sobre la convención heredada y el usuario necesitaba ejecutar exactamente los mismos flujos manualmente en terminal con flexibilidad para iniciar desde `IDEAS`, `REQ`, `PLAN` o `TODO`.

---

## 2. Decisión

1. **Implantar la jerarquía `/doc` v2** numerada del ciclo documental (`00-governance/` hasta `06-backlog/`), dejando en la raíz de `doc/` exclusivamente `INDEX.md`, `CONTEXT.md`, `STATUS.md` y `LOG.md`.
2. **Adoptar la convención universal `<folder>/dgrms/`** separando `.puml` (casos de uso), `.bpmn` (procesos de negocio) y `.mmd` (arquitectura, dominio y flujos).
3. **Centralizar la resolución de rutas en `scripts/py/docs_map.py`** consumiendo `.governance/docs-map.json` (esquema `schema_version: 2`) con **fallback automático** a las rutas clásicas v1 (`home-lab`), junto con validación estricta anti path-traversal.
4. **Habilitar flujo flexible `[IDEAS -> REQUISITOS -> PLAN -> TODO]`** en `new_lifecycle_task.py` (`--phase ALL|IDEAS|REQ|PLAN|TODO|DOCS|REVIEW`) y documentar paridad CLI 1-a-1 en [`doc/00-governance/MANUAL_WORKFLOW.md`](../00-governance/MANUAL_WORKFLOW.md).

---

## 3. Consecuencias

- **Positivas**:
  - Cero deriva o duplicidad documental en raíz (`doc/README.md` eliminado, `TEMPLATE_ADR.md` y `TEMPLATE_POSTMORTEM.md` unificados en `00-governance/templates/`).
  - Retrocompatibilidad del 100% (*Zero-Breaking*) para `home-lab` mientras no adopte v2.
  - Operación determinista desde terminal (`pwsh`, `bash`, `python`) equivalente al 100% al uso mediante agentes/plugin.
- **Costes / Mitigaciones**:
  - Actualización de wrappers `.ps1`/`.sh` y suites de prueba para validar ambos esquemas (v2 y fallback clásico), mitigado con pruebas unitarias dedicadas en [`test_docs_map.py`](../../scripts/py/tests/test_docs_map.py).
