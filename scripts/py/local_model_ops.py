#!/usr/bin/env python3
"""
Bench y check DOC-16 del modelo local (local_model_ops.py).

Separado de local_model.py para mantener los ficheros por debajo de 400 líneas.
Lo usan ``local_model.py bench`` y los dos doctores (DOC-16). Solo stdlib.
Se espeja en aagy-ecc/scripts/py/ mediante sync_aagy_ecc.py.
"""

from __future__ import annotations

import json
from pathlib import Path
import sys
import time
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

from local_model import (  # noqa: E402
    DEFAULT_NUM_CTX, DEFAULT_TASKS, ENCODING, K_CONTENT, MODE_AUTO, MODE_OFF, MODE_ONLY, SERVER_NAME,
    Settings, _model_present, _repo_root, build_instruction, chat_raw, get_status, load_settings,
    tokens_per_second,
)

# --------------------------------------------------------------------------- bench (RF-15)

BENCH_FILE = Path(".governance") / "local-model-bench.json"
BENCH_EXT_LABELS = {".py": "python", ".md": "markdown", ".json": "json", ".sh": "shell", ".ps1": "powershell"}
BENCH_SAMPLE = 12


def _bench_files(root: Path) -> List[Tuple[Path, str]]:
    found: List[Tuple[Path, str]] = []
    for path in sorted(root.rglob("*")):
        label = BENCH_EXT_LABELS.get(path.suffix)
        parts = set(path.relative_to(root).parts)
        if label and path.is_file() and not parts & {".git", "node_modules", "__pycache__"}:
            found.append((path, label))
        if len(found) >= BENCH_SAMPLE:
            break
    return found


def bench_model(settings: Settings, model: str, root: Path) -> Dict[str, Any]:
    """Clasifica ficheros del repo por lenguaje sin ver la extensión: precisión y tokens/s."""
    files = _bench_files(root)
    labels = sorted(set(BENCH_EXT_LABELS.values()))
    instruction = build_instruction(DEFAULT_TASKS["classify"], {"labels": labels})
    hits = 0
    speeds: List[float] = []
    for path, label in files:
        text = path.read_text(encoding=ENCODING, errors="replace")[:2000]
        data = chat_raw(settings, instruction, text, False, model)
        answer = str(data.get("message", {}).get(K_CONTENT, "")).strip().lower()
        hits += 1 if label in answer else 0
        speeds.append(tokens_per_second(data))
    return {
        "model": model,
        "samples": len(files),
        "accuracy": round(hits / len(files), 2) if files else 0.0,
        "tokens_per_s": round(sum(speeds) / len(speeds), 1) if speeds else 0.0,
        "measured_at": time.strftime("%Y-%m-%d"),
    }


def bench_path(settings: Settings, root: Optional[Path] = None) -> Path:
    base = settings.project_file.parent.parent if settings.project_file else _repo_root(root)
    return base / BENCH_FILE


def save_bench(results: Sequence[Mapping[str, Any]], path: Path) -> None:
    data: Dict[str, Any] = {}
    if path.is_file():
        data = json.loads(path.read_text(encoding=ENCODING) or "{}")
    models = data.setdefault("models", {})
    for row in results:
        models[str(row["model"])] = dict(row)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding=ENCODING)


def measured_models(settings: Settings, root: Optional[Path] = None) -> List[str]:
    path = bench_path(settings, root)
    if not path.is_file():
        return []
    try:
        return sorted(json.loads(path.read_text(encoding=ENCODING)).get("models", {}))
    except ValueError:
        return []


# --------------------------------------------------------------------------- doctor (DOC-16, RF-13)

STATUS_PASS = "PASS"
STATUS_WARN = "WARN"
STATUS_FAIL = "FAIL"
STATUS_SKIP = "SKIP"


def doctor_findings(start: Optional[Path] = None, registered: Optional[bool] = None,
                    environ: Optional[Mapping[str, str]] = None) -> Tuple[str, str, List[str], List[str]]:
    """(estado, mensaje, evidencias, modelos que faltan) para DOC-16 en los dos doctores."""
    settings = load_settings(start, environ)
    status = get_status(settings)
    evidence = [f"Modo: {settings.mode} (efectivo: {status.effective})", f"Ollama: {settings.url}"]
    if settings.mode == MODE_OFF:
        return STATUS_SKIP, "Modelo local apagado (local_model.mode=off).", evidence, []
    if not status.reachable:
        if settings.mode == MODE_AUTO:
            return STATUS_SKIP, "Sin Ollama: el modo auto se queda en off.", evidence, []
        return STATUS_FAIL, f"Modo {settings.mode} pero Ollama no responde en {settings.url}.", evidence, []
    wanted = [m for m in (settings.tool_model, settings.only_model if settings.mode == MODE_ONLY else "") if m]
    missing = [m for m in wanted if not _model_present(m, status.models)]
    problems: List[str] = []
    if not settings.tool_model:
        problems.append("Falta local_model.tool (modelo de herramienta) en la capa de entorno o del proyecto.")
    if missing:
        problems.append(f"Modelos sin descargar: {', '.join(missing)}.")
    if registered is False:
        problems.append(f"El servidor MCP {SERVER_NAME} no está registrado en el harness.")
    unmeasured = [m for m in wanted if m not in measured_models(settings, start) and m not in missing]
    if unmeasured:
        problems.append(f"Modelos sin medir: {', '.join(unmeasured)} (local_model.py bench).")
    if settings.num_ctx < DEFAULT_NUM_CTX:
        problems.append(f"num_ctx={settings.num_ctx} es menor de {DEFAULT_NUM_CTX}.")
    evidence.append(f"Modelos en Ollama: {', '.join(status.models[:8]) or 'ninguno'}")
    if problems:
        return STATUS_WARN, problems[0], problems[1:] + evidence, missing
    return STATUS_PASS, f"Modelo local listo ({settings.tool_model}).", evidence, []


def pull_argv(model: str) -> List[str]:
    return ["ollama", "pull", model]
