#!/usr/bin/env python3
"""
SBWAA Automation — Dispatcher principal
Invocado pelo Task Scheduler via launcher.vbs

Uso direto:
    python scripts/automation/main.py --slot morning
    python scripts/automation/main.py --slot eod
    python scripts/automation/main.py --slot weekend
    python scripts/automation/main.py --slot morning --dry-run   (lista tasks sem executar)
"""

import sys
import logging
import argparse
from datetime import date, datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
LOGS_DIR = PROJECT_ROOT / "logs"
LOGS_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    handlers=[
        logging.FileHandler(str(LOGS_DIR / "automation.log"), encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s — %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

log = logging.getLogger("sbwaa.automation")

sys.path.insert(0, str(PROJECT_ROOT))

from scripts.automation.tasks import (
    MORNING_TASKS, EOD_TASKS, WEEKEND_TASKS, MONTHLY_TASKS, ALERTA_TASKS,
)
from scripts.automation.runner import run_task
from scripts.automation.notifier import notify


# Feriados nacionais fixos (mês, dia)
FERIADOS_BR = {
    (1, 1), (4, 21), (5, 1), (9, 7), (10, 12),
    (11, 2), (11, 15), (11, 20), (12, 25),
}


def eh_dia_util(d: date) -> bool:
    if d.weekday() >= 5:
        return False
    return (d.month, d.day) not in FERIADOS_BR


def eh_primeiro_fds_do_mes(d: date) -> bool:
    """Primeiro sábado ou domingo do mês (dia 1–7 + fim de semana)."""
    return d.day <= 7 and d.weekday() >= 5


def selecionar_tasks(slot: str, hoje: date | None = None) -> list:
    hoje = hoje or date.today()

    if slot == "morning":
        if not eh_dia_util(hoje):
            log.info(f"{hoje} não é dia útil — slot morning ignorado.")
            return []
        return [t for t in MORNING_TASKS if t.enabled]

    elif slot == "eod":
        if not eh_dia_util(hoje):
            log.info(f"{hoje} não é dia útil — slot EOD ignorado.")
            return []
        return [t for t in EOD_TASKS if t.enabled]

    elif slot == "weekend":
        tasks = []
        # Domingo → relatório semanal
        if hoje.weekday() == 6:
            tasks += [t for t in WEEKEND_TASKS if t.enabled]
        # Primeiro fim de semana do mês → relatório mensal
        if eh_primeiro_fds_do_mes(hoje):
            tasks += [t for t in MONTHLY_TASKS if t.enabled]
        if not tasks:
            log.info(f"{hoje} — slot weekend sem tasks (não é domingo nem 1° fds).")
        return tasks

    elif slot == "alerta":
        if not eh_dia_util(hoje):
            log.info(f"{hoje} não é dia útil — slot alerta ignorado.")
            return []
        hora = datetime.now().hour
        if not (10 <= hora <= 17):
            log.info(f"Slot alerta: fora do horário de pregão ({hora}h). Ignorando.")
            return []
        return [t for t in ALERTA_TASKS if t.enabled]

    log.error(f"Slot desconhecido: '{slot}'")
    return []


def executar_slot(slot: str, dry_run: bool = False):
    agora = datetime.now().strftime("%Y-%m-%d %H:%M")

    log.info(f"{'═'*60}")
    log.info(f"SBWAA AUTOMATION | slot={slot} | {agora}{' | DRY-RUN' if dry_run else ''}")
    log.info(f"{'═'*60}")

    tasks = selecionar_tasks(slot)

    if not tasks:
        log.info("Nenhuma task para executar. Encerrando.")
        return

    if dry_run:
        log.info(f"Tasks que seriam executadas ({len(tasks)}):")
        for t in tasks:
            log.info(f"  [{t.task_type:6}] {t.name:<30} timeout={t.timeout}s")
        return

    resultados: list[tuple[str, bool]] = []

    for task in tasks:
        log.info(f"── {task.description}")
        ok, _ = run_task(task)
        resultados.append((task.name, ok))

    ok_count = sum(1 for _, ok in resultados if ok)
    total = len(resultados)
    falhas = [n for n, ok in resultados if not ok]

    log.info(f"{'═'*60}")
    log.info(f"Concluído: {ok_count}/{total} OK | slot={slot} | {agora}")

    if falhas:
        log.warning(f"Falhas: {', '.join(falhas)}")
        notify(
            "SBWAA — Automation",
            f"Slot {slot}: {ok_count}/{total} OK\nFalhas: {', '.join(falhas)}",
        )
    else:
        notify(
            "SBWAA — Automation",
            f"Slot {slot} concluído: {ok_count}/{total} tarefas OK",
        )


def main():
    parser = argparse.ArgumentParser(
        description="SBWAA Automation Dispatcher",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Slots disponíveis:
  morning  — pré-mercado (seg-sex 07:45)
  eod      — fechamento  (seg-sex 17:00)
  weekend  — relatórios  (sáb-dom 08:00)

Exemplos:
  python main.py --slot morning
  python main.py --slot morning --dry-run
        """,
    )
    parser.add_argument(
        "--slot",
        choices=["morning", "eod", "weekend"],
        required=True,
        help="Qual slot executar",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Lista tasks sem executar",
    )
    args = parser.parse_args()
    executar_slot(args.slot, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
