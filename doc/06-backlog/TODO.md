# PROTOCOLO DE EJECUCIÓN Y BACKLOG MAESTRO | AAGY ECOSYSTEM

> **Directiva de Agente Autónomo:**
>
> 1. **Orden Topológico:** Analiza las dependencias entre tareas y resuélvelas en el orden secuencial óptimo (gobernanza/harness → tokens/contexto → guardrails de calidad → automatización de git/PRs).
> 2. **Flujo Git Automatizado:** Genera ramas atómicas por tarea, resuelve conflictos de forma contextual, ejecuta tests unitarios/e2e y realiza `auto-merge` continuo en la rama principal hasta agotar el presupuesto de tokens asignado.
> 3. **Tarea Final Obligatoria (Higiene y Meta-Herramientas):** Al completar el backlog funcional, ejecuta una fase final de limpieza: purgar dependencias huérfanas, eliminar código muerto, actualizar documentación técnica y desplegar el motor de autodescubrimiento para sintetizar `skills`, `rules`, `agents` y `git hooks` optimizados para los flujos repetitivos del repositorio.

---

## 0. Backlog Activo

> **Estado Actual (`v4.1.0`)**: **0 tareas pendientes (`100%` completado).**  
> Todas las tareas de optimización de tokens (`Tarea 0.1`), arquitectura documental `/doc` v2 (`Tarea 0.2`), motor unificado de autodescubrimiento y automejora (`Tarea 0.3`), consolidación `scripts/{py,ps1,sh}/tests/` (`Tarea 0.4`) y cierre maestro / rebranding a `aagy` (`Tarea 5.1`) han sido completadas, verificadas y archivadas en [`doc/06-backlog/done/`](done/).

---

## 6. Gobernanza de Modelos, Tokens y Política de Auto-Compact

### 6.1. Matriz de Asignación de Modelos por Dominio (Token Optimization)

| Dominio / Tipo de Tarea | Agente Elemental | Modelo Gemini 3.8 | Presupuesto Tokens / Turno | Justificación de Eficiencia |
| :--- | :--- | :--- | :--- | :--- |
| **Gobernanza `/doc` v2 & Paridad CLI** | **Argon ($Ar_{18}$)** $\rightarrow$ **Carbon ($C_6$)** | `pro` (diseño) + `flash` (scripts) | ~6.000 tokens | Resolvedor `.governance/docs-map.json` con fallback y paridad CLI 1-a-1. |
| **Autodescubrimiento & Automejora** | **Argon ($Ar_{18}$)** $\rightarrow$ **Carbon ($C_6$)** | `pro` (diseño) + `flash` (código) | ~6.000 tokens | Motor `self_improve.py`, instintos a doble nivel y 4 compuertas con budget gate. |
| **Higiene de Scripts & Paridad `aagy-ecc`** | **Carbon ($C_6$)** | `flash` | ~1.500 tokens | Mantenimiento de `scripts/{py,ps1,sh}/tests/`, `AGENTS.md` y paridad `aagy-ecc`. |
| **Arquitectura & Cutover de Ecosistema** | **Argon ($Ar_{18}$)** $\rightarrow$ **Carbon ($C_6$)** | `pro` (cutover) + `flash` (rename) | ~6.000 tokens | Evolución estructural con historial Git y sincronización multi-harness. |

---

### 6.2. Política de Compactación & Disparadores de Auto-Compact

Para preservar la atención del modelo y minimizar el consumo de tokens en sesiones largas:

```
┌────────────────────────────────────────────────────────────────────────┐
│                   POLÍTICA DE COMPACTACIÓN DE SESIÓN                   │
├───────────────────────────────────┬────────────────────────────────────┤
│ DISPARADOR POR EVENTO (LIFECYCLE) │ DISPARADOR POR UMBRAL DE TOKENS    │
├───────────────────────────────────┼────────────────────────────────────┤
│ • Al completar la Fase 4 de tarea │ • Sesión acumulada > 45.000 tokens │
│ • Tras 'complete-task-pr.ps1'     │ • Aviso inmediato de telemetría    │
│ • Antes de cambiar de rama / tarea│ • Ejecutar /compact recomendado    │
└───────────────────────────────────┴────────────────────────────────────┘
```

1. **Disparador Basado en Eventos del Ciclo de Vida**:
   - Tras ejecutar exitosamente `scripts/ps1/complete-task-pr.ps1` y fusionar la rama de tarea en `main`, el contexto de implementación de esa tarea ya no es necesario para la siguiente. Ese es el **punto exacto de compactación** para purgar el historial y comenzar la siguiente tarea con contexto limpio.
2. **Disparador Basado en Umbral Cuantitativo (> 45k tokens)**:
   - Si una tarea compleja requiere múltiples iteraciones de TDD y el transcript acumulado supera los **45.000 tokens**, el agente debe sugerir de inmediato la ejecución del comando `/compact` para consolidar el estado de los archivos modificados y liberar el 70%+ de la ventana de contexto.
3. **Mecanismo de Auto-Compact**:
   - `scripts/ps1/complete-task-pr.ps1` emitirá en su reporte de cierre el aviso: `[ADVICE] Tarea finalizada. Presupuesto acumulado sugerido para compactación. Ejecute /compact antes de iniciar la siguiente tarea.`
