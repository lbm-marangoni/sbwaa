"""
SBWAA Automation — Executor de tarefas

Executa tasks do tipo "python" (subprocess direto) ou "claude" (claude -p não-interativo).
Retorna (sucesso: bool, output: str) para cada task.
"""

import logging
import os
import subprocess
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent

log = logging.getLogger("sbwaa.runner")

# Força UTF-8 em todos os subprocessos Python — evita UnicodeEncodeError no Windows (cp1252)
_ENV = os.environ.copy()
_ENV["PYTHONUTF8"] = "1"


def _run(cmd: list[str], timeout: int, name: str, cwd: str | None = None) -> tuple[bool, str]:
    start = time.time()
    cwd = cwd or str(PROJECT_ROOT)
    try:
        r = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=cwd,
            encoding="utf-8",
            errors="replace",
            env=_ENV,
        )
        duration = time.time() - start
        if r.returncode == 0:
            log.info(f"[OK] {name} ({duration:.1f}s)")
            return True, r.stdout
        log.warning(f"[FALHOU] {name} — exit {r.returncode} ({duration:.1f}s)\n{r.stderr[:500]}")
        return False, r.stderr
    except subprocess.TimeoutExpired:
        log.error(f"[TIMEOUT] {name} — limite de {timeout}s atingido")
        return False, f"Timeout após {timeout}s"
    except FileNotFoundError as e:
        log.error(f"[NOTFOUND] {name} — executável não encontrado: {e}")
        return False, str(e)
    except Exception as e:
        log.error(f"[EXCEÇÃO] {name}: {e}")
        return False, str(e)


def run_python(cmd: list[str], timeout: int, name: str) -> tuple[bool, str]:
    return _run(cmd, timeout, name)


def run_claude(prompt: str, timeout: int, name: str) -> tuple[bool, str]:
    """
    Executa um prompt/slash-command no Claude Code em modo não-interativo.
    --dangerously-skip-permissions é necessário para rodar sem confirmações manuais.
    """
    return _run(
        ["claude", "--dangerously-skip-permissions", "-p", prompt],
        timeout,
        name,
    )


def run_task(task) -> tuple[bool, str]:
    if not task.enabled:
        log.info(f"[SKIP] {task.name} — desativada")
        return True, "desativada"

    if task.task_type == "python":
        return run_python(task.command, task.timeout, task.name)
    elif task.task_type == "claude":
        return run_claude(task.command, task.timeout, task.name)
    else:
        log.error(f"[ERRO] Tipo desconhecido: {task.task_type}")
        return False, f"Tipo '{task.task_type}' não reconhecido"
