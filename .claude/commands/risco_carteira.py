"""
risco_carteira.py — Snapshot rápido de risco da carteira.
Uso: python sbwaa.py /risco-carteira
"""

import sys
import json
import subprocess
from datetime import datetime, timedelta
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
SCRIPTS_DATA = PROJECT_ROOT / "scripts" / "data"
AGENTS_DIR = PROJECT_ROOT / ".claude" / "agents"
CACHE_DIR = SCRIPTS_DATA / "cache"


def carregar_json_cache(prefixo: str, hoje: str) -> dict | None:
    for d in range(4):
        dt = (datetime.strptime(hoje, "%Y-%m-%d") - timedelta(days=d)).strftime("%Y-%m-%d")
        path = CACHE_DIR / f"{prefixo}_{dt}.json"
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
    return None


def fmt_pct(v):
    return f"{v:.2f}%" if v is not None else "N/D"


def main():
    hoje = datetime.now().strftime("%Y-%m-%d")
    print(f"\n{'═'*55}")
    print(f"  SBWAA — Risco Carteira | {hoje}")
    print(f"{'═'*55}\n")

    print("[1/2] Quant / Data Engineer...")
    subprocess.run(
        [sys.executable, str(AGENTS_DIR / "quant-data-engineer" / "run_quant.py")],
        text=True,
    )

    print("\n[2/2] Risk Engineer...")
    subprocess.run(
        [sys.executable, str(AGENTS_DIR / "risk-engineer" / "run_risk_engineer.py")],
        text=True,
    )

    risk = carregar_json_cache("risk", hoje)
    quant = carregar_json_cache("quant", hoje)

    if not risk:
        print("\n⚠️  Dados de risco não disponíveis.\n")
        return

    cart = (quant or {}).get("carteira", {})
    cbs = risk.get("circuit_breakers", {})

    print(f"\n{'═'*55}")
    print(f"  PORTFÓLIO — MÉTRICAS HF | {hoje}")
    print(f"{'─'*55}")
    print(f"  Sharpe Ratio (12m):     {cart.get('sharpe', 'N/D')}")
    print(f"  Volatilidade Anual:     {fmt_pct(cart.get('volatilidade_pct'))}")
    print(f"  VaR 95% (1 dia):        {fmt_pct(risk.get('var_historico_95_pct'))} | R$ {risk.get('var_historico_95_pct', 0) * 100_000 / 100:.0f}*" if risk.get('var_historico_95_pct') else f"  VaR 95% (1 dia):        N/D")
    print(f"  CVaR 95% (1 dia):       {fmt_pct(risk.get('cvar_95_pct'))}")
    print(f"  Drawdown Atual:         {fmt_pct(cart.get('drawdown_maximo_pct'))}")
    print(f"  Beta vs IBOV:           {cart.get('beta_ibov', 'N/D')}")
    print(f"  Correlação Média:       {cart.get('corr_media', 'N/D')}")
    print(f"  Maior Concentração:     {fmt_pct(risk.get('concentracao_maxima_pct'))} ({risk.get('concentracao_maxima_ticker', 'N/D')})")
    print(f"{'─'*55}")

    cb_status = "✅ OK" if all(cbs.values()) else "⚠️ VIOLAÇÕES"
    print(f"  Circuit Breakers:       {cb_status}")
    for nome, ok in cbs.items():
        icone = "✅" if ok else "🚨"
        print(f"    {icone} {nome.replace('_', ' ').upper()}")

    flags = risk.get("flags_pm", [])
    if flags:
        print(f"\n  Flags:")
        for f in flags:
            print(f"    {f}")

    print(f"\n  * Valor normalizado R$ 100k — privacidade preservada")
    print(f"{'═'*55}\n")


if __name__ == "__main__":
    main()
