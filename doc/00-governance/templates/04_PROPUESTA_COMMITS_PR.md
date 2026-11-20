# Fase 4: Propuesta de Commits Atómicos, Pre-Flight Review y Apertura de PR

> **Referencias Previas Verificadas**:  
>
> - Requisitos & Impacto: [`doc/plan/REQ_<id_tarea>.md`](REQ_<id_tarea>.md)  
> - Plan de Acción & TDD: [`doc/plan/PLAN_<id_tarea>.md`](PLAN_<id_tarea>.md)  
> - Docs & Release Notes: [`doc/plan/DOCS_<id_tarea>.md`](DOCS_<id_tarea>.md)  
> **Fecha**: `YYYY-MM-DD` | **Estado**: `LISTO PARA COMMIT Y PR`  

---

## 1. Identificación y Gobernanza de Ramas

- **Rama de Origen**: `<tipo>/<proyecto>/<nombre>` (ej. `feat/kakebo/export-csv`, `fix/cluster/oom-timeout`).
  - *Validación Canónica*: Verificada con éxito mediante `python scripts/py/validate_branch.py --branch <nombre-rama>`.
- **Rama Destino**: `main` (Trunk canónico).

---

## 2. Propuesta de Título Estructurado del Commit

Formato obligatorio: `[type]-[projects]: <título imperativo en minúsculas>`

- **Título Propuesto**: `[feat]-[kakebo,sdk]: implementar exportacion de transacciones y sincronizar sdk`

---

## 3. Cuerpo Explicativo Obligatorio (Commit Message & PR Body)

```text
Motivación y Contexto:
- Justificación técnica de la intervención resolviendo la necesidad planteada en la Fase 1.
- Satisface los criterios de aceptación CA-01, CA-02 y CA-03.

Garantía de Retrocompatibilidad e Impacto en Home-Lab:
- [x] Zero Breaking Changes: Contratos, endpoints y schemas de PostgreSQL LTS 100% retrocompatibles.
- [x] Paridad home-lab-sdk: Clientes sincronizados y verificados sin contract drift.
- [x] SRE & Throttling: Configurado GOMEMLIMIT=80% / límites de memoria y rotación de logs.

Cambios Introducidos:
- Lógica de negocio y controladores del servicio.
- Modelos y clientes políglotas en home-lab-sdk/.
- Tests unitarios e integración (cobertura >= 80%).
- Notas de la versión en doc/ y espina documental actualizada.

Verificación de Compuertas de Calidad (Quality Gate Rating A):
- [x] Tests unitarios pasando al 100%: XX tests superados (código 0).
- [x] SonarQube Quality Gate: Rating A alcanzado (0 violaciones críticas, Cognitive Complexity <= 15).
- [x] markdownlint DavidAnson: 100% compliant (--check-only).
- [x] Auditoría de seguridad estática: 0 vulnerabilidades detectadas / 0 secretos.

Estrategia Fast-Rollback:
- Reversión atómica en caso de incidente: git revert <sha-del-squash-commit>.
- Reversión de persistencia si aplica: down-migration.sql verificado.
```

---

## 4. Resumen de Archivos a Comprometer (`git status -s`)

*(Incluye código fuente, pruebas, documentación, notas de la versión y archivado de TODOs)*

```text
M  services/kakebo/src/main/java/TransactionController.java
M  services/kakebo/src/main/java/TransactionService.java
M  home-lab-sdk/java/src/main/java/TransactionClient.java
A  services/kakebo/src/test/java/TransactionServiceTest.java
M  doc/TODO.md
A  doc/TODO_DONE/TODO_Tarea_export_csv_20261120.md
A  doc/plan/REQ_kakebo_export_csv.md
A  doc/plan/PLAN_kakebo_export_csv.md
A  doc/plan/DOCS_kakebo_export_csv.md
M  doc/STATUS.md
M  doc/LOG.md
```

---

## 5. Invocación Estandarizada del Cierre y Promoción Multi-Tier

### 5.1. Ejecución del Ciclo Automatizado de PR

```powershell
# 1. Modo de revisión previa sin mutaciones:
pwsh -File scripts/ps1/complete-task-pr.ps1 -ReviewOnly

# 2. Confirmación y fusión atómica tras visto bueno del usuario:
pwsh -File scripts/ps1/complete-task-pr.ps1 -Yes -Title "[type]-[projects]: <título>"
```

### 5.2. Promoción Multi-Tier Home-Lab (ADR-0006)

Tras la fusión en `main` (entorno `LOCAL`), disparar la promoción hacia servidores FRACTAL y NEO:

```powershell
# Promoción a SANDBOX (Servidor FRACTAL):
pwsh -File scripts/ps1/git-flow-helper.ps1 -Action promote -Tag vX.Y.Z-sandbox

# Promoción a LIVE (Servidor NEO):
pwsh -File scripts/ps1/git-flow-helper.ps1 -Action promote -Tag vX.Y.Z
```
