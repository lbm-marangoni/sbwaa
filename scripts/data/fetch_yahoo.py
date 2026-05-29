"""
fetch_yahoo.py — Busca cotações, macro e histórico via Yahoo Finance.
Uso: python fetch_yahoo.py VT IVV BOVA11 BRL=X CL=F
     python fetch_yahoo.py --macro   (busca todos os tickers macro padrão)
"""

import sys
import json
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
import yfinance as yf

CACHE_DIR = Path(__file__).parent / "cache"
CACHE_DIR.mkdir(exist_ok=True)
CACHE_TTL_HORAS = 4

MACRO_TICKERS = {
    "IBOV": "^BVSP",
    "SP500": "^GSPC",
    "NASDAQ": "^IXIC",
    "DXY": "DX-Y.NYB",
    "BRL_USD": "BRL=X",
    "PETROLEO_WTI": "CL=F",
    "OURO": "GC=F",
    "JUROS_US_10Y": "^TNX",
}


def cache_valido(caminho: Path) -> bool:
    if not caminho.exists():
        return False
    modificado = datetime.fromtimestamp(caminho.stat().st_mtime)
    return datetime.now() - modificado < timedelta(hours=CACHE_TTL_HORAS)


def buscar_ticker(ticker_yahoo: str, nome_alias: str = "") -> dict:
    ticker_safe = ticker_yahoo.replace("^", "INDICE_").replace("=", "_").replace("-", "_")
    hoje = datetime.now().strftime("%Y-%m-%d")
    cache_json = CACHE_DIR / f"yahoo_{ticker_safe}_{hoje}.json"
    cache_hist = CACHE_DIR / f"hist_{ticker_safe}_{hoje}.csv"

    if cache_valido(cache_json):
        with open(cache_json, "r", encoding="utf-8") as f:
            print(f"  [{ticker_yahoo}] Usando cache")
            return json.load(f)

    try:
        ativo = yf.Ticker(ticker_yahoo)
        info = ativo.info or {}
        hist = ativo.history(period="1y")
    except Exception as e:
        raise ValueError(f"Erro ao buscar {ticker_yahoo} no Yahoo Finance: {e}")

    cotacao = info.get("regularMarketPrice") or info.get("currentPrice") or info.get("previousClose")
    variacao = info.get("regularMarketChangePercent")
    if variacao is None:
        prev = info.get("previousClose")
        if cotacao and prev and prev != 0:
            variacao = round((cotacao - prev) / prev * 100, 2)

    dados = {
        "ticker_yahoo": ticker_yahoo,
        "nome": nome_alias or info.get("longName") or info.get("shortName") or ticker_yahoo,
        "tipo": info.get("quoteType", "").lower(),
        "cotacao_atual": cotacao,
        "variacao_dia_pct": round(variacao, 2) if variacao is not None else None,
        "moeda": info.get("currency", ""),
        "historico_disponivel": not hist.empty,
        "fonte": "yahoo_finance",
        "atualizado_em": datetime.now().isoformat(timespec="seconds"),
    }

    if not hist.empty:
        hist.to_csv(cache_hist)

    with open(cache_json, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)

    return dados


def buscar_brl_usd() -> float | None:
    """Retorna cotação BRL/USD atual (quanto reais por 1 dólar)."""
    try:
        dados = buscar_ticker("BRL=X", "BRL/USD")
        v = dados.get("cotacao_atual")
        return float(v) if v else None
    except Exception:
        return None


def exibir_resumo(dados: dict) -> None:
    d = dados
    var = f"{d['variacao_dia_pct']:+.2f}%" if d["variacao_dia_pct"] is not None else "—"
    print(f"  {d['ticker_yahoo']:<14} {d['nome']:<25} {str(d['cotacao_atual']):<12} {var}")


def main():
    args = sys.argv[1:]
    if not args:
        print("Uso: python fetch_yahoo.py TICKER1 TICKER2 ...")
        print("     python fetch_yahoo.py --macro")
        sys.exit(1)

    if "--macro" in args:
        tickers = list(MACRO_TICKERS.values())
        aliases = {v: k for k, v in MACRO_TICKERS.items()}
    else:
        tickers = [t.upper() for t in args]
        aliases = {}

    print(f"\n{'Ticker':<14} {'Nome':<25} {'Cotação':<12} {'Variação'}")
    print("-" * 65)

    resultados = {}
    for ticker in tickers:
        try:
            dados = buscar_ticker(ticker, aliases.get(ticker, ""))
            exibir_resumo(dados)
            resultados[ticker] = dados
        except ValueError as e:
            print(f"  AVISO: {e}")

    print(f"\n{len(resultados)}/{len(tickers)} ticker(s) processado(s) com sucesso.")
    return resultados


if __name__ == "__main__":
    main()
