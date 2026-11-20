# Fase 1: Toma de Requisitos, Análisis de Superficie e Impacto Home-Lab

> **Referencia de Gobernanza**: Fase 1 del Workflow de Ingeniería ECC / Home-Lab  
> **ID de Tarea**: `refactor/ecc/doc-templates-standardization`  
> **Fecha**: `2026-11-20` | **Autor/Rol**: `Carbon (C6) / Documentation Governance Architect`  
> **Estado**: `APROBADO`  

---

## 1. Contexto, Necesidad y Objetivos de Negocio

- **Problema de Negocio / Técnico**: Las plantillas base de toma de requisitos/ADR y de autopsias post-mortem presentaban denominaciones y ubicaciones dispares: `doc/TEMPLATE_REQUISITOS_ARQUITECTURA.md` se encontraba suelto en la raíz de `doc/` en lugar de alojarse en `doc/adr/`, y `TEMPLATE_POSTMORTEM_5W.md` contenía el sufijo redundante `_5W.md` en vez del canónico `TEMPLATE_POSTMORTEM.md`. Esta dispersión dificulta la localización y el cumplimiento del estándar de documentación estandarizada (`<project>/doc/`).
- **Objetivo Principal**: Reubicar `doc/TEMPLATE_REQUISITOS_ARQUITECTURA.md` a `doc/adr/TEMPLATE_ADR.md` y renombrar `doc/post-mortem/TEMPLATE_POSTMORTEM_5W.md` a `doc/post-mortem/TEMPLATE_POSTMORTEM.md`, actualizando atómicamente todas las referencias en scripts, documentación, índices y tests con cero enlaces rotos.
- **Alcance (`In-Scope`)**:
  - `git mv doc/TEMPLATE_REQUISITOS_ARQUITECTURA.md doc/adr/TEMPLATE_ADR.md`.
  - `git mv doc/post-mortem/TEMPLATE_POSTMORTEM_5W.md doc/post-mortem/TEMPLATE_POSTMORTEM.md`.
  - Actualización de referencias en `scripts/ecc-agy/generate_postmortem.py`, `generate-postmortem.ps1` / `.sh`.
  - Actualización de enlaces en `README.md`, `doc/INDEX.md`, `doc/README.md`, `doc/LOG.md`, `.gemini/GEMINI.md`.
  - Actualización de tests y validación de DavidAnson markdownlint.
- **Fuera de Alcance (`Out-of-Scope`)**:
  - Modificar la estructura de contenido interno de las plantillas (salvo rutas o cabeceras actualizadas).

---

## 2. Requisitos Funcionales (`RF`) y Criterios de Aceptación (`CA`)

### 2.1. Requisitos Funcionales

- **`RF-01` (Movimiento de Plantilla ADR)**: `doc/TEMPLATE_REQUISITOS_ARQUITECTURA.md` pasa a `doc/adr/TEMPLATE_ADR.md`.
- **`RF-02` (Renombrado de Plantilla Post-Mortem)**: `doc/post-mortem/TEMPLATE_POSTMORTEM_5W.md` pasa a `doc/post-mortem/TEMPLATE_POSTMORTEM.md`.
- **`RF-03` (Actualización de Generador Post-Mortem)**: `generate_postmortem.py` y wrappers deben apuntar por defecto a `doc/post-mortem/TEMPLATE_POSTMORTEM.md`.
- **`RF-04` (Cero Enlaces Rotos)**: Ningún archivo Markdown del repositorio debe contener referencias rotas hacia las rutas antiguas.

### 2.2. Criterios de Aceptación Verificables (Given / When / Then)

- [x] **`CA-01`**: Dados los archivos de destino, `doc/adr/TEMPLATE_ADR.md` y `doc/post-mortem/TEMPLATE_POSTMORTEM.md` existen y las rutas antiguas ya no existen.
- [x] **`CA-02`**: Cuando se ejecute `generate_postmortem.py`, la plantilla por defecto cargada es `doc/post-mortem/TEMPLATE_POSTMORTEM.md` y los tests pasan al 100%.
- [x] **`CA-03`**: `audit-workspace.ps1` y `lint-markdown.ps1` pasan con código de salida `0`.

---

## 3. Matriz de Impacto en Arquitectura Home-Lab

| Dimensión Arquitectónica | ¿Impactado? (`SÍ/NO`) | Nivel de Riesgo (`Bajo/Medio/Alto`) | Detalle de la Afectación y Mitigación |
| :--- | :---: | :---: | :--- |
| **Paridad `home-lab-sdk`** | `NO` | - | Sin impacto en código ejecutable de SDKs. |
| **Persistencia PostgreSQL LTS** | `NO` | - | Sin base de datos. |
| **Ingress Único (`cluster-lb`)** | `NO` | - | Sin cambios de red. |
| **Resolución Split-DNS** | `NO` | - | Sin cambios DNS. |
| **Restricciones de Hardware** | `NO` | Bajo | Solo reubicación de documentación Markdown. |
| **Variables `.env` / Secretos** | `NO` | - | Sin secretos requeridos. |

---

## 4. Garantía Estricta de Retrocompatibilidad (Zero-Breaking Policy)

- **¿Introduce Breaking Changes?**: `[x] NO (100% Retrocompatible)`
- **Estrategia Aditiva (Non-Breaking)**:
  - Todas las referencias internas se actualizan atómicamente en el mismo commit.
