---
title: "**UI de Claude Code y AGY: status line, avisos de escritorio, ccusage y extensiones de VS Code**"
status: COMPLETED
completed_at: "2026-11-25 06:00:00"
---

# TODO: **UI de Claude Code y AGY: status line, avisos de escritorio, ccusage y extensiones de VS Code**

## 1. Descripción de la Tarea

- **Estado**: COMPLETED
- **Fecha de Finalización**: 2026-11-25 06:00:00

### Detalle Original

  <!-- aagy-task: id=ui-statusline-notify epic=ui-de-claude-code-y-agy-116 issue=116 -->

## 2. Verificación y Criterios de Aceptación

- [x] Tarea implementada y verificada contra criterios de aceptación (CA-01..CA-06 de #116, `test_aagy_ui.py`).

## 3. Entregables y Notas de Cierre

`aagy_statusline.py`, `aagy_notify.py` y `aagy_ui.py` (espejados en aagy-ecc), comando `/aagy-ui`, skill `aagy-ui`,
hooks `SessionStart`/`Stop`/`Notification` en aagy-ecc y `Stop` en aagy, clave `ui` en `aagy_config`,
REQ/PLAN en `doc/06-backlog/plans/` y runbook `MANUAL_ui.md`.

## 4. Metadatos de Integración y Commit

- **Rama / PR**: `feat/aagy/ui-statusline-notify`
- **Commit SHA**: `pendiente del squash`
- **Fecha**: `2026-11-25 06:00:00`
- **Gobernanza**: Quality Gate A / markdownlint OK
