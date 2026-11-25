# Fase 4: Commits y PR

> **ID de Tarea**: `<id_tarea>`
> **Fecha**: `YYYY-MM-DD` | **Autor/Rol**: `<autor / rol>`
> **Estado**: `BORRADOR | LISTO PARA PR`
> **Ubicación en el repo**: `<carpeta de planes>/REVIEW_<id_tarea>.md`

---

## 0. Estado actual

- **Rama**: `<tipo>/<proyecto>/<nombre>` (`validate_branch.py`). **Destino**: `main`.
- **Ficheros**: salida de `git status -s`.

## 1. Contexto y objetivos

- **Problema**: resumen del REQ.
- **Objetivo**: integrar el cambio en un único squash reversible.
- **Alcance**: ficheros de la rama.
- **Fuera de alcance**: lo que va en otra tarea.

## 2. Título y cuerpo

- **Título**: `[type]-[projects]: <título imperativo>`
- **Cuerpo** (mismas secciones que la plantilla de PR): Motivación, Issues (`Closes #N`), Checklist, Rollback.

## 3. Revisión previa (pre-flight)

- [ ] Tests en verde y cobertura ≥ 80 % en la lógica nueva.
- [ ] Linters, Sonar Rating A y auditoría de seguridad sin hallazgos.
- [ ] `python scripts/py/ci_local.py run` en verde.
- [ ] Documentación de la fase 3 en la misma rama.

<!-- aagy-extensions -->

## 4. Criterios de aceptación

- [ ] **CA-01**: la PR cumple la plantilla y la fusiona una persona (sin auto-merge).

## 5. Paridad aagy ↔ aagy-ecc

`complete-task-pr` en los dos plugins; asimetrías si las hay.

## 6. Preguntas abiertas

- **P-01**: `<pregunta>`. Por defecto: `<valor>`.

## 7. Referencias

- `REQ_<id_tarea>.md`, `PLAN_<id_tarea>.md`, `DOCS_<id_tarea>.md`
