"""
garch_model.py — Modelagem GARCH de volatilidade condicional
SBWAA | Econometrician Agent

Tenta usar a biblioteca `arch`. Se não disponível, usa rolling std como fallback.
"""

import numpy as np
import pandas as pd
from typing import Optional


def _half_life(alpha: float, beta: float) -> Optional[float]:
    """Número de dias para que um choque de volatilidade decaia pela metade."""
    persistencia = alpha + beta
    if persistencia >= 1.0:
        return None
    return round(np.log(0.5) / np.log(persistencia), 1)


def _regime(vol_atual: float, vol_media: float) -> str:
    ratio = vol_atual / vol_media if vol_media > 0 else 1.0
    if ratio < 0.8:
        return "BAIXA"
    if ratio < 1.2:
        return "NORMAL"
    if ratio < 1.6:
        return "ELEVADA"
    return "ALTA"


def rodar_garch(retornos: pd.Series) -> dict:
    """
    Ajusta GARCH(1,1) nos retornos diários.
    Retorna dict com parâmetros, vol condicional atual e regime.
    """
    retornos_limpos = retornos.dropna()
    if len(retornos_limpos) < 60:
        return {"disponivel": False, "motivo": "Histórico insuficiente (<60 obs)"}

    # Tenta arch
    try:
        from arch import arch_model
        modelo = arch_model(retornos_limpos * 100, vol="Garch", p=1, q=1,
                            dist="normal", rescale=False)
        resultado = modelo.fit(disp="off", show_warning=False)

        params = resultado.params
        omega = float(params.get("omega", 0))
        alpha = float(params.get("alpha[1]", 0))
        beta  = float(params.get("beta[1]", 0))

        vol_cond_serie = resultado.conditional_volatility / 100  # volta para decimal
        vol_atual      = float(vol_cond_serie.iloc[-1])
        vol_media      = float(vol_cond_serie.mean())

        vol_anual_atual = vol_atual * np.sqrt(252)
        vol_anual_media = vol_media * np.sqrt(252)

        persistencia = alpha + beta

        return {
            "disponivel": True,
            "motor": "arch GARCH(1,1)",
            "omega": round(omega, 8),
            "alpha": round(alpha, 4),
            "beta_garch": round(beta, 4),
            "persistencia": round(persistencia, 4),
            "half_life_dias": _half_life(alpha, beta),
            "vol_condicional_atual": round(vol_atual, 6),
            "vol_anualizada_atual_pct": round(vol_anual_atual * 100, 2),
            "vol_anualizada_media_pct": round(vol_anual_media * 100, 2),
            "regime_volatilidade": _regime(vol_atual, vol_media),
        }

    except ImportError:
        pass  # arch não instalado — usa rolling

    except Exception as e:
        pass

    # Fallback: rolling std
    try:
        vol_rolling = retornos_limpos.rolling(21).std()
        vol_atual   = float(vol_rolling.iloc[-1])
        vol_media   = float(vol_rolling.mean())
        return {
            "disponivel": True,
            "motor": "rolling_std_21d (arch não instalado)",
            "vol_condicional_atual": round(vol_atual, 6),
            "vol_anualizada_atual_pct": round(vol_atual * np.sqrt(252) * 100, 2),
            "vol_anualizada_media_pct": round(vol_media * np.sqrt(252) * 100, 2),
            "regime_volatilidade": _regime(vol_atual, vol_media),
            "alpha": None, "beta_garch": None, "persistencia": None, "half_life_dias": None,
        }
    except Exception as e:
        return {"disponivel": False, "motivo": str(e)}
