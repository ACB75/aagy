---
name: Chore / Refactor (chore, refactor, infra, docs)
about: Refactorización, mantenimiento de CI/CD, optimización de tokens o gobernanza documental
title: "[refactor]-[aagy,aagy-ecc]: "
labels:
  - harness:both
assignees:
  - ACB75
---

# Chore / Refactor (`refactor/*`, `chore/*`, `infra/*`, `docs/*`)

## 1. Objetivo y Justificación Técnica

Explica qué se simplifica, optimiza o automatiza sin alterar contratos existentes (*Zero-Breaking Changes*).

## 2. Módulos y Scripts Afectados

- `rules/` / `skills/` / `agents/`
- `scripts/py/` / `scripts/ps1/` / `scripts/sh/` (POSIX LF `\n`)
- `aagy-ecc/` (sincronizado vía `scripts/py/sync_aagy_ecc.py`)
- `doc/` (`.governance/docs-map.json` v2)

## 3. Checklist de Calidad y Paridad

- [ ] SonarQube Quality Gate Rating `A` (`S3776 <= 15`, `S107 <= 7`, `S1192 = 0`)
- [ ] `sync_aagy_ecc.py --check` en `[IN_SYNC]` y `audit-plugin-parity.ps1` en `[PASS]`
- [ ] `lint-markdown.ps1 -CheckOnly` y `map_docs.py --check-docs-map` sin errores
