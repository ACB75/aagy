# Manual: Un Worktree Fijo por Agente (`MANUAL_agent_worktrees.md`)

> **Decisión**: [ADR-0006](../../02-adr/ADR_aagy_0006_agent_worktrees.md) | **Motor**: [`agent_worktree.py`](../../../scripts/py/agent_worktree.py)
> **Claude Code**: `/aagy-worktree` | **Antigravity**: skill `agent-worktrees`

---

## 1. Disposición

| Carpeta | Quién | Estado en reposo |
| :--- | :--- | :--- |
| `<padre>\app` | Master | `main` |
| `<padre>\app-aagy` | Antigravity | desacoplado en `origin/main` |
| `<padre>\app-aagy-ecc` | Claude Code | desacoplado en `origin/main` |

Lo mismo para `aagy` (`aagy-aagy`, `aagy-aagy-ecc`) y cualquier repo. Los tres
checkouts son el mismo clon: comparten ramas, `git fetch` y el estado del backlog.

## 2. Puesta en marcha (una vez por repo)

```powershell
cd <padre>\app
pwsh -File scripts/ps1/agent-worktree.ps1 init
pwsh -File scripts/ps1/agent-worktree.ps1 status
```

Antes, cierra o entrega (`backlog.py handoff`) las sesiones de agente que estén
trabajando en el principal. Después abre `app-aagy` en Antigravity y
`app-aagy-ecc` en Claude Code.

## 3. Ciclo de una tarea

1. El agente hace `backlog.py claim <id>` en su worktree: se crea la rama `feat/<proyecto>/<id>` desde `origin/main`.
2. Trabaja y cierra con `python scripts/py/complete_task_pr.py` (abre la PR; la fusiona una persona).
3. Tras el merge, `agent_worktree.py recycle`:
   1. Comprueba con `gh` que la PR está `MERGED`.
   2. Comprueba que no hay trabajo sin guardar. Si lo hay, **se para y lo lista**.
   3. Limpia el worktree en sitio (`switch --detach origin/main`, `reset --hard`, `clean -ffdx`), o lo recrea si algún fichero está bloqueado.
   4. Borra la rama local y libera la entrada del backlog.
   5. Copia los `.env` del principal y regenera `node_modules` / `.venv`.
   6. Actualiza tu principal con `--ff-only` si está en `main` y limpio.

El reciclado se lanza solo al final de `complete_task_pr.py --merge`, en el siguiente
`claim`/`done` y, en Claude Code, al iniciar sesión. A mano:

```powershell
pwsh -File scripts/ps1/agent-worktree.ps1 recycle --agent claude
pwsh -File scripts/ps1/agent-worktree.ps1 recycle --agent agy --hard-recreate
```

| Código | Significado |
| :--- | :--- |
| `0` | Reciclado, o no había nada que hacer |
| `3` | Bloqueado: trabajo sin guardar |
| `4` | La PR no está fusionada |
| `5` | Falta `gh` |

## 4. Configuración por repo (opcional)

`.governance/agent-worktrees.json`:

```json
{
  "base": "main",
  "copy": [".env", ".env.*"],
  "copy_exclude": ["node_modules", ".venv", "venv"],
  "install": "auto",
  "install_timeout_s": 900,
  "extra_install": [{"cwd": "web", "argv": ["npm", "run", "codegen"]}]
}
```

- `install: "auto"` regenera solo lo que el principal tiene (`node_modules` con `npm ci`, `pnpm`, `yarn` o `bun` según el lockfile; `.venv` con `uv sync`, `poetry install` o `pip install -r requirements.txt`). Maven, Gradle y Go usan cachés globales y no hace falta regenerarlos.
- `install: "none"` no regenera nada; una lista `[{cwd, argv}]` sustituye la detección.

## 5. Guarda

Con el marcador `.git/aagy-worktrees.json` (lo crea `init`), los hooks PreToolUse deniegan:

- Escribir ficheros en el principal o en el worktree del otro agente.
- Comandos que modifican (git que no sea de lectura, `rm`, `>`, `Set-Content`…) con `cwd`, `cd` o `git -C` hacia esas carpetas.
- `git worktree add|remove|move` a mano y el worktree nativo de Claude Code (`EnterWorktree`, `claude --worktree`).

Leer sí está permitido, también con redirecciones inocuas (`2>&1`, `>$null`). Los worktrees que crea la propia app de Claude Code dentro de `<repo>/.claude/worktrees/` (sesiones de escritorio y Remote Control) son checkouts aislados y la guarda no los bloquea. Para desactivarla en un repo, borra el marcador.

## 6. Relevo

`backlog.py handoff` suelta la rama (`git switch --detach`) si el worktree está
limpio; el otro agente hace `claim` en el suyo y continúa la misma rama. Si hay
cambios sin commit, la nota de relevo lo indica y la rama sigue abierta en el
worktree original hasta que alguien haga commit.

## 7. Problemas

| Síntoma | Causa | Solución |
| :--- | :--- | :--- |
| `No se puede borrar ...` | IDE, terminal o servidor con la carpeta abierta | Ciérralo y repite `recycle --hard-recreate` |
| `HEAD desacoplado con commits ...` | Commits hechos sin rama | Crea una rama y empújala |
| El principal no se actualiza | Tienes cambios o estás en otra rama | `git pull` cuando quieras |
| `DOC-15 WARN` | Falta un worktree o quedan `<repo>.wt/` | `agent-worktree init` / `backlog.py done` |
