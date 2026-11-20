# Fase 4: Propuesta de Commits Atómicos, Pre-Flight Review y Apertura de PR

> **Referencias Previas Verificadas**:  
>
> - Requisitos & Impacto: [`doc/plan/REQ_ecc_gemini_mcp_deep_ops.md`](REQ_ecc_gemini_mcp_deep_ops.md)  
> - Plan de Acción & TDD: [`doc/plan/PLAN_ecc_gemini_mcp_deep_ops.md`](PLAN_ecc_gemini_mcp_deep_ops.md)  
> - Docs & Release Notes: [`doc/plan/DOCS_ecc_gemini_mcp_deep_ops.md`](DOCS_ecc_gemini_mcp_deep_ops.md)  
> **Fecha**: `2026-11-20` | **Estado**: `LISTO PARA COMMIT Y PR`  

---

## 1. Identificación y Gobernanza de Ramas

- **Rama de Origen**: `feat/ecc/gemini-mcp-deep-ops`
  - *Validación Canónica*: Verificada con éxito mediante `python scripts/ecc-agy/validate_branch.py`.
- **Rama Destino**: `main` (Trunk canónico).

---

## 2. Propuesta de Título Estructurado del Commit

Formato obligatorio: `[type]-[projects]: <título imperativo en minúsculas>`

- **Título Propuesto**: `[feat]-[ecc,skills]: integracion zero-overhead de gemini-mcp y skill gemini-deep-ops`

---

## 3. Cuerpo Explicativo Obligatorio (Commit Message & PR Body)

```text
Motivación y Contexto:
- Proveer capacidades avanzadas de RLabs-Inc/gemini-mcp (Context Caching, Deep Research, análisis de logs/volcados multimodales) con 0 sobrecarga de tokens en reposo.
- Implementar plantilla opcional templates/plugins/gemini-mcp/ con 'disabled: true' y parametrización de GEMINI_API_KEY por entorno.
- Crear skill Tier 2 skills/gemini-deep-ops/SKILL.md (<= 140 chars) y CLI determinista gemini_deep_ops.py.
- Cumple los criterios de aceptación CA-01 a CA-05 de la Fase 1.

Garantía de Retrocompatibilidad e Impacto en Home-Lab:
- [x] Zero Breaking Changes: 100% retrocompatible y aditivo en Tier 2.
- [x] Presupuesto de Contexto: 0 incremento de tokens en Tier 1 global; 0 tokens en reposo verificado por workspace_audit.py.
- [x] Seguridad: GEMINI_API_KEY se lee estrictamente de variables de entorno del sistema; cero secretos hardcodeados.

Cambios Introducidos:
- templates/plugins/gemini-mcp/: Manifiestos plugin.json, mcp_config.json y README.md.
- scripts/ecc-agy/toggle_gemini_mcp.py & scripts/bin/ecc-agy/toggle-gemini-mcp.ps1/.sh.
- scripts/ecc-agy/gemini_deep_ops.py & scripts/bin/ecc-agy/gemini-deep-ops.ps1/.sh.
- skills/gemini-deep-ops/SKILL.md: Skill bajo demanda para análisis 5W y logs masivos.
- doc/manual/MANUAL_gemini_deep_ops_multimodal.md: Guía técnica de uso multimodal.
- scripts/ecc-agy/tests/test_gemini_deep_ops.py: Pruebas unitarias de alternancia y CLI.
- doc/TODO.md & doc/TODO_DONE/: Tarea 2.2 completada y archivada.

Verificación de Compuertas de Calidad (Quality Gate Rating A):
- [x] Tests unitarios pasando al 100% (73+ tests pasando con código 0).
- [x] SonarQube Quality Gate: Rating A alcanzado (0 violaciones, Complejidad Cognitiva <= 15).
- [x] markdownlint DavidAnson: 100% compliant.
- [x] Auditoría de seguridad estática: 0 vulnerabilidades / 0 secretos.

Estrategia Fast-Rollback:
- Reversión atómica mediante revert del squash commit: git revert <sha>.
```

---

## 4. Invocación Estandarizada del Cierre

```powershell
# 1. Modo de revisión previa sin mutaciones:
pwsh -File scripts/bin/ecc-agy/complete-task-pr.ps1 -ReviewOnly

# 2. Confirmación y fusión atómica tras visto bueno del usuario:
pwsh -File scripts/bin/ecc-agy/complete-task-pr.ps1 -Yes -Title "[feat]-[ecc,skills]: integracion zero-overhead de gemini-mcp y skill gemini-deep-ops"
```
