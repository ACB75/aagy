# Fase 1: Toma de Requisitos, Análisis de Superficie e Impacto Home-Lab

> **Referencia de Gobernanza**: Fase 1 del Workflow de Ingeniería ECC / Home-Lab  
> **ID de Tarea**: `feat/ecc/workspace-audit-budget-hard-gate`  
> **Fecha**: `2026-11-20` | **Autor/Rol**: `Carbon (C6) / Principal AI Harness Architect`  
> **Estado**: `APROBADO`  

---

## 1. Contexto, Necesidad y Objetivos de Negocio

- **Problema de Negocio / Técnico**:
  `workspace_audit.py` auditaba la longitud de descripciones de skills ($\le 140$c) y subagentes ($\le 120$c), pero carecía de compuertas duras (*hard gates*) para:
  1. El límite de tamaño por archivo de reglas de Antigravity (máximo 24.000 bytes / 24 KB por archivo).
  2. El techo seguro de tokens agregados en reglas (`defaultRulesBudget` = 20.000 tokens; techo seguro configurado en 16.000 tokens).
  3. El presupuesto de personalizaciones *eager* en plugins activos (`MAX_EAGER_CUSTOMIZATION_TOKENS` = 3.000 tokens) y la detección de servidores MCP pesados habilitados por defecto (ej. `gemini-mcp` con 30+ tools) sin `"disabled": true`, lo que causa desbordamientos de contexto en reposo.
- **Objetivo Principal**:
  Implementar en `workspace_audit.py` un guardrail determinista y bloqueante (exit code != 0) que valide límites de bytes/tokens de reglas, configuración de MCPs activos y presupuesto de personalizaciones eager, con soporte nativo en `audit-workspace.ps1` y suite exhaustiva de tests `pytest`.
- **Alcance (`In-Scope`)**:
  - Constantes de presupuesto (`MAX_RULE_FILE_BYTES = 24_000`, `MAX_RULES_TOTAL_TOKENS = 16_000`, `MAX_EAGER_CUSTOMIZATION_TOKENS = 3_000`, `ACTIVE_MCP_BASE_TOKENS = 1_500`, `HEAVY_MCP_SERVERS = {"gemini-mcp"}`, `HEAVY_MCP_TOKENS = 4_500`).
  - Funciones de auditoría `audit_rules(target_dir, include_rules)` y `audit_mcps(target_dir)`.
  - Integración en `AgentTarget` (`is_plugin: bool = False`) y cómputo de tokens en `BudgetReport`.
  - Auditoría del plugin global `~/.gemini/config/plugins/ecc-agy` si está presente.
  - Tests unitarios en `scripts/ecc-agy/tests/test_workspace_audit.py` cubriendo todos los casos de violación y casos conformes.
- **Fuera de Alcance (`Out-of-Scope`)**:
  - Instalación o empaquetado del plugin `gemini-mcp` (objeto de la Tarea 2.2).
  - Modificación de la configuración de red de Home-Lab o despliegues en servidores remotos.

---

## 2. Requisitos Funcionales (`RF`) y Criterios de Aceptación (`CA`)

### 2.1. Requisitos Funcionales

- **`RF-01` (Auditoría de Archivos de Reglas Individuales)**:
  Verificar que ningún archivo `.md` de reglas exceda los 24.000 bytes. Ante cualquier archivo que supere este umbral, generar una infracción tipada y bloquear el arnés.
- **`RF-02` (Auditoría de Presupuesto Agregado de Reglas)**:
  Calcular la suma estimada de tokens de todas las reglas activas. Si supera los 16.000 tokens (techo seguro frente al límite de 20.000 tokens), generar infracción bloqueante.
- **`RF-03` (Auditoría de MCPs y Servidores Pesados)**:
  Inspeccionar `mcp_config.json` en los objetivos de auditoría. Si un servidor perteneciente a `HEAVY_MCP_SERVERS` (como `gemini-mcp`) no tiene `"disabled": true`, generar infracción bloqueante. Servidores con `"disabled": true` deben contabilizar 0 tokens de sobrecarga en reposo.
- **`RF-04` (Auditoría de Personalizaciones Eager en Plugins)**:
  Para objetivos identificados como plugin (`is_plugin=True` o existencia de `plugin.json`), calcular la suma de tokens en reposo (skills Tier 1 + agentes Tier 1 + MCPs activos). Si supera `MAX_EAGER_CUSTOMIZATION_TOKENS` (3.000 tokens), generar infracción bloqueante.
