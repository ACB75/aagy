# Fase 4: Propuesta de Commits Atómicos, Pre-Flight Review y Apertura de PR | Despliegue Tagged

> **Referencias Previas Verificadas**:  
>
> - Requisitos & Impacto: [`doc/plan/REQ_ecc_git_flow_deploy.md`](REQ_ecc_git_flow_deploy.md)  
> - Plan de Acción & TDD: [`doc/plan/PLAN_ecc_git_flow_deploy.md`](PLAN_ecc_git_flow_deploy.md)  
> - Docs & Release Notes: [`doc/plan/DOCS_ecc_git_flow_deploy.md`](DOCS_ecc_git_flow_deploy.md)  
> **Fecha**: 2026-11-20 | **Estado**: `LISTO PARA COMMIT Y PR`  

---

## 1. Identificación y Gobernanza de Ramas

- **Rama de Origen**: `feat/ecc/git-flow-deploy`
  - *Validación Canónica*: Verificada con éxito mediante `python scripts/ecc-agy/validate_branch.py --branch feat/ecc/git-flow-deploy`.
- **Rama Destino**: `main` (Trunk canónico).

---

## 2. Propuesta de Título Estructurado del Commit

Formato obligatorio: `[type]-[projects]: <título imperativo en minúsculas>`

- **Título Propuesto**: `[feat]-[scripts,infra]: despliegue automatizado por etiquetas y sondas en git-flow-helper`

---

## 3. Cuerpo Explicativo Obligatorio (Commit Message & PR Body)

```text
Motivación y Contexto:
- Extensión de git-flow-helper para cerrar el ciclo Trunk-Based Development con despliegue automatizado por tag (-Deploy, -Environment, -DryRun).
- Añade sondeo de salud (liveness probes) con 3 reintentos x 5s y protocolo de rollback desatendido en < 2 minutos ante fallos.

Garantía de Retrocompatibilidad e Impacto en Home-Lab:
- [x] Zero Breaking Changes: Parámetros aditivos opcionales; 'promote' sin -Deploy conserva comportamiento anterior.
- [x] Multi-Tier Deployment: Soporte nativo para FRACTAL (sandbox) y NEO (live).
- [x] SRE & Throttling: Rollback automático en < 120s garantizando disponibilidad continua.

Cambios Introducidos:
- scripts/bin/ecc-agy/git-flow-helper.ps1 y .sh: Nuevos parámetros -Deploy, -Environment [sandbox|live] y -DryRun con probes y rollback.
- scripts/ecc-agy/tests/test_git_flow_deploy.py: Suite de pruebas unitarias y de simulación.
- doc/manual/MANUAL_multitier_deployment.md y actualización de la espina documental.

Verificación de Compuertas de Calidad (Quality Gate Rating A):
- [x] Tests unitarios pasando al 100% (código 0).
- [x] SonarQube Quality Gate: Rating A alcanzado (0 violaciones críticas, Cognitive Complexity <= 15).
- [x] markdownlint DavidAnson: 100% compliant (--check-only).
- [x] Auditoría de seguridad estática: 0 vulnerabilidades detectadas / 0 secretos.
```

---

## 4. Estrategia Fast-Rollback

- Reversión atómica mediante `git revert <sha>` del squash commit único.
