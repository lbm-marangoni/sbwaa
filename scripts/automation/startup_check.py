"""
SBWAA Automation — Verificação na abertura do sistema

Chamado pelo iniciar.bat antes de abrir o painel.
Lê a fila de teses do dia (ou do dia anterior) e dispara
tray notification se houver sinais COMPRAR pendentes.
"""

import json
import sys
from datetime import date, timedelta
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
LOGS_DIR = PROJECT_ROOT / "logs"
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.automation.notifier import notify


def carregar_fila() -> dict | None:
    for delta in range(2):  # hoje e ontem
        d = (date.today() - timedelta(days=delta)).strftime("%Y-%m-%d")
        path = LOGS_DIR / f"tese_queue_{d}.json"
        if path.exists():
            try:
                return json.loads(path.read_text(encoding="utf-8"))
            except Exception:
                return None
    return None


def main():
    fila = carregar_fila()
    if not fila:
        return

    comprar = [a for a in fila.get("ativos", []) if a.get("veredicto") == "COMPRAR"]
    if not comprar:
        return

    tickers = " · ".join(
        f"{a['ticker']} ({a.get('status', '?')})" for a in comprar
    )
    n = len(comprar)
    notify(
        f"SBWAA — {n} sinal{'is' if n > 1 else ''} COMPRAR",
        f"{tickers}\nAbra o painel para ver os comandos",
    )


if __name__ == "__main__":
    main()
