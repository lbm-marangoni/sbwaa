"""
factor_model.py — Modelo de 3 fatores (Fama-French estilo) para o Brasil
SBWAA | Econometrician Agent

Fatores usados (proxies BR via ETFs da B3):
  Mercado (Mkt-Rf): retorno IBOV - Selic
  SMB (Small Minus Big): SMLL11.SA - BOVA11.SA
  HML (High Minus Low): DIVO11.SA - IVVB11.SA (dividend/value vs intl growth)

Os fatores são proxies — não são os fatores oficiais do NEFIN.
Resultados devem ser interpretados com essa ressalva.
"""

import numpy as np
import pandas as pd
import yfinance as yf
from typing import Optional


FATORES_BR = {
    "smb_long":  ["SMLL11.SA", "SMAL11.SA"],  # Small cap (tenta em ordem)
    "smb_short": ["BOVA11.SA"],               # Large cap (IBOV)
    "hml_long":  ["DIVO11.SA"],               # High dividend / value
    "hml_short": ["IVVB11.SA"],               # Internacional / growth
}


def _baixar_precos(ticker_ou_lista, periodo: str = "2y") -> Optional[pd.Series]:
    """Aceita string ou lista de tickers (tenta em ordem até encontrar dados)."""
    tickers = [ticker_ou_lista] if isinstance(ticker_ou_lista, str) else ticker_ou_lista
    for ticker in tickers:
        try:
            dados = yf.download(ticker, period=periodo, auto_adjust=True, progress=False)
            if not dados.empty:
                return dados["Close"].squeeze()
        except Exception:
            continue
    return None


def _retornos(precos: pd.Series) -> pd.Series:
    return precos.pct_change().dropna()


def _ols_multivariado(y: np.ndarray, X: np.ndarray) -> tuple[np.ndarray, float, np.ndarray]:
    """OLS múltiplo. Retorna (coeficientes, r2_ajustado, p_valores)."""
    n, k = X.shape
    try:
        coef, _, _, _ = np.linalg.lstsq(X, y, rcond=None)
        y_hat = X @ coef
        ss_res = np.sum((y - y_hat) ** 2)
        ss_tot = np.sum((y - y.mean()) ** 2)
        r2 = 1 - ss_res / ss_tot if ss_tot > 0 else 0.0
        r2_adj = 1 - (1 - r2) * (n - 1) / (n - k) if n > k else r2

        # p-valores via t-test
        sigma2 = ss_res / (n - k) if n > k else ss_res
        try:
            XtX_inv = np.linalg.inv(X.T @ X)
            se = np.sqrt(np.diag(XtX_inv) * sigma2)
            t_stats = coef / se
            from scipy import stats
            p_vals = 2 * (1 - stats.t.cdf(np.abs(t_stats), df=n - k))
        except Exception:
            p_vals = np.full(len(coef), float("nan"))

        return coef, round(float(r2_adj), 4), p_vals
    except Exception:
        return np.zeros(X.shape[1]), 0.0, np.full(X.shape[1], float("nan"))


def calcular_fator_model(retornos_ativo: pd.Series,
                          retornos_ibov: pd.Series,
                          selic_anual: float = 0.1275) -> dict:
    """
    Regressão Fama-French 3 fatores adaptada para o Brasil.
    """
    selic_diaria = (1 + selic_anual) ** (1/252) - 1

    # Baixar proxies de fatores
    smb_long  = _baixar_precos(FATORES_BR["smb_long"])
    smb_short = _baixar_precos(FATORES_BR["smb_short"])
    hml_long  = _baixar_precos(FATORES_BR["hml_long"])
    hml_short = _baixar_precos(FATORES_BR["hml_short"])

    fatores_disponiveis = []
    notas = []

    # Fator mercado (sempre disponível)
    r_mkt_rf = retornos_ibov - selic_diaria
    fatores_disponiveis.append(("mkt_rf", r_mkt_rf))

    # SMB
    if smb_long is not None and smb_short is not None:
        smb = _retornos(smb_long) - _retornos(smb_short)
        fatores_disponiveis.append(("smb", smb))
    else:
        notas.append("SMB não disponível (SMLL11 ou BOVA11 sem dados)")

    # HML
    if hml_long is not None and hml_short is not None:
        hml = _retornos(hml_long) - _retornos(hml_short)
        fatores_disponiveis.append(("hml", hml))
    else:
        notas.append("HML não disponível (DIVO11 ou IVVB11 sem dados)")

    # Alinhar séries
    r_ativo = retornos_ativo - selic_diaria  # excess return
    series = [r_ativo] + [f[1] for f in fatores_disponiveis]
    nomes  = ["excess_ret"] + [f[0] for f in fatores_disponiveis]
    df = pd.concat(series, axis=1, keys=nomes).dropna()

    if len(df) < 60:
        return {
            "disponivel": False,
            "motivo": f"Dados insuficientes após alinhamento ({len(df)} obs)",
            "notas": notas,
        }

    y = df["excess_ret"].values
    X = np.column_stack([np.ones(len(df))] + [df[n].values for n in nomes[1:]])

    coef, r2_adj, p_vals = _ols_multivariado(y, X)

    alpha_diario = float(coef[0])
    alpha_anual  = (1 + alpha_diario) ** 252 - 1

    resultado = {
        "disponivel": True,
        "n_observacoes": len(df),
        "periodo_dias": (df.index[-1] - df.index[0]).days,
        "alpha_diario": round(alpha_diario, 6),
        "alpha_anualizado_pct": round(alpha_anual * 100, 2),
        "p_valor_alpha": round(float(p_vals[0]), 4),
        "alpha_significativo": bool(float(p_vals[0]) < 0.05),
        "r2_ajustado": r2_adj,
        "notas": [
            "Proxies BR: SMB=SMLL11-BOVA11, HML=DIVO11-IVVB11",
            "Não são fatores oficiais NEFIN — interpretar como aproximação",
        ] + notas,
    }

    # Adicionar betas por fator
    nomes_fat = [f[0] for f in fatores_disponiveis]
    for i, nome in enumerate(nomes_fat):
        resultado[f"beta_{nome}"] = round(float(coef[i + 1]), 4)
        resultado[f"p_valor_{nome}"] = round(float(p_vals[i + 1]), 4)

    return resultado
