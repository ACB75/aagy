---
title: "**Desarrollar validador de congruencia de Ingress único, Split-DNS y catálogo de servicios `/portal`**"
status: COMPLETED
completed_at: "2026-11-20 21:11:40"
---

# TODO: **Desarrollar validador de congruencia de Ingress único, Split-DNS y catálogo de servicios `/portal`**

## 1. Descripción de la Tarea

- **Estado**: COMPLETED
- **Fecha de Finalización**: 2026-11-20 21:11:40

### Detalle Original

- **01 - ROLE:** Edge Ingress & Network Infrastructure Architect.
- **02 - CONTEXT:** `[Sector: Home-Lab Networking & Service Mesh]` `[Data Type: docker-compose.yml (traefik labels), Corefile / zone files, Go source (main.go)]` `[Objective: Implementar un script de validación que certifique que cualquier servicio HTTP definido en docker-compose tenga configuradas sus etiquetas Traefik (router, service, middleware TLS), su registro DNS coincidente en CoreDNS y su entrada en el catálogo /portal]` `[Restrictions: Python stdlib / PowerShell, sin requerir daemon Docker corriendo en modo estático]`.
- **03 - PHASE 1 (ANALYSIS):**
  - El Pilar 2 de Google Engineering ("Single Ingress & Unified TLS") y la regla 7 de `GEMINI.md` requieren que los microservicios no expongan puertos crudos y que el catálogo `/portal` se mantenga sincronizado.
  - La configuración manual de etiquetas Traefik y registros DNS puede sufrir desalineaciones sutiles (ej. un subdominio mal escrito en un router).
- **04 - PHASE 2 (STRATEGY):**
  - Parser estático que cruce:
      1. Servicios en `docker-compose*.yml` con etiquetas `traefik.http.routers.*.rule=Host(...)`.
      2. Registros en los archivos de zona de CoreDNS.
      3. Entradas del mapa `/portal` en `cluster/cmd/server/main.go`.
- **05 - PHASE 3 (EXECUTION):**
    1. Desarrollar `scripts/ecc-agy/validate_ingress_routes.py` y `validate-ingress-routes.ps1`.
    2. Añadir opción `-Audit` y `-Fix` para sugerir las líneas faltantes en `/portal` o DNS.
    3. Crear tests unitarios en `test_validate_ingress_routes.py`.
    4. Documentar en `doc/manual/`.
- **06 - PHASE 4 (CRITIC):**
  - *Auditoría*: Soportar servicios internos deliberadamente aislados (ej. PostgreSQL, Redis, exportadores de métricas) que no deben tener entrada Ingress.
- **07 - PHASE 5 (FORMAT):**
  - Script CLI con validación determinista y reporte estructurado de congruencia.
- **MODELO & AGENTE ASIGNADO:** **Carbon ($C_6$) / Gemini 3.8 Flash** (~1.200 tokens).
- **COMPACT TRIGGER:** Tras squash-automerge de PR en `main`.

## 2. Verificación y Criterios de Aceptación

- [x] Tarea implementada y verificada contra criterios de aceptación.

## 3. Entregables y Notas de Cierre

Desarrollo de validate_ingress_routes.py y wrappers CLI para congruencia Ingress, DNS y Portal

## 4. Metadatos de Integración y Commit

- **Rama / PR**: `feat/ecc/validate-ingress-routes`
- **Commit SHA**: `bc8990f`
- **Fecha**: `2026-11-20 21:11:40`
- **Gobernanza**: Quality Gate A / markdownlint OK
