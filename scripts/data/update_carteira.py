"""
update_carteira.py — Atualiza cotações e P&L na carteira.md.
Uso: python update_carteira.py
Nunca transmite dados privados (quantidade, preço médio) para fora.
"""

import re
import sys
from datetime import datetime
from pathlib import Path

VAULT_ROOT = Path(__file__).parent.parent.parent / "vault"
CARTEIRA_PATH = VAULT_ROOT / "00-portfolio" / "carteira.md"
SCRIPTS_DIR = Path(__file__).parent

sys.path.insert(0, str(SCRIPTS_DIR))
from fetch_brapi import buscar_ticker as brapi_buscar
from fetch_yahoo import buscar_ticker as yahoo_buscar

TICKERS_BR_SUFFIX = ".SA"


def cotacao_br(ticker: str) -> float | None:
    try:
        dados = brapi_buscar(ticker)
        return dados.get("cotacao")
    except Exception as e:
        print(f"  AVISO Brapi [{ticker}]: {e}")
    # fallback Yahoo com sufixo .SA
    try:
        dados = yahoo_buscar(ticker + TICKERS_BR_SUFFIX)
        return dados.get("cotacao_atual")
    except Exception as e:
        print(f"  AVISO Yahoo [{ticker}.SA]: {e}")
    return None


def cotacao_intl(ticker: str) -> float | None:
    try:
        dados = yahoo_buscar(ticker)
        return dados.get("cotacao_atual")
    except Exception as e:
        print(f"  AVISO Yahoo [{ticker}]: {e}")
    return None


def parsear_tabela(conteudo: str) -> list[dict]:
    """Extrai linhas da tabela de posições do carteira.md."""
    linhas = []
    dentro = False
    cabecalho = []
    for linha in conteudo.splitlines():
        stripped = linha.strip()
        if stripped.startswith("| Ticker") or stripped.startswith("|Ticker"):
            cabecalho = [c.strip() for c in stripped.split("|")[1:-1]]
            dentro = True
            continue
        if dentro and stripped.startswith("|---"):
            continue
        if dentro and stripped.startswith("|"):
            celulas = [c.strip() for c in stripped.split("|")[1:-1]]
            if len(celulas) >= len(cabecalho[:5]):
                row = dict(zip(cabecalho, celulas + [""] * 10))
                linhas.append(row)
        elif dentro and stripped == "":
            break
    return linhas


def eh_ticker_br(ticker: str) -> bool:
    t = ticker.upper()
    return bool(re.match(r"^[A-Z]{4}[0-9]{1,2}[FBP]?$", t)) and not t.startswith("^")


