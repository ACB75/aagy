#!/usr/bin/env python3
"""
Modelos inmutables, sanitización y renderizado Markdown para live_status.py.

Mantiene las estructuras de telemetría de sesiones (Antigravity / Claude Code),
catálogo vivo (aagy <-> aagy-ecc) y trazabilidad arquitectónica Two-Tier
(ADR-0001 -> ADR-0004) separadas del I/O y dentro del umbral SonarQube A.

Solo stdlib. Se espeja en aagy-ecc/scripts/py/ mediante sync_aagy_ecc.py.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
import re
from typing import Any, Dict, Iterable, Sequence, Tuple

ORIGIN_SESSION_ID = "cc240ae0-bb1b-4e71-8287-891d6f5ee2a0"

MARKER_CATALOG_START = "<!-- aagy-live-catalog:start -->"
MARKER_CATALOG_END = "<!-- aagy-live-catalog:end -->"
MARKER_TELEMETRY_START = "<!-- aagy-live-telemetry:start -->"
MARKER_TELEMETRY_END = "<!-- aagy-live-telemetry:end -->"
MARKER_TRACE_START = "<!-- aagy-live-traceability:start -->"
MARKER_TRACE_END = "<!-- aagy-live-traceability:end -->"

WORKSPACE_AAGY = "aagy"
WORKSPACE_EXTERNAL = "external"
REDACTED_TOKEN = "[redacted]"
STATUS_COMPACT = "COMPACT"
STATUS_OK = "OK"
NONE_LABEL = "ninguno"

_VERSION_LINE_RE = re.compile(r"^(>\s*\*\*Versión\*\*:\s*`[^`]+`\s*\(`/doc` v2\))(?:\s*\|\s*\*\*Fecha de Auditoría\*\*:\s*[^\n]+)?$", re.MULTILINE)
_SECTION_HEADING_FMT = "## {heading}"


@dataclass(frozen=True)
class CatalogStats:
    agy_skills: int
    agy_agents: int
    rules_bytes: int
    rules_tokens: int
    ecc_skills: int
    ecc_agents: int
    ecc_commands: int
    ecc_packs: Tuple[str, ...]
    agy_hook_events: Tuple[str, ...]
    ecc_hook_events: Tuple[str, ...]


@dataclass(frozen=True)
class BacklogStats:
    open_tasks: int
    active_claims: int
    done_tasks: int


@dataclass(frozen=True)
class AgySessionRow:
    session_id: str
    updated_at: str
    steps: int
    estimated_tokens: int
    compact_recommended: bool


@dataclass(frozen=True)
class AgyTelemetry:
    total_sessions: int
    total_steps: int
    total_estimated_tokens: int
    over_threshold: int
    threshold: int
    recent: Tuple[AgySessionRow, ...]


@dataclass(frozen=True)
class ClaudeSessionRow:
    session_id: str
    workspace: str
    updated_at: str
    model: str
    context_tokens: int
    output_tokens: int


@dataclass(frozen=True)
class ClaudeTelemetry:
    total_sessions: int
    total_context_tokens: int
    total_output_tokens: int
    recent: Tuple[ClaudeSessionRow, ...]


@dataclass(frozen=True)
class LiveSnapshot:
    generated_at: str
    version: str
    ecc_version: str
    branch: str
    head: str
    worktree_active: bool
    catalog: CatalogStats
    backlog: BacklogStats
    antigravity: AgyTelemetry
    claude: ClaudeTelemetry

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def _norm(text: str) -> str:
    return text.lower().replace("\\", "/")


def sanitize_workspace_label(folder_name: str, forbidden_terms: Sequence[str]) -> str:
    """Normaliza el nombre de carpeta de Claude Projects sin filtrar proyectos consumidores."""
    lowered = _norm(folder_name)
    for term in forbidden_terms:
        clean = _norm(term).strip()
        if clean and clean in lowered:
            return WORKSPACE_EXTERNAL
    if lowered.endswith(("-projects-aagy", "-aagy", "-aagy-ecc")) or lowered == WORKSPACE_AAGY:
        return WORKSPACE_AAGY
    return WORKSPACE_EXTERNAL


def sanitize_text(text: str, forbidden_terms: Iterable[str]) -> str:
    """Enmascara cualquier término declarado en consumer_refs antes de escribir en el repo."""
    result = text
    for term in forbidden_terms:
        clean = str(term).strip()
        if not clean:
            continue
        variants = {clean, clean.replace("\\", "/"), clean.replace("/", "\\")}
        for variant in variants:
            result = re.sub(re.escape(variant), REDACTED_TOKEN, result, flags=re.IGNORECASE)
    return result


def render_catalog_block(snap: LiveSnapshot) -> str:
    """Bloque vivo del catálogo aagy <-> aagy-ecc calculado desde disco."""
    cat = snap.catalog
    packs_label = ", ".join(f"`{p}`" for p in cat.ecc_packs) if cat.ecc_packs else NONE_LABEL
    agy_hooks = ", ".join(f"`{e}`" for e in cat.agy_hook_events) or NONE_LABEL
    ecc_hooks = ", ".join(f"`{e}`" for e in cat.ecc_hook_events) or NONE_LABEL
    lines = [
        MARKER_CATALOG_START,
        f"> Última sincronización de catálogo: `{snap.generated_at}` | `aagy` `{snap.version}` ↔ `aagy-ecc` `{snap.ecc_version}`",
        "",
        "| Pieza | `aagy` (Antigravity) | `aagy-ecc` (Claude Code) |",
        "| :--- | :--- | :--- |",
        f"| Skills | {cat.agy_skills} en `skills/` | {cat.ecc_skills} en núcleo (`generic`); packs opcionales: {packs_label} |",
        f"| Subagentes | {cat.agy_agents} en `agents/` | {cat.ecc_agents} en núcleo (`generic`); resto distribuido en `packs/` |",
        "| Comandos slash | Equivalentes por skill (sin `commands/`) | " + f"{cat.ecc_commands} en `aagy-ecc/commands/` |",
        f"| Reglas Tier 1 | `rules/AGENTS.md` ({cat.rules_bytes:,} bytes, ~{cat.rules_tokens:,} tokens) | Inyección condensada en `SessionStart` (≤ 2 KB) |",
        f"| Hooks activos | {agy_hooks} | {ecc_hooks} |",
        MARKER_CATALOG_END,
    ]
    return "\n".join(lines)


def render_traceability_block() -> str:
    """Tabla de trazabilidad arquitectónica desde Two-Tier (ADR-0001) hasta ADR-0006 y v5.2.0."""
    lines = [
        MARKER_TRACE_START,
        f"Origen documentado en la sesión `{ORIGIN_SESSION_ID}` (2026-10-24: `affaan-m/ecc` → `ecc-agy` → `aagy`):",
        "",
        "| Hito / ADR | Fecha | Evolución arquitectónica desde Two-Tier |",
        "| :--- | :---: | :--- |",
        "| [**ADR-0001**](02-adr/ADR_aagy_0001_two_tier_global_plugin_and_project_scaffolding.md) | 2026-10-24 | **Two-Tier original**: Nivel 1 plugin global (`rules/AGENTS.md` + core) y Nivel 2 scaffolding `.agents/` por proyecto. |",
        "| [**ADR-0002**](02-adr/ADR_aagy_0002_multi_harness_architecture_and_agent_runtime_design.md) | 2026-11-01 | **Multi-Harness**: distribución simétrica `aagy` (Antigravity) ↔ `aagy-ecc` (Claude Code) con espejo único. |",
        "| [**ADR-0003**](02-adr/ADR_aagy_0003_doc_structure_v2_and_manual_parity.md) | 2026-11-20 | **Gobernanza `/doc` v2**: `.governance/docs-map.json`, esqueleto común y paridad manual CLI 1-a-1. |",
        "| [**ADR-0004**](02-adr/ADR_aagy_0004_stack_profiles_declared_by_consumer_repo.md) | 2026-11-21 | **Supera Nivel 2 de ADR-0001**: perfiles de stack declarados por el repo consumidor; plugin 100 % agnóstico. |",
        "| [**ADR-0005**](02-adr/ADR_aagy_0005_shared_backlog_multi_harness.md) | 2026-11-21 | **Backlog compartido**: `TODO.md` + estado en `.git/aagy-backlog/` y relevo entre agentes. |",
        "| [**ADR-0006**](02-adr/ADR_aagy_0006_agent_worktrees.md) | 2026-11-22 | **Worktrees fijos**: `<repo>-aagy` y `<repo>-aagy-ecc` con guarda PreToolUse y reciclado post-merge. |",
        "| `v5.0.0`–`v5.2.0` | 2026-11-25 | Motor único de hooks, LLM local (`local_model.py`), telemetría [`session_token_monitor`](04-operations/runbooks/MANUAL_session_token_telemetry.md) y [`aagy_ui`](04-operations/runbooks/MANUAL_ui.md). |",
        MARKER_TRACE_END,
    ]
    return "\n".join(lines)


def _format_agy_rows(rows: Sequence[AgySessionRow]) -> Tuple[str, ...]:
    if not rows:
        return ("| _(sin sesiones)_ | - | 0 | 0 | - |",)
    out = []
    for row in rows:
        state = f"⚠️ `{STATUS_COMPACT}`" if row.compact_recommended else f"✅ `{STATUS_OK}`"
        out.append(f"| `{row.session_id}` | `{row.updated_at}` | {row.steps} | ~{row.estimated_tokens:,} | {state} |")
    return tuple(out)


def _format_claude_rows(rows: Sequence[ClaudeSessionRow]) -> Tuple[str, ...]:
    if not rows:
        return ("| _(sin sesiones)_ | - | - | - | 0 | 0 |",)
    out = []
    for row in rows:
        out.append(
            f"| `{row.session_id}` | `{row.workspace}` | `{row.updated_at}` | `{row.model}` | {row.context_tokens:,} | {row.output_tokens:,} |"
        )
    return tuple(out)


def render_telemetry_block(snap: LiveSnapshot) -> str:
    """Bloque vivo de telemetría de sesiones para doc/STATUS.md y .agents/LIVE_TELEMETRY.md."""
    agy = snap.antigravity
    claude = snap.claude
    lines = [
        MARKER_TELEMETRY_START,
        f"> Actualizado: `{snap.generated_at}` | Rama: `{snap.branch}` (`{snap.head}`) | Worktrees activos: `{'sí' if snap.worktree_active else 'no'}`",
        "",
        "### Antigravity (`session_token_monitor` / `aagy_ui usage --harness agy`)",
        "",
        f"- **Sesiones en `~/.gemini/antigravity/brain/`**: `{agy.total_sessions}` ({agy.total_steps:,} pasos, ~{agy.total_estimated_tokens:,} tokens estimados).",
        f"- **Sobre umbral `/compact` (`{agy.threshold:,}` tokens)**: `{agy.over_threshold}` sesión(es).",
        "",
        "| Sesión (`brain/<id>`) | Última actividad | Pasos | Tokens (est.) | Estado |",
        "| :--- | :---: | :---: | :---: | :---: |",
        *_format_agy_rows(agy.recent),
        "",
        "### Claude Code (`~/.claude/projects/` / `aagy_statusline`)",
        "",
        f"- **Sesiones detectadas**: `{claude.total_sessions}` (contexto último turno acumulado: {claude.total_context_tokens:,} tokens; salida: {claude.total_output_tokens:,}).",
        "",
        "| Sesión (`sessionId`) | Entorno | Última actividad | Modelo | Contexto | Salida |",
        "| :--- | :---: | :---: | :--- | :---: | :---: |",
        *_format_claude_rows(claude.recent),
        "",
        "Los hooks `SessionStart` y `Stop` refrescan automáticamente `.agents/LIVE_TELEMETRY.md` en el worktree del agente sin ensuciar git; ejecuta `python scripts/py/live_status.py sync` para volcar métricas en `doc/STATUS.md`.",
        MARKER_TELEMETRY_END,
    ]
    return "\n".join(lines)


def render_live_telemetry_page(snap: LiveSnapshot, forbidden_terms: Sequence[str] = ()) -> str:
    """Página autónoma .agents/LIVE_TELEMETRY.md generada por los hooks SessionStart / Stop."""
    lines = [
        "# Telemetría Viva y Memoria de Sesiones | `aagy`",
        "",
        f"> **Versión**: `{snap.version}` (`aagy-ecc` `{snap.ecc_version}`) | **Backlog activo**: {snap.backlog.open_tasks} abiertas, {snap.backlog.active_claims} reclamadas",
        "",
        "## 1. Catálogo en vivo (`aagy` ↔ `aagy-ecc`)",
        "",
        render_catalog_block(snap),
        "",
        "## 2. Telemetría de sesiones y memoria",
        "",
        render_telemetry_block(snap),
        "",
        "## 3. Trazabilidad Two-Tier (`ADR-0001` → `ADR-0004`)",
        "",
        f"- Sesión origen: `{ORIGIN_SESSION_ID}` (2026-10-24).",
        "- Evolución: `ADR-0001` (Two-Tier) → `ADR-0002` (Multi-Harness) → `ADR-0003` (`/doc` v2) → `ADR-0004` (perfiles declarados por consumidor) → `ADR-0005` (backlog compartido) → `ADR-0006` (worktrees por agente).",
        "- Fuente de estado versionada: `doc/STATUS.md`.",
        "",
    ]
    return sanitize_text("\n".join(lines), forbidden_terms)


def _replace_or_insert_block(text: str, start_marker: str, end_marker: str, block: str, heading: str) -> str:
    pattern = re.compile(re.escape(start_marker) + r".*?" + re.escape(end_marker), re.DOTALL)
    if pattern.search(text):
        return pattern.sub(lambda _m: block, text, count=1)

    heading_re = re.compile(rf"^##\s+\d*\.?\s*{re.escape(heading)}\b[^\n]*$", re.MULTILINE)
    match = heading_re.search(text)
    if match:
        next_h2 = re.search(r"^##\s+", text[match.end():], re.MULTILINE)
        end_idx = match.end() + next_h2.start() if next_h2 else len(text)
        prefix = text[:match.end()].rstrip()
        suffix = text[end_idx:].lstrip("\n")
        return f"{prefix}\n\n{block}\n\n{suffix}" if suffix else f"{prefix}\n\n{block}\n"

    section = f"{_SECTION_HEADING_FMT.format(heading=heading)}\n\n{block}"
    backlog_match = re.search(r"^(?:---\n+)?##\s+\d+\.\s+Backlog\b", text, re.MULTILINE)
    if backlog_match:
        before = text[:backlog_match.start()].rstrip()
        after = text[backlog_match.start():].lstrip("-\n")
        return f"{before}\n\n---\n\n{section}\n\n---\n\n{after}"

    return f"{text.rstrip()}\n\n---\n\n{section}\n"


def update_status_markdown(existing: str, snap: LiveSnapshot, forbidden_terms: Sequence[str] = ()) -> str:
    """Actualiza de forma idempotente doc/STATUS.md manteniendo sus secciones y enlaces válidos."""
    text = existing.strip() or "# Estado de Salud y Métricas Operacionales | AAGY / `aagy` Ecosystem\n"
    audit_date = snap.generated_at.split("T", 1)[0]
    header_line = f"> **Versión**: `{snap.version}` (`/doc` v2) | **Fecha de Auditoría**: {audit_date}"
    if _VERSION_LINE_RE.search(text):
        text = _VERSION_LINE_RE.sub(header_line, text, count=1)

    text = _replace_or_insert_block(text, MARKER_CATALOG_START, MARKER_CATALOG_END, render_catalog_block(snap), "3. Catálogo")
    text = _replace_or_insert_block(
        text, MARKER_TRACE_START, MARKER_TRACE_END, render_traceability_block(), "4. Trazabilidad Two-Tier (ADR-0001 -> ADR-0004)"
    )
    text = _replace_or_insert_block(
        text,
        MARKER_TELEMETRY_START,
        MARKER_TELEMETRY_END,
        render_telemetry_block(snap),
        "5. Telemetría y memoria de sesiones (Antigravity / Claude Code)",
    )
    backlog_heading = re.compile(r"^##\s+\d+\.\s+Backlog\b", re.MULTILINE)
    if backlog_heading.search(text):
        text = backlog_heading.sub("## 6. Backlog", text, count=1)
    else:
        text = text.rstrip() + (
            f"\n\n---\n\n## 6. Backlog\n\n[`doc/06-backlog/TODO.md`](06-backlog/TODO.md) ({snap.backlog.open_tasks} tareas abiertas). "
            "Historial en [`LOG.md`](LOG.md).\n"
        )
    return sanitize_text(text.rstrip() + "\n", forbidden_terms)
