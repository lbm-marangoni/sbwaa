"""
Métricas de portfólio — SBWAA Quant/Data Engineer
"""
import numpy as np
import pandas as pd


def volatilidade_carteira(pesos: np.ndarray,
                          matriz_cov: np.ndarray) -> float:
    """
    σ_carteira = √(w' × Σ × w)
    onde w = vetor de pesos, Σ = matriz de covariância dos retornos
    Multiplicar por √252 para anualizar.
    """
    return np.sqrt(pesos @ matriz_cov @ pesos) * np.sqrt(252)


def matriz_correlacao(retornos_df: pd.DataFrame) -> pd.DataFrame:
    """Matriz de correlação de Pearson entre todos os ativos"""
    return retornos_df.corr()


def contribuicao_risco(pesos: np.ndarray,
                       matriz_cov: np.ndarray) -> np.ndarray:
    """
    RC_i = w_i × (Σ × w)_i / σ_carteira²
    Contribuição marginal de cada ativo para a variância total.
    Retorna vetor de frações (soma = 1).
    """
    variancia_cart = pesos @ matriz_cov @ pesos
    if variancia_cart == 0:
        return np.zeros_like(pesos)
    marginal = matriz_cov @ pesos
    return (pesos * marginal) / variancia_cart


def retorno_ponderado(retornos: dict, pesos: dict) -> float:
    """Σ(w_i × r_i) para todos os ativos"""
    total = 0.0
    for ticker, retorno in retornos.items():
        peso = pesos.get(ticker, 0)
        if not (np.isnan(retorno) or np.isnan(peso)):
            total += peso * retorno
    return total


def beta_carteira(betas: dict, pesos: dict) -> float:
    """β_carteira = Σ(w_i × β_i)"""
    total = 0.0
    peso_valido = 0.0
    for ticker, b in betas.items():
        p = pesos.get(ticker, 0)
        if not np.isnan(b):
            total += p * b
            peso_valido += p
    return total / peso_valido if peso_valido > 0 else float("nan")


def hhi(pesos: dict) -> float:
    """
    Índice Herfindahl-Hirschman: Σ(peso_i²)
    Próximo de 0 = bem diversificado | próximo de 1 = concentrado
    """
    return sum(p ** 2 for p in pesos.values())


def drawdown_carteira_historico(retornos_carteira: pd.Series) -> float:
    """Drawdown máximo histórico da série de retornos da carteira"""
    cum = (1 + retornos_carteira).cumprod()
    rolling_max = cum.cummax()
    dd = (cum / rolling_max) - 1
    return dd.min()
