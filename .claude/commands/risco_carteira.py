"""
risco_carteira.py — Snapshot rápido de risco da carteira.
Uso: python sbwaa.py /risco-carteira
"""

import sys
import json
import subprocess
from datetime import datetime, timedelta
from pathlib import Path

PROJECT_ROOT   = Path(__file__).parent.parent.parent
SCRIPTS_DATA   = PROJECT_ROOT / "scripts" / "data"
AGENTS_DIR     = PROJECT_ROOT / ".claude" / "agents"
CACHE_DIR      = SCRIPTS_DATA / "cache"
RELATORIOS_DIR = PROJECT_ROOT / "vault" / "02-relatorios"


def carregar_json_cache(prefixo: str, hoje: str) -> dict | None:
    for d in range(4):
        dt = (datetime.strptime(hoje, "%Y-%m-%d") - timedelta(days=d)).strftime("%Y-%m-%d")
        path = CACHE_DIR / f"{prefixo}_{dt}.json"
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
    return None


def fmt_pct(v):
    return f"{v:.2f}%" if v is not None else "N/D"


def _salvar_risco_md(hoje: str, risk: dict, quant: dict | None):
    """Salva snapshot de risco em vault/02-relatorios/risco-carteira.md."""
    try:
        RELATORIOS_DIR.mkdir(parents=True, exist_ok=True)
        md_path = RELATORIOS_DIR / "risco-carteira.md"
        agora_s = datetime.now().strftime("%Y-%m-%d %H:%M")
        cart    = (quant or {}).get("carteira", {})
        cbs     = risk.get("circuit_breakers", {})
        optim   = (quant or {}).get("otimizacao", {})

        linhas = [
            "---",
            "tags: [portfolio, risco, snapshot]",
            "cssclasses: [node-relatorio]",
            f"data: {hoje}",
            "---",
            "",
            f"# 🔔 Risco Carteira — {hoje}",
            "",
            f"> [!info] Snapshot gerado em {agora_s} — sobreescrito a cada execução de `/risco-carteira`",
            "",
            "## Métricas de Risco",
            "",
            "| Métrica | Valor |",
            "|---------|-------|",
            f"| Sharpe Ratio (12m) | {cart.get('sharpe', 'N/D')} |",
            f"| Volatilidade Anual | {fmt_pct(cart.get('volatilidade_pct'))} |",
            f"| VaR 95% (1 dia) | {fmt_pct(risk.get('var_historico_95_pct'))} |",
            f"| CVaR 95% (1 dia) | {fmt_pct(risk.get('cvar_95_pct'))} |",
            f"| Drawdown Atual | {fmt_pct(cart.get('drawdown_maximo_pct'))} |",
            f"| Beta vs IBOV | {cart.get('beta_ibov', 'N/D')} |",
            f"| Correlação Média | {cart.get('corr_media', 'N/D')} |",
            f"| Maior Concentração | {fmt_pct(risk.get('concentracao_maxima_pct'))} ({risk.get('concentracao_maxima_ticker', 'N/D')}) |",
            "",
            "> \\* Valores em R$ normalizados para R$ 100k — privacidade preservada",
            "",
        ]

        # Circuit breakers
        cb_ok  = all(cbs.values()) if cbs else True
        cb_str = "✅ Todos OK" if cb_ok else "⚠️ Violações detectadas"
        tipo_cb = "tip" if cb_ok else "danger"
        linhas += [
            "## Circuit Breakers",
            "",
            f"> [!{tipo_cb}] {cb_str}",
            "",
            "| Breaker | Status |",
            "|---------|--------|",
        ]
        for nome, ok in cbs.items():
            icone = "✅" if ok else "🚨"
            linhas.append(f"| {nome.replace('_', ' ').upper()} | {icone} |")

        flags = risk.get("flags_pm", [])
        if flags:
            linhas += ["", "## ⚠️ Flags PM", ""]
            for f in flags:
                linhas.append(f"> [!warning] {f}")

        # Fronteira eficiente
        if optim and "erro" not in optim:
            atual_sh = (optim.get("atual") or {}).get("sharpe")
            ms       = optim.get("max_sharpe") or {}
            mv       = optim.get("min_vol") or {}
            ajustes  = optim.get("ajustes_sugeridos") or []

            sh_atual = f"{atual_sh:.3f}" if atual_sh else "N/D"
            sh_ms    = f"{ms.get('sharpe', 'N/D'):.3f}" if ms.get("sharpe") else "N/D"
            vol_atual = fmt_pct(cart.get("volatilidade_pct"))
            vol_mv   = fmt_pct(mv.get("volatilidade_pct"))

            linhas += [
                "",
                "## 📈 Fronteira Eficiente — Markowitz",
                "",
                "| | Atual | Ótimo Markowitz |",
                "|---|-------|----------------|",
                f"| Sharpe Ratio | {sh_atual} | {sh_ms} |",
                f"| Volatilidade | {vol_atual} | {vol_mv} |",
            ]

            if ajustes:
                linhas += ["", "### Ajustes Sugeridos (→ Max Sharpe)", "", "| Ativo | Atual | Alvo | Δ |", "|-------|-------|------|---|"]
                for a in ajustes[:5]:
                    seta = "▲" if a["acao"] == "AUMENTAR" else "▼"
                    linhas.append(
                        f"| {a['ticker']} | {a['peso_atual_pct']:.1f}% | {a['peso_alvo_pct']:.1f}% | {seta} {a['delta_pct']:+.1f}% |"
                    )

        linhas += ["", "---", "", "## Links", "", "[[carteira]] | [[ips]]"]

        md_path.write_text("\n".join(linhas), encoding="utf-8")
        print(f"\n  📄 Relatório completo : vault/02-relatorios/risco-carteira.md")
    except Exception as e:
        print(f"\n  AVISO: não foi possível salvar risco-carteira.md: {e}")


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

    # ── Fronteira Eficiente ───────────────────────────────────────────────────
    optim = (quant or {}).get("otimizacao", {})
    if optim and "erro" not in optim:
        atual_sh = (optim.get("atual") or {}).get("sharpe")
        ms = optim.get("max_sharpe") or {}
        mv = optim.get("min_vol") or {}
        ajustes = optim.get("ajustes_sugeridos") or []

        print(f"\n{'─'*55}")
        print(f"  FRONTEIRA EFICIENTE — Markowitz")
        print(f"{'─'*55}")
        sh_atual_str = f"{atual_sh:.3f}" if atual_sh else "N/D"
        sh_ms_str    = f"{ms.get('sharpe', 'N/D'):.3f}" if ms.get("sharpe") else "N/D"
        vol_atual_str = fmt_pct(cart.get("volatilidade_pct"))
        vol_mv_str    = fmt_pct(mv.get("volatilidade_pct"))
        ganho = optim.get("ganho_sharpe_potencial")
        ganho_str = f"  (+{ganho:.3f})" if ganho and ganho > 0 else ""
        print(f"  Sharpe atual:           {sh_atual_str}  →  Max Sharpe possível: {sh_ms_str}{ganho_str}")
        print(f"  Volatilidade atual:     {vol_atual_str}  →  Min Vol possível:    {vol_mv_str}")

        if ajustes:
            print(f"\n  Ajustes sugeridos (atual → Max Sharpe):")
            for a in ajustes[:5]:
                seta = "▲" if a["acao"] == "AUMENTAR" else "▼"
                print(f"    {seta} {a['ticker']:8s} {a['peso_atual_pct']:5.1f}% → {a['peso_alvo_pct']:5.1f}%  ({a['delta_pct']:+.1f}%)")
        else:
            print(f"  Carteira já próxima do ótimo (delta < 2% por ativo).")

    print(f"\n  * Valor normalizado R$ 100k — privacidade preservada")
    print(f"{'═'*55}")

    # Salvar relatório Obsidian
    _salvar_risco_md(hoje, risk, quant)

    print()


if __name__ == "__main__":
    main()
