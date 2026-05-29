"""
SBWAA Automation — Instala/remove tarefas no Windows Task Scheduler

Uso:
    python setup_scheduler.py --instalar      # instala as 3 tarefas + configura wake
    python setup_scheduler.py --remover       # remove todas
    python setup_scheduler.py --status        # mostra status de cada tarefa
    python setup_scheduler.py --instalar --sem-wake   # sem wake-to-run
    python setup_scheduler.py --testar morning        # dispara agora (teste rápido)
"""

import sys
import subprocess
import argparse
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
LAUNCHER_VBS = Path(__file__).parent / "launcher.vbs"
LOGS_DIR = PROJECT_ROOT / "logs"

# Cada entrada: nome da tarefa, slot, expressão schtasks de agendamento
SCHEDULER_TASKS = [
    {
        "name":     "SBWAA_Morning",
        "slot":     "morning",
        "schedule": ["/SC", "WEEKLY", "/D", "MON,TUE,WED,THU,FRI", "/ST", "07:45"],
        "desc":     "SBWAA — Morning call pré-mercado (seg–sex 07:45)",
    },
    {
        "name":     "SBWAA_EOD",
        "slot":     "eod",
        "schedule": ["/SC", "WEEKLY", "/D", "MON,TUE,WED,THU,FRI", "/ST", "17:00"],
        "desc":     "SBWAA — Snapshot EOD (seg–sex 17:00)",
    },
    {
        "name":     "SBWAA_Weekend",
        "slot":     "weekend",
        "schedule": ["/SC", "WEEKLY", "/D", "SAT,SUN", "/ST", "08:00"],
        "desc":     "SBWAA — Relatórios fim de semana (sáb–dom 08:00)",
    },
    {
        "name":     "SBWAA_Alerta",
        "slot":     "alerta",
        "schedule": ["/SC", "MINUTE", "/MO", "60", "/ST", "10:00"],
        "desc":     "SBWAA — Monitor de preços intraday (seg–sex a cada 60min)",
    },
]


def _schtasks(*args: str) -> tuple[bool, str]:
    try:
        r = subprocess.run(
            ["schtasks"] + list(args),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        return r.returncode == 0, (r.stdout + r.stderr).strip()
    except FileNotFoundError:
        return False, "schtasks.exe não encontrado (requer Windows)"
    except Exception as e:
        return False, str(e)


def _powershell(script: str) -> bool:
    try:
        r = subprocess.run(
            ["powershell", "-NonInteractive", "-NoProfile", "-Command", script],
            capture_output=True,
            timeout=20,
        )
        return r.returncode == 0
    except Exception:
        return False


def _configurar_wake_e_missed(task_name: str):
    """Ativa WakeToRun e StartWhenAvailable via PowerShell."""
    script = f"""
$task = Get-ScheduledTask -TaskName '{task_name}' -ErrorAction SilentlyContinue
if ($null -ne $task) {{
    $s = $task.Settings
    $s.WakeToRun = $true
    $s.StartWhenAvailable = $true
    Set-ScheduledTask -TaskName '{task_name}' -Settings $s | Out-Null
}}
"""
    _powershell(script)


def instalar(wake: bool = True):
    print(f"\n{'═'*65}")
    print("  SBWAA — Instalar automação no Task Scheduler")
    print(f"  Launcher: {LAUNCHER_VBS}")
    print(f"{'═'*65}\n")

    for t in SCHEDULER_TASKS:
        action = f'wscript.exe "{LAUNCHER_VBS}" {t["slot"]}'

        ok, out = _schtasks(
            "/Create", "/F",
            "/TN", t["name"],
            "/TR", action,
            *t["schedule"],
        )
        status = "✅" if ok else "❌"
        print(f"  {status}  {t['name']:<20}  {t['desc']}")
        if not ok:
            print(f"       Erro: {out[:200]}")

        if ok and wake:
            _configurar_wake_e_missed(t["name"])
            print(f"       ↳ WakeToRun + StartWhenAvailable ativados")

    print(f"\n  Log: {LOGS_DIR / 'automation.log'}")
    print(f"\n  Para verificar: python scripts/automation/setup_scheduler.py --status")
    print(f"{'═'*65}\n")


def remover():
    print(f"\n{'═'*65}")
    print("  SBWAA — Remover automação do Task Scheduler")
    print(f"{'═'*65}\n")

    for t in SCHEDULER_TASKS:
        ok, _ = _schtasks("/Delete", "/TN", t["name"], "/F")
        status = "✅ removida" if ok else "⚠️  não existia"
        print(f"  {status}  {t['name']}")

    print(f"\n{'═'*65}\n")


def status():
    print(f"\n{'═'*65}")
    print("  SBWAA — Status da automação")
    print(f"{'═'*65}\n")

    for t in SCHEDULER_TASKS:
        ok, out = _schtasks("/Query", "/TN", t["name"], "/FO", "LIST")
        if ok:
            proxima = "N/D"
            ultima = "N/D"
            for line in out.splitlines():
                if "Próxima" in line or "Next Run" in line:
                    proxima = line.split(":", 1)[-1].strip()
                if "Última" in line or "Last Run" in line:
                    ultima = line.split(":", 1)[-1].strip()
            print(f"  ✅  {t['name']:<22} próxima={proxima}")
            print(f"      última={ultima}")
        else:
            print(f"  ❌  {t['name']:<22} não instalada")

    log_path = LOGS_DIR / "automation.log"
    if log_path.exists():
        linhas = log_path.read_text(encoding="utf-8", errors="replace").splitlines()
        relevantes = [l for l in linhas[-30:] if "AUTOMATION" in l or "Concluído" in l or "FALHOU" in l]
        if relevantes:
            print(f"\n  Últimas entradas do log:")
            for l in relevantes[-5:]:
                print(f"    {l}")
    else:
        print(f"\n  Log ainda não existe: {log_path}")

    print(f"\n{'═'*65}\n")


def testar(slot: str):
    """Dispara o slot agora via schtasks /Run (útil para teste rápido)."""
    names = {t["slot"]: t["name"] for t in SCHEDULER_TASKS}
    if slot not in names:
        print(f"  Slot '{slot}' inválido. Opções: {', '.join(names)}")
        return
    ok, out = _schtasks("/Run", "/TN", names[slot])
    if ok:
        print(f"  ✅ {names[slot]} disparado. Verifique {LOGS_DIR / 'automation.log'}")
    else:
        print(f"  ❌ Erro: {out}")


def main():
    parser = argparse.ArgumentParser(
        description="Setup SBWAA Task Scheduler",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
  python setup_scheduler.py --instalar
  python setup_scheduler.py --instalar --sem-wake
  python setup_scheduler.py --status
  python setup_scheduler.py --remover
  python setup_scheduler.py --testar morning
        """,
    )
    parser.add_argument("--instalar", action="store_true", help="Instala as 4 tarefas (morning, eod, weekend, alerta)")
    parser.add_argument("--remover", action="store_true", help="Remove todas as tarefas")
    parser.add_argument("--status", action="store_true", help="Mostra status")
    parser.add_argument("--sem-wake", action="store_true", help="Não ativa WakeToRun")
    parser.add_argument("--testar", metavar="SLOT", help="Dispara um slot agora (morning|eod|weekend|alerta)")
    args = parser.parse_args()

    if args.instalar:
        instalar(wake=not args.sem_wake)
    elif args.remover:
        remover()
    elif args.status:
        status()
    elif args.testar:
        testar(args.testar)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
