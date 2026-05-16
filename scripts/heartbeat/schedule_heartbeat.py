"""
schedule_heartbeat.py — Configura o agendamento automático do heartbeat SBWAA.
Uso:
    python schedule_heartbeat.py --instalar
    python schedule_heartbeat.py --remover
    python schedule_heartbeat.py --status
"""

import platform
import subprocess
import os
import argparse
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
HEARTBEAT_PATH = PROJECT_ROOT / "scripts" / "heartbeat" / "heartbeat.py"
LOG_PATH = PROJECT_ROOT / "logs" / "heartbeat.log"
PYTHON = "python"


def instalar_cron():
    """Linux/Mac: instrução para adicionar ao crontab."""
    cron = f"15 7 * * 1-5 {PYTHON} {HEARTBEAT_PATH} >> {LOG_PATH} 2>&1"
    print(f"\n{'═'*60}")
    print("  SBWAA — Configurar Heartbeat (Linux/Mac)")
    print(f"{'═'*60}")
    print("\n  Execute no terminal:")
    print("  crontab -e")
    print("\n  Adicione esta linha:")
    print(f"\n  {cron}\n")
    print("  O heartbeat rodará às 07h15 de segunda a sexta.")
    print(f"  Log: {LOG_PATH}")
    print(f"{'═'*60}\n")


def verificar_cron() -> bool:
    """Verifica se o cron está configurado."""
    try:
        result = subprocess.run(["crontab", "-l"], capture_output=True, text=True)
        return str(HEARTBEAT_PATH) in result.stdout
    except Exception:
        return False


def remover_cron():
    """Remove entry do crontab."""
    try:
        result = subprocess.run(["crontab", "-l"], capture_output=True, text=True)
        linhas = [l for l in result.stdout.splitlines()
                  if str(HEARTBEAT_PATH) not in l]
        novo = "\n".join(linhas) + "\n"
        subprocess.run(["crontab", "-"], input=novo, text=True)
        print("  ✅ Entrada removida do crontab.")
    except Exception as e:
        print(f"  ❌ Erro ao remover crontab: {e}")


def instalar_windows():
    """Windows: instrução para Task Scheduler."""
    print(f"\n{'═'*60}")
    print("  SBWAA — Configurar Heartbeat (Windows)")
    print(f"{'═'*60}")
    print("\n  Opção A — Task Scheduler (GUI):")
    print("  1. Abrir 'Agendador de Tarefas' (taskschd.msc)")
    print("  2. Criar Tarefa Básica > Nome: SBWAA Heartbeat")
    print(f"  3. Programa: {PYTHON}")
    print(f"  4. Argumentos: \"{HEARTBEAT_PATH}\"")
    print(f"  5. Pasta inicial: {PROJECT_ROOT}")
    print("  6. Gatilho: Diariamente às 08:00")
    print("  7. Condição: Executar apenas se conectado à rede")
    print("\n  Opção B — PowerShell (executar como Administrador):")
    task_name = "SBWAA_Heartbeat"
    ps_cmd = (
        f'$action = New-ScheduledTaskAction -Execute "{PYTHON}" '
        f'-Argument "{HEARTBEAT_PATH}" -WorkingDirectory "{PROJECT_ROOT}"; '
        f'$trigger = New-ScheduledTaskTrigger -Daily -At 08:00 -DaysOfWeek Monday,Tuesday,Wednesday,Thursday,Friday; '
        f'Register-ScheduledTask -TaskName "{task_name}" -Action $action -Trigger $trigger -RunLevel Highest'
    )
    print(f"\n  {ps_cmd}\n")
    print(f"  Log: {LOG_PATH}")
    print(f"{'═'*60}\n")


def status_windows():
    try:
        result = subprocess.run(
            ["schtasks", "/query", "/tn", "SBWAA_Heartbeat", "/fo", "LIST"],
            capture_output=True, text=True,
        )
        if result.returncode == 0:
            print("\n  ✅ Heartbeat agendado (SBWAA_Heartbeat).")
            print(result.stdout[:300])
        else:
            print("\n  ❌ Heartbeat não encontrado no Task Scheduler.")
            print("     Execute: python schedule_heartbeat.py --instalar")
    except Exception as e:
        print(f"\n  Erro ao verificar status: {e}")


def main():
    parser = argparse.ArgumentParser(description="Agendar Heartbeat SBWAA")
    parser.add_argument("--instalar", action="store_true")
    parser.add_argument("--remover", action="store_true")
    parser.add_argument("--status", action="store_true")
    args = parser.parse_args()

    sistema = platform.system()

    if args.instalar:
        if sistema in ("Linux", "Darwin"):
            instalar_cron()
        elif sistema == "Windows":
            instalar_windows()
        else:
            print(f"  Sistema {sistema} — configure manualmente.")
            print(f"  Script: {HEARTBEAT_PATH}")
            print(f"  Horário recomendado: 07h15, dias úteis.")

    elif args.remover:
        if sistema in ("Linux", "Darwin"):
            remover_cron()
        else:
            print("  Windows: remova manualmente no Agendador de Tarefas (SBWAA_Heartbeat).")

    elif args.status:
        if sistema in ("Linux", "Darwin"):
            ativo = verificar_cron()
            print(f"\n  Heartbeat no crontab: {'✅ Sim' if ativo else '❌ Não'}")
            if LOG_PATH.exists():
                linhas = LOG_PATH.read_text(encoding="utf-8").splitlines()
                print(f"  Última execução: {linhas[-1] if linhas else 'N/D'}")
        elif sistema == "Windows":
            status_windows()

    else:
        parser.print_help()
        print(f"\n  Script: {HEARTBEAT_PATH}")
        print(f"  Log:    {LOG_PATH}\n")


if __name__ == "__main__":
    main()
