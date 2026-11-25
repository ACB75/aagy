# ADR-0001: Arquitectura en dos niveles: Plugin Global (`aagy`) y Scaffolding por Proyecto (`.agents/`)

**Date**: 2026-10-24
**Status**: superseded (Nivel 2) por [ADR-0004](ADR_aagy_0004_stack_profiles_declared_by_consumer_repo.md)
**Deciders**: Master, Antigravity (AAGY)

## Context

El workspace `<padre>\app` alberga proyectos heterogéneos (`app` en Java 25/Spring Boot 4 + Angular 21, `cluster` en FastAPI/Docker/Kubernetes/Apache, `net` en PowerShell/CoreDNS/OpenVPN, `web` en Python y `scripts` en PowerShell/Bash). Cargar todas las skills y subagentes especializados de todos los stacks de forma global en cada sesión saturaría el presupuesto de contexto, mientras que duplicar las reglas universales en cada repositorio dificultaría el mantenimiento.

## Decision

Adoptar una arquitectura de personalización en **dos niveles (Two-Tier Customization Architecture)**:

1. **Nivel 1 — Plugin Global (`C:\Users\Master\.gemini\config\plugins\aagy`)**: Contiene las reglas universales (`rules/AGENTS.md`) y las skills/agentes transversales a todo el workspace (`search-first`, `tdd-workflow`, `verification-loop`, `security-review`, `coding-standards`, `docs-governance`, `architecture-decision-records`).
2. **Nivel 2 — Scaffolding por Proyecto (`<project>/.agents/skills/` y `<project>/.agents/agents/`)**: Sincronizado mediante `aagy-sync.ps1` / `aagy-sync.sh`, inyecta únicamente las skills y agentes específicos del stack de cada proyecto (`springboot-*`, `angular-developer`, `docker-patterns`, `app-*`).

## Alternatives Considered

### Alternative 1: Instalar todas las skills y agentes en el plugin global

- **Pros**: Un único directorio de instalación sin necesidad de sincronizar carpetas `.agents/` por proyecto.
- **Cons**: Infla la lista global de skills y agentes en todas las conversaciones, degradando la eficiencia de tokens y mezclando dominios irrelevantes.
- **Why not**: Viola el principio de eficiencia de contexto (`context-budget`) de AAGY.

### Alternative 2: Copiar manualmente todas las reglas y skills en cada proyecto sin plugin global

- **Pros**: Independencia total entre repositorios.
- **Cons**: Alta deriva de configuración (*configuration drift*) al actualizar reglas de seguridad o gobernanza documental.
- **Why not**: Las reglas núcleo (`AGENTS.md`) y el flujo de ingeniería deben aplicarse sin excepción en todo el workspace.

## Consequences

### Positive

- Presupuesto de tokens optimizado: cada proyecto carga solo las skills de su dominio además del núcleo global.
- Gobernanza unificada y sincronización reproducible mediante `aagy-sync.ps1`.

### Negative

- Requiere ejecutar el script de sincronización cuando se añaden nuevas skills específicas de dominio al catálogo de `aagy`.

### Risks

- Desincronización entre el repositorio fuente `<padre>\aagy` y el plugin desplegado; mitigado mediante `install.ps1` y `aagy-sync.ps1`.
