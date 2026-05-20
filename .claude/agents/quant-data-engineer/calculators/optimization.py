"""
optimization.py — Otimização de portfólio (Fronteira Eficiente de Markowitz)
SBWAA Quant/Data Engineer

Calcula:
- Fronteira eficiente via Monte Carlo (10k simulações)
- Portfólio Max Sharpe (scipy.optimize)
- Portfólio Min Volatilidade (scipy.optimize)
- Posição atual na fronteira
- Sugestão de pesos para convergir ao Max Sharpe respeitando IPS
"""

import math
import numpy as np
import pandas as pd
from scipy.optimize import minimize


# ─── Métricas de portfólio ────────────────────────────────────────────────────

def _portfolio_stats(pesos: np.ndarray, retornos_anuais: np.ndarray,
                     cov_anual: np.ndarray, selic: float) -> tuple[float, float, float]:
    """Retorna (retorno, volatilidade, sharpe) para um vetor de pesos."""
    ret = float(np.dot(pesos, retornos_anuais))
    vol = float(np.sqrt(pesos @ cov_anual @ pesos))
    sh = (ret - selic) / vol if vol > 1e-9 else float("-inf")
    return ret, vol, sh


# ─── Monte Carlo — fronteira eficiente ───────────────────────────────────────

def fronteira_monte_carlo(retornos_anuais: np.ndarray, cov_anual: np.ndarray,
                          selic: float, n_sim: int = 10_000,
                          seed: int = 42) -> list[dict]:
    """
    Gera n_sim portfólios aleatórios e retorna lista de pontos na fronteira.
    Cada ponto: {retorno, volatilidade, sharpe, pesos}
    """
    rng = np.random.default_rng(seed)
    n = len(retornos_anuais)
    pontos = []
    for _ in range(n_sim):
        w = rng.random(n)
        w /= w.sum()
        ret, vol, sh = _portfolio_stats(w, retornos_anuais, cov_anual, selic)
        if math.isfinite(ret) and math.isfinite(vol) and vol > 0:
            pontos.append({
                "retorno_pct": round(ret * 100, 3),
                "volatilidade_pct": round(vol * 100, 3),
                "sharpe": round(sh, 3),
                "pesos": [round(float(x), 4) for x in w],
            })
    return pontos


# ─── Otimização exata (scipy) ────────────────────────────────────────────────

def _otimizar(retornos_anuais: np.ndarray, cov_anual: np.ndarray,
              selic: float, objetivo: str,
              limites_pct: list[tuple[float, float]] | None = None) -> dict | None:
    """
    objetivo: 'max_sharpe' | 'min_vol'
    limites_pct: lista de (min%, max%) por ativo, em decimal (ex: 0.0, 0.20)
    """
    n = len(retornos_anuais)
    bounds = limites_pct if limites_pct else [(0.0, 1.0)] * n
    constraints = [{"type": "eq", "fun": lambda w: w.sum() - 1.0}]
    w0 = np.array([1.0 / n] * n)

    if objetivo == "max_sharpe":
        def neg_sharpe(w):
            ret, vol, _ = _portfolio_stats(w, retornos_anuais, cov_anual, selic)
            return -(ret - selic) / vol if vol > 1e-9 else 1e6

        res = minimize(neg_sharpe, w0, method="SLSQP",
                       bounds=bounds, constraints=constraints,
                       options={"maxiter": 500, "ftol": 1e-9})
    else:  # min_vol
        def vol_obj(w):
            return float(np.sqrt(w @ cov_anual @ w))

        res = minimize(vol_obj, w0, method="SLSQP",
                       bounds=bounds, constraints=constraints,
                       options={"maxiter": 500, "ftol": 1e-9})

    if not res.success:
        return None

    w_opt = np.array(res.x)
    w_opt = np.clip(w_opt, 0, 1)
    w_opt /= w_opt.sum()
    ret, vol, sh = _portfolio_stats(w_opt, retornos_anuais, cov_anual, selic)
    return {
        "retorno_pct": round(ret * 100, 2),
        "volatilidade_pct": round(vol * 100, 2),
        "sharpe": round(sh, 3),
        "pesos": [round(float(x), 4) for x in w_opt],
        "convergiu": True,
    }


# ─── Sugestão de ajuste de pesos ─────────────────────────────────────────────

