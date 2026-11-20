# Estándar de Documentación y Gobernanza `/doc` v2 (`DOC_STANDARDS.md`)

> **Versión del Esquema**: `2.0`  
> **Contrato de Rutas**: [`.governance/docs-map.json`](../../.governance/docs-map.json) | **Motor**: [`docs_map.py`](../../scripts/py/docs_map.py)  
> **ADR Asociada**: [`ADR-0003`](../02-adr/ADR_aagy_0003_doc_structure_v2_and_manual_parity.md)

---

## 1. Jerarquía Canónica `/doc` v2

La raíz de [`doc/`](../INDEX.md) contiene **exclusivamente** 4 documentos vivos y 7 carpetas numeradas por ciclo de vida:

```text
doc/
├── INDEX.md                      # Mapa maestro de navegación (sin README.md duplicado)
├── CONTEXT.md                    # Glosario de dominio y fronteras de módulos
├── STATUS.md                     # Métricas actuales de calidad, cobertura y tokens
├── LOG.md                        # Histórico cronológico append-only de cambios materiales
├── 00-governance/                # Estándares, guía manual, referencias y plantillas
│   ├── DOC_STANDARDS.md          # Este estándar
│   ├── MANUAL_WORKFLOW.md        # Guía de paridad 1-a-1 Manual <-> Plugin
│   ├── references/               # the-security-guide.md, google-modern-stack.md
│   └── templates/                # TEMPLATE_ADR.md, TEMPLATE_POSTMORTEM.md y 01..04_*
├── 01-architecture/              # Guías de arquitectura, contratos API y diagramas
│   ├── api-contracts/            # Índices y esquemas de contratos
│   └── dgrms/                    # Diagramas arquitectónicos (.mmd, .puml, .bpmn)
├── 02-adr/                       # Architecture Decision Records (README.md + ADR_*)
├── 03-domain-and-flows/          # Procesos de negocio, dominio y secuencias
│   ├── business-processes/       # Procesos BPMN / negocio
│   ├── domain-models/            # Modelos conceptuales y flujos
│   ├── sequences/                # Secuencias e interacciones
│   └── dgrms/                    # Diagramas transversales (.puml, .bpmn, .mmd)
├── 04-operations/                # Operación diaria SRE y guías de entorno
│   ├── runbooks/                 # Runbooks operativos (PG locks, Ingress, SDK, CD)
│   └── setup-guides/             # Guías de configuración (hooks, prompt caching, skills)
├── 05-post-mortems/              # Autopsias SRE 5W (PM_<rama>_<timestamp>.md)
└── 06-backlog/                   # Gestión viva de demanda y ejecución
    ├── IDEAS.md                  # Banco de propuestas Draft / Approved
    ├── TODO.md                   # Backlog activo bajo metodología de 7 fases
    ├── done/                     # Histórico archivado de TODOs completados
    ├── plans/                    # Planes y REQs activos
    └── quick/                    # Notas ligeras de entrada directa (--phase TODO)
```

### Reglas de Higiene en `/doc`

1. **Cero duplicidad en raíz**: Queda prohibido mantener `doc/README.md`; el índice único es [`doc/INDEX.md`](../INDEX.md). El archivo `README.md` reside únicamente en la raíz del repositorio.
2. **Cero directorios vacíos**: Todo subdirectorio activo bajo `doc/` debe contener al menos un documento o `README.md` índice (`audit-workspace.ps1` falla ante carpetas vacías).
3. **Convención de nombres**:
   - Documentos transversales de referencia en minúsculas con guion (`the-security-guide.md`, `google-modern-stack.md`).
   - Plantillas unificadas en `00-governance/templates/` con prefijo canónico `TEMPLATE_*.md` o `01..04_*.md`.

---

## 2. Convención Universal de Diagramas (`<folder>/dgrms/`)

Toda carpeta que almacene diagramas organiza sus fuentes dentro de una subcarpeta `dgrms/`, separando por formato y propósito:

| Extensión | Lenguaje / Motor | Uso Canónico | Ubicación Ejemplo |
| :---: | :--- | :--- | :--- |
| **`.mmd`** | Mermaid (`flowchart`, `sequenceDiagram`, `stateDiagram-v2`, `erDiagram`) | Arquitectura, modelos de dominio, actividad y flujos técnicos | [`01-architecture/dgrms/`](../01-architecture/dgrms/) |
| **`.puml`** | PlantUML | Diagramas de casos de uso (`@startuml`) y actores del sistema | [`03-domain-and-flows/dgrms/`](../03-domain-and-flows/dgrms/) |
| **`.bpmn`** | BPMN 2.0 XML | Procesos de negocio y orquestación funcional end-to-end | [`03-domain-and-flows/dgrms/`](../03-domain-and-flows/dgrms/) |

---

## 3. Parametrización `.governance/docs-map.json` y Retrocompatibilidad

Todos los scripts de automatización (`scripts/py/`, `scripts/pwsh/`, `scripts/sh/`) consumen [`scripts/py/docs_map.py`](../../scripts/py/docs_map.py) en lugar de concatenar rutas fijas a `doc/`.

1. **Esquema v2 (`schema_version: 2`)**: Declara tanto roles estándar en nivel superior (`constitution`, `map`, `context`, `status`, `history`, `adr_dir`, `adr_index`) como el mapa granular `"paths"` (`todo`, `todo_done`, `ideas`, `plans`, `quick`, `templates`, `postmortems`, `postmortem_template`, `adr_template`, etc.).
2. **Fallback Clásico Automático (`home-lab`)**: Si `.governance/docs-map.json` no existe o declara esquema v1, `docs_map.py` resuelve automáticamente las rutas heredadas (`doc/TODO.md`, `doc/TODO_DONE/`, `doc/IDEAS.md`, `doc/plan/`, `doc/templates/`, `doc/post-mortem/`, `doc/adr/`), garantizando **Zero-Breaking Changes** en repositorios consumidores.
3. **Bastionado Anti Path-Traversal**: `validate_repo_relative_path()` rechaza cadenas vacías, bytes nulos, rutas absolutas (POSIX/Windows), unidades de disco o secuencias `../` que resuelvan fuera de `RepoRoot`.

---

## 4. Compuertas de Calidad Documental

Todo cambio documental debe superar antes del merge:

- `pwsh -NoProfile -File scripts/pwsh/lint-markdown.ps1 -CheckOnly` (exit `0`, estándar DavidAnson `.markdownlint.json`).
- `pwsh -NoProfile -File scripts/pwsh/map-docs.ps1` (`0` enlaces relativos rotos y `.governance/docs-map.json` íntegro).
- `python skills/docs-governance/scripts/audit-docs.py --root . --scope spine` y `--scope adr` (integridad estructural y de índices ADR).
