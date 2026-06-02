"""
fetch_fundamentals.py — Busca fundamentalistas de ativos BR via Yahoo Finance (yfinance).
Substitui fetch_brapi.py. Mesmo formato de saída, sem dependência de API key.
Uso: python fetch_fundamentals.py PETR4 VALE3 XPML11
"""

import sys
import json
import time
from datetime import datetime, timedelta
from pathlib import Path

import yfinance as yf

from cache_manager import CACHE_DIR, is_valid as cache_valido


def buscar_ticker(ticker: str) -> dict:
    ticker = ticker.upper().strip()
    hoje = datetime.now().strftime("%Y-%m-%d")
    cache_path = CACHE_DIR / f"fundamentals_{ticker}_{hoje}.json"

    if cache_valido(cache_path):
        with open(cache_path, "r", encoding="utf-8") as f:
            print(f"  [{ticker}] Usando cache ({cache_path.name})")
            return json.load(f)

    ticker_yf = f"{ticker}.SA"
    print(f"  [{ticker}] Buscando via Yahoo Finance ({ticker_yf})...")

    try:
        ativo = yf.Ticker(ticker_yf)
        info = ativo.info or {}
        hist_divs = ativo.dividends
    except Exception as e:
        raise ValueError(f"Erro ao buscar {ticker} no Yahoo Finance: {e}")

    if not info or not info.get("regularMarketPrice") and not info.get("currentPrice"):
        raise ValueError(f"Ticker {ticker} não encontrado no Yahoo Finance ({ticker_yf}).")

    # Dividend history
    dividendos_historico = []
    dividendos_recentes = []
    if hist_divs is not None and len(hist_divs) > 0:
        for dt, valor in hist_divs.items():
            if valor > 0:
                dividendos_historico.append({
                    "data": str(dt)[:10],
                    "valor": round(float(valor), 6),
                    "tipo": "Dividendo",
                })
        dividendos_historico.sort(key=lambda x: x["data"])
        dividendos_recentes = [
            {"data": d["data"], "valor": d["valor"]}
            for d in reversed(dividendos_historico[-3:])
        ]

    cotacao = (
        info.get("currentPrice")
        or info.get("regularMarketPrice")
        or info.get("previousClose")
    )
    variacao = info.get("regularMarketChangePercent")
    if variacao is None:
        prev = info.get("previousClose")
        if cotacao and prev and prev != 0:
            variacao = round((cotacao - prev) / prev * 100, 4)

    dy_raw = info.get("dividendYield")
    # Yahoo Finance retorna dividendYield como decimal (0.10) para a maioria dos ativos,
    # mas para alguns ativos BR retorna já como percentual (10.32). Normaliza para %.
    if dy_raw is not None:
        dy_pct = round(dy_raw if dy_raw > 1 else dy_raw * 100, 4)
    else:
        dy_pct = None

    roe_raw = info.get("returnOnEquity")
    roe_pct = round(roe_raw * 100, 4) if roe_raw else None

    dados = {
        "ticker": ticker,
        "tipo": "",
        "nome": info.get("longName") or info.get("shortName") or ticker,
        "setor": info.get("sector") or info.get("industry") or "",
        "cotacao": cotacao,
        "variacao_dia_pct": variacao,
        "volume": info.get("regularMarketVolume") or info.get("averageVolume"),
        "pl": info.get("trailingPE") or info.get("forwardPE"),
        "ev_ebitda": info.get("enterpriseToEbitda"),
        "pvp": info.get("priceToBook"),
        "dy": dy_pct,
        "roe": roe_pct,
        "divida_liquida_ebitda": info.get("debtToEquity"),
        "dividendos_recentes": dividendos_recentes,
        "dividendos_historico": dividendos_historico,
        "fonte": "yahoo_finance",
        "atualizado_em": datetime.now().isoformat(timespec="seconds"),
        # Campos extras vs brapi
        "market_cap": info.get("marketCap"),
        "volume_medio_3m": info.get("averageVolume"),
        "beta": info.get("beta"),
        "52w_high": info.get("fiftyTwoWeekHigh"),
        "52w_low": info.get("fiftyTwoWeekLow"),
        "pvp_book_value": info.get("bookValue"),
        "eps_trailing": info.get("trailingEps"),
        "eps_forward": info.get("forwardEps"),
        "payout_ratio": info.get("payoutRatio"),
    }

    with open(cache_path, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)
    print(f"  [{ticker}] OK — salvo em {cache_path.name}")
    return dados


def exibir_resumo(dados: dict) -> None:
    t = dados
    cotacao_str = f"R$ {t['cotacao']}" if t["cotacao"] else "—"
    var_str = f"({t['variacao_dia_pct']:+.2f}%)" if t["variacao_dia_pct"] is not None else ""
    print(f"\n{'='*50}")
    print(f"  Ticker : {t['ticker']}  |  {t['nome']}")
    print(f"  Setor  : {t['setor'] or '—'}")
    print(f"  Cotação: {cotacao_str} {var_str}")
    print(f"  P/L    : {t['pl'] or '—'}  |  P/VP: {t['pvp'] or '—'}  |  DY: {t['dy'] or '—'}%")
    if t["dividendos_recentes"]:
        print("  Últimos dividendos:")
        for d in t["dividendos_recentes"]:
            print(f"    {d['data']}  R$ {d['valor']}")
    print(f"{'='*50}")


def main():
    tickers = [t.upper() for t in sys.argv[1:] if t]
    if not tickers:
        print("Uso: python fetch_fundamentals.py TICKER1 TICKER2 ...")
        sys.exit(1)

    resultados = {}
    for ticker in tickers:
        print(f"\nBuscando {ticker}...")
        try:
            dados = buscar_ticker(ticker)
            exibir_resumo(dados)
            resultados[ticker] = dados
        except ValueError as e:
            print(f"  AVISO: {e}")
        time.sleep(0.3)

    print(f"\n{len(resultados)}/{len(tickers)} ticker(s) processado(s) com sucesso.")
    return resultados


if __name__ == "__main__":
    main()