def atualizar_carteira():
    if not CARTEIRA_PATH.exists():
        print(f"Erro: {CARTEIRA_PATH} não encontrado.")
        sys.exit(1)

    conteudo = CARTEIRA_PATH.read_text(encoding="utf-8")
    posicoes = parsear_tabela(conteudo)

    posicoes_validas = [
        p for p in posicoes
        if p.get("Ticker", "").strip() and
           p.get("Qtd", "").strip() and
           p.get("Preço Médio", "").strip()
    ]

    if not posicoes_validas:
        print("Carteira sem posições preenchidas — nada a atualizar.")
        return

    total_investido = 0.0
    total_atual = 0.0
    linhas_novas = []

    for pos in posicoes_validas:
        ticker_raw = pos["Ticker"].strip().strip("[]").split("|")[0].replace("[[", "").strip()
        ticker = ticker_raw.upper()

        try:
            qtd = float(pos["Qtd"].replace(",", "."))
            pm = float(pos["Preço Médio"].replace(",", ".").replace("R$", "").strip())
        except ValueError:
            print(f"  AVISO: {ticker} — quantidade ou preço médio inválido, pulando.")
            continue

        tipo = pos.get("Tipo", "").strip()
        setor = pos.get("Setor", "").strip()

        print(f"  Atualizando {ticker}...")
        if eh_ticker_br(ticker):
            preco_atual = cotacao_br(ticker)
        else:
            preco_atual = cotacao_intl(ticker)

        if preco_atual is None:
            print(f"  AVISO: cotação não obtida para {ticker}, mantendo linha sem cálculo.")
            linhas_novas.append(pos)
            continue

        valor_pos = round(qtd * preco_atual, 2)
        pl_rs = round(valor_pos - qtd * pm, 2)
        pl_pct = round((preco_atual - pm) / pm * 100, 1) if pm else 0.0

        total_investido += qtd * pm
        total_atual += valor_pos

        ticker_display = ticker

        linhas_novas.append({
            "Ticker": ticker_display,
            "Tipo": tipo,
            "Setor": setor,
            "Qtd": str(int(qtd) if qtd.is_integer() else qtd),
            "Preço Médio": f"{pm:.2f}",
            "Preço Atual": f"{preco_atual:.2f}",
            "Valor (R$)": f"{valor_pos:,.2f}",
            "P&L (R$)": f"{pl_rs:+,.2f}",
            "P&L (%)": f"{pl_pct:+.1f}%",
            "Alocação (%)": "__ALLOC__",
        })

    # calcular alocação
    for row in linhas_novas:
        if row.get("Alocação (%)") == "__ALLOC__" and total_atual > 0:
            try:
                val = float(row["Valor (R$)"].replace(",", "").replace("+", ""))
                row["Alocação (%)"] = f"{val / total_atual * 100:.1f}%"
            except Exception:
                row["Alocação (%)"] = "—"

    pl_total = round(total_atual - total_investido, 2)
    pl_total_pct = round((total_atual - total_investido) / total_investido * 100, 1) if total_investido else 0.0
    agora = datetime.now().strftime("%Y-%m-%d %H:%M")

    cabecalho_tabela = "| Ticker | Tipo | Setor | Qtd | Preço Médio | Preço Atual | Valor (R$) | P&L (R$) | P&L (%) | Alocação (%) |"
    separador = "|--------|------|-------|-----|-------------|-------------|------------|----------|---------|--------------|"
    linhas_md = [cabecalho_tabela, separador]
    for row in linhas_novas:
        cols = [
            row.get("Ticker", ""), row.get("Tipo", ""), row.get("Setor", ""),
            row.get("Qtd", ""), row.get("Preço Médio", ""), row.get("Preço Atual", ""),
            row.get("Valor (R$)", ""), row.get("P&L (R$)", ""), row.get("P&L (%)", ""),
            row.get("Alocação (%)", ""),
        ]
        linhas_md.append("| " + " | ".join(cols) + " |")

    tabela_nova = "\n".join(linhas_md)

    resumo_novo = (
        f"- **Patrimônio Total:** R$ {total_atual:,.2f}\n"
        f"- **Total Investido:** R$ {total_investido:,.2f}\n"
        f"- **P&L Total:** R$ {pl_total:+,.2f} ({pl_total_pct:+.1f}%)\n"
        f"- **Última atualização:** {agora}"
    )

    # substituir tabela e resumo no conteúdo original
    novo_conteudo = re.sub(
        r"\| Ticker \|.*?(?=\n##|\Z)", tabela_nova, conteudo, flags=re.DOTALL
    )
    novo_conteudo = re.sub(
        r"- \*\*Patrimônio Total:\*\*.*?- \*\*Última atualização:\*\*.*",
        resumo_novo, novo_conteudo, flags=re.DOTALL
    )

    CARTEIRA_PATH.write_text(novo_conteudo, encoding="utf-8")
    print(f"\nCarteira atualizada em {agora}")
    print(f"  Patrimônio Total : R$ {total_atual:,.2f}")
    print(f"  Total Investido  : R$ {total_investido:,.2f}")
    print(f"  P&L Total        : R$ {pl_total:+,.2f} ({pl_total_pct:+.1f}%)")


if __name__ == "__main__":
    atualizar_carteira()
