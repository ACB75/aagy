---
name: Bug Report (fix)
about: Reportar un fallo, regresión o incidente operativo en aagy / aagy-ecc
title: "[fix]-[aagy,aagy-ecc]: "
labels:
  - bug
  - harness:both
assignees:
  - ACB75
---

# Bug Report (`fix/*`)

## 1. Síntoma y Comportamiento Observado

Describe el fallo, mensaje de error y código de salida observado.

## 2. Pasos para Reproducir

1. Comando o hook ejecutado:
2. Arnés afectado (`aagy` Antigravity | `aagy-ecc` Claude Code | ambos):
3. Sistema operativo (`Windows 11 pwsh` | `Linux / WSL bash`):

## 3. Comportamiento Esperado

Describe el resultado esperado y la invariante que debe cumplirse.

## 4. Paridad y Post-Mortem (`5-Whys`)

- [ ] Test de regresión (`RED -> GREEN`) incluido en `scripts/py/tests/`
- [ ] Paridad verificada con `pwsh -File scripts/ps1/audit-plugin-parity.ps1`
- [ ] Post-Mortem 5W requerido en `doc/05-post-mortems/PM_fix_<slug>.md`
