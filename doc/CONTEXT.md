# Contexto de Dominio y Fronteras del Sistema (`doc/CONTEXT.md`)

> **Rol Documental**: Vocabulario estable, arquitectura Two-Tier y límites del ecosistema `aagy` / `aagy-ecc`.  
> **Mapa Maestro**: Ver [doc/INDEX.md](INDEX.md) y [`.governance/docs-map.json`](../.governance/docs-map.json).

---

## 1. Glosario Canónico del Ecosistema

- **Anything Antigravity (`aagy`)**: Plugin y arnés maestro multiplataforma para Google Antigravity y Gemini 3.8, desarrollado desde `AGENTS.md`, `rules/`, `skills/` y `agents/`.
- **Claude Code Subplugin (`aagy-ecc`)**: Distribución coordinada en `aagy-ecc/` para Claude Code CLI con paridad funcional validada por [scripts/py/audit_plugin_parity.py](../scripts/py/audit_plugin_parity.py).
- **Arquitectura Two-Tier (ADR-0001)**:
  - **Tier 1 (Global Plugin)**: Reglas mínimas (`rules/`) y skills transversales instaladas globalmente mediante `install.ps1` o `install.sh` respetando el presupuesto estricto de contexto.
  - **Tier 2 (Lazy / Por Proyecto)**: Skills especializadas, manuales y plantillas cargadas bajo demanda desde el repositorio.
- **Resolución Parametrizada (`.governance/docs-map.json`)**: Contrato en dos esquemas mantenido por [scripts/py/docs_map.py](../scripts/py/docs_map.py):
  - **Esquema v2**: Estructura numerada bajo `doc/` (`doc/00-governance/` hasta `doc/06-backlog/`).
  - **Fallback Clásico v1**: Rutas heredadas para mantener retrocompatibilidad total con consumidores existentes como `app`.

---

## 2. Fronteras de Responsabilidad

| Superficie | Propietario / Responsable | Prohibición / Límite |
| :--- | :--- | :--- |
| **Gobernanza y Estándares** | [doc/00-governance/DOC_STANDARDS.md](00-governance/DOC_STANDARDS.md) | Sin reglas duplicadas en raíz |
| **Paridad Manual CLI** | [doc/00-governance/MANUAL_WORKFLOW.md](00-governance/MANUAL_WORKFLOW.md) | Todo comando de plugin tiene CLI equivalente |
| **Backlog y Ejecución** | [doc/06-backlog/TODO.md](06-backlog/TODO.md) | Sin tareas completadas `[x]` activas |
| **Estado y Métricas** | [doc/STATUS.md](STATUS.md) | Sin historial narrativo extenso |
| **Registro Histórico** | [doc/LOG.md](LOG.md) | Solo hitos e incidentes materiales (append-only) |
