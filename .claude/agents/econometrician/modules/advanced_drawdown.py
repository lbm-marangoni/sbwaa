"""
advanced_drawdown.py — Métricas avançadas de drawdown
SBWAA | Econometrician Agent

Calcula: Calmar Ratio, Ulcer Index, Pain Index,
tempo médio de recuperação, duração máxima de drawdown.
"""

import numpy as np
import pandas as pd


def _serie_drawdown(precos: pd.Series) -> pd.Series:
    """Drawdown relativo ao pico anterior em cada ponto."""
    pico = precos.cummax()
    return (precos / pico) - 1


def calmar_ratio(retorno_anualizado: float, max_dd: float) -> float:
    """Retorno anualizado / |Max Drawdown|. Mede retorno por unidade de dor máxima."""
    if max_dd == 0:
        return float("nan")
    return round(retorno_anualizado / abs(max_dd), 4)


def ulcer_index(precos: pd.Series) -> float:
    """
    Ulcer Index = sqrt(mean(drawdown²))
    Penaliza drawdowns profundos e longos mais que o max drawdown simples.
    """
    dd = _serie_drawdown(precos)
    return round(float(np.sqrt(np.mean(dd ** 2))) * 100, 4)  # em %


def pain_index(precos: pd.Series) -> float:
    """
    Pain Index = mean(|drawdown|)
    Média simples da magnitude dos drawdowns ao longo do período.
    """
    dd = _serie_drawdown(precos)
    return round(float(np.mean(np.abs(dd))) * 100, 4)  # em %


def tempo_recuperacao(precos: pd.Series) -> dict:
    """
    Analisa períodos de drawdown: início, mínimo, fim e duração.
    Retorna tempo médio de recuperação e duração máxima.
    """
    dd = _serie_drawdown(precos)
    em_dd = dd < 0

    periodos = []
    inicio = None

    for i, (idx, em) in enumerate(zip(dd.index, em_dd)):
        if em and inicio is None:
            inicio = i
        elif not em and inicio is not None:
            periodos.append({
                "inicio_idx": inicio,
                "fim_idx": i,
                "duracao_dias": i - inicio,
                "min_dd_pct": round(float(dd.iloc[inicio:i].min()) * 100, 2),
            })
            inicio = None

    if not periodos:
        return {
            "tempo_medio_recuperacao_dias": 0,
            "duracao_maxima_dias": 0,
            "n_periodos_dd": 0,
        }

    duracoes = [p["duracao_dias"] for p in periodos]
    return {
        "tempo_medio_recuperacao_dias": round(float(np.mean(duracoes)), 1),
        "duracao_maxima_dias": int(max(duracoes)),
        "n_periodos_dd": len(periodos),
    }


def calcular_drawdown_avancado(precos: pd.Series,
                                retorno_anualizado: float) -> dict:
    """Wrapper: calcula todas as métricas avançadas de drawdown."""
    if len(precos) < 30:
        return {"disponivel": False, "motivo": "Histórico insuficiente (<30 obs)"}

    dd = _serie_drawdown(precos)
    max_dd = float(dd.min())

    return {
        "disponivel": True,
        "max_drawdown_pct": round(max_dd * 100, 2),
        "drawdown_atual_pct": round(float(dd.iloc[-1]) * 100, 2),
        "calmar_ratio": calmar_ratio(retorno_anualizado, max_dd),
        "ulcer_index_pct": ulcer_index(precos),
        "pain_index_pct": pain_index(precos),
        **tempo_recuperacao(precos),
        "interpretacao": {
            "calmar_ratio": "Retorno anual / |Max DD|. Acima de 0.5 é razoável; >1.0 é bom.",
            "ulcer_index": "Raiz da média dos DD². Penaliza drawdowns profundos e prolongados.",
            "pain_index": "Média simples dos DD. Quanto o investidor 'sofreu' em média.",
        },
    }
