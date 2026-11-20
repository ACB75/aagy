"""
Tests unitarios para el monitor de telemetría de tokens en sesión (session_token_monitor.py).
"""
import json
from pathlib import Path
import subprocess
import sys


REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
MONITOR_SCRIPT = REPO_ROOT / "scripts" / "py" / "session_token_monitor.py"


def test_analyze_empty_or_missing_transcript(tmp_path):
    sys.path.insert(0, str(REPO_ROOT / "scripts" / "py"))
    import session_token_monitor

    # Archivo inexistente
    missing_file = tmp_path / "non_existent.jsonl"
    res_missing = session_token_monitor.analyze_transcript(missing_file)
    assert res_missing.steps == 0
    assert res_missing.estimated_tokens == 0
    assert not res_missing.compact_recommended

    # Archivo vacío
    empty_file = tmp_path / "empty.jsonl"
    empty_file.write_text("", encoding="utf-8")
    res_empty = session_token_monitor.analyze_transcript(empty_file)
    assert res_empty.steps == 0
    assert res_empty.estimated_tokens == 0
    assert not res_empty.compact_recommended


def test_analyze_synthetic_transcript_under_and_over_threshold(tmp_path):
    sys.path.insert(0, str(REPO_ROOT / "scripts" / "py"))
    import session_token_monitor

    # Transcript pequeño (<45.000 tokens)
    small_file = tmp_path / "small_transcript.jsonl"
    lines = [
        json.dumps({"step_index": 1, "type": "USER_INPUT", "content": "Hola mundo"}),
        json.dumps({"step_index": 2, "type": "PLANNER_RESPONSE", "content": "Respuesta breve", "thinking": "pensando"}),
    ]
    small_file.write_text("\n".join(lines), encoding="utf-8")

    res_small = session_token_monitor.analyze_transcript(small_file, threshold=45000)
    assert res_small.steps == 2
    assert res_small.estimated_tokens > 0
    assert res_small.estimated_tokens < 1000
    assert not res_small.compact_recommended

    # Transcript grande (>45.000 tokens)
    # 45.000 tokens * 3.8 = 171.000 chars
    large_file = tmp_path / "large_transcript.jsonl"
    heavy_content = "x" * 200000
    large_lines = [
        json.dumps({"step_index": 1, "type": "PLANNER_RESPONSE", "content": heavy_content}),
    ]
    large_file.write_text("\n".join(large_lines), encoding="utf-8")

    res_large = session_token_monitor.analyze_transcript(large_file, threshold=45000)
    assert res_large.steps == 1
    assert res_large.estimated_tokens > 45000
    assert res_large.compact_recommended


def test_cli_json_and_alert_modes(tmp_path):
    target_file = tmp_path / "cli_transcript.jsonl"
    heavy_content = "y" * 190000
    target_file.write_text(json.dumps({"content": heavy_content}), encoding="utf-8")

    # Ejecutar en modo JSON
    proc_json = subprocess.run(
        [sys.executable, str(MONITOR_SCRIPT), "--transcript", str(target_file), "--json"],
        capture_output=True,
        text=True,
    )
    assert proc_json.returncode == 0
    payload = json.loads(proc_json.stdout)
    assert payload["steps"] == 1
    assert payload["estimated_tokens"] > 45000
    assert payload["compact_recommended"] is True

    # Ejecutar en modo alert-only (debe salir con código 1 al superar umbral)
    proc_alert = subprocess.run(
        [sys.executable, str(MONITOR_SCRIPT), "--transcript", str(target_file), "--alert-only"],
        capture_output=True,
        text=True,
    )
    assert proc_alert.returncode == 1
