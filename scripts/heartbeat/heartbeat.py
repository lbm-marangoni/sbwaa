"""
SBWAA — Heartbeat Diário
Roda automaticamente. Não requer interação.
Agendado via cron (Linux/Mac) ou Task Scheduler (Windows).

Execução recomendada: 08h00 em dias úteis (antes da abertura)
"""

import sys
import json
import subprocess
import logging
from datetime import datetime, date, timedelta
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
SCRIPTS_DATA = PROJECT_ROOT / "scripts" / "data"
AGENTS_DIR = PROJECT_ROOT / ".claude" / "agents"
VAULT_ROOT = PROJECT_ROOT / "vault"
CACHE_DIR = SCRIPTS_DATA / "cache"
LOGS_DIR = PROJECT_ROOT / "logs"
ALERTS_SCRIPT = PROJECT_ROOT / "scripts" / "alerts" / "check_alerts.py"

LOGS_DIR.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    handlers=[logging.FileHandler(str(LOGS_DIR / "heartbeat.log"), encoding="utf-8")],
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s — %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

FERIADOS_BR = {
    # Feriados nacionais fixos
    (1, 1), (4, 21), (5, 1), (9, 7), (10, 12), (11, 2), (11, 15), (11, 20), (12, 25),
}


def eh_dia_util(d: date) -> bool:
    if d.weekday() >= 5:
        return False
    if (d.month, d.day) in FERIADOS_BR:
        return False
    return True


def rodar(descricao: str, cmd: list[str]) -> bool:
    logging.info(f"Iniciando: {descricao}")
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        if r.returncode == 0:
            logging.info(f"OK: {descricao}")
            return True
        logging.warning(f"FALHOU ({r.returncode}): {descricao}\n{r.stderr[:500]}")
        return False
    except subprocess.TimeoutExpired:
        logging.error(f"TIMEOUT: {descricao}")
        return False
    except Exception as e:
        logging.error(f"EXCEÇÃO em {descricao}: {e}")
        return False


def gerar_morning_call_vault(hoje: str):
    """Gera versão simplificada do morning call e salva no vault."""
    try:
        from pathlib import Path as _P
        import json as _j

        vault = PROJECT_ROOT / "vault"
        mc_dir = vault / "02-relatorios" / "diarios"
        mc_dir.mkdir(parents=True, exist_ok=True)
        mc_path = mc_dir / f"morning-call-{hoje}.md"

        if mc_path.exists():
            logging.info("Morning call já existe — pulando.")
            return

        # Ler risk e quant para métricas
        risk_path = CACHE_DIR / f"risk_{hoje}.json"
        quant_path = CACHE_DIR / f"quant_{hoje}.json"
        risk = _j.loads(risk_path.read_text(encoding="utf-8")) if risk_path.exists() else {}
        quant = _j.loads(quant_path.read_text(encoding="utf-8")) if quant_path.exists() else {}

        cart = quant.get("carteira", {})
        cbs = risk.get("circuit_breakers", {})
        flags = risk.get("flags_pm", [])
        hora = datetime.now().strftime("%H:%M")

        conteudo = f"""---
tags: [diario, morning-call]
cssclasses: [node-diario]
data: {hoje}
fonte: heartbeat
---

# Morning Call — {hoje} (Heartbeat)
*Gerado automaticamente às {hora}*

## 📊 Métricas HF

- Sharpe (12m): {cart.get('sharpe', 'N/D')}
- Volatilidade: {cart.get('volatilidade_pct', 'N/D')}%
- VaR 95%: {risk.get('var_historico_95_pct', 'N/D')}%
- Drawdown atual: {cart.get('drawdown_maximo_pct', 'N/D')}%
- Circuit breakers: {'✅ OK' if all(cbs.values()) else '⚠️ VERIFICAR'}

## ⚡ Flags

{chr(10).join(f'- {f}' for f in flags) if flags else '- Nenhum alerta ativo.'}

## Links
[[market-researcher-{hoje}]] | [[risk-{hoje}]]
"""
        mc_path.write_text(conteudo, encoding="utf-8")
        logging.info(f"Morning call salvo: {mc_path.name}")
    except Exception as e:
        logging.error(f"Erro ao gerar morning call: {e}")


def main():
    hoje_date = date.today()
    hoje = hoje_date.strftime("%Y-%m-%d")
    hora = datetime.now().strftime("%H:%M")

    logging.info(f"=== HEARTBEAT INICIADO | {hoje} {hora} ===")

    if not eh_dia_util(hoje_date):
        logging.info(f"{hoje} não é dia útil — heartbeat encerrado.")
        return

    # 0. Coletar RSS na base de conhecimento
    try:
        sys.path.insert(0, str(PROJECT_ROOT))
        from knowledge.rss_collector import coletar_todos_feeds
        novos_artigos = coletar_todos_feeds()
        if novos_artigos > 0:
            logging.info(f"RSS: {novos_artigos} novos artigos indexados")
        else:
            logging.info("RSS: nenhum artigo novo")
    except Exception as e:
        logging.warning(f"RSS collector falhou (base de conhecimento pode estar vazia): {e}")

    # 1. Snapshot de mercado
    rodar("Market Snapshot", [sys.executable, str(SCRIPTS_DATA / "market_snapshot.py")])

    # 2. Quant (métricas da carteira)
    rodar("Quant / Data Engineer",
          [sys.executable, str(AGENTS_DIR / "quant-data-engineer" / "run_quant.py")])

    # 3. Risk Engineer
    rodar("Risk Engineer",
          [sys.executable, str(AGENTS_DIR / "risk-engineer" / "run_risk_engineer.py")])

    # 4. Verificar alertas
    if ALERTS_SCRIPT.exists():
        rodar("Check Alerts", [sys.executable, str(ALERTS_SCRIPT)])
    else:
        logging.warning("check_alerts.py não encontrado — pulando alertas.")

    # 5. Morning call no vault
    gerar_morning_call_vault(hoje)

    logging.info(f"=== HEARTBEAT CONCLUÍDO | {hoje} {hora} ===")


if __name__ == "__main__":
    main()
