"""
rolling_stats.py — Correlações rolling e estabilidade
SBWAA | Econometrician Agent

Calcula correlações em janelas móveis entre o ativo analisado e os demais
ativos da carteira, detecta instabilidade e períodos de correlação extrema.
"""

import numpy as np
import pandas as pd
from typing import Optional


def correlacao_rolling(r1: pd.Series, r2: pd.Series,
                        janela: int = 60) -> pd.Series:
    """Correlação de Pearson em janela móvel."""
    df = pd.concat([r1, r2], axis=1).dropna()
    if len(df) < janela:
        return pd.Series(dtype=float)
    return df.iloc[:, 0].rolling(janela).corr(df.iloc[:, 1]).dropna()


def _estabilidade(serie: pd.Series) -> str:
    """Classifica estabilidade da correlação rolling."""
    if serie.empty:
        return "indefinida"
    amplitude = serie.max() - serie.min()
    std = serie.std()
    if amplitude < 0.2 and std < 0.08:
        return "ESTAVEL"
    if amplitude < 0.4 and std < 0.15:
        return "MODERADA"
    return "INSTAVEL"


def calcular_correlacoes_rolling(retornos_ativo: pd.Series,
                                  retornos_carteira: dict[str, pd.Series]) -> dict:
    """
    Para cada ativo da carteira, calcula correlação rolling (60d e 252d)
    vs o ativo em análise.
    """
    if not retornos_carteira:
        return {"disponivel": False, "motivo": "Nenhum ativo na carteira para comparar"}

    resultado_60d  = {}
    resultado_252d = {}
    estabilidade   = {}
    alertas        = []

    for ticker, r_outro in retornos_carteira.items():
        if ticker == retornos_ativo.name:
            continue

        # Correlação pontual nas duas janelas
        df = pd.concat([retornos_ativo, r_outro], axis=1).dropna()
        if len(df) >= 60:
            resultado_60d[ticker] = round(
                float(df.iloc[-60:, 0].corr(df.iloc[-60:, 1])), 4
            )
        if len(df) >= 252:
            resultado_252d[ticker] = round(
                float(df.iloc[-252:, 0].corr(df.iloc[-252:, 1])), 4
            )

        # Série rolling 60d para estabilidade
        serie_roll = correlacao_rolling(retornos_ativo, r_outro, 60)
        if not serie_roll.empty:
            est = _estabilidade(serie_roll)
            estabilidade[ticker] = est
            corr_atual = resultado_60d.get(ticker, float("nan"))
            if abs(corr_atual) > 0.80:
                alertas.append(
                    f"{ticker}: correlação muito alta ({corr_atual:.2f}) — "
                    "diversificação comprometida"
                )
            if est == "INSTAVEL":
                alertas.append(
                    f"{ticker}: correlação instável — relação não confiável"
                )

    return {
        "disponivel": True,
        "correlacao_60d": resultado_60d,
        "correlacao_252d": resultado_252d,
        "estabilidade": estabilidade,
        "alertas": alertas,
    }
