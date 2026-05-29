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
from calculators.stress_test import rodar_todos_cenarios, CENARIOS, impacto_cenario

PATRIMONIO = 100_000.0
VAULT_ROOT = PROJECT_ROOT / "vault"
ATIVOS_DIR = VAULT_ROOT / "01-ativos"


def calcular_peso_intl() -> tuple[float, float]:
    """
    Lê carteira.md e retorna (peso_intl_indireto, peso_intl_direto).
    indireto = ETF INTL B3-BRL (moeda: BRL ou ausente)
    direto   = ETF INTL moeda: USD (ou outro)
    """
    carteira_path = VAULT_ROOT / "00-portfolio" / "carteira.md"
    TIPOS_ETF_INTL = {"🟥 ETF INTL", "ETF INTL"}

    if not carteira_path.exists():
        return 0.0, 0.0

    posicoes = []
    dentro = False
    for linha in carteira_path.read_text(encoding="utf-8").splitlines():
        s = linha.strip()
        if s.startswith("| Ticker"):
            dentro = True
            continue
        if dentro and s.startswith("|---"):
            continue
        if dentro and s.startswith("|"):
            cols = [c.strip() for c in s.split("|")[1:-1]]
            if len(cols) >= 5:
                tk   = cols[0]
                tipo = cols[1]
                valor = 0.0
                # Tenta col 6 (Valor R$) ou fallback qtd×pm
                if len(cols) >= 7:
                    try:
                        valor = float(cols[6].replace(",", ""))
                    except Exception:
                        pass
                if not valor:
                    try:
                        valor = float(cols[3].replace(",", ".")) * float(cols[4].replace(",", "."))
                    except Exception:
                        pass
                posicoes.append({"ticker": tk, "tipo": tipo, "valor": valor})
        elif dentro and s and not s.startswith("|"):
            break

    total = sum(p["valor"] for p in posicoes)
    if total <= 0:
        return 0.0, 0.0

    peso_ind = peso_dir = 0.0
    for p in posicoes:
        if p["tipo"] not in TIPOS_ETF_INTL:
            continue
        tk = p["ticker"]
        moeda = "BRL"
        tese = ATIVOS_DIR / tk / "tese.md"
        if tese.exists():
            for linha in tese.read_text(encoding="utf-8").splitlines():
                if linha.lower().startswith("moeda:"):
                    moeda = linha.split(":", 1)[1].strip().upper()
                    break
        peso = p["valor"] / total
        if moeda == "BRL":
            peso_ind += peso
        else:
            peso_dir += peso

    return round(peso_ind, 4), round(peso_dir, 4)


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


def exibir_stress(resultados: dict, titulo: str = "STRESS TEST", tem_fx: bool = False):
    W = 68 if tem_fx else 55
    print(f"\n{'═'*W}")
    print(f"  {titulo} | {datetime.now().strftime('%Y-%m-%d')}")
    print(f"{'─'*W}")
    if tem_fx:
        print(f"  {'Cenário':<30} {'Mercado%':>9}  {'Câmbio%':>8}  {'Total%':>7}  {'R$*':>10}")
        print(f"  {'─'*30} {'─'*9}  {'─'*8}  {'─'*7}  {'─'*10}")
    else:
        print(f"  {'Cenário':<30} {'Impacto%':>9}  {'Impacto R$*':>12}")
        print(f"  {'─'*30} {'─'*9}  {'─'*12}")
    for v in resultados.values():
        if tem_fx and "impacto_mercado_pct" in v:
            m   = v["impacto_mercado_pct"]
            fx  = v["impacto_fx_pct"]
            tot = v["impacto_pct"]
            brl = v["impacto_reais_normalizado"]
            fx_str = f"{fx:>+7.1f}%" if fx != 0 else "      —"
            print(f"  {v['cenario']:<30} {m:>+8.1f}%  {fx_str}  {tot:>+6.1f}%  {fmt_brl(brl):>10}")
        else:
            print(f"  {v['cenario']:<30} {v['impacto_pct']:>+8.1f}%  {fmt_brl(v['impacto_reais_normalizado']):>12}")
    print(f"\n  * Patrimônio normalizado R$ 100k — privacidade preservada")
    if tem_fx:
        print(f"  Câmbio+: posições USD se beneficiam quando BRL enfraquece")
    print(f"{'═'*W}\n")


def main():
    parser = argparse.ArgumentParser(description="/stress-test — SBWAA")
    parser.add_argument("cenario", nargs="?", default=None,
                        help="Nome do cenário ou 'custom'")
    parser.add_argument("choque", nargs="?", type=float, default=None,
                        help="Choque percentual para cenário custom (ex: -30)")
    args = parser.parse_args()

    risk = carregar_risk_recente()
    beta = (risk or {}).get("beta_ibov", 1.0) or 1.0
    cbs  = (risk or {}).get("circuit_breakers", {})

    # Exposição cambial da carteira
    peso_ind, peso_dir = calcular_peso_intl()
    tem_fx = (peso_ind + peso_dir) > 0.001

    if args.cenario == "custom":
        choque = args.choque if args.choque is not None else -20.0
        cenario_custom = {
            "nome": f"Custom ({choque:+.0f}% mercado)",
            "ibov_queda_pct": choque,
            "brl_usd_alta_pct": 0.0,
            "descricao": "Choque personalizado",
        }
        res = impacto_cenario(beta, cenario_custom, PATRIMONIO, peso_ind, peso_dir)
        resultados = {"custom": res}
        exibir_stress(resultados, f"STRESS CUSTOM {choque:+.0f}%", tem_fx)
        _salvar_stress_md(resultados, beta, f"STRESS CUSTOM {choque:+.0f}%", cbs)
        print()
        return

    todos = rodar_todos_cenarios(beta, PATRIMONIO, peso_ind, peso_dir)

    if args.cenario:
        key_map = {
            "covid-2020": "covid_2020", "crise-2008": "crise_2008",
            "eleicoes-2022": "eleicoes_2022", "lula-2002": "lula1_2002",
            "brl-usd": "brl_usd_mais_20", "fiscal": "crise_fiscal_br",
        }
        chave = key_map.get(args.cenario.lower(), args.cenario.lower())
        filtrado = {k: v for k, v in todos.items()
                    if chave in k or args.cenario.lower() in v["cenario"].lower()}
        if not filtrado:
            print(f"\n❌ Cenário '{args.cenario}' não encontrado.")
            print(f"   Disponíveis: {', '.join(todos.keys())}")
            print(f"   Use 'custom' para choque personalizado.\n")
            return
        exibir_stress(filtrado, f"STRESS — {args.cenario.upper()}", tem_fx)
        _salvar_stress_md(filtrado, beta, f"STRESS — {args.cenario.upper()}", cbs)
    else:
        exibir_stress(todos, "STRESS TEST — TODOS OS CENÁRIOS", tem_fx)
        _salvar_stress_md(todos, beta, "TODOS OS CENÁRIOS", cbs)

    if risk:
        status = "✅ OK" if all(cbs.values()) else "⚠️ VIOLAÇÕES detectadas"
        print(f"  Circuit Breakers atuais: {status}")
        print(f"  Beta IBOV carteira: {beta:.2f}")
    if tem_fx:
        print(f"  Exposição USD: {(peso_ind+peso_dir)*100:.1f}% carteira "
              f"({peso_dir*100:.1f}% direto / {peso_ind*100:.1f}% indireto B3)")

    print()


if __name__ == "__main__":
    main()
