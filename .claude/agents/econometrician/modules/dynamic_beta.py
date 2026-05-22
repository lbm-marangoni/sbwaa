"""
dynamic_beta.py — Beta dinâmico via rolling OLS
SBWAA | Econometrician Agent

Calcula beta em janelas móveis (60d, 126d, 252d) para capturar
como a sensibilidade ao mercado evolui ao longo do tempo.
"""

import numpy as np
import pandas as pd
from typing import Optional


def _ols_beta(r_ativo: pd.Series, r_bench: pd.Series) -> tuple[float, float]:
    """
    Regressão OLS simples: r_ativo = alpha + beta * r_bench + eps
    Retorna (beta, r2)
    """
    df = pd.concat([r_ativo, r_bench], axis=1).dropna()
    if len(df) < 15:
        return float("nan"), float("nan")
    x = df.iloc[:, 1].values
    y = df.iloc[:, 0].values
    X = np.column_stack([np.ones(len(x)), x])
    try:
        coef, _, _, _ = np.linalg.lstsq(X, y, rcond=None)
        alpha, beta = coef
        y_hat = X @ coef
        ss_res = np.sum((y - y_hat) ** 2)
        ss_tot = np.sum((y - y.mean()) ** 2)
        r2 = 1 - ss_res / ss_tot if ss_tot > 0 else 0.0
        return round(float(beta), 4), round(float(r2), 4)
    except Exception:
        return float("nan"), float("nan")


def _tendencia_beta(betas: list[float]) -> str:
    """Detecta tendência nos últimos betas calculados."""
    validos = [b for b in betas if not np.isnan(b)]
    if len(validos) < 2:
        return "indefinida"
    delta = validos[-1] - validos[0]
    if delta > 0.10:
        return "crescente"
    if delta < -0.10:
        return "decrescente"
    return "estavel"


def calcular_beta_dinamico(retornos_ativo: pd.Series,
                            retornos_bench: pd.Series) -> dict:
    """
    Calcula betas em múltiplas janelas e série temporal do beta rolling.
    """
    janelas = {
        "beta_60d":  60,
        "beta_126d": 126,
        "beta_252d": 252,
    }
    resultado = {}
    betas_lista = []

    for chave, n in janelas.items():
        if len(retornos_ativo) >= n and len(retornos_bench) >= n:
            b, r2 = _ols_beta(retornos_ativo.iloc[-n:], retornos_bench.iloc[-n:])
            resultado[chave] = b
            resultado[f"r2_{n}d"] = r2
            betas_lista.append(b)
        else:
            resultado[chave] = None
            resultado[f"r2_{n}d"] = None

    resultado["tendencia"] = _tendencia_beta(betas_lista)

    # Beta estático (janela completa)
    b_full, r2_full = _ols_beta(retornos_ativo, retornos_bench)
    resultado["beta_estatico"] = b_full
    resultado["r2_estatico"] = r2_full

    # Série rolling 60d (últimos 12 meses)
    rolling_betas = []
    for i in range(len(retornos_ativo) - 59):
        janela_a = retornos_ativo.iloc[i:i+60]
        janela_b = retornos_bench.iloc[i:i+60]
        b, _ = _ols_beta(janela_a, janela_b)
        rolling_betas.append({
            "data": retornos_ativo.index[i+59].strftime("%Y-%m-%d")
            if hasattr(retornos_ativo.index[i+59], "strftime") else str(retornos_ativo.index[i+59]),
            "beta": b
        })
    resultado["rolling_60d_serie"] = rolling_betas[-252:]  # último ano

    return resultado
