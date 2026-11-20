# Fase 1: Requisitos e Impacto Home-Lab | Despliegue Automatizado por Tag en git-flow-helper

> **Referencia de Gobernanza**: Fase 1 del Workflow de Ingeniería ECC / Home-Lab  
> **ID de Tarea**: `feat/ecc/git-flow-deploy`  
> **Fecha**: 2026-11-20 | **Autor/Rol**: Argon ($Ar_{18}$) & Carbon ($C_6$) - Release Automation & Deployment Engineer  
> **Estado**: `APROBADO`  

---

## 1. Contexto, Necesidad y Objetivos de Negocio

- **Problema de Negocio / Técnico**:
  Actualmente `git-flow-helper.ps1 -Action promote` crea el tag semántico anotado (`vX.Y.Z-sandbox` o `vX.Y.Z`) y lo publica en GitHub, pero el despliegue físico de contenedores en los hosts de Home-Lab (FRACTAL para SANDBOX y NEO para LIVE) requiere pasos manuales o scripts ad-hoc. Para cerrar el ciclo Trunk-Based Development (ADR-0006), la promoción debe soportar opcionalmente el despliegue físico (`-Deploy`) con verificación automática de sondas de salud (health probes) y rollback automático en menos de 2 minutos ante fallos.
- **Objetivo Principal**:
  Extender `git-flow-helper.ps1` y su homólogo Bash `git-flow-helper.sh` con los parámetros `-Deploy`, `-Environment [sandbox|live]` y `-DryRun`, implementando un pipeline de despliegue determinista que levante contenedores, verifique liveness probes (3 reintentos x 5s) y ejecute rollback automático en caso de código de salida no-cero.
- **Alcance (`In-Scope`)**:
  1. Extensión de `git-flow-helper.ps1` y `git-flow-helper.sh` con:
     - `-Deploy`: switch para activar el despliegue tras crear y subir el tag.
     - `-Environment`: entorno destino (`sandbox` o `live`).
     - `-DryRun`: switch para simular la secuencia completa sin ejecutar comandos destructivos o mutaciones de contenedores.
  2. Protocolo de resiliencia y rollback:
     - Captura del estado/tag anterior antes de mutar.
     - Ejecución de `docker compose pull` / `up -d`.
     - Sondeo de salud (healthcheck / liveness probe) con 3 reintentos x 5s.
     - Si falla el sondeo: rollback inmediato al tag anterior en $< 2\text{ minutos}$ y notificación de error.
  3. Soporte de ejecución local o remota simulada con variables de entorno de host (`HOMELAB_SANDBOX_HOST`, `HOMELAB_LIVE_HOST`).
  4. Protección estricta de secretos: ninguna variable sensible (`.env`) debe volcarse en texto claro a la consola.
  5. Suite de pruebas unitarias en `scripts/ecc-agy/tests/test_git_flow_deploy.py`.
  6. Documentación técnica y manual operativo en `doc/manual/MANUAL_multitier_deployment.md`.
- **Fuera de Alcance (`Out-of-Scope`)**:
  - Aprovisionamiento de hardware físico o instalación de Docker desde cero.

---

## 2. Requisitos Funcionales (`RF`) y Criterios de Aceptación (`CA`)

### 2.1. Requisitos Funcionales

- **`RF-01 (Parámetro -Deploy en Acción promote)`**:
  Cuando `-Action promote` se invoque con `-Deploy`, el script debe ejecutar la secuencia de despliegue para el entorno indicado por `-Environment` (defecto: `sandbox`).
- **`RF-02 (Modo Simulación -DryRun)`**:
  Con `-DryRun`, el script debe imprimir paso a paso los comandos y validaciones que ejecutaría sin modificar tags ni contenedores reales.
- **`RF-03 (Sondas de Salud y Liveness Probes)`**:
  Tras levantar los contenedores, el pipeline debe verificar el estado `healthy` de los contenedores o responder a una sonda HTTP con 3 reintentos espaciados 5 segundos.
- **`RF-04 (Rollback Automático en < 2 Minutos)`**:
  Si la sonda de salud falla tras 3 intentos, el pipeline debe revertir automáticamente el despliegue al tag/commit anterior de forma desatendida.
- **`RF-05 (Paridad Dual PowerShell / Bash)`**:
  Tanto `git-flow-helper.ps1` como `git-flow-helper.sh` deben soportar la misma interfaz y parámetros.

### 2.2. Criterios de Aceptación Verificables (Given / When / Then)

- [ ] **`CA-01`**: Dado `git-flow-helper.ps1 -Action promote -Tag v1.0.0-sandbox -Deploy -DryRun`, cuando se ejecuta, muestra la secuencia completa de despliegue simulado retornando código 0.
- [ ] **`CA-02`**: Dado un fallo en la sonda de salud simulada, cuando se ejecuta el despliegue, el pipeline activa el rollback automático al estado previo y finaliza con código de error.
- [ ] **`CA-03`**: Cobertura de tests unitarios $\ge 80\%$ y SonarQube Rating A (0 violaciones, Cognitive Complexity $\le 15$).

---

## 3. Matriz de Impacto en Arquitectura Home-Lab

| Dimensión Arquitectónica | ¿Impactado? (`SÍ/NO`) | Nivel de Riesgo (`Bajo/Medio/Alto`) | Detalle de la Afectación y Mitigación |
| :--- | :---: | :---: | :--- |
| **Paridad `home-lab-sdk`** | `NO` | - | Sin impacto en SDKs. |
| **Persistencia PostgreSQL LTS** | `NO` | - | No altera esquemas ni datos. |
| **Ingress Único (`cluster-lb`)** | `SÍ` | `Bajo` | Despliega contenedores bajo la red Traefik validando sus probes. |
| **Resolución Split-DNS** | `NO` | - | Sin impacto en DNS. |
| **Restricciones de Hardware** | `NO` | - | Control de despliegue secuencial sin sobrecargar CPU/RAM. |
| **Variables `.env` / Secretos** | `SÍ` | `Bajo` | Se garantiza que ningún secreto se exponga en logs de despliegue. |

---

## 4. Garantía Estricta de Retrocompatibilidad (Zero-Breaking Policy)

- **¿Introduce Breaking Changes?**: `[x] NO (100% Retrocompatible)`
- **Estrategia Aditiva**:
  Los nuevos parámetros `-Deploy`, `-Environment` y `-DryRun` son estrictamente opcionales. La acción `promote` clásica sin `-Deploy` mantiene su comportamiento habitual de solo etiquetar y subir a GitHub.

---

## 5. Compuertas SRE de Rendimiento y Seguridad

- **Tiempo de Rollback**: $< 120\text{ segundos}$ garantizado mediante reversión de tag / compose recreate.
- **Seguridad**: Cero exposición de secretos o credenciales en salidas estándar o de error.
