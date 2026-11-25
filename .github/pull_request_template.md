# Pull Request

<!-- Mismas secciones que las issues y las tareas de TODO.md (plantilla base, #93). -->

## 1. Motivación

- **Qué cambia y por qué**:
- **Áreas**: `[aagy]`, `[aagy-ecc]`, `[scripts]`, `[doc]`

## 2. Issues

- Closes #

## 3. Criterios de aceptación

- [ ] `python scripts/py/ci_local.py run` en verde (tests, linters, Sonar, seguridad, plantillas, espejo y paridad).
- [ ] Doctores sin `FAIL`: `python scripts/py/aagy_doctor.py` y `python aagy-ecc/scripts/py/aagy_ecc_doctor.py`.
- [ ] Los criterios de la issue tienen un test que los cubre.

## 4. Paridad aagy ↔ aagy-ecc

- [ ] `python scripts/py/sync_aagy_ecc.py --check` en `[SYNCED]` y `python scripts/py/audit_plugin_parity.py` en `[PASS]`.
- [ ] Asimetrías declaradas (si un harness no lo permite).

## 5. Artefactos

- REQ / PLAN / ADR / runbook: `<rutas>`

## 6. Rollback

- `git revert <sha-del-squash>` y reinstalar el plugin.
