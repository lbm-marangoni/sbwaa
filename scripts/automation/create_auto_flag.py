"""
SBWAA Automation — Cria flag de morning automático

Rodado como última task do slot morning quando disparado pelo Task Scheduler.
A existência do arquivo logs/morning_auto_{data}.flag é o que autoriza
o slot "tese" a rodar — sem o flag, o slot tese aborta silenciosamente.
"""

from datetime import date
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
LOGS_DIR = PROJECT_ROOT / "logs"
LOGS_DIR.mkdir(parents=True, exist_ok=True)

flag = LOGS_DIR / f"morning_auto_{date.today()}.flag"
flag.touch()
print(f"Flag criada: {flag.name}")