def sugestao_ajuste(tickers: list[str], pesos_atual: np.ndarray,
                    pesos_alvo: np.ndarray, threshold_pct: float = 2.0) -> list[dict]:
    """
    Retorna ajustes necessários (apenas onde |delta| >= threshold_pct).
    Ordenado do maior ajuste absoluto para o menor.
    """
    ajustes = []
    for i, t in enumerate(tickers):
        delta = (pesos_alvo[i] - pesos_atual[i]) * 100
        if abs(delta) >= threshold_pct:
            ajustes.append({
                "ticker": t,
                "peso_atual_pct": round(float(pesos_atual[i]) * 100, 1),
                "peso_alvo_pct": round(float(pesos_alvo[i]) * 100, 1),
                "delta_pct": round(delta, 1),
                "acao": "AUMENTAR" if delta > 0 else "REDUZIR",
            })
    return sorted(ajustes, key=lambda x: abs(x["delta_pct"]), reverse=True)


# ─── Função principal ─────────────────────────────────────────────────────────

def otimizar_carteira(tickers: list[str], retornos_df: pd.DataFrame,
                      pesos_atual: dict[str, float], selic: float,
                      limites_ips: dict[str, tuple[float, float]] | None = None,
                      n_sim: int = 10_000) -> dict:
    """
    Parâmetros:
        tickers       — lista ordenada de tickers presentes em retornos_df
        retornos_df   — DataFrame de retornos diários (já alinhado e sem NaN)
        pesos_atual   — {ticker: peso_decimal} — pesos reais da carteira
        selic         — taxa livre de risco anual (decimal)
        limites_ips   — {ticker: (min_decimal, max_decimal)} ou None
        n_sim         — número de simulações Monte Carlo

    Retorno: dict com seções monte_carlo, max_sharpe, min_vol, atual, ajustes
    """
    n = len(tickers)
    if n < 2:
        return {"erro": "Mínimo 2 ativos para otimização."}

    # Retornos anualizados e covariância anual
    ret_anuais = np.array([
        retornos_df[t].mean() * 252 for t in tickers
    ])
    cov_anual = retornos_df[tickers].cov().values * 252

    # Pesos atuais como array
    w_atual = np.array([pesos_atual.get(t, 0.0) for t in tickers])
    if w_atual.sum() > 0:
        w_atual = w_atual / w_atual.sum()

    # Limites por ativo (respeita IPS)
    bounds = None
    if limites_ips:
        bounds = [limites_ips.get(t, (0.0, 1.0)) for t in tickers]

    # Monte Carlo
    mc_pontos = fronteira_monte_carlo(ret_anuais, cov_anual, selic, n_sim)

    # Max Sharpe e Min Vol (scipy)
    max_sharpe = _otimizar(ret_anuais, cov_anual, selic, "max_sharpe", bounds)
    min_vol = _otimizar(ret_anuais, cov_anual, selic, "min_vol", bounds)

    # Posição atual
    ret_at, vol_at, sh_at = _portfolio_stats(w_atual, ret_anuais, cov_anual, selic)
    atual = {
        "retorno_pct": round(ret_at * 100, 2),
        "volatilidade_pct": round(vol_at * 100, 2),
        "sharpe": round(sh_at, 3) if math.isfinite(sh_at) else None,
        "pesos": {t: round(float(w_atual[i]) * 100, 1) for i, t in enumerate(tickers)},
    }

    # Ajustes sugeridos (atual → Max Sharpe)
    ajustes = []
    if max_sharpe:
        w_ms = np.array(max_sharpe["pesos"])
        ajustes = sugestao_ajuste(tickers, w_atual, w_ms, threshold_pct=2.0)

    # Resumo do upside
    ganho_sharpe = None
    if max_sharpe and atual["sharpe"]:
        ganho_sharpe = round(max_sharpe["sharpe"] - atual["sharpe"], 3)

    return {
        "tickers": tickers,
        "n_simulacoes": len(mc_pontos),
        "atual": atual,
        "max_sharpe": max_sharpe,
        "min_vol": min_vol,
        "ganho_sharpe_potencial": ganho_sharpe,
        "ajustes_sugeridos": ajustes,
        "fronteira_mc_resumo": {
            "melhor_sharpe_mc": max(mc_pontos, key=lambda p: p["sharpe"]) if mc_pontos else None,
            "menor_vol_mc": min(mc_pontos, key=lambda p: p["volatilidade_pct"]) if mc_pontos else None,
            "maior_retorno_mc": max(mc_pontos, key=lambda p: p["retorno_pct"]) if mc_pontos else None,
        },
    }
