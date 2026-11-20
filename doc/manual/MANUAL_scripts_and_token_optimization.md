# Manual de Arquitectura de Scripts, Poda de Reglas y Optimización de Tokens

> **Referencia de Gobernanza**: Guía Oficial de Arquitectura del Repositorio `aagy`  
> **ID**: `MANUAL-SCRIPTS-TOKEN-OPT-01` | **Fecha**: `2026-11-20`  
> **Estado**: `VIGENTE`

---

## 1. Visión General y Objetivos de Diseño

El sistema de agentes y herramientas Anything Antigravity (`aagy`) requiere operar bajo límites estrictos de consumo de tokens, separación de responsabilidades y modularidad limpia. Este manual documenta la reorganización modular de scripts, la poda estricta de `rules/` y la eliminación de duplicidad entre el espacio de trabajo local y el plugin global.

---

## 2. Nueva Estructura Modular de `scripts/`

A partir de la versión `2.2.0`, los scripts se organizan estrictamente por entorno de ejecución (*runtime*), alojando sus pruebas unitarias en subdirectorios `tests/` dedicados:

```text
scripts/
├── py/                  # Scripts en Python 3.11+
│   ├── workspace_audit.py
│   ├── sonar_audit.py
│   ├── ...
│   └── tests/           # 16 suites unitarias de Python (pytest)
├── pwsh/                # Scripts en PowerShell 7 para Windows 11
│   ├── complete-task-pr.ps1
│   ├── audit-workspace.ps1
│   ├── sonar-audit.ps1
│   ├── ...
│   └── tests/           # Suites de verificación para PowerShell
├── sh/                  # Scripts POSIX Bash (LF estricto) para Linux/WSL
│   ├── complete-task-pr.sh
│   ├── audit-workspace.sh
│   ├── ...
│   └── tests/           # Suites de verificación para Bash
├── bin/ecc-agy/         # Proxies de retrocompatibilidad (.ps1, .sh)
└── ecc-agy/             # Proxies de retrocompatibilidad (.py)
```

### Garantía de Retrocompatibilidad (Zero-Breaking Changes)

Cualquier invocación heredada a:

```powershell
pwsh -File scripts/bin/ecc-agy/sonar-audit.ps1
```

o en Linux:

```bash
bash scripts/bin/ecc-agy/sonar-audit.sh
```

se delega de forma transparente e inmediata a:

```powershell
pwsh -File scripts/pwsh/sonar-audit.ps1
```

manteniendo códigos de salida, paso de argumentos (`$@`) y rendimiento idéntico.

---

## 3. Poda de `rules/` y Carga Bajo Demanda (*Lazy-Loading*)

### Política de Reglas Nucleares

El directorio `rules/` solo debe contener reglas transversales invariantes de aplicación global en cada turno de conversación:

1. `rules/AGENTS.md`: Constitución y estándares universales de ingeniería (Google 5-Pillars, SRE, TBD, SonarQube Rating A).
2. `rules/pr-automerge-lifecycle.md`: Ciclo de vida completo de PR, autoresolución de conflictos y squash-automerge.

### Migración de Reglas de Stack a Skills

Las 37 guías de desarrollo por lenguaje (Angular, Go, Java, Python, TypeScript, Web) se han trasladado al almacén de habilidades lazy-loaded:

- `skills/typescript-patterns/SKILL.md`: Tipos, interfaces, estrechamiento de `unknown` y prohibición de `any`.
- `skills/angular-developer/`: Componentes standalone, Signals, OnPush y control flow.
- `skills/golang-patterns/`: Concurrencia, interfaces y gestión de errores idiomáticos.
- `skills/java-coding-standards/`: Registros, inmutabilidad y Spring Boot.
- `skills/python-patterns/`: PEP 8, anotaciones de tipo y dataclasses congeladas.
- `skills/frontend-patterns/`: Composición, rendimiento y accesibilidad web.

---

## 4. Deduplicación de `AGENTS.md`

Para evitar que Antigravity cargue dos veces el contenido completo de `AGENTS.md` (una como regla global del plugin `~/.gemini/config/plugins/aagy` y otra como regla local del repositorio), el archivo en la raíz del repositorio actúa como un puntero de referencia:

- Conserva el marcador `<!-- GEMINI CONTEXT CACHING: STATIC PREFIX INVARIANT -->`.
- Define las cabeceras canónicas `## 1. Core Engineering Invariants` y `## 2. Dynamic Task Lifecycle`.
- Reduce el consumo de tokens en turnos de desarrollo dentro de `aagy` en más de 5.500 tokens.
