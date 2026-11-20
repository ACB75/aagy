# Fase 1: Toma de Requisitos, Análisis de Superficie e Impacto Home-Lab

> **Referencia de Gobernanza**: Fase 1 del Workflow de Ingeniería ECC / Home-Lab  
> **ID de Tarea**: `feat/ecc/skill-promotion-cli`  
> **Fecha**: `2026-11-20` | **Autor/Rol**: `Carbon (C6) / Modular Plugin Architect`  
> **Estado**: `APROBADO`  

---

## 1. Contexto, Necesidad y Objetivos de Negocio

- **Problema de Negocio / Técnico**: En la arquitectura actual de dos niveles (*Two-Tier*), contamos con 171 skills en el repositorio base (`ACB75/ecc`) pero solo 22 skills activas en el plugin global (`~/.gemini/config/plugins/ecc-agy/skills/`) para mantener el presupuesto siempre activo en $< 1.000$ tokens (~945 tokens). Cuando surge una tarea puntual que requiere una skill especializada de Tier 2 (por ejemplo, `chrome-devtools`, `generative_ui`, `a11y-debugging`), el desarrollador o agente debe copiar manualmente la carpeta o recargar el plugin completo, arriesgándose a olvidar retirarla y degradar el presupuesto de contexto.
- **Objetivo Principal**: Desarrollar un subsistema CLI determinista (`skill_promotion.py` y wrappers `enable-skill.ps1` / `.sh` y `disable-skill.ps1` / `.sh`) que permita promover temporalmente una skill de Tier 2 a la carpeta activa del plugin validando límites ($\le 140$c frontmatter) y registrarla en `.active_promotions.json`, facilitando su desactivación limpia.
- **Alcance (`In-Scope`)**:
  - `scripts/ecc-agy/skill_promotion.py` (motor de promoción y despromoción).
  - `scripts/bin/ecc-agy/enable-skill.ps1` y `enable-skill.sh`.
  - `scripts/bin/ecc-agy/disable-skill.ps1` y `disable-skill.sh`.
  - Validación de existencia, frontmatter $\le 140$c y no-sobrescritura de skills core de Tier 1.
  - Registro de estado en `.active_promotions.json` dentro del plugin.
  - Manual operativo `doc/manual/MANUAL_skill_promotion.md`.
  - Batería de tests unitarios en `scripts/ecc-agy/tests/test_skill_promotion.py`.
- **Fuera de Alcance (`Out-of-Scope`)**:
  - Modificar el contenido de las 171 skills existentes.
  - Comprometer archivos temporales de promoción en el repositorio Git.

---

## 2. Requisitos Funcionales (`RF`) y Criterios de Aceptación (`CA`)

### 2.1. Requisitos Funcionales

- **`RF-01` (Promoción On-Demand `enable-skill`)**: Validar que la skill exista en `skills/<nombre>/SKILL.md`, verificar que `description` $\le 140$ caracteres, comprobar que no sea una skill core ya presente en Tier 1, copiar la carpeta a `~/.gemini/config/plugins/ecc-agy/skills/<nombre>` y registrar la entrada en `.active_promotions.json`.
- **`RF-02` (Desactivación On-Demand `disable-skill`)**: Eliminar la copia en el plugin activo y remover la entrada de `.active_promotions.json`.
- **`RF-03` (Listado de Promociones `list`)**: Listar qué skills están actualmente promovidas en el plugin.
- **`RF-04` (Protección de Skills Core)**: Prohibir expresamente la eliminación o sobreescritura accidental de skills nucleares de Tier 1 (por ejemplo, `engineering-lifecycle`, `sre-reliability`, `verification-loop`).

### 2.2. Criterios de Aceptación Verificables (Given / When / Then)

- [x] **`CA-01`**: Dada una skill válida en `skills/`, cuando se ejecute `enable-skill.ps1 -Name <skill>`, entonces la skill se copia al plugin y `.active_promotions.json` contiene su registro.
- [x] **`CA-02`**: Dada una skill promovida, cuando se ejecute `disable-skill.ps1 -Name <skill>`, entonces se elimina del plugin y de `.active_promotions.json` sin alterar el resto de skills.
- [x] **`CA-03`**: Dada una skill inexistente o con frontmatter $> 140$ caracteres, la promoción se rechaza con código de salida `1`.
- [x] **`CA-04`**: Intento de deshabilitar una skill core de Tier 1 es rechazado con error explícito.

---

## 3. Matriz de Impacto en Arquitectura Home-Lab

| Dimensión Arquitectónica | ¿Impactado? (`SÍ/NO`) | Nivel de Riesgo (`Bajo/Medio/Alto`) | Detalle de la Afectación y Mitigación |
| :--- | :---: | :---: | :--- |
| **Paridad `home-lab-sdk`** | `NO` | - | Sin impacto en SDKs. |
| **Persistencia PostgreSQL LTS** | `NO` | - | Sin cambios de base de datos. |
| **Ingress Único (`cluster-lb`)** | `NO` | - | Sin cambios de red. |
| **Resolución Split-DNS** | `NO` | - | Sin cambios DNS. |
| **Restricciones de Hardware** | `NO` | Bajo | Mantiene el presupuesto de tokens siempre en reposo $\le 1.000$ tokens. |
| **Variables `.env` / Secretos** | `NO` | - | Sin secretos requeridos. |

---

## 4. Garantía Estricta de Retrocompatibilidad (Zero-Breaking Policy)

- **¿Introduce Breaking Changes?**: `[x] NO (100% Retrocompatible)`
- **Estrategia Aditiva (Non-Breaking)**:
  - Las 22 skills core de Tier 1 permanecen intactas e inmutables.
  - `.active_promotions.json` reside en la carpeta local del plugin del usuario y no contamina el control de versiones de Git.
