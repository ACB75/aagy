#!/usr/bin/env python3
"""
Modo solo local (local_model_only.py): sesiones sin modelo en la nube.

- ``claude``: lanza Claude Code contra la API compatible con Anthropic de Ollama
  (``ANTHROPIC_BASE_URL=<url de Ollama>``, ``ANTHROPIC_AUTH_TOKEN=ollama``,
  ``ANTHROPIC_API_KEY=""``) con ``claude --model <local_model.only>``. Las
  variables solo valen para ese proceso: una sesión normal de ``claude`` nunca
  hereda el modo (REQ P-03). ``AAGY_LOCAL_MODEL=only`` hace que el SessionStart
  de aagy-ecc lo anuncie e inyecte las reglas reducidas.
- ``agy``: agente del SDK de Antigravity (``pip install google-antigravity``) con
  ``LocalOpenAIAgentConfig`` contra ``<url de Ollama>/v1``. El SDK es una
  dependencia blanda: si no está, se dice cómo instalarlo y no pasa nada más.

Uso::

    python local_model.py only --harness claude [-- <argumentos de claude>]
    python local_model.py only --harness agy

Se espeja en aagy-ecc/scripts/py/ mediante sync_aagy_ecc.py.
"""

from __future__ import annotations

import os
from pathlib import Path
import shutil
import subprocess
import sys
from typing import Dict, List, Mapping, Optional, Sequence

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

import local_model as lm  # noqa: E402

HARNESS_CLAUDE = "claude"
HARNESS_AGY = "agy"
MIN_ONLY_CTX = 32768
RECOMMENDED_ONLY_CTX = 65536
SDK_PACKAGE = "google-antigravity"
ONLY_BANNER = "[aagy-local] MODO SOLO LOCAL: no hay modelo en la nube en esta sesión."
REDUCED_RULES = (
    "Reglas mínimas (modo solo local): ramas <tipo>/<proyecto>/<nombre>; nunca escribas secretos; "
    "tests antes de dar algo por hecho; no hagas merge ni push sin que el usuario lo pida; "
    "si la tarea te supera, dilo y para."
)


def context_warning(environ: Mapping[str, str]) -> str:
    """Aviso si OLLAMA_CONTEXT_LENGTH es pequeño para un agente (Ollama recomienda 64k)."""
    raw = environ.get("OLLAMA_CONTEXT_LENGTH", "").strip()
    if not raw:
        return f"Comprueba que Ollama tiene al menos {RECOMMENDED_ONLY_CTX // 1024}k de contexto (OLLAMA_CONTEXT_LENGTH)."
    try:
        value = int(raw)
    except ValueError:
        return f"OLLAMA_CONTEXT_LENGTH={raw} no es un número."
    if value < MIN_ONLY_CTX:
        return f"OLLAMA_CONTEXT_LENGTH={value} es menor de {MIN_ONLY_CTX}: el agente se quedará sin contexto."
    return ""


def claude_env(settings: lm.Settings, environ: Mapping[str, str]) -> Dict[str, str]:
    env = dict(environ)
    env.update({
        "ANTHROPIC_BASE_URL": settings.url,
        "ANTHROPIC_AUTH_TOKEN": "ollama",
        "ANTHROPIC_API_KEY": "",
        lm.ALIASES["mode"]: lm.MODE_ONLY,
    })
    return env


def claude_argv(settings: lm.Settings, extra: Sequence[str], claude: str = "claude") -> List[str]:
    return [claude, "--model", settings.only_model, *extra]


def _preflight(settings: lm.Settings) -> Optional[str]:
    if not settings.only_model:
        return "Falta local_model.only (modelo del modo solo local) en la capa de entorno o del proyecto."
    status = lm.get_status(settings)
    if not status.reachable:
        return status.reason
    if settings.only_model not in status.models and f"{settings.only_model}:latest" not in status.models:
        return f"El modelo {settings.only_model} no está descargado (ollama pull {settings.only_model})."
    return None


def run_claude(settings: lm.Settings, extra: Sequence[str], environ: Optional[Mapping[str, str]] = None) -> int:
    env_in = dict(os.environ if environ is None else environ)
    problem = _preflight(settings)
    if problem:
        print(f"[aagy-local] {problem}", file=sys.stderr)
        return 1
    claude = shutil.which("claude")
    if not claude:
        print("[aagy-local] No encuentro el ejecutable claude en el PATH.", file=sys.stderr)
        return 1
    print(ONLY_BANNER)
    warning = context_warning(env_in)
    if warning:
        print(f"  {warning}")
    return subprocess.call(claude_argv(settings, extra, claude), env=claude_env(settings, env_in))  # noqa: S603


def _agy_config(sdk: object, settings: lm.Settings) -> object:
    config_cls = getattr(sdk, "LocalOpenAIAgentConfig")
    base = {"model": settings.only_model, "base_url": f"{settings.url}/v1"}
    try:
        return config_cls(**base, system_instructions=REDUCED_RULES)
    except TypeError:  # versiones del SDK sin system_instructions en esta clase
        return config_cls(**base)


async def _agy_loop(sdk: object, settings: lm.Settings) -> None:
    agent_cls = getattr(sdk, "Agent")
    async with agent_cls(_agy_config(sdk, settings)) as agent:
        while True:
            try:
                prompt = input("agy-local> ").strip()
            except EOFError:
                return
            if prompt in ("", "exit", "salir"):
                return
            response = await agent.chat(prompt)
            async for token in response:
                print(token, end="", flush=True)
            print()


def run_agy(settings: lm.Settings) -> int:
    try:
        import google.antigravity as sdk  # noqa: PLC0415 - dependencia blanda
    except ImportError:
        print(f"[aagy-local] El modo solo local de Antigravity necesita el SDK: pip install {SDK_PACKAGE}", file=sys.stderr)
        return 1
    problem = _preflight(settings)
    if problem:
        print(f"[aagy-local] {problem}", file=sys.stderr)
        return 1
    import asyncio  # noqa: PLC0415

    print(ONLY_BANNER)
    print("  Escribe 'salir' para terminar.")
    asyncio.run(_agy_loop(sdk, settings))
    return 0


def sdk_available() -> bool:
    try:
        import importlib.util  # noqa: PLC0415

        return importlib.util.find_spec("google.antigravity") is not None
    except (ImportError, ValueError):
        return False
