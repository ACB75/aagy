# ADR-0004: Perfiles de Stack Declarados por el Repositorio Consumidor (Plugin Desacoplado)

**Date**: 2026-11-21
**Status**: accepted
**Deciders**: Master
**Supersedes**: Nivel 2 de [ADR-0001](ADR_aagy_0001_two_tier_global_plugin_and_project_scaffolding.md)

## Context

El Nivel 2 de ADR-0001 sincronizaba skills de dominio en `<project>/.agents/` con fases nombradas según proyectos de `app` (`app`, `cluster`, `web`) y `-TargetProject` apuntando a subcarpetas concretas. Eso acoplaba el plugin a un consumidor y dejaba copias repetidas en cinco subcarpetas versionadas de `app` (94 ficheros idénticos al catálogo).

## Decision

1. **Perfiles de stack, no de proyecto**: `aagy-sync.{ps1,sh}` ofrece `generic` (global), `network-infra`, `java-spring`, `angular`, `go`, `python` y `all`. Las fases antiguas (`infra`, `app`, `cluster`, `web`) se retiran con un error explicativo.
2. **El consumidor declara, el plugin instala**: cada repositorio declara sus perfiles en `<repo>/.governance/aagy-profiles.json` (`{"profiles": [...]}`). `aagy-sync -Repo <repo>` / `aagy-sync.sh --repo <repo>` delega en [`repo_profiles.py`](../../scripts/py/repo_profiles.py), que instala una sola vez la unión de perfiles (menos lo ya incluido en `generic`) en `<repo>/.agents/`.
3. **Sin versionar copias**: lo instalado se registra en `.agents/.aagy-profiles.lock.json` y en un bloque gestionado de `.agents/.gitignore`; las skills y agentes propios del repositorio nunca se tocan.
4. **Fuente única**: las listas de cada perfil siguen viviendo en `scripts/sh/aagy-sync.sh` (las lee `/aagy-doctor` y `repo_profiles.py`).

## Consequences

### Positive

- El plugin no contiene nombres de consumidores; cualquier repositorio puede adoptar perfiles.
- Coste eager: `generic` (~1.025 tokens) en todos los proyectos y el extra de los perfiles (~1.110 tokens para Java/Angular/Go/Python/red) solo en las sesiones del repositorio que los declara.

### Negative

- Hay que reejecutar `aagy-sync -Repo` cuando cambian los perfiles o el catálogo.

### Risks

- Un `.agents/` anidado en subcarpetas del consumidor volvería a duplicar contenido; los consumidores lo bloquean en su auditoría (`app`: `workspace_audit.find_nested_agents_dirs`).
