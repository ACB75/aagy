# Fase 1: Toma de Requisitos, Análisis de Superficie e Impacto Home-Lab

> **Referencia de Gobernanza**: Fase 1 del Workflow de Ingeniería ECC / Home-Lab  
> **ID de Tarea**: `feat/ecc/gemini-mcp-deep-ops`  
> **Fecha**: `2026-11-20` | **Autor/Rol**: `Carbon (C6) / Gemini Platform Architect`  
> **Estado**: `APROBADO`  

---

## 1. Contexto, Necesidad y Objetivos de Negocio

- **Problema de Negocio / Técnico**:
  `gemini-mcp` (RLabs-Inc) expone más de 30 herramientas avanzadas (Context Caching, Deep Research, análisis multimodal de PDFs/vídeos/logs y salida estructurada). Habilitarlo permanentemente en el plugin global inyecta entre 4.500 y 10.000 tokens en cada turno conversacional, desbordando el presupuesto de contexto en reposo.
- **Objetivo Principal**:
  Crear una integración de *zero-overhead* consistente en:
  1. Una plantilla aislada de plugin opcional `templates/plugins/gemini-mcp/` con `"disabled": true` por defecto y lectura de `GEMINI_API_KEY` vía variable de entorno.
  2. Una skill bajo demanda Tier 2 `skills/gemini-deep-ops/SKILL.md` ($\le 140$c) que delega en un script determinista en `scripts/ecc-agy/gemini_deep_ops.py` y wrappers en `scripts/bin/ecc-agy/`.
  3. Guía de diagnóstico multimodal para post-mortems SRE en Home-Lab.
- **Alcance (`In-Scope`)**:
  - Plantilla `templates/plugins/gemini-mcp/` (`plugin.json`, `mcp_config.json`, `README.md`).
  - Utilidad CLI `scripts/ecc-agy/toggle_gemini_mcp.py` y wrappers `.ps1` / `.sh`.
  - Skill Tier 2 `skills/gemini-deep-ops/SKILL.md`.
  - Script CLI determinista `scripts/ecc-agy/gemini_deep_ops.py` y wrappers `.ps1` / `.sh`.
  - Guía técnica `doc/manual/MANUAL_gemini_deep_ops_multimodal.md`.
  - Pruebas unitarias en `scripts/ecc-agy/tests/test_gemini_deep_ops.py`.
- **Fuera de Alcance (`Out-of-Scope`)**:
  - Activación forzada de `gemini-mcp` en el catálogo Tier 1 global.
  - Almacenamiento persistente de claves de API en texto plano.

---

## 2. Requisitos Funcionales (`RF`) y Criterios de Aceptación (`CA`)

### 2.1. Requisitos Funcionales

- **`RF-01` (Plantilla de Plugin Aislado Zero-Overhead)**:
  Proveer en `templates/plugins/gemini-mcp/` la configuración de `gemini-mcp` con `"disabled": true` tanto en `plugin.json` como en `mcp_config.json`, parametrizando `GEMINI_API_KEY` vía `${GEMINI_API_KEY}` sin credenciales hardcodeadas.
- **`RF-02` (Utilidad de Alternancia Determinista `toggle-gemini-mcp`)**:
  Crear un script idempotente que permita habilitar (`--enable`) o deshabilitar (`--disable`) el servidor MCP opcional en proyectos específicos, verificando siempre que en reposo permanezca desactivado.
- **`RF-03` (Skill Tier 2 `gemini-deep-ops`)**:
  Crear `skills/gemini-deep-ops/SKILL.md` con descripción en frontmatter $\le 140$ caracteres y fronteras negativas claras, enfocada en análisis de volcados de memoria, logs masivos y generación de diagnósticos para Post-Mortems 5W.
- **`RF-04` (CLI de Apoyo `gemini-deep-ops`)**:
  Implementar `scripts/ecc-agy/gemini_deep_ops.py` en Python stdlib pura (con soporte de mock y fallback seguro si falta `GEMINI_API_KEY`) y wrappers en `scripts/bin/ecc-agy/`.
