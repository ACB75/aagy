# Manual de Operación: Telemetría de Tokens en Sesión y Política de Compactación

> **Referencia de Gobernanza**: Optimización de Contexto y Gestión del Ciclo de Vida de Agentes  
> **Ámbito**: Ecosistema Antigravity (`AGY`), Harness `aagy` y Monorepo `home-lab`  
> **Fecha de Publicación**: `2026-11-20`  

---

## 1. Fundamentos y Necesidad de Telemetría

Durante sesiones prolongadas de desarrollo, ejecución de pruebas y análisis de código, el archivo de registro estructurado de la conversación (`transcript.jsonl`) acumula difs, salidas de terminal, llamadas a herramientas y razonamiento interno (*thinking*).

### 1.1. Degradación Atencional y Coste por Turno

- **Crecimiento Lineal del Coste**: En cada turno sucesivo, todo el historial de la conversación previa debe ser re-evaluado, incrementando el coste de inferencia.
- **Degradación Atencional (*Needle-in-a-Haystack*)**: A partir de los 45.000 tokens en sesión, la capacidad del modelo para recordar restricciones operacionales o detalles específicos introducidos al inicio de la sesión experimenta una degradación progresiva.
- **Solución Canónica**: Ejecución oportuna del comando de compactación `/compact`, que resume la trayectoria conservando el estado crítico.

---

## 2. Herramienta `session-token-monitor`

El monitor analiza el archivo `transcript.jsonl` de la sesión en $< 150\text{ ms}$, estimando el recuento total de tokens computados mediante el ratio estándar del arnés ($3.8\text{ caracteres/token}$).

### 2.1. Opciones de Invocación

En Windows 11 (`pwsh`):

```powershell
# Diagnóstico completo interactivo
pwsh -File scripts/pwsh/session-token-monitor.ps1

# Salida en JSON para automatizaciones
pwsh -File scripts/pwsh/session-token-monitor.ps1 -Json

# Modo alerta (silencioso salvo si excede 45k tokens)
pwsh -File scripts/pwsh/session-token-monitor.ps1 -AlertOnly
```

En Linux o WSL (`bash` / `sh`):

```sh
./scripts/sh/session-token-monitor.sh --alert-only
```

---

## 3. Integración en el Pipeline de Finalización de PR (`complete-task-pr.ps1`)

Al concluir con éxito una tarea e integrar su PR en `main`, `complete-task-pr.ps1` ejecuta automáticamente:

```powershell
pwsh -File scripts/pwsh/session-token-monitor.ps1 -Threshold 45000 -AlertOnly
```

Si el transcript supera los 45.000 tokens acumulados, el arnés emite una advertencia destacada recomendando al desarrollador o agente ejecutar `/compact` antes de comenzar la siguiente tarea del backlog.

---

## 4. Métricas de Rendimiento y Rendimiento SRE

- **Tiempo de Parseo**: $< 120\text{ ms}$ para transcripts de más de 2.000 pasos.
- **Tolerancia a Concurrencia**: Manejo de lecturas en caliente con reintentos defensivos ante bloqueos transitorios de I/O.
- **Aislamiento**: Implementado íntegramente con Python stdlib sin dependencias externas pesadas.
