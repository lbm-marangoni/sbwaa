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

PROJECT_ROOT   = Path(__file__).parent.parent.parent
SCRIPTS_DATA   = PROJECT_ROOT / "scripts" / "data"
AGENTS_DIR     = PROJECT_ROOT / ".claude" / "agents"
CACHE_DIR      = SCRIPTS_DATA / "cache"
RELATORIOS_DIR = PROJECT_ROOT / "vault" / "02-relatorios"

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


def _salvar_stress_md(resultados: dict, beta: float, titulo: str, cbs: dict):
    """Salva relatório de stress test em vault/02-relatorios/stress-test.md."""
    try:
        RELATORIOS_DIR.mkdir(parents=True, exist_ok=True)
        md_path = RELATORIOS_DIR / "stress-test.md"
        hoje_s  = datetime.now().strftime("%Y-%m-%d")
        agora_s = datetime.now().strftime("%Y-%m-%d %H:%M")

        linhas = [
            "---",
            "tags: [portfolio, stress-test, risco, snapshot]",
            "cssclasses: [node-relatorio]",
            f"data: {hoje_s}",
            f"beta_ibov: {beta:.2f}",
            "---",
            "",
            f"# 🧪 Stress Test — {hoje_s}",
            "",
            f"> [!info] Gerado em {agora_s} — sobreescrito a cada execução de `/stress-test`",
            f"> Patrimônio normalizado R$ 100k — privacidade preservada. Beta IBOV carteira: {beta:.2f}",
            "",
            f"## {titulo}",
            "",
            "| Cenário | Impacto % | Impacto R$* |",
            "|---------|-----------|------------|",
        ]

        for v in resultados.values():
            pct  = v["impacto_pct"]
            brl  = v["impacto_reais_normalizado"]
            icone = "🟢" if pct >= 0 else ("🟡" if pct > -10 else ("🔴" if pct > -20 else "⛔"))
            linhas.append(f"| {icone} {v['cenario']} | {pct:+.1f}% | R$ {brl:+,.0f} |")

        linhas += ["", "> \\* Patrimônio normalizado R$ 100k", ""]

        # Pior cenário destaque
        pior = min(resultados.values(), key=lambda x: x["impacto_pct"])
        pior_pct = pior["impacto_pct"]
        tipo_alerta = "danger" if pior_pct < -20 else "warning"
        linhas.append(
            f"> [!{tipo_alerta}] Pior cenário: **{pior['cenario']}** — {pior_pct:+.1f}%"
        )
        linhas.append("")

        # Circuit breakers
        if cbs:
            cb_ok  = all(cbs.values())
            cb_str = "✅ Todos OK" if cb_ok else "⚠️ Violações detectadas"
            tipo_cb = "tip" if cb_ok else "danger"
            linhas += [
                "## Circuit Breakers (referência)",
                "",
                f"> [!{tipo_cb}] {cb_str}",
                "",
            ]

        linhas += ["---", "", "## Links", "", "[[carteira]] | [[risco-carteira]] | [[ips]]"]

        md_path.write_text("\n".join(linhas), encoding="utf-8")
        print(f"\n  📄 Relatório completo : vault/02-relatorios/stress-test.md")
    except Exception as e:
        print(f"\n  AVISO: não foi possível salvar stress-test.md: {e}")


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

    cbs = (risk or {}).get("circuit_breakers", {})

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
        _salvar_stress_md(resultados, beta, f"STRESS CUSTOM {choque:+.0f}%", cbs)
        print()
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
        _salvar_stress_md(filtrado, beta, f"STRESS — {args.cenario.upper()}", cbs)
    else:
        exibir_stress(todos, "STRESS TEST — TODOS OS CENÁRIOS")
        _salvar_stress_md(todos, beta, "TODOS OS CENÁRIOS", cbs)

    if risk:
        status = "✅ OK" if all(cbs.values()) else "⚠️ VIOLAÇÕES detectadas"
        print(f"  Circuit Breakers atuais: {status}")
        print(f"  Beta IBOV carteira: {beta:.2f}")

    print()


if __name__ == "__main__":
    main()
