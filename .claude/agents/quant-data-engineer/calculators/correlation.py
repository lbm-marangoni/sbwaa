"""
Análise de correlação — SBWAA Quant/Data Engineer
"""
import pandas as pd
import numpy as np


def pares_alta_correlacao(corr_matrix: pd.DataFrame,
                          threshold: float = 0.7) -> list:
    """
    Retorna lista de pares com correlação acima do threshold.
    Alta correlação = diversificação reduzida.
    """
    pares = []
    tickers = corr_matrix.columns.tolist()
    for i in range(len(tickers)):
        for j in range(i + 1, len(tickers)):
            corr = corr_matrix.iloc[i, j]
            if pd.isna(corr):
                continue
            if abs(corr) >= threshold:
                pares.append({
                    "ativo_a": tickers[i],
                    "ativo_b": tickers[j],
                    "correlacao": round(float(corr), 3),
                    "tipo": "positiva" if corr > 0 else "negativa"
                })
    return sorted(pares, key=lambda x: abs(x["correlacao"]), reverse=True)


def diversificacao_efetiva(corr_matrix: pd.DataFrame) -> float:
    """
    Número efetivo de ativos independentes.
    1 / média(correlação²) — quanto mais próximo do nº real de ativos,
    melhor diversificado.
    """
    media_corr_sq = (corr_matrix ** 2).mean().mean()
    return 1 / media_corr_sq if media_corr_sq > 0 else 0


def correlacao_media(corr_matrix: pd.DataFrame) -> float:
    """Média das correlações fora da diagonal principal"""
    n = len(corr_matrix)
    if n < 2:
        return float("nan")
    mascara = ~np.eye(n, dtype=bool)
    valores = corr_matrix.values[mascara]
    return float(np.nanmean(valores))
