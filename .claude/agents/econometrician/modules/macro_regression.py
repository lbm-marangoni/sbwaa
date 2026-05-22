"""
macro_regression.py — Sensibilidade do ativo a variáveis macro (BCB)
SBWAA | Econometrician Agent

Regressão OLS múltipla: retorno_mensal_ativo ~ ΔSELIC + ΔIPCA + ΔBRL_USD + ΔIBC
Usa dados mensais dos últimos 24 meses (BCB SGS).
"""

import json
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import date


CACHE_DIR = Path(__file__).resolve().parent.parent.parent.parent.parent / "scripts" / "data" / "cache"


def _carregar_bcb() -> dict | None:
    """Carrega o cache BCB mais recente."""
    arquivos = sorted(CACHE_DIR.glob("bcb_*.json"), reverse=True)
    if not arquivos:
        return None
    return json.loads(arquivos[0].read_text(encoding="utf-8"))


def _serie_para_df(historico: list[dict], col: str) -> pd.DataFrame:
    """Converte lista [{data, valor}] para DataFrame com DatetimeIndex."""
    if not historico:
        return pd.DataFrame()
    df = pd.DataFrame(historico)
    df["data"] = pd.to_datetime(df["data"], dayfirst=True)
    df = df.set_index("data").rename(columns={"valor": col})
    return df


def _resamplar_mensal(precos_diarios: pd.Series) -> pd.Series:
    """Retornos mensais a partir de preços diários."""
    return precos_diarios.resample("ME").last().pct_change().dropna()


def _ols_multiplo(y: np.ndarray, X: np.ndarray) -> tuple[np.ndarray, float, np.ndarray]:
    n, k = X.shape
    try:
        coef, _, _, _ = np.linalg.lstsq(X, y, rcond=None)
        y_hat = X @ coef
        ss_res = np.sum((y - y_hat) ** 2)
        ss_tot = np.sum((y - y.mean()) ** 2)
        r2 = 1 - ss_res / ss_tot if ss_tot > 0 else 0.0
        r2_adj = 1 - (1 - r2) * (n - 1) / (n - k) if n > k else r2
        return coef, round(float(r2_adj), 4), np.array([])
    except Exception:
        return np.zeros(k), 0.0, np.array([])


def calcular_macro_sensibilidade(retornos_diarios: pd.Series) -> dict:
    """
    Regride retornos mensais do ativo contra variações das variáveis macro do BCB.
    """
    bcb = _carregar_bcb()
    if bcb is None:
        return {
            "disponivel": False,
            "motivo": "Cache BCB não encontrado — rode fetch_bcb.py primeiro",
        }

    series_bcb = bcb.get("series", {})

    # Montar DataFrames mensais das variáveis macro
    df_ipca = _serie_para_df(
        series_bcb.get("ipca_mensal", {}).get("historico", []), "ipca"
    ).resample("ME").last()

    df_selic = _serie_para_df(
        series_bcb.get("selic_acum_mes", {}).get("historico", []), "selic"
    ).resample("ME").last()

    # BRL/USD: variação mensal do câmbio
    df_brl_diario = _serie_para_df(
        series_bcb.get("brl_usd", {}).get("historico", []), "brl_usd"
    )
    df_brl = pd.DataFrame()
    if not df_brl_diario.empty:
        df_brl = df_brl_diario.resample("ME").last().pct_change().dropna()
        df_brl.columns = ["delta_brl_usd_pct"]

    # IBC-Br mensal
    df_ibc = _serie_para_df(
        series_bcb.get("ibc_br", {}).get("historico", []), "ibc_br"
    ).resample("ME").last()

    # Retornos mensais do ativo
    r_mensal = _resamplar_mensal(
        retornos_diarios.apply(lambda x: 1 + x).cumprod()
    )
    r_mensal.name = "ret_ativo"

    # Juntar tudo
    partes = [r_mensal]
    nomes_vars = []

    if not df_selic.empty:
        df_selic["delta_selic"] = df_selic["selic"].diff()
        partes.append(df_selic["delta_selic"])
        nomes_vars.append("delta_selic_pp")

    if not df_ipca.empty:
        partes.append(df_ipca["ipca"])
        nomes_vars.append("ipca_pct")

    if not df_brl.empty:
        partes.append(df_brl["delta_brl_usd_pct"])
        nomes_vars.append("delta_brl_usd_pct")

    if not df_ibc.empty:
        partes.append(df_ibc["ibc_br"])
        nomes_vars.append("ibc_br_pct")

    if len(partes) < 2:
        return {"disponivel": False, "motivo": "Dados macro insuficientes no cache BCB"}

    df = pd.concat(partes, axis=1).dropna()
    df.columns = ["ret_ativo"] + nomes_vars

    if len(df) < 12:
        return {
            "disponivel": False,
            "motivo": f"Observações mensais insuficientes ({len(df)} < 12)",
        }

    y = df["ret_ativo"].values
    X = np.column_stack([np.ones(len(df))] + [df[n].values for n in nomes_vars])

    coef, r2_adj, _ = _ols_multiplo(y, X)

    sensibilidades = {}
    for i, nome in enumerate(nomes_vars):
        sensibilidades[nome] = round(float(coef[i + 1]), 4)

    # Driver principal (maior coef em valor absoluto)
    if sensibilidades:
        principal = max(sensibilidades, key=lambda k: abs(sensibilidades[k]))
    else:
        principal = None

    return {
        "disponivel": True,
        "n_observacoes": int(len(df)),
        "periodo": f"{df.index[0].strftime('%Y-%m')} a {df.index[-1].strftime('%Y-%m')}",
        "r2_ajustado": r2_adj,
        "sensibilidades": sensibilidades,
        "principal_driver": principal,
        "interpretacao": {
            "delta_selic_pp": "Variação de 1pp na Selic → impacto no retorno mensal (%)",
            "ipca_pct": "IPCA de 1% no mês → impacto no retorno mensal (%)",
            "delta_brl_usd_pct": "BRL/USD +1% (depreciação real) → impacto no retorno mensal (%)",
            "ibc_br_pct": "IBC-Br +1% → impacto no retorno mensal (%)",
        },
        "notas": "OLS múltiplo, retornos mensais. R² baixo é esperado — macro explica parcialmente.",
    }
