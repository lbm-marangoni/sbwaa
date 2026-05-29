"""
run_quant.py — Executa o agente Quant/Data Engineer do SBWAA.
Uso: python run_quant.py
"""

import re
import sys
import json
import math
import subprocess
from datetime import datetime, date
from pathlib import Path

import numpy as np
import pandas as pd
import yfinance as yf

AGENT_DIR = Path(__file__).parent
PROJECT_ROOT = AGENT_DIR.parent.parent.parent
VAULT_ROOT = PROJECT_ROOT / "vault"
SCRIPTS_DATA = PROJECT_ROOT / "scripts" / "data"
SKILL_PATH = AGENT_DIR / "SKILL.md"
CACHE_DIR = SCRIPTS_DATA / "cache"
RISK_DIR = VAULT_ROOT / "05-risk" / "snapshots"

sys.path.insert(0, str(AGENT_DIR))
from calculators.returns import (retorno_total, retorno_anualizado,
                                  volatilidade_anualizada, sharpe,
                                  drawdown_maximo, beta as calc_beta,
                                  retorno_periodo, retorno_ytd)
from calculators.portfolio_metrics import (volatilidade_carteira,
                                            matriz_correlacao,
                                            contribuicao_risco,
                                            retorno_ponderado,
                                            beta_carteira, hhi,
                                            drawdown_carteira_historico)
from calculators.correlation import (pares_alta_correlacao,
                                      diversificacao_efetiva,
                                      correlacao_media)
from calculators.optimization import otimizar_carteira

CARTEIRA_PATH = VAULT_ROOT / "00-portfolio" / "carteira.md"
IBOV_TICKER = "^BVSP"
SELIC_PADRAO = 0.1275

# Tipos sem cotação em bolsa — excluídos do quant (sem série histórica no yfinance)
TIPOS_RF_SKIP = {
    "⬜ RF", "🟪 TD", "🟫 DEB", "🟧 CRI/CRA",
    "RF", "TD", "DEB", "CRI/CRA",
}
TICKERS_ESPECIAIS_SKIP = {"RF-OPRT"}


# ─── Helpers ──────────────────────────────────────────────────────────────────

def eh_ticker_br(ticker: str) -> bool:
    return bool(re.match(r"^[A-Z]{4}[0-9]{1,2}[FBP]?$", ticker))


def ticker_yahoo(ticker: str) -> str:
    """Converte ticker BR para formato Yahoo Finance."""
    if eh_ticker_br(ticker):
        return f"{ticker}.SA"
    return ticker


def extrair_carteira() -> dict:
    """
    Retorna {ticker: peso_decimal} lendo Ticker e Tipo da carteira.md.
    Filtra tipos RF/TD/DEB/CRI-CRA (sem histórico em bolsa).
    """
    tickers = []
    if not CARTEIRA_PATH.exists():
        return {}
    conteudo = CARTEIRA_PATH.read_text(encoding="utf-8")
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
            if len(celulas) >= 1:
                t = celulas[0].replace("[[", "").replace("]]", "").split("|")[0].strip()
                t = re.sub(r"01-ativos/([^/]+)/tese", r"\1", t).upper()
                tipo = celulas[1].strip() if len(celulas) >= 2 else ""
                # Pula RF/TD/DEB/CRI-CRA e tickers especiais sem histórico em bolsa
                if t and t not in TICKERS_ESPECIAIS_SKIP and tipo not in TIPOS_RF_SKIP:
                    tickers.append(t)
        elif dentro and stripped:
            # Linha não-vazia e não-pipe dentro da tabela = fim da tabela
            break
        # Linhas em branco dentro da tabela são silenciosamente ignoradas
    n = len(tickers)
    if n == 0:
        return {}
    peso = round(1.0 / n, 6)
    return {t: peso for t in tickers}


def buscar_historico(ticker_yf: str) -> pd.Series | None:
    """Busca série histórica de fechamento ajustado via yfinance."""
    try:
        hist = yf.download(ticker_yf, period="1y", auto_adjust=True,
                           progress=False, threads=False)
        if hist.empty:
            return None
        close = hist["Close"]
        if isinstance(close, pd.DataFrame):
            close = close.iloc[:, 0]
        close = close.dropna()
        return close if len(close) >= 20 else None
    except Exception as e:
        print(f"  AVISO [{ticker_yf}]: {e}")
        return None


