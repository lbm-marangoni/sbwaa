"""
run_econometrician.py — Agente Econometrician do SBWAA
Uso: python run_econometrician.py TICKER

Executa: GARCH, Beta Dinâmico, Fama-French 3F, Macro Regression, Rolling Corr, Drawdown Avançado
Salva: scripts/data/cache/econometria_{TICKER}_{DATA}.json
"""

import re
import sys
import json
import math
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd
import yfinance as yf

AGENT_DIR   = Path(__file__).parent
PROJECT_ROOT = AGENT_DIR.parent.parent.parent
VAULT_ROOT  = PROJECT_ROOT / "vault"
CACHE_DIR   = PROJECT_ROOT / "scripts" / "data" / "cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

sys.path.insert(0, str(AGENT_DIR))
from modules.garch_model       import rodar_garch
from modules.dynamic_beta      import calcular_beta_dinamico
from modules.factor_model      import calcular_fator_model
from modules.macro_regression  import calcular_macro_sensibilidade
from modules.rolling_stats     import calcular_correlacoes_rolling
from modules.advanced_drawdown import calcular_drawdown_avancado

IBOV_TICKER  = "^BVSP"
PERIODO      = "3y"


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _nan_safe(obj):
    """Converte NaN/inf para None recursivamente para serialização JSON."""
    if isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            return None
        return obj
    if isinstance(obj, dict):
        return {k: _nan_safe(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_nan_safe(i) for i in obj]
    return obj


def _eh_ticker_br(ticker: str) -> bool:
    return bool(re.match(r"^[A-Z]{4}[0-9]{1,2}[FBP]?$", ticker))


def _yahoo(ticker: str) -> str:
    return f"{ticker}.SA" if _eh_ticker_br(ticker) else ticker


def _baixar(ticker_yahoo: str) -> pd.Series:
    dados = yf.download(ticker_yahoo, period=PERIODO, auto_adjust=True, progress=False)
    if dados.empty:
        raise ValueError(f"Sem dados para {ticker_yahoo}")
    return dados["Close"].squeeze()


def _extrair_carteira() -> dict[str, float]:
    """Lê carteira.md e retorna {ticker: peso_%}"""
    caminho = VAULT_ROOT / "00-portfolio" / "carteira.md"
    if not caminho.exists():
        return {}
    texto = caminho.read_text(encoding="utf-8")
    ativos = {}
    for linha in texto.splitlines():
        m = re.match(r"\|\s*([A-Z]{4}[0-9]{1,2})\s*\|.*?\|\s*([\d.]+)%", linha)
        if m:
            ativos[m.group(1)] = float(m.group(2))
    return ativos


def _selic_do_bcb() -> float:
    """Tenta ler Selic do cache BCB. Fallback: 12.75%."""
    arquivos = sorted(CACHE_DIR.glob("bcb_*.json"), reverse=True)
    if arquivos:
        try:
            bcb = json.loads(arquivos[0].read_text(encoding="utf-8"))
            return (bcb.get("selic_anual_pct") or 12.75) / 100
        except Exception:
            pass
    return 0.1275


# ─── Main ─────────────────────────────────────────────────────────────────────

def main(ticker: str) -> dict:
    ticker = ticker.upper().strip()
    hoje   = date.today().isoformat()

    print(f"\n{'═'*58}")
    print(f"  ECONOMETRICIAN — {ticker} | {hoje}")
    print(f"{'═'*58}")

    # ── Baixar preços ────────────────────────────────────────────────────────
    print("\n[1/6] Baixando preços históricos...")
    try:
        precos_ativo = _baixar(_yahoo(ticker))
        precos_ibov  = _baixar(IBOV_TICKER)
    except Exception as e:
        print(f"  ❌ Erro ao baixar preços: {e}")
        sys.exit(1)

    r_ativo = precos_ativo.pct_change().dropna()
    r_ibov  = precos_ibov.pct_change().dropna()

    # Alinhar ao índice comum
    idx_comum = r_ativo.index.intersection(r_ibov.index)
    r_ativo = r_ativo.loc[idx_comum]
    r_ibov  = r_ibov.loc[idx_comum]
    precos_alinhado = precos_ativo.reindex(idx_comum).dropna()

    selic_anual = _selic_do_bcb()
    n_dias = len(r_ativo)
    print(f"  → {n_dias} dias úteis | Selic: {selic_anual*100:.2f}% a.a.")

    # Retorno anualizado simples (para Calmar)
    if n_dias >= 20:
        ret_anual = (1 + (precos_alinhado.iloc[-1] / precos_alinhado.iloc[0] - 1)) ** (252 / n_dias) - 1
    else:
        ret_anual = 0.0

    saida = {
        "ticker": ticker,
        "data":   hoje,
        "periodo_dias": n_dias,
        "selic_anual_pct": round(selic_anual * 100, 2),
    }

    # ── Módulo 1: GARCH ──────────────────────────────────────────────────────
    print("\n[2/6] GARCH — volatilidade condicional...")
    saida["garch"] = rodar_garch(r_ativo)
    regime = saida["garch"].get("regime_volatilidade", "N/D")
    vol    = saida["garch"].get("vol_anualizada_atual_pct", "N/D")
    print(f"  → Vol anual: {vol}% | Regime: {regime}")

    # ── Módulo 2: Beta Dinâmico ──────────────────────────────────────────────
    print("\n[3/6] Beta dinâmico (rolling OLS)...")
    saida["beta_dinamico"] = calcular_beta_dinamico(r_ativo, r_ibov)
    beta_60 = saida["beta_dinamico"].get("beta_60d", "N/D")
    tend    = saida["beta_dinamico"].get("tendencia", "N/D")
    print(f"  → Beta 60d: {beta_60} | Tendência: {tend}")

    # ── Módulo 3: Fama-French ────────────────────────────────────────────────
    print("\n[4/6] Fama-French 3 fatores (proxies BR)...")
    r_ativo_named = r_ativo.copy()
    r_ativo_named.name = ticker
    saida["fator_model"] = calcular_fator_model(r_ativo_named, r_ibov, selic_anual)
    if saida["fator_model"].get("disponivel"):
        alpha = saida["fator_model"].get("alpha_anualizado_pct", "N/D")
        r2    = saida["fator_model"].get("r2_ajustado", "N/D")
        print(f"  → Alpha anual: {alpha}% | R² adj: {r2}")
    else:
        print(f"  → {saida['fator_model'].get('motivo', 'indisponível')}")

    # ── Módulo 4: Macro Regression ───────────────────────────────────────────
    print("\n[5/6] Regressão macro (BCB SGS)...")
    saida["macro_sensibilidade"] = calcular_macro_sensibilidade(r_ativo)
    if saida["macro_sensibilidade"].get("disponivel"):
        driver = saida["macro_sensibilidade"].get("principal_driver", "N/D")
        r2m    = saida["macro_sensibilidade"].get("r2_ajustado", "N/D")
        print(f"  → Driver principal: {driver} | R² adj: {r2m}")
    else:
        print(f"  → {saida['macro_sensibilidade'].get('motivo', 'indisponível')}")

    # ── Módulo 5: Rolling Correlations ──────────────────────────────────────
    print("\n[6/6] Correlações rolling vs carteira...")
    carteira = _extrair_carteira()
    retornos_outros = {}
    for t, _ in carteira.items():
        if t == ticker:
            continue
        try:
            p = _baixar(_yahoo(t))
            r = p.pct_change().dropna()
            idx_c = r_ativo.index.intersection(r.index)
            retornos_outros[t] = r.loc[idx_c]
        except Exception:
            pass

    saida["correlacoes_rolling"] = calcular_correlacoes_rolling(r_ativo, retornos_outros)
    n_comp = len(retornos_outros)
    print(f"  → {n_comp} ativo(s) da carteira comparados")

    # ── Drawdown Avançado ────────────────────────────────────────────────────
    saida["drawdown_avancado"] = calcular_drawdown_avancado(precos_alinhado, ret_anual)
    calmar = saida["drawdown_avancado"].get("calmar_ratio", "N/D")
    ulcer  = saida["drawdown_avancado"].get("ulcer_index_pct", "N/D")
    print(f"\n  Drawdown avançado → Calmar: {calmar} | Ulcer: {ulcer}%")

    # ── Salvar JSON ──────────────────────────────────────────────────────────
    saida_limpa = _nan_safe(saida)
    path = CACHE_DIR / f"econometria_{ticker}_{hoje}.json"
    path.write_text(json.dumps(saida_limpa, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"\n{'─'*58}")
    print(f"  ✅ Salvo: econometria_{ticker}_{hoje}.json")
    print(f"{'─'*58}\n")

    return saida_limpa


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python run_econometrician.py TICKER")
        sys.exit(1)
    main(sys.argv[1])
