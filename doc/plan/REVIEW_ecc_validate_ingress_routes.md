# Fase 4: Propuesta de Commits Atómicos, Pre-Flight Review y Apertura de PR | Validador Ingress / DNS / Portal

> **Referencias Previas Verificadas**:  
>
> - Requisitos & Impacto: [`doc/plan/REQ_ecc_validate_ingress_routes.md`](REQ_ecc_validate_ingress_routes.md)  
> - Plan de Acción & TDD: [`doc/plan/PLAN_ecc_validate_ingress_routes.md`](PLAN_ecc_validate_ingress_routes.md)  
> - Docs & Release Notes: [`doc/plan/DOCS_ecc_validate_ingress_routes.md`](DOCS_ecc_validate_ingress_routes.md)  
> **Fecha**: 2026-11-20 | **Estado**: `LISTO PARA COMMIT Y PR`  

---

## 1. Identificación y Gobernanza de Ramas

- **Rama de Origen**: `feat/ecc/validate-ingress-routes`
  - *Validación Canónica*: Verificada con éxito mediante `python scripts/ecc-agy/validate_branch.py --branch feat/ecc/validate-ingress-routes`.
- **Rama Destino**: `main` (Trunk canónico).

---

## 2. Propuesta de Título Estructurado del Commit

Formato obligatorio: `[type]-[projects]: <título imperativo en minúsculas>`

- **Título Propuesto**: `[feat]-[cluster,net,scripts]: validador de congruencia de ingress split-dns y portal`

---

## 3. Cuerpo Explicativo Obligatorio (Commit Message & PR Body)

```text
Motivación y Contexto:
- Construcción de validador estático de congruencia para certificar alineación entre rutas Traefik, registros Split-DNS en CoreDNS y el catálogo de /portal.
- Asegura el cumplimiento del Pilar 2 de Google Engineering ("Single Ingress & Unified TLS") evitando subdominios huérfanos o servicios sin visibilidad.

Garantía de Retrocompatibilidad e Impacto en Home-Lab:
- [x] Zero Breaking Changes: Modo skip seguro ante ausencia de archivos de infraestructura.
- [x] Ingress Único & Split-DNS: Comprobación estática de etiquetas y resolución *.home.lab.
- [x] SRE & Throttling: Tiempo de ejecución estático < 150 ms en Python stdlib pura.

Cambios Introducidos:
- scripts/ecc-agy/validate_ingress_routes.py: Parser y validador trilateral con soporte --audit, --fix y --json.
- scripts/bin/ecc-agy/validate-ingress-routes.ps1 y .sh: Wrappers CLI multiplataforma.
- scripts/ecc-agy/tests/test_validate_ingress_routes.py: Suite de tests con fixtures congruentes y discrepantes.
- doc/manual/MANUAL_ingress_routes_validator.md y actualización de la espina documental.

Verificación de Compuertas de Calidad (Quality Gate Rating A):
- [x] Tests unitarios pasando al 100% (código 0).
- [x] SonarQube Quality Gate: Rating A alcanzado (0 violaciones críticas, Cognitive Complexity <= 15).
- [x] markdownlint DavidAnson: 100% compliant (--check-only).
- [x] Auditoría de seguridad estática: 0 vulnerabilidades detectadas / 0 secretos.
```

---

## 4. Estrategia Fast-Rollback

- Reversión atómica mediante `git revert <sha>` del squash commit único.
