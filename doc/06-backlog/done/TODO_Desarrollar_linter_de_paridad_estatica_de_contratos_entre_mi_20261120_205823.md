---
title: "**Desarrollar linter de paridad estática de contratos entre microservicios (`services/`, `cluster/`) y `home-lab-sdk`**"
status: COMPLETED
completed_at: "2026-11-20 20:58:23"
---

# TODO: **Desarrollar linter de paridad estática de contratos entre microservicios (`services/`, `cluster/`) y `home-lab-sdk`**

## 1. Descripción de la Tarea

- **Estado**: COMPLETED
- **Fecha de Finalización**: 2026-11-20 20:58:23

### Detalle Original

- **01 - ROLE:** Distributed Systems Contract Architect & Polyglot SDK Engineer.
- **02 - CONTEXT:** `[Sector: Microservices Contract Parity & Type Safety]` `[Data Type: Go structs/routes (Gin/chi/mux), TypeScript interfaces, Python models]` `[Objective: Implementar un validador estático automatizado que inspeccione las rutas y modelos expuestos por los microservicios y certifique que el SDK cliente polyglot (Go/TS/Python) contiene los métodos y tipos correspondientes, bloqueando PRs con divergencia]` `[Restrictions: Sin dependencias pesadas de terceros; análisis determinista con Python stdlib (ast, regex)]`.
- **03 - PHASE 1 (ANALYSIS):**
  - La regla "Mandatory Microservice & SDK Contract Parity" es un pilar crítico para evitar errores 404/400 en tiempo de ejecución entre microservicios.
  - Actualmente la sincronización depende de la disciplina del desarrollador. Si se añade un endpoint en Go sin actualizar el cliente en TypeScript de `home-lab-sdk`, la compilación local no siempre falla hasta las pruebas E2E.
- **04 - PHASE 2 (STRATEGY):**
  - Parser estático en Python que extraiga endpoints declarados en controladores Go (`r.GET(...)`, `r.POST(...)`) y los contraste contra los métodos cliente en `home-lab-sdk/`.
  - Reporte de diferencias: endpoints sin cliente, modelos con campos desalineados.
- **05 - PHASE 3 (EXECUTION):**
    1. Desarrollar `scripts/ecc-agy/audit_sdk_parity.py` y wrapper `scripts/bin/ecc-agy/audit-sdk-parity.ps1`.
    2. Integrar el chequeo como paso de validación en la Fase 4 del lifecycle (`04_PROPUESTA_COMMITS_PR.md` y `complete-task-pr.ps1`).
    3. Crear suite de tests `scripts/ecc-agy/tests/test_audit_sdk_parity.py` simulando contratos sincronizados y desincronizados.
    4. Ejecutar verificación y documentar en `doc/manual/`.
- **06 - PHASE 4 (CRITIC):**
  - *Auditoría*: Excluir del escaneo rutas internas no públicas como `/metrics`, `/health`, `/livez`, `/readyz` y endpoints de depuración.
- **07 - PHASE 5 (FORMAT):**
  - Script Python tipado con salida JSON/tabular y código de salida `0` (aprobado) o `1` (divergencia).
- **MODELO & AGENTE ASIGNADO:** **Argon ($Ar_{18}$) / Gemini 3.8 Pro Thinking** (~8.000 tokens) para el diseño del AST y análisis de contratos; **Carbon ($C_6$)** para la implementación del parser y tests.
- **COMPACT TRIGGER:** Tras squash-automerge de PR en `main`.

## 2. Verificación y Criterios de Aceptación

- [x] Tarea implementada y verificada contra criterios de aceptación.

## 3. Entregables y Notas de Cierre

Desarrollo de audit_sdk_parity.py y wrappers CLI para auditoria estatica de contratos

## 4. Metadatos de Integración y Commit

- **Rama / PR**: `feat/ecc/audit-sdk-parity`
- **Commit SHA**: `4a22c4e`
- **Fecha**: `2026-11-20 20:58:23`
- **Gobernanza**: Quality Gate A / markdownlint OK
