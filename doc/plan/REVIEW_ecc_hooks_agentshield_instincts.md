# Fase 4: Propuesta de Commits Atómicos, Pre-Flight Review y Apertura de PR

> **Referencias Previas Verificadas**:  
>
> - Requisitos & Impacto: [`doc/plan/REQ_ecc_hooks_agentshield_instincts.md`](REQ_ecc_hooks_agentshield_instincts.md)  
> - Plan de Acción & TDD: [`doc/plan/PLAN_ecc_hooks_agentshield_instincts.md`](PLAN_ecc_hooks_agentshield_instincts.md)  
> - Docs & Release Notes: [`doc/plan/DOCS_ecc_hooks_agentshield_instincts.md`](DOCS_ecc_hooks_agentshield_instincts.md)  
> **Fecha**: `2026-11-20` | **Estado**: `LISTO PARA COMMIT Y PR`  

---

## 1. Identificación y Gobernanza de Ramas

- **Rama de Origen**: `feat/ecc/hooks-agentshield-instincts`
  - *Validación Canónica*: Verificada con éxito mediante `python scripts/ecc-agy/validate_branch.py`.
- **Rama Destino**: `main` (Trunk canónico).

---

## 2. Propuesta de Título Estructurado del Commit

Formato obligatorio: `[type]-[projects]: <título imperativo en minúsculas>`

- **Título Propuesto**: `[feat]-[ecc,sec]: hooks nativos, auditoria agentshield e instintos por proyecto`

---

## 3. Cuerpo Explicativo Obligatorio (Commit Message & PR Body)

```text
Motivación y Contexto:
- Trasladar controles críticos de formateo y seguridad a hooks.json deterministas (0 tokens de system prompt).
- Integrar auditoría AgentShield en security_audit.py para auditar hooks.json, mcp_config.json y skills/ contra inyecciones y secretos.
- Implementar motor de instintos por proyecto en .agents/instincts/ desacoplado de AGENTS.md.
- Cumple los criterios de aceptación CA-01 a CA-05 de la Fase 1.

Garantía de Retrocompatibilidad e Impacto en Home-Lab:
- [x] Zero Breaking Changes: 100% retrocompatible y aditivo.
- [x] Presupuesto de Contexto: Permite delegar reglas operativas fuera del prompt del sistema.
- [x] Seguridad: Blindaje integral contra prompt injection y comandos destructivos.

Cambios Introducidos:
- hooks.json: Handlers para run_command (safety-gate) y write_file/edit_file (auto-linter).
- scripts/bin/ecc-agy/hook-post-write.ps1/.sh & safety-check.ps1/.sh.
- scripts/ecc-agy/security_audit.py: Módulo AgentShield (scan_agentshield_hooks, skills y mcp).
- scripts/ecc-agy/instinct_manager.py & scripts/bin/ecc-agy/manage-instincts.ps1/.sh.
- scripts/ecc-agy/tests/test_agentshield_instincts.py: Suite de pruebas unitarias.
- doc/TODO.md & doc/TODO_DONE/: Tarea 2.3 completada y archivada.

Verificación de Compuertas de Calidad (Quality Gate Rating A):
- [x] Tests unitarios pasando al 100% (78+ tests superados con código 0).
- [x] SonarQube Quality Gate: Rating A alcanzado (0 violaciones, Complejidad Cognitiva <= 15).
- [x] markdownlint DavidAnson: 100% compliant.
- [x] Auditoría de seguridad estática: 0 vulnerabilidades.

Estrategia Fast-Rollback:
- Reversión atómica mediante revert del squash commit: git revert <sha>.
```

---

## 4. Invocación Estandarizada del Cierre

```powershell
# 1. Modo de revisión previa sin mutaciones:
pwsh -File scripts/bin/ecc-agy/complete-task-pr.ps1 -ReviewOnly

# 2. Confirmación y fusión atómica tras visto bueno del usuario:
pwsh -File scripts/bin/ecc-agy/complete-task-pr.ps1 -Yes -Title "[feat]-[ecc,sec]: hooks nativos, auditoria agentshield e instintos por proyecto"
```
