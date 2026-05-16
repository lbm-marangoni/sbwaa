"""
Calculadora de VaR e CVaR — SBWAA Risk Engineer
Fórmulas documentadas. Resultados em fração (não em R$).
A conversão para R$ é feita no script principal.
"""
import numpy as np
import pandas as pd


def var_historico(retornos_carteira: pd.Series,
                  confianca: float = 0.95) -> float:
    """
    VaR Histórico: percentil (1-α) da distribuição de retornos.
    Retorna valor positivo (a perda).
    Ex: VaR 95% = 0.025 significa perda potencial de 2.5% em 1 dia.
    """
    return -np.percentile(retornos_carteira.dropna(),
                          (1 - confianca) * 100)


def var_parametrico(volatilidade_diaria: float,
                    confianca: float = 0.95) -> float:
    """
    VaR Paramétrico (Normal): z_α × σ_diária
    z_95% = 1.645 | z_99% = 2.326
    """
    z_scores = {0.95: 1.645, 0.99: 2.326, 0.90: 1.282}
    z = z_scores.get(confianca, 1.645)
    return z * volatilidade_diaria


def cvar(retornos_carteira: pd.Series,
         confianca: float = 0.95) -> float:
    """
    CVaR / Expected Shortfall: média dos retornos abaixo do VaR.
    Sempre maior que o VaR — mede a perda esperada dado que o VaR foi violado.
    """
    var = var_historico(retornos_carteira, confianca)
    retornos = retornos_carteira.dropna()
    tail = retornos[retornos <= -var]
    if len(tail) == 0:
        return var
    return -tail.mean()


def retornos_carteira_historicos(retornos_ativos: pd.DataFrame,
                                  pesos: dict) -> pd.Series:
    """
    Retornos históricos da carteira ponderada pelos pesos.
    retornos_ativos: DataFrame com retornos diários por ticker
    pesos: dict {ticker: peso_decimal}
    """
    pesos_series = pd.Series(pesos)
    pesos_alinhados = pesos_series.reindex(
        retornos_ativos.columns).fillna(0)
    pesos_norm = pesos_alinhados / pesos_alinhados.sum()
    return (retornos_ativos * pesos_norm).sum(axis=1)
