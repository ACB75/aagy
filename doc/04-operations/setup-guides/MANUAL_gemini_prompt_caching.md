# Manual de Operación: Optimización de Prompt Caching de Gemini 3.8

> **Referencia de Gobernanza**: Optimización de Rendimiento y Presupuesto de Contexto  
> **Ámbito**: Ecosistema Antigravity (`AGY`), Plugin `ecc-agy` y Reglas Globales `AGENTS.md`  
> **Fecha de Publicación**: `2026-11-20`  

---

## 1. Fundamentos de Gemini Context Caching

Los modelos fundacionales de la familia Gemini (en especial Gemini 3.8 y Gemini Flash/Pro) integran compilación de contexto y reutilización de matrices de Clave/Valor (*KV-Cache*) a nivel de infraestructura.

### 1.1. Principio de Coincidencia de Prefijo Determinista

A diferencia de los sistemas de caché basados en hashing del texto completo, el motor de Gemini Context Caching opera por **coincidencia de prefijo continuo desde el token 0**:

- Si dos solicitudes consecutivas comparten los primeros $K$ tokens de forma idéntica, el compilador reutiliza directamente el estado de atención computado previamente.
- Si un único carácter o token varía al inicio o a mitad del prefijo (por ejemplo, una marca temporal `${TIMESTAMP}`, un ID de sesión aleatorio o un reordenamiento de directivas), **todo el caché posterior queda invalidado inmediatamente**, obligando a recomputar el contexto completo.

---

## 2. Arquitectura Binaria de Reglas (`AGENTS.md`)

Para maximizar la tasa de aciertos de caché (*cache hit ratio*) en turnos sucesivos, las reglas unificadas de trabajo se organizan en dos bloques disjuntos:

### 2.1. Bloque 1: Invariantes Estáticos Universales (Prefijo Determinista)

Este bloque ocupa los primeros miles de tokens del contexto del sistema y permanece **100% inmutable** entre tareas, turnos y sesiones.

Contenido del Bloque 1:

1. Core Engineering Pipeline & Google 5-Pillar Architectural Alignment.
2. Software Reliability Engineering (SRE) & Operational Resilience Baseline (ADR-0008).
3. Trunk-Based Development, Canonical Branching & Multi-Tier Promotion (ADR-0006).
4. Code Quality Standards & SonarQube Quality Gate A.
5. Security & Secrets Baseline.
6. Stack-Specific Standards (Java 25, Angular 21, Python/FastAPI, Multi-Environment).
7. Microservice & SDK Contract Parity.

Delimitador canónico obligatorio:

```markdown
<!-- GEMINI CONTEXT CACHING: STATIC PREFIX INVARIANT -->
```

### 2.2. Bloque 2: Directivas de Tarea, Gobernanza y Flujo (Sufijo Contextual)

Este bloque se sitúa al final de las reglas del sistema y aloja las directivas operativas que pueden requerir adaptación o contexto dinámico específico de la interacción:

1. Mandatory 4-Phase Engineering Lifecycle (`doc/templates/`).
2. Git Commit Formatting & Automated Task Integration (`complete-task-pr.ps1`).
3. Task Lifecycle, Archival & 7-Phase Meta-Prompt Transformation.
4. Tooling Synthesis, Automation & Skill Optimization.
5. Documentation, Diagrams & Write-Time Markdown Linting.
6. Token Efficiency, Context Compaction & Exhaustion Guard.

---

## 3. Directrices para Desarrolladores y Agentes

Para garantizar que las optimizaciones de context caching permanezcan efectivas:

1. **Prohibido inyectar marcas dinámicas al inicio**: Nunca añadir fechas, marcas de tiempo (`date/time`), hashes efímeros o nombres de ramas antes del Bloque Estático.
2. **Sincronización multi-ubicación**: Mantener siempre paridad estricta entre:
   - `./AGENTS.md` (raíz del repositorio)
   - `./rules/AGENTS.md` (subdirectorio de reglas versionadas)
   - `~/.gemini/config/plugins/ecc-agy/rules/AGENTS.md` (plugin global cargado en memoria de Antigravity)
3. **Verificación automatizada en CI/Tests**: Toda modificación a las reglas del sistema debe ser validada mediante `test_static_prompt_caching_prefix_invariance` en `scripts/ecc-agy/tests/test_workspace_audit.py`.

---

## 4. Beneficios SRE y Métricas de Impacto

- **Reducción de Latencia (TTFT)**: Hasta un 60% de decremento en el tiempo de respuesta inicial en conversaciones largas.
- **Eficiencia de Costes**: Los tokens de entrada leídos desde el context cache se facturan con un descuento sustancial respecto a los tokens no cacheados.
- **Estabilidad de Atención**: Menor dispersión atencional del modelo al mantener ancladas las directivas nucleares de ingeniería y seguridad en las capas base del prompt.
