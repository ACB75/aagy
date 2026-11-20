# Fase 4: Propuesta de Commits Atómicos, Pre-Flight Review y Apertura de PR

> **Referencias Previas Verificadas**:  
>
> - Requisitos & Impacto: [`doc/plan/REQ_ecc_workspace_audit_budget_hard_gate.md`](REQ_ecc_workspace_audit_budget_hard_gate.md)  
> - Plan de Acción & TDD: [`doc/plan/PLAN_ecc_workspace_audit_budget_hard_gate.md`](PLAN_ecc_workspace_audit_budget_hard_gate.md)  
> - Docs & Release Notes: [`doc/plan/DOCS_ecc_workspace_audit_budget_hard_gate.md`](DOCS_ecc_workspace_audit_budget_hard_gate.md)  
> **Fecha**: `2026-11-20` | **Estado**: `LISTO PARA COMMIT Y PR`  

---

## 1. Identificación y Gobernanza de Ramas

- **Rama de Origen**: `feat/ecc/workspace-audit-budget-hard-gate`
  - *Validación Canónica*: Verificada con éxito mediante `python scripts/ecc-agy/validate_branch.py`.
- **Rama Destino**: `main` (Trunk canónico).

---

## 2. Propuesta de Título Estructurado del Commit

Formato obligatorio: `[type]-[projects]: <título imperativo en minúsculas>`

- **Título Propuesto**: `[feat]-[ecc,scripts]: hard gate de presupuesto de rules y mcps en workspace audit`

---

## 3. Cuerpo Explicativo Obligatorio (Commit Message & PR Body)

```text
Motivación y Contexto:
- Incorporar un guardrail bloqueante determinista en workspace_audit.py para garantizar que el tamaño por archivo de reglas no supere los 24 KB y el total agregado no exceda los 16.000 tokens (límite defaultRulesBudget de Antigravity = 20k).
- Auditar configuraciones mcp_config.json en plugins activos, exigiendo 'disabled: true' para servidores pesados como gemini-mcp y limitando el presupuesto de personalizaciones eager a 3.000 tokens.
- Cumple los criterios de aceptación CA-01 a CA-05 de la Fase 1.

Garantía de Retrocompatibilidad e Impacto en Home-Lab:
- [x] Zero Breaking Changes: Configuración 100% retrocompatible y tolerante a ausencias opcionales.
- [x] Presupuesto de Contexto: Plugin global ecc-agy y ECC Root conformes con margen de seguridad.
- [x] Rendimiento: Inspección stdlib pura en < 1.5s.

Cambios Introducidos:
- scripts/ecc-agy/workspace_audit.py: Nuevas funciones audit_rules() y audit_mcps(), constantes de presupuesto y cálculo integrado en BudgetReport.
- scripts/ecc-agy/tests/test_workspace_audit.py: Nuevos tests unitarios para límites de archivos, presupuesto de reglas y servidores MCP activos/desactivados.
- doc/plan/REQ|PLAN|DOCS|REVIEW_ecc_workspace_audit_budget_hard_gate.md: Artefactos del Engineering Lifecycle completos.
- doc/TODO.md & doc/TODO_DONE/: Tarea 2.1 completada y archivada.

Verificación de Compuertas de Calidad (Quality Gate Rating A):
- [x] Tests unitarios pasando al 100% (pytest con 69+ tests superados).
- [x] SonarQube Quality Gate: Rating A alcanzado (0 violaciones, Complejidad Cognitiva <= 15).
- [x] markdownlint DavidAnson: 100% compliant con .markdownlint.json.
- [x] Auditoría de seguridad estática: 0 vulnerabilidades detectadas.

Estrategia Fast-Rollback:
- Reversión atómica en caso de incidente: git revert <sha-del-squash-commit>.
```

---

## 4. Invocación Estandarizada del Cierre

```powershell
# 1. Modo de revisión previa sin mutaciones:
pwsh -File scripts/bin/ecc-agy/complete-task-pr.ps1 -ReviewOnly

# 2. Confirmación y fusión atómica tras visto bueno del usuario:
pwsh -File scripts/bin/ecc-agy/complete-task-pr.ps1 -Yes -Title "[feat]-[ecc,scripts]: hard gate de presupuesto de rules y mcps en workspace audit"
```
