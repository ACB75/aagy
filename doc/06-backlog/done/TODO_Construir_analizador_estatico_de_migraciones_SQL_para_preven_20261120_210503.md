---
title: "**Construir analizador estático de migraciones SQL para prevención de bloqueos `ACCESS EXCLUSIVE` en PostgreSQL LTS**"
status: COMPLETED
completed_at: "2026-11-20 21:05:03"
---

# TODO: **Construir analizador estático de migraciones SQL para prevención de bloqueos `ACCESS EXCLUSIVE` en PostgreSQL LTS**

## 1. Descripción de la Tarea

- **Estado**: COMPLETED
- **Fecha de Finalización**: 2026-11-20 21:05:03

### Detalle Original

- **01 - ROLE:** Principal Database Reliability Engineer (DBRE) & PostgreSQL Internalist.
- **02 - CONTEXT:** `[Sector: Multi-Tenant Database Infrastructure]` `[Data Type: SQL migration files (*.sql), PostgreSQL DDL syntax]` `[Objective: Desarrollar un analizador estático que escanee scripts de migración SQL buscando operaciones que tomen bloqueos ACCESS EXCLUSIVE prolongados o causen reescrituras de tabla, bloqueando despliegues que pongan en riesgo la disponibilidad de la base de datos central multitenant]` `[Restrictions: Python stdlib, tiempo de ejecución < 500ms, aplicable en Fase 1 y Fase 4 del lifecycle]`.
- **03 - PHASE 1 (ANALYSIS):**
  - proyecto consumidor consolida todos los microservicios en una instancia única y endurecida de PostgreSQL LTS.
  - Ciertas operaciones DDL (ej. `ALTER TABLE t ADD COLUMN c int NOT NULL DEFAULT now()`, `CREATE INDEX` sin `CONCURRENTLY`, cambios de tipo de columna incompatibles) adquieren bloqueos `ACCESS EXCLUSIVE` que congelan todas las lecturas y escrituras, provocando agotamiento del pool de conexiones en los microservicios.
- **04 - PHASE 2 (STRATEGY):**
  - Clasificar las sentencias DDL en 3 categorías de riesgo:
    - *Verde*: Operaciones concurrentes o metadata-only (ej. añadir columna nullable, `CREATE INDEX CONCURRENTLY`).
    - *Amarillo*: Bloqueos compartidos breves.
    - *Rojo*: `ACCESS EXCLUSIVE` o reescritura de tabla completa.
  - Para sentencias en *Rojo*, sugerir la alternativa segura sin bloqueo (estrategia dual-write o adición en 3 pasos).
- **05 - PHASE 3 (EXECUTION):**
    1. Programar `scripts/aagy/audit_pg_locks.py` y `audit-pg-locks.ps1`.
    2. Crear reglas de detección léxica para sentencias DDL bloqueantes de PostgreSQL.
    3. Añadir suite de tests `test_audit_pg_locks.py` con fixtures de migraciones seguras y peligrosas.
    4. Integrar en `complete-task-pr.ps1` cuando se detecten archivos `.sql` modificados.
- **06 - PHASE 4 (CRITIC):**
  - *Auditoría*: Distinguir entre versiones de PostgreSQL: en PG 11+ añadir columna con default constante no reescribe la tabla, pero expresiones volátiles (ej. `random()`, funciones PL/pgSQL) sí lo hacen.
- **07 - PHASE 5 (FORMAT):**
  - Script CLI con reporte estructurado de riesgos y remediaciones sugeridas.
- **MODELO & AGENTE ASIGNADO:** **Argon ($Ar_{18}$) / Gemini 3.8 Pro Thinking** (~10.000 tokens) para el modelado de concurrencia y catálogo de bloqueos; **Carbon ($C_6$)** para el parser.
- **COMPACT TRIGGER:** Tras squash-automerge de PR en `main`.

## 2. Verificación y Criterios de Aceptación

- [x] Tarea implementada y verificada contra criterios de aceptación.

## 3. Entregables y Notas de Cierre

Desarrollo de audit_pg_locks.py y wrappers CLI para prevencion de bloqueos DDL en PostgreSQL LTS

## 4. Metadatos de Integración y Commit

- **Rama / PR**: `feat/aagy/audit-pg-locks`
- **Commit SHA**: `1e57bad`
- **Fecha**: `2026-11-20 21:05:03`
- **Gobernanza**: Quality Gate A / markdownlint OK
