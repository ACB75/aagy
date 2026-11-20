# Fase 4: Propuesta de Commits Atómicos, Pre-Flight Review y Apertura de PR | Migración /ecc a /aagy

> **Referencias Previas Verificadas**:  
>
> - Requisitos & Impacto: [`doc/plan/REQ_aagy_clean_docs_and_repo_migration.md`](REQ_aagy_clean_docs_and_repo_migration.md)  
> - Plan de Acción & TDD: [`doc/plan/PLAN_aagy_clean_docs_and_repo_migration.md`](PLAN_aagy_clean_docs_and_repo_migration.md)  
> - Docs & Release Notes: [`doc/plan/DOCS_aagy_clean_docs_and_repo_migration.md`](DOCS_aagy_clean_docs_and_repo_migration.md)  
> **Fecha**: 2026-11-20 | **Estado**: `LISTO PARA COMMIT Y PR`  

---

## 1. Identificación y Gobernanza de Ramas

- **Rama de Origen**: `chore/aagy/repo-migration-cutover`
  - *Validación Canónica*: Verificada con éxito mediante `python scripts/ecc-agy/validate_branch.py --branch chore/aagy/repo-migration-cutover`.
- **Rama Destino**: `main` (Trunk canónico).

---

## 2. Propuesta de Título Estructurado del Commit

Formato obligatorio: `[type]-[projects]: <título imperativo en minúsculas>`

- **Título Propuesto**: `[chore]-[aagy,ecc]: migracion a Anything Antigravity y paridad de plugins con Claude Code`

---

## 3. Cuerpo Explicativo Obligatorio (Commit Message & PR Body)

```text
Motivación y Contexto:
- Cierre maestro del backlog: migración del repositorio a Anything Antigravity (aagy) preservando el historial Git completo.
- Consolidación del plugin para Claude Code en 'aagy/ecc/' con verificación continua de paridad multiagente.
- Incorporación del linter 'audit_plugin_parity.py' integrado en el pipeline de complete-task-pr.

Garantía de Retrocompatibilidad e Impacto en Home-Lab:
- [x] Dual-Harness Support: Soporte coordinado de Google Antigravity y Claude Code.
- [x] Preservación de Historial Git: 100% del historial preservado sin reescribir commits.
- [x] Calidad y Presupuesto de Contexto: Cumplimiento de límites de tokens de rules y skills.

Cambios Introducidos:
- plugin.json: Actualización de identidad a 'aagy' (Anything Antigravity).
- ecc/: Consolidación de ecc-claude como subplugin oficial para Claude Code.
- scripts/ecc-agy/audit_plugin_parity.py, wrappers en scripts/bin/ y suite de pruebas.
- doc/manual/MANUAL_aagy_ecc_parity_and_migration.md y actualización de la espina documental.

Verificación de Compuertas de Calidad (Quality Gate Rating A):
- [x] Tests unitarios pasando al 100% (código 0).
- [x] SonarQube Quality Gate: Rating A alcanzado (0 violaciones, Cognitive Complexity <= 15).
- [x] markdownlint DavidAnson: 100% compliant (--check-only).
- [x] Paridad de contratos SDK, bloqueos DDL PostgreSQL e Ingress Congruence: 100% verificados.
```

---

## 4. Estrategia Fast-Rollback

- Reversión atómica mediante `git revert <sha>` del squash commit único.