def calcular_selic() -> float:
    """Tenta extrair Selic do snapshot macro mais recente."""
    snap_dir = VAULT_ROOT / "02-relatorios" / "diarios"
    snapshots = sorted(snap_dir.glob("snapshot-*.md"), reverse=True)
    for snap in snapshots[:3]:
        conteudo = snap.read_text(encoding="utf-8")
        m = re.search(r"Selic[^\d]*(\d+[\.,]\d+)%", conteudo, re.IGNORECASE)
        if m:
            try:
                return float(m.group(1).replace(",", ".")) / 100
            except ValueError:
                pass
    return SELIC_PADRAO


# ─── Main ──────────────────────────────────────────────────────────────────────

def main():
    hoje = datetime.now().strftime("%Y-%m-%d")
    print(f"Quant/Data Engineer — {hoje}")
    print("=" * 50)

    carteira = extrair_carteira()
    if not carteira:
        print("Carteira vazia — nenhum ativo para calcular.")
        carteira_vazia = {
            "data_calculo": hoje,
            "periodo_historico_dias": 0,
            "selic_anual": SELIC_PADRAO,
            "ativos": {},
            "carteira": {"retorno_ponderado_pct": None, "volatilidade_pct": None,
                         "sharpe": None, "drawdown_maximo_pct": None,
                         "beta_ibov": None, "num_ativos": 0},
            "matriz_correlacao": {},
            "contribuicao_risco": {},
        }
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        cache_path = CACHE_DIR / f"quant_{hoje}.json"
        cache_path.write_text(json.dumps(carteira_vazia, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"JSON salvo: {cache_path}")
        return carteira_vazia

    selic = calcular_selic()
    print(f"Selic: {selic*100:.2f}% | Ativos: {list(carteira.keys())}")

    # Carregar histórico IBOV (benchmark)
    print("Carregando IBOV...")
    hist_ibov = buscar_historico(IBOV_TICKER)

    # Carregar históricos dos ativos
    historicos = {}
    for ticker in carteira:
        ty = ticker_yahoo(ticker)
        print(f"  Carregando {ticker} ({ty})...")
        h = buscar_historico(ty)
        if h is not None:
            historicos[ticker] = h
        else:
            print(f"  AVISO: histórico não disponível para {ticker}")

    if not historicos:
        print("Nenhum histórico disponível. Salvando JSON vazio e encerrando.")
        carteira_sem_dados = {
            "data_calculo": hoje,
            "periodo_historico_dias": 0,
            "selic_anual": selic,
            "ativos": {},
            "carteira": {"retorno_ponderado_pct": None, "volatilidade_pct": None,
                         "sharpe": None, "drawdown_maximo_pct": None,
                         "beta_ibov": None, "num_ativos": 0},
            "matriz_correlacao": {},
            "contribuicao_risco": {},
            "pares_alta_correlacao": [],
        }
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        cache_path = CACHE_DIR / f"quant_{hoje}.json"
        cache_path.write_text(json.dumps(carteira_sem_dados, ensure_ascii=False, indent=2), encoding="utf-8")
        return carteira_sem_dados

    # ── Métricas por ativo ────────────────────────────────────────────────────
    metricas_ativos = {}
    retornos_dict = {}

    for ticker, prices in historicos.items():
        dias = len(prices)
        r_total = retorno_total(prices)
        r_anual = retorno_anualizado(prices, dias)
        vol = volatilidade_anualizada(prices)
        sh = sharpe(r_anual, vol, selic)
        dd = drawdown_maximo(prices)
        beta_v = calc_beta(prices, hist_ibov) if hist_ibov is not None else float("nan")

        # Correlação direta com IBOV
        corr_ibov_val = None
        if hist_ibov is not None:
            r_ativo = prices.pct_change().dropna()
            r_ibov  = hist_ibov.pct_change().dropna()
            df_pair = pd.concat([r_ativo, r_ibov], axis=1).dropna()
            if len(df_pair) >= 20:
                c = df_pair.iloc[:, 0].corr(df_pair.iloc[:, 1])
                corr_ibov_val = round(float(c), 3) if not math.isnan(c) else None

        metricas_ativos[ticker] = {
            "retorno_total_pct": round(r_total * 100, 2),
            "retorno_anualizado_pct": round(r_anual * 100, 2),
            "volatilidade_anualizada_pct": round(vol * 100, 2),
            "sharpe": round(sh, 3) if not math.isnan(sh) else None,
            "beta_ibov": round(beta_v, 3) if not math.isnan(beta_v) else None,
            "correlacao_ibov": corr_ibov_val,
            "drawdown_maximo_pct": round(dd * 100, 2),
            "retorno_1m": safe_pct(retorno_periodo(prices, 21)),
            "retorno_3m": safe_pct(retorno_periodo(prices, 63)),
            "retorno_6m": safe_pct(retorno_periodo(prices, 126)),
            "retorno_12m": safe_pct(retorno_periodo(prices, 252)),
            "retorno_ytd": safe_pct(retorno_ytd(prices)),
            "peso_carteira_pct": round(carteira[ticker] * 100, 2),
            "dias_historico": dias,
        }

        # Retornos diários para cálculos de carteira
        retornos_dict[ticker] = prices.pct_change().dropna()

    # ── Métricas de carteira ──────────────────────────────────────────────────
    retornos_df = pd.DataFrame(retornos_dict).dropna()
    pesos_array = np.array([carteira[t] for t in retornos_df.columns])
    pesos_norm = pesos_array / pesos_array.sum()

    corr_matrix = matriz_correlacao(retornos_df)
    cov_matrix = retornos_df.cov().values
    vol_cart = volatilidade_carteira(pesos_norm, cov_matrix)

    ret_ponderado = retorno_ponderado(
        {t: metricas_ativos[t]["retorno_anualizado_pct"] / 100 for t in metricas_ativos},
        {t: carteira[t] for t in carteira}
    )
    sh_cart = sharpe(ret_ponderado, vol_cart, selic)

    betas = {t: metricas_ativos[t].get("beta_ibov") or float("nan")
             for t in metricas_ativos}
    beta_cart = beta_carteira(betas, carteira)

    retornos_carteira = (retornos_df * pesos_norm).sum(axis=1)
    dd_cart = drawdown_carteira_historico(retornos_carteira)

    contrib_risco = contribuicao_risco(pesos_norm, cov_matrix)
    contrib_dict = {t: round(float(c) * 100, 2)
                    for t, c in zip(retornos_df.columns, contrib_risco)}

    # Correlação
    corr_dict = {}
    for i, ti in enumerate(corr_matrix.index):
        corr_dict[ti] = {}
        for j, tj in enumerate(corr_matrix.columns):
            v = corr_matrix.iloc[i, j]
            corr_dict[ti][tj] = round(float(v), 3) if not math.isnan(v) else None

    # ── Otimização de portfólio (Fronteira Eficiente) ────────────────────────
    tickers_opt = list(retornos_df.columns)
    print("Calculando fronteira eficiente (10k simulações)...")
    try:
        otimizacao = otimizar_carteira(
            tickers=tickers_opt,
            retornos_df=retornos_df,
            pesos_atual={t: carteira.get(t, 0.0) for t in tickers_opt},
            selic=selic,
            limites_ips=None,  # sem limites por ativo por padrão
        )
    except Exception as e:
        print(f"  AVISO: otimização falhou — {e}")
        otimizacao = {"erro": str(e)}

    metricas_json = {
        "data_calculo": hoje,
        "periodo_historico_dias": len(retornos_df),
        "selic_anual": selic,
        "ativos": metricas_ativos,
        "carteira": {
            "retorno_ponderado_pct": round(ret_ponderado * 100, 2),
            "volatilidade_pct": round(vol_cart * 100, 2),
            "sharpe": round(sh_cart, 3) if not math.isnan(sh_cart) else None,
            "drawdown_maximo_pct": round(dd_cart * 100, 2),
            "beta_ibov": round(beta_cart, 3) if not math.isnan(beta_cart) else None,
            "num_ativos": len(historicos),
            "hhi": round(hhi(carteira), 4),
            "corr_media": round(correlacao_media(corr_matrix), 3),
            "diversificacao_efetiva": round(diversificacao_efetiva(corr_matrix), 2),
        },
        "matriz_correlacao": corr_dict,
        "contribuicao_risco": contrib_dict,
        "pares_alta_correlacao": pares_alta_correlacao(corr_matrix, threshold=0.7),
        "otimizacao": otimizacao,
    }

    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_path = CACHE_DIR / f"quant_{hoje}.json"
    cache_path.write_text(json.dumps(metricas_json, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nJSON salvo: {cache_path}")
    # Síntese textual é feita pelo Claude Code ao ler o cache — não via API direta.

    return metricas_json


def safe_pct(val):
    if val is None or (isinstance(val, float) and (math.isnan(val) or math.isinf(val))):
        return None
    return round(float(val) * 100, 2)


if __name__ == "__main__":
    main()
