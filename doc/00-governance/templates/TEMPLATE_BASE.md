# <Tipo>: <título>

> **ID de Tarea**: `<id_tarea>`
> **Fecha**: `YYYY-MM-DD` | **Autor/Rol**: `<autor / rol>`
> **Estado**: `BORRADOR | EN REVISIÓN | APROBADO`
> **Ubicación en el repo**: `<ruta del documento>`

Esqueleto común de todos los documentos del harness. Cada tipo (REQ, PLAN, DOCS, PR, ADR, POSTMORTEM, RUNBOOK) copia estas secciones en este orden y solo añade su cuerpo propio entre `1. Contexto y objetivos` y `Criterios de aceptación`. `doc_templates.py check` lo comprueba.

---

## 0. Estado actual

Qué hay hoy (ficheros, comportamiento, datos) y qué falla o falta. Cita rutas y commits.

## 1. Contexto y objetivos

- **Problema**: qué se resuelve y por qué ahora.
- **Objetivo**: resultado observable en una o dos líneas.
- **Alcance**: qué entra.
- **Fuera de alcance**: qué no entra.

## 2. Cuerpo del tipo

Secciones propias del tipo de documento.

<!-- aagy-extensions -->

## 3. Criterios de aceptación

- [ ] **CA-01**: Dado `<contexto>`, cuando `<acción>`, entonces `<resultado verificable>`.

## 4. Paridad aagy ↔ aagy-ecc

Cómo se comporta en los dos plugins. Si un harness no lo permite, declara la asimetría.

## 5. Preguntas abiertas

- **P-01**: `<pregunta>`. Por defecto: `<valor que se usa si nadie responde>`.

## 6. Referencias

- `<rutas, ADR, issues>`