- **`RF-05` (Conformidad con Guardrails de Presupuesto)**:
  Verificar que `workspace_audit.py` certifique 0 tokens de incremento en Tier 1 global y 0 violaciones en el hard gate de MCPs.

### 2.2. Criterios de Aceptación Verificables (Given / When / Then)

- [x] **`CA-01`**: Dado el manifiesto de la plantilla `templates/plugins/gemini-mcp/mcp_config.json`, cuando se ejecuta `workspace_audit.py`, entonces no emite ninguna violación de servidor pesado activo y computa 0 tokens en reposo.
- [x] **`CA-02`**: Dada la skill `skills/gemini-deep-ops/SKILL.md`, cuando se audita su frontmatter, su longitud de descripción es $\le 140$ caracteres y `workspace_audit.py` pasa con código 0.
- [x] **`CA-03`**: Dado el CLI `gemini_deep_ops.py`, cuando se ejecuta con `--help` o subcommand `status`, retorna exit code 0 y muestra el estado seguro sin filtrar secretos.
- [x] **`CA-04`**: Dada la utilidad `toggle_gemini_mcp.py`, cuando se ejecuta `--status`, reporta correctamente si el plugin está desactivado o activado.
- [x] **`CA-05`**: Cobertura de tests unitarios $\ge 80\%$ y SonarQube Quality Gate Rating A (0 violaciones).

---

## 3. Matriz de Impacto en Arquitectura Home-Lab

| Dimensión Arquitectónica | ¿Impactado? (`SÍ/NO`) | Nivel de Riesgo (`Bajo/Medio/Alto`) | Detalle de la Afectación y Mitigación |
| :--- | :---: | :---: | :--- |
| **Paridad `home-lab-sdk`** | `NO` | - | Sin cambios de contratos ni DTOs compartidos. |
| **Persistencia PostgreSQL LTS** | `NO` | - | Sin impacto en bases de datos. |
| **Ingress Único (`cluster-lb`)** | `NO` | - | Sin impacto en red o proxies inversos. |
| **Resolución Split-DNS** | `NO` | - | Sin afectación a DNS. |
| **Consumo de Contexto (Tokens)** | `SÍ` | `Bajo` | Impacto nulo en reposo (0 tokens); activación bajo demanda exclusivamente. |
| **Gestión de Secretos** | `SÍ` | `Bajo` | `GEMINI_API_KEY` se lee exclusivamente de variables de entorno del sistema o `.env`. |

---

## 4. Garantía Estricta de Retrocompatibilidad (Zero-Breaking Policy)

- **¿Introduce Breaking Changes?**: `[x] NO (100% Retrocompatible)`.
- **Estrategia Aditiva**:
  - La skill `gemini-deep-ops` se ubica en Tier 2 (`skills/`), sin modificar el catálogo Tier 1 sincronizado.
  - La plantilla es opt-in y permanece desactivada por defecto.

---

## 5. Compuertas SRE de Rendimiento y Persistencia Segura

- **Latencia de Ejecución**: CLI local responde en $< 300\text{ ms}$ en modo diagnóstico.
- **Consumo de Memoria**: $< 50\text{ MB}$ en entorno local.
- **Manejo Seguro de Errores**: Si `GEMINI_API_KEY` no está configurada, el CLI emite un mensaje instructivo sin lanzar excepciones no controladas ni exponer trazas de pila.

---

## 6. Threat Modeling y Bastionado de Seguridad

| Vector de Ataque / Amenaza | Riesgo (`Bajo/Medio/Alto/N/A`) | Mitigación y Bastionado Aplicado |
| :--- | :---: | :--- |
| **Filtración de `GEMINI_API_KEY`** | `Medio` | Lectura exclusiva por entorno (`os.environ`), cero claves en código o JSON de plantillas. |
| **Inyección de Comandos en Wrappers** | `Bajo` | Argumentos pasados como arrays sin interpolación directa de cadenas shell. |
| **Desbordamiento de Contexto por MCP** | `Medio` | Forzado permanente de `"disabled": true` verificado por `workspace_audit.py`. |
