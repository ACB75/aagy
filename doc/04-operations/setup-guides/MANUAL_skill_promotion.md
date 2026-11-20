# Manual de Operación: Promoción On-Demand de Skills (Tier 2 a Tier 1)

> **Referencia de Gobernanza**: Arquitectura Modular Two-Tier y Presupuesto de Contexto  
> **Ámbito**: Ecosistema Antigravity (`AGY`), Plugin `aagy` y Repositorio Base  
> **Fecha de Publicación**: `2026-11-20`  

---

## 1. Arquitectura de Dos Niveles (Two-Tier Skills)

Para mantener una experiencia de desarrollo ágil con bajo consumo de tokens en reposo y a la vez disponer de un catálogo amplio de especialización técnica, el ecosistema adopta una estructura de dos niveles:

1. **Tier 1 (Always-On Global Plugin `~/.gemini/config/plugins/aagy/skills/`)**:
   - Aloja exclusivamente las 22 skills transversales esenciales (como `engineering-lifecycle`, `sre-reliability`, `verification-loop`, `tdd-workflow`).
   - Mantiene una huella ligera de ~945 tokens en reposo en la ventana del sistema.
2. **Tier 2 (Repositorio Base `skills/` en `ACB75/aagy`)**:
   - Alberga 171 skills hiper-especializadas (diagnóstico BGP, depuración de memoria, optimizaciones Postgres, devtools).
   - Coste de 0 tokens en reposo mientras permanezcan en el repositorio.

---

## 2. Promoción y Desactivación On-Demand

Cuando una tarea específica requiere una skill de Tier 2, esta puede promoverse temporalmente al plugin activo para la duración de la intervención y retirarse una vez completada.

### 2.1. Activar / Promover una Skill

En Windows 11 (`pwsh`):

```powershell
pwsh -File scripts/ps1/enable-skill.ps1 -Name network-bgp-diagnostics
```

En Linux o WSL (`bash` / `sh`):

```sh
./scripts/sh/enable-skill.sh network-bgp-diagnostics
```

### 2.2. Listar Skills Promovidas

```powershell
pwsh -File scripts/ps1/enable-skill.ps1 -List
```

### 2.3. Desactivar / Retirar una Skill

Una vez concluida la tarea y fusionada la PR:

```powershell
pwsh -File scripts/ps1/disable-skill.ps1 -Name network-bgp-diagnostics
```

---

## 3. Compuertas y Protecciones Automatizadas

El subsistema `skill_promotion.py` aplica los siguientes guardrails bloqueantes:

- **Límite de Frontmatter**: Exige que la descripción de la skill sea $\le 140$ caracteres (`MAX_SKILL_DESC_CHARS`). Si supera este umbral, la promoción es rechazada.
- **Protección de Skills Core**: Prohíbe terminantemente desactivar o sobrescribir las 22 skills nucleares de Tier 1.
- **Registro Transaccional**: Toda promoción se anota en `.active_promotions.json` dentro de la carpeta del plugin, permitiendo una limpieza determinista sin dejar residuos.

---

## 4. Métricas de Rendimiento y Rendimiento SRE

- **Tiempo de Promoción/Retirada**: $< 80\text{ ms}$ (copia directa y serialización JSON).
- **Higiene de Git**: `.active_promotions.json` se almacena exclusivamente en la carpeta local del plugin del usuario, manteniendo el árbol de trabajo de Git completamente limpio.
