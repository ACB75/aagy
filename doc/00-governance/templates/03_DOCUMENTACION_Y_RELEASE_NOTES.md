# Fase 3: Documentación y notas de versión

> **ID de Tarea**: `<id_tarea>`
> **Fecha**: `YYYY-MM-DD` | **Autor/Rol**: `<autor / rol>`
> **Estado**: `BORRADOR | COMPLETO`
> **Ubicación en el repo**: `<carpeta de planes>/DOCS_<id_tarea>.md` (versión `vX.Y.Z`)

---

## 0. Estado actual

Qué documentos describen hoy lo que cambia y cuáles quedan desfasados.

## 1. Contexto y objetivos

- **Problema**: resumen del REQ y del PLAN.
- **Objetivo**: que la documentación refleje el código al cerrar la tarea.
- **Alcance**: documentos que se tocan.
- **Fuera de alcance**: documentos que no.

## 2. Notas de versión (`vX.Y.Z`)

- **feat**: funcionalidad nueva y su valor.
- **fix**: errores corregidos.
- **perf / sec**: mejoras de rendimiento o seguridad.
- **Retrocompatibilidad**: `100 % retrocompatible` o pasos de migración.

## 3. Espina documental

- [ ] ADR en la carpeta de ADR si la decisión es difícil de revertir, e índice actualizado.
- [ ] Manual, runbook o guía afectados.
- [ ] Diagramas afectados.
- [ ] `STATUS.md` (métricas) y `LOG.md` (hito y PR).
- [ ] Postmortem si la rama es `fix/*` (`generate_postmortem.py`).

<!-- aagy-extensions -->

## 4. Criterios de aceptación

- [ ] **CA-01**: ningún documento cita scripts, rutas o flujos que no existan.

## 5. Paridad aagy ↔ aagy-ecc

Documentos que existen en un plugin y deben existir en el otro.

## 6. Preguntas abiertas

- **P-01**: `<pregunta>`. Por defecto: `<valor>`.

## 7. Referencias

- `REQ_<id_tarea>.md`, `PLAN_<id_tarea>.md`