- **`RF-05` (Exit Code Determinista y Logging Estructurado)**:
  Cualquier violación en reglas, MCPs o presupuesto eager debe reflejarse en el reporte final y provocar un código de salida `1` en `workspace_audit.py`.

### 2.2. Criterios de Aceptación Verificables (Given / When / Then)

- [x] **`CA-01`**: Dado un archivo de regla con $> 24.000$ bytes, cuando se ejecuta `workspace_audit.py`, entonces se emite `[VIOLATION] Rule file ... is X bytes (>24000 max limit)` y retorna exit code 1.
- [x] **`CA-02`**: Dadas reglas cuyo total de tokens excede 16.000 tokens, cuando se ejecuta `workspace_audit.py`, entonces se emite `[VIOLATION] Aggregated rules exceed safe budget ...` y retorna exit code 1.
- [x] **`CA-03`**: Dado un `mcp_config.json` con `gemini-mcp` sin `"disabled": true`, cuando se ejecuta `workspace_audit.py`, entonces se emite `[VIOLATION] Heavy MCP server 'gemini-mcp' is enabled by default ...` y retorna exit code 1.
- [x] **`CA-04`**: Dado un `mcp_config.json` con `gemini-mcp` y `"disabled": true`, cuando se ejecuta la auditoría, entonces no se emite violación por servidor pesado y sus tokens en reposo son 0.
- [x] **`CA-05`**: Cobertura de tests unitarios $\ge 80\%$ en `test_workspace_audit.py` y SonarQube Rating A (0 violaciones).

---

## 3. Matriz de Impacto en Arquitectura Home-Lab

| Dimensión Arquitectónica | ¿Impactado? (`SÍ/NO`) | Nivel de Riesgo (`Bajo/Medio/Alto`) | Detalle de la Afectación y Mitigación |
| :--- | :---: | :---: | :--- |
| **Paridad `home-lab-sdk`** | `NO` | - | Sin impacto en modelos ni clientes políglotas. |
| **Persistencia PostgreSQL LTS** | `NO` | - | Sin impacto en esquemas ni bases de datos. |
| **Ingress Único (`cluster-lb`)** | `NO` | - | Sin impacto en balanceador o proxy inverso. |
| **Resolución Split-DNS** | `NO` | - | Sin cambios de hostnames ni zonas DNS. |
| **Restricciones de Hardware** | `NO` | - | Auditoría local en tiempo de desarrollo / CI. |
| **Variables `.env` / Secretos** | `NO` | - | Sin secretos nuevos requeridos. |

---

## 4. Garantía Estricta de Retrocompatibilidad (Zero-Breaking Policy)

- **¿Introduce Breaking Changes?**: `[x] NO (100% Retrocompatible)`.
- **Estrategia Aditiva (Non-Breaking)**:
  - Todas las nuevas funciones y campos son aditivos con valores por defecto conservadores.
  - La suite de tests existente continúa pasando sin modificaciones no deseadas.
  - La raíz actual del workspace y el plugin global cumplen estrictamente los nuevos guardrails.

---

## 5. Compuertas SRE de Rendimiento y Persistencia Segura

### 5.1. Rendimiento y Throttling de Recursos

- **Latencia Objetivo**: Ejecución completa de la auditoría en $< 1.5\text{ s}$ en entorno local.
- **Complejidad Algorítmica**:
  - Tiempo: $O(N)$ donde $N$ es el número de archivos en el workspace.
  - Espacio: $O(1)$ adicional más memoria estricta para buffers de lectura.
- **Dependencias**: 100% Python Standard Library (sin paquetes de terceros).

---

## 6. Threat Modeling y Bastionado de Seguridad

| Vector de Ataque / Amenaza | Riesgo (`Bajo/Medio/Alto/N/A`) | Mitigación y Bastionado Aplicado |
| :--- | :---: | :--- |
| **Inyección (JSON / Path Traversal)** | `Bajo` | Parseo seguro con `json.loads` y resolución de rutas canónicas (`resolve()`). |
| **Denegación de Servicio (DoS por archivos enormes)** | `Bajo` | Inspección de `stat().st_size` previa antes de leer el contenido completo en memoria. |
| **Exposición de Secretos** | `Bajo` | No se registran ni leen tokens ni claves API de servidores MCP en los logs de auditoría. |
