"""
Calculadora de retornos — SBWAA Quant/Data Engineer
Todas as fórmulas documentadas explicitamente.
"""
import numpy as np
import pandas as pd


def retorno_total(prices: pd.Series) -> float:
    """(P_final / P_inicial) - 1"""
    return (prices.iloc[-1] / prices.iloc[0]) - 1


def retorno_anualizado(prices: pd.Series, dias: int) -> float:
    """(1 + retorno_total) ^ (252 / dias) - 1"""
    rt = retorno_total(prices)
    return (1 + rt) ** (252 / dias) - 1


def volatilidade_anualizada(prices: pd.Series) -> float:
    """std(retornos_diarios) × √252"""
    retornos_diarios = prices.pct_change().dropna()
    return retornos_diarios.std() * np.sqrt(252)


def sharpe(retorno_anual: float, volatilidade_anual: float,
           risk_free: float) -> float:
    """(Retorno_anual - Risk_free) / Volatilidade_anual"""
    if volatilidade_anual == 0:
        return 0.0
    return (retorno_anual - risk_free) / volatilidade_anual


def drawdown_maximo(prices: pd.Series) -> float:
    """min((P_t / max(P_0..P_t)) - 1)"""
    rolling_max = prices.cummax()
    drawdowns = (prices / rolling_max) - 1
    return drawdowns.min()


def beta(prices_ativo: pd.Series, prices_benchmark: pd.Series) -> float:
    """Cov(r_ativo, r_ibov) / Var(r_ibov)"""
    r_ativo = prices_ativo.pct_change().dropna()
    r_bench = prices_benchmark.pct_change().dropna()
    df = pd.concat([r_ativo, r_bench], axis=1).dropna()
    if len(df) < 20:
        return float("nan")
    cov_matrix = np.cov(df.iloc[:, 0], df.iloc[:, 1])
    var_bench = cov_matrix[1][1]
    if var_bench == 0:
        return float("nan")
    return cov_matrix[0][1] / var_bench


def retorno_periodo(prices: pd.Series, dias: int) -> float:
    """Retorno dos últimos N dias"""
    if len(prices) < dias:
        return float("nan")
    return (prices.iloc[-1] / prices.iloc[-dias]) - 1


def retorno_ytd(prices: pd.Series) -> float:
    """Retorno desde o início do ano corrente"""
    from datetime import date
    ano_atual = date.today().year
    prices_ano = prices[prices.index.year == ano_atual]
    if len(prices_ano) < 2:
        return float("nan")
    return retorno_total(prices_ano)
