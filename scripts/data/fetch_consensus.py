"""
fetch_consensus.py — Consenso de analistas via yfinance (primário) + Investing.com (fallback).
Uso: python fetch_consensus.py TICKER  (ex: PETR4, XPML11)
"""

import sys
import json
import requests
from datetime import datetime, timedelta
from pathlib import Path

import yfinance as yf
from bs4 import BeautifulSoup

CACHE_DIR = Path(__file__).parent / "cache"
CACHE_DIR.mkdir(exist_ok=True)
CACHE_TTL_HORAS = 24

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "application/json, text/html, */*",
    "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
    "Referer": "https://www.investing.com/",
}


def _cache_valido(path: Path) -> bool:
    if not path.exists():
        return False
    return datetime.now() - datetime.fromtimestamp(path.stat().st_mtime) < timedelta(hours=CACHE_TTL_HORAS)


def _rec_label(rec_key: str | None, rec_score: float | None) -> str:
    if rec_key:
        mapa = {
            "strong_buy": "COMPRA FORTE",
            "buy": "COMPRA",
            "hold": "NEUTRO",
            "underperform": "ABAIXO DA MÉDIA",
            "sell": "VENDA",
        }
        return mapa.get(rec_key.lower(), rec_key.upper())
    if rec_score is not None:
        if rec_score <= 1.5:
            return "COMPRA FORTE"
        if rec_score <= 2.5:
            return "COMPRA"
        if rec_score <= 3.5:
            return "NEUTRO"
        if rec_score <= 4.5:
            return "ABAIXO DA MÉDIA"
        return "VENDA"
    return "N/D"


def buscar_yfinance(ticker: str) -> dict | None:
    ticker_yahoo = ticker if ticker.endswith(".SA") else f"{ticker}.SA"
    try:
        info = yf.Ticker(ticker_yahoo).info or {}
        target_mean = info.get("targetMeanPrice")
        rec_key = info.get("recommendationKey")
        rec_score = info.get("recommendationMean")
        num_analistas = info.get("numberOfAnalystOpinions")

        if not any([target_mean, rec_key, num_analistas]):
            return None

        cotacao = info.get("regularMarketPrice") or info.get("currentPrice")
        upside = None
        if target_mean and cotacao:
            upside = round((target_mean - cotacao) / cotacao * 100, 1)

        return {
            "fonte": "Yahoo Finance",
            "price_target_mean": target_mean,
            "price_target_high": info.get("targetHighPrice"),
            "price_target_low": info.get("targetLowPrice"),
            "cotacao_referencia": cotacao,
            "upside_consenso_pct": upside,
            "recomendacao_raw": rec_key,
            "recomendacao_score": rec_score,
            "recomendacao": _rec_label(rec_key, rec_score),
            "num_analistas": num_analistas,
        }
    except Exception:
        return None


def _buscar_slug_investing(ticker: str) -> str | None:
    try:
        url = "https://api.investing.com/api/search/v2/search"
        params = {"q": ticker, "domain": "br", "lang": "pt"}
        resp = requests.get(url, params=params, headers=HEADERS, timeout=8)
        if resp.status_code != 200:
            return None
        data = resp.json()
        for article in data.get("articles", []):
            link = article.get("link", "")
            if "/equities/" in link and article.get("type") == "equity":
                return link.split("/equities/")[-1].strip("/")
    except Exception:
        pass
    return None


def _scrape_investing(slug: str) -> dict | None:
    url = f"https://www.investing.com/equities/{slug}-consensus-estimates"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=12)
        if resp.status_code != 200:
            return None
        soup = BeautifulSoup(resp.text, "html.parser")

        resultado: dict = {"fonte": "Investing.com", "url": url}

        # Price target — tenta seletores comuns
        for sel in [
            "[data-test='consensusTarget']",
            ".consensusTarget",
            "[class*='target']",
            "[id*='target']",
        ]:
            el = soup.select_one(sel)
            if el:
                txt = el.get_text(strip=True).replace(",", ".").replace("R$", "").strip()
                try:
                    resultado["price_target_mean"] = float(txt)
                    break
                except ValueError:
                    pass

        # Recomendação
        for sel in [
            "[data-test='consensusRecommendation']",
            ".consensusRecommendation",
            "[class*='recommendation']",
            "[class*='consensus']",
        ]:
            el = soup.select_one(sel)
            if el:
                resultado["recomendacao"] = el.get_text(strip=True).upper()
                break

        # Número de analistas
        for sel in [
            "[data-test='analystCount']",
            ".analystCount",
            "[class*='analyst']",
        ]:
            el = soup.select_one(sel)
            if el:
                txt = el.get_text(strip=True).split()[0]
                try:
                    resultado["num_analistas"] = int(txt)
                    break
                except ValueError:
                    pass

        if resultado.get("price_target_mean") or resultado.get("recomendacao"):
            return resultado

    except Exception:
        pass
    return None


def buscar_consensus(ticker: str) -> dict:
    hoje = datetime.now().strftime("%Y-%m-%d")
    cache_path = CACHE_DIR / f"consensus_{ticker}_{hoje}.json"

    if _cache_valido(cache_path):
        return json.loads(cache_path.read_text(encoding="utf-8"))

    envelope: dict = {
        "ticker": ticker,
        "atualizado_em": datetime.now().isoformat(timespec="seconds"),
        "disponivel": False,
        "aviso": None,
        "dados": None,
    }

    # Tier 1: yfinance
    dados = buscar_yfinance(ticker)
    if dados:
        envelope["disponivel"] = True
        envelope["dados"] = dados
    else:
        # Tier 2: Investing.com
        slug = _buscar_slug_investing(ticker)
        if slug:
            dados = _scrape_investing(slug)
            if dados:
                envelope["disponivel"] = True
                envelope["dados"] = dados

    if not envelope["disponivel"]:
        envelope["aviso"] = "Sem cobertura de analistas disponível para este ativo (yfinance sem dados; Investing.com inacessível ou ativo sem cobertura)."

    cache_path.write_text(json.dumps(envelope, ensure_ascii=False, indent=2), encoding="utf-8")
    return envelope


def exibir_resumo(envelope: dict) -> None:
    print(f"\n  Consenso — {envelope['ticker']}")
    print(f"  {'─' * 42}")
    if not envelope["disponivel"]:
        print(f"  ⚠️  {envelope['aviso']}")
        return
    d = envelope["dados"]
    print(f"  Fonte:           {d.get('fonte', 'N/D')}")
    print(f"  # Analistas:     {d.get('num_analistas', 'N/D')}")
    print(f"  Target Médio:    {d.get('price_target_mean', 'N/D')}")
    print(f"  Target Alto:     {d.get('price_target_high', 'N/D')}")
    print(f"  Target Baixo:    {d.get('price_target_low', 'N/D')}")
    print(f"  Upside Consenso: {d.get('upside_consenso_pct', 'N/D')}%")
    print(f"  Recomendação:    {d.get('recomendacao', 'N/D')}")


def main():
    if len(sys.argv) < 2:
        print("Uso: python fetch_consensus.py TICKER")
        sys.exit(1)
    ticker = sys.argv[1].upper()
    print(f"\nBuscando consenso de analistas para {ticker}...")
    envelope = buscar_consensus(ticker)
    exibir_resumo(envelope)


if __name__ == "__main__":
    main()
