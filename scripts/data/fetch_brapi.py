"""
fetch_brapi.py — Busca cotações e fundamentalistas de ativos BR via Brapi.
Uso: python fetch_brapi.py PETR4 VALE3 MXRF11
"""

import sys
import json
import time
import requests
from datetime import datetime, timedelta
from pathlib import Path

CACHE_DIR = Path(__file__).parent / "cache"
CACHE_DIR.mkdir(exist_ok=True)
CACHE_TTL_HORAS = 4

BASE_URL = "https://brapi.dev/api/quote/{ticker}?modules=summaryProfile,defaultKeyStatistics,financialData,balanceSheetHistory"


def cache_valido(caminho: Path) -> bool:
    if not caminho.exists():
        return False
    modificado = datetime.fromtimestamp(caminho.stat().st_mtime)
    return datetime.now() - modificado < timedelta(hours=CACHE_TTL_HORAS)


def buscar_ticker(ticker: str) -> dict:
    ticker = ticker.upper().strip()
    hoje = datetime.now().strftime("%Y-%m-%d")
    cache_path = CACHE_DIR / f"brapi_{ticker}_{hoje}.json"

    if cache_valido(cache_path):
        with open(cache_path, "r", encoding="utf-8") as f:
            print(f"  [{ticker}] Usando cache ({cache_path.name})")
            return json.load(f)

    url = BASE_URL.format(ticker=ticker)
    try:
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
    except requests.exceptions.HTTPError as e:
        raise ValueError(f"Erro HTTP ao buscar {ticker}: {e}")
    except requests.exceptions.ConnectionError:
        raise ValueError(f"Erro de conexão ao buscar {ticker}. Verifique sua internet.")
    except requests.exceptions.Timeout:
        raise ValueError(f"Timeout ao buscar {ticker}. Tente novamente.")

    raw = resp.json()
    resultados = raw.get("results", [])
    if not resultados:
        raise ValueError(f"Ticker {ticker} não encontrado na Brapi.")

    r = resultados[0]
    modulos = r.get("summaryProfile", {}) or {}
    stats = r.get("defaultKeyStatistics", {}) or {}
    financials = r.get("financialData", {}) or {}

    dividendos_raw = r.get("dividendsData", {}) or {}
    cash_dividends = dividendos_raw.get("cashDividends", []) or []
    dividendos_recentes = [
        {"data": d.get("paymentDate", ""), "valor": round(d.get("rate", 0), 4)}
        for d in sorted(cash_dividends, key=lambda x: x.get("paymentDate", ""), reverse=True)[:3]
    ]

    dados = {
        "ticker": ticker,
        "tipo": "",
        "nome": r.get("longName") or r.get("shortName") or ticker,
        "setor": modulos.get("sector") or modulos.get("industry") or "",
        "cotacao": r.get("regularMarketPrice"),
        "variacao_dia_pct": r.get("regularMarketChangePercent"),
        "volume": r.get("regularMarketVolume"),
        "pl": stats.get("trailingPE") or r.get("priceEarnings"),
        "ev_ebitda": stats.get("enterpriseToEbitda"),
        "pvp": stats.get("priceToBook"),
        "dy": r.get("dividendYield"),
        "roe": financials.get("returnOnEquity"),
        "divida_liquida_ebitda": None,
        "dividendos_recentes": dividendos_recentes,
        "fonte": "brapi",
        "atualizado_em": datetime.now().isoformat(timespec="seconds"),
    }

    with open(cache_path, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)

    return dados


def exibir_resumo(dados: dict) -> None:
    t = dados
    print(f"\n{'='*50}")
    print(f"  Ticker : {t['ticker']}  |  {t['nome']}")
    print(f"  Setor  : {t['setor'] or '—'}")
    print(f"  Cotação: R$ {t['cotacao']}  ({t['variacao_dia_pct']:+.2f}%)" if t['cotacao'] and t['variacao_dia_pct'] else f"  Cotação: —")
    print(f"  P/L    : {t['pl'] or '—'}  |  P/VP: {t['pvp'] or '—'}  |  DY: {t['dy'] or '—'}%")
    if t["dividendos_recentes"]:
        print(f"  Últimos dividendos:")
        for d in t["dividendos_recentes"]:
            print(f"    {d['data']}  R$ {d['valor']}")
    print(f"{'='*50}")


def main():
    tickers = [t.upper() for t in sys.argv[1:] if t]
    if not tickers:
        print("Uso: python fetch_brapi.py TICKER1 TICKER2 ...")
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
        time.sleep(0.5)

    print(f"\n{len(resultados)}/{len(tickers)} ticker(s) processado(s) com sucesso.")
    return resultados


if __name__ == "__main__":
    main()
