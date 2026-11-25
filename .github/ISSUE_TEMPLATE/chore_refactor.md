---
name: Chore / Refactor (chore, refactor, infra, docs)
about: Refactorización, mantenimiento, optimización de tokens o documentación
title: "[refactor]-[aagy,aagy-ecc]: "
labels:
  - harness:both
---

# Chore / Refactor (`refactor/*`, `chore/*`, `infra/*`, `docs/*`)

<!-- Mismas secciones que la PR y la tarea de TODO.md (plantilla base, #93). La tarea lleva issue=<N>. -->

## 1. Motivación

Qué se simplifica, optimiza o automatiza, sin romper contratos.

## 2. Criterios de aceptación

- [ ] `python scripts/py/ci_local.py run` en verde.

## 3. Paridad aagy ↔ aagy-ecc

- [ ] `sync_aagy_ecc.py --check` en `[SYNCED]` y `audit_plugin_parity.py` en `[PASS]`.

## 4. Artefactos

- Ficheros o documentos afectados: `<rutas>`
