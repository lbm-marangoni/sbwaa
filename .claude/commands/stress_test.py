"""
stress_test.py — Roda stress tests na carteira atual.
Uso:
    python sbwaa.py /stress-test
    python sbwaa.py /stress-test covid-2020
    python sbwaa.py /stress-test custom -30
"""

import sys
import json
import argparse
from datetime import datetime, timedelta
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
SCRIPTS_DATA = PROJECT_ROOT / "scripts" / "data"
AGENTS_DIR = PROJECT_ROOT / ".claude" / "agents"
CACHE_DIR = SCRIPTS_DATA / "cache"

sys.path.insert(0, str(AGENTS_DIR / "risk-engineer"))
from calculators.stress_test import rodar_todos_cenarios, CENARIOS

PATRIMONIO = 100_000.0


def carregar_risk_recente() -> dict | None:
    hoje = datetime.now().strftime("%Y-%m-%d")
    for d in range(4):
        dt = (datetime.strptime(hoje, "%Y-%m-%d") - timedelta(days=d)).strftime("%Y-%m-%d")
        path = CACHE_DIR / f"risk_{dt}.json"
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
    return None


def fmt_brl(v: float) -> str:
    return f"R$ {v:+,.0f}"


def exibir_stress(resultados: dict, titulo: str = "STRESS TEST"):
    print(f"\n{'═'*55}")
    print(f"  {titulo} | {datetime.now().strftime('%Y-%m-%d')}")
    print(f"{'─'*55}")
    print(f"  {'Cenário':<30} {'Impacto%':>9}  {'Impacto R$*':>12}")
    print(f"  {'─'*30} {'─'*9}  {'─'*12}")
    for v in resultados.values():
        print(f"  {v['cenario']:<30} {v['impacto_pct']:>+8.1f}%  {fmt_brl(v['impacto_reais_normalizado']):>12}")
    print(f"\n  * Patrimônio normalizado R$ 100k — privacidade preservada")
    print(f"{'═'*55}\n")


def main():
    parser = argparse.ArgumentParser(description="/stress-test — SBWAA")
    parser.add_argument("cenario", nargs="?", default=None,
                        help="Nome do cenário ou 'custom'")
    parser.add_argument("choque", nargs="?", type=float, default=None,
                        help="Choque percentual para cenário custom (ex: -30)")
    args = parser.parse_args()

    risk = carregar_risk_recente()
    beta = (risk or {}).get("beta_ibov", 1.0) or 1.0

    if args.cenario == "custom":
        choque = args.choque if args.choque is not None else -20.0
        impacto_pct = choque * beta
        impacto_brl = impacto_pct / 100 * PATRIMONIO
        resultados = {
            "custom": {
                "cenario": f"Custom ({choque:+.0f}% mercado)",
                "impacto_pct": impacto_pct,
                "impacto_reais_normalizado": impacto_brl,
            }
        }
        exibir_stress(resultados, f"STRESS CUSTOM {choque:+.0f}%")
        return

    todos = rodar_todos_cenarios(beta, PATRIMONIO)

    if args.cenario:
        # Filtrar por nome parcial
        filtrado = {k: v for k, v in todos.items()
                    if args.cenario.lower() in v["cenario"].lower()}
        if not filtrado:
            print(f"\n❌ Cenário '{args.cenario}' não encontrado.")
            print(f"   Cenários disponíveis: {', '.join(todos.keys())}")
            print(f"   Use 'custom' com valor para choque personalizado.\n")
            return
        exibir_stress(filtrado, f"STRESS — {args.cenario.upper()}")
    else:
        exibir_stress(todos, "STRESS TEST — TODOS OS CENÁRIOS")

    if risk:
        cbs = risk.get("circuit_breakers", {})
        status = "✅ OK" if all(cbs.values()) else "⚠️ VIOLAÇÕES detectadas"
        print(f"  Circuit Breakers atuais: {status}")
        print(f"  Beta IBOV carteira: {beta:.2f}\n")


if __name__ == "__main__":
    main()
