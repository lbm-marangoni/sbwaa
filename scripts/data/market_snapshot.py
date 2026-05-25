"""
market_snapshot.py — Gera snapshot diário de mercado no vault.
Uso: python market_snapshot.py
"""

import re
import sys
from datetime import datetime, timedelta
from pathlib import Path

VAULT_ROOT = Path(__file__).parent.parent.parent / "vault"
CARTEIRA_PATH = VAULT_ROOT / "00-portfolio" / "carteira.md"
SNAPSHOTS_DIR = VAULT_ROOT / "02-relatorios" / "diarios"
SCRIPTS_DIR = Path(__file__).parent
sys.path.insert(0, str(SCRIPTS_DIR))

from fetch_yahoo import buscar_ticker as yahoo_buscar, MACRO_TICKERS
from fetch_fundamentals import buscar_ticker as brapi_buscar

MACRO_NOMES = {
    "^BVSP":    "IBOVESPA",
    "^GSPC":    "S&P 500",
    "^IXIC":    "NASDAQ",
    "DX-Y.NYB": "DXY",
    "BRL=X":    "BRL/USD",
    "CL=F":     "Petróleo WTI",
    "GC=F":     "Ouro",
    "^TNX":     "Juros US 10Y",
}


def extrair_tickers_carteira() -> list[str]:
    if not CARTEIRA_PATH.exists():
        return []
    conteudo = CARTEIRA_PATH.read_text(encoding="utf-8")
    tickers = []
    dentro = False
    for linha in conteudo.splitlines():
        stripped = linha.strip()
        if stripped.startswith("| Ticker"):
            dentro = True
            continue
        if dentro and stripped.startswith("|---"):
            continue
        if dentro and stripped.startswith("|"):
            celulas = [c.strip() for c in stripped.split("|")[1:-1]]
            if celulas:
                ticker_raw = celulas[0].replace("[[", "").replace("]]", "").split("|")[0].strip()
                ticker_raw = re.sub(r"01-ativos/([^/]+)/tese", r"\1", ticker_raw)
                if ticker_raw:
                    tickers.append(ticker_raw.upper())
        elif dentro:
            break
    return tickers


def eh_ticker_br(ticker: str) -> bool:
    return bool(re.match(r"^[A-Z]{4}[0-9]{1,2}[FBP]?$", ticker)) and not ticker.startswith("^")


def gerar_snapshot():
    hoje = datetime.now().strftime("%Y-%m-%d")
    ontem = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")

    print("Buscando dados macro...")
    macro_rows = []
    for ticker_y, nome in MACRO_NOMES.items():
        try:
            d = yahoo_buscar(ticker_y, nome)
            val = d.get("cotacao_atual")
            var = d.get("variacao_dia_pct")
            val_str = f"{val:,.2f}" if isinstance(val, (int, float)) else "—"
            var_str = f"{var:+.2f}%" if isinstance(var, (int, float)) else "—"
            macro_rows.append((nome, val_str, var_str))
        except Exception as e:
            print(f"  AVISO macro [{ticker_y}]: {e}")
            macro_rows.append((nome, "—", "—"))

    tickers_carteira = extrair_tickers_carteira()
    print(f"Buscando {len(tickers_carteira)} ativo(s) da carteira...")

    carteira_rows = []
    for ticker in tickers_carteira:
        try:
            if eh_ticker_br(ticker):
                d = brapi_buscar(ticker)
                preco = d.get("cotacao")
                var = d.get("variacao_dia_pct")
            else:
                d = yahoo_buscar(ticker)
                preco = d.get("cotacao_atual")
                var = d.get("variacao_dia_pct")
            preco_str = f"R$ {preco:,.2f}" if isinstance(preco, (int, float)) else "—"
            var_str = f"{var:+.2f}%" if isinstance(var, (int, float)) else "—"
            carteira_rows.append((ticker, preco_str, var_str, "—"))
        except Exception as e:
            print(f"  AVISO [{ticker}]: {e}")
            carteira_rows.append((ticker, "—", "—", "—"))

    tabela_macro = "| Indicador | Valor | Variação |\n|-----------|-------|----------|\n"
    tabela_macro += "\n".join(f"| {n} | {v} | {var} |" for n, v, var in macro_rows)

    if carteira_rows:
        tabela_carteira = "| Ticker | Preço Atual | Variação Dia | P&L Total |\n|--------|-------------|--------------|----------|\n"
        tabela_carteira += "\n".join(f"| {t} | {p} | {v} | {pl} |" for t, p, v, pl in carteira_rows)
    else:
        tabela_carteira = "_Nenhum ativo na carteira ainda._"

    nota = f"""---
tags: [relatorio, snapshot, diario]
cssclasses: [node-relatorio]
data: {hoje}
---

# Market Snapshot — {hoje}

## Macro Global
{tabela_macro}

## Carteira — Posições Hoje
{tabela_carteira}

## Links
- [[carteira]] — posição completa
- [[snapshot-{ontem}]] — dia anterior
"""

    SNAPSHOTS_DIR.mkdir(parents=True, exist_ok=True)
    saida = SNAPSHOTS_DIR / f"snapshot-{hoje}.md"
    saida.write_text(nota, encoding="utf-8")
    print(f"\nSnapshot salvo em: {saida}")
    print(f"  Macro: {len(macro_rows)} indicadores | Carteira: {len(carteira_rows)} ativo(s)")


if __name__ == "__main__":
    gerar_snapshot()
