---
title: "**Paridad de hooks entre plugins con un solo motor Python (relevo, compactación e inicio)**"
status: COMPLETED
completed_at: "2026-11-25 05:19:24"
---

# TODO: **Paridad de hooks entre plugins con un solo motor Python (relevo, compactación e inicio)**

## 1. Descripción de la Tarea

- **Estado**: COMPLETED
- **Fecha de Finalización**: 2026-11-25 05:19:24

### Detalle Original

  <!-- aagy-task: id=parity-hooks epic=plantilla-generica-ampliable-y-paridad-entre-plugins-91 issue=96 -->

## 2. Verificación y Criterios de Aceptación

- [x] Tarea implementada y verificada contra criterios de aceptación.

## 3. Entregables y Notas de Cierre

hook_safety.py y hook_post_write.py motor único (--format claude|agy); hooks.json raíz con ${AAGY_PLUGIN_ROOT}; asimetrías documentadas; audit_plugin_parity compara eventos y motores.

## 4. Metadatos de Integración y Commit

- **Rama / PR**: `feat/aagy/hooks-parity`
- **Commit SHA**: `b116039`
- **Fecha**: `2026-11-25 05:19:24`
- **Gobernanza**: Quality Gate A / markdownlint OK
