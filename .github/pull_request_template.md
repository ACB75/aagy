# Pull Request — Anything Antigravity (`aagy` & `aagy-ecc`)

## 1. Motivación y Resumen de Cambios

- **Qué cambia y por qué**:
- **Módulos afectados**: `[aagy]`, `[aagy-ecc]`, `[scripts]`, `[doc]`
- **Decisiones de diseño / ADR**:

## 2. Development (Issues Vinculadas)

- Closes #

## 3. Checklist de Paridad Multi-Harness (`aagy <-> aagy-ecc`) y Quality Gate `A`

- [ ] **Paridad `aagy <-> aagy-ecc`**: `python scripts/py/sync_aagy_ecc.py --check` (`[IN_SYNC]`) y `pwsh -File scripts/ps1/audit-plugin-parity.ps1` (`[PASS]`).
- [ ] **Doctores en Verde**: `python scripts/py/aagy_doctor.py` y `python aagy-ecc/scripts/py/aagy_ecc_doctor.py` sin `FAIL`.
- [ ] **Tests Unitarios**: `python -m pytest scripts/py/tests/ scripts/ps1/tests/ scripts/sh/tests/ -q` (`exit 0`).
- [ ] **SonarQube Quality Gate `A`**: `pwsh -File scripts/ps1/sonar-audit.ps1` (`0` violaciones, `S3776 <= 15`, `S1192 = 0`).
- [ ] **Documentación y Linting**: `pwsh -File scripts/ps1/lint-markdown.ps1 -CheckOnly` (`[OK]`) y `python scripts/py/map_docs.py --check-docs-map` (`0` enlaces rotos).
- [ ] **Multi-OS & Presupuesto de Tokens**: `.sh` con finales de línea estrictamente POSIX LF (`\n`), `skills <= 140c`, `agents <= 120c`, `rules/AGENTS.md <= 12 KB`.

## 4. Estrategia de Rollback (`< 2 min`)

- Reversión atómica del squash commit en `main`: `git revert <sha>` y reinstalación limpia (`install.ps1`).
