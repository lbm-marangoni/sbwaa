"""
run_risk_engineer.py — Executa o agente Risk Engineer do SBWAA.
Uso: python run_risk_engineer.py
"""

import re
import sys
import json
import math
import subprocess
from datetime import datetime, date
from pathlib import Path

import numpy as np
import pandas as pd
import yfinance as yf

AGENT_DIR = Path(__file__).parent
PROJECT_ROOT = AGENT_DIR.parent.parent.parent
VAULT_ROOT = PROJECT_ROOT / "vault"
SCRIPTS_DATA = PROJECT_ROOT / "scripts" / "data"
AGENTS_DIR = PROJECT_ROOT / ".claude" / "agents"
SKILL_PATH = AGENT_DIR / "SKILL.md"
CACHE_DIR = SCRIPTS_DATA / "cache"
RISK_DIR = VAULT_ROOT / "05-risk" / "snapshots"

sys.path.insert(0, str(AGENT_DIR))
from calculators.var import (var_historico, var_parametrico, cvar,
                               retornos_carteira_historicos)
from calculators.stress_test import rodar_todos_cenarios

CARTEIRA_PATH = VAULT_ROOT / "00-portfolio" / "carteira.md"
IPS_PATH = VAULT_ROOT / "00-portfolio" / "ips.md"
PATRIMONIO_NORMALIZADO = 100_000.0

# Defaults usados quando IPS não está preenchido
IPS_DEFAULTS = {
    "var_maximo_pct": 0.03,      # 3% do patrimônio
    "drawdown_maximo_pct": 0.15,  # 15%
    "concentracao_maxima_pct": 0.20,  # 20%
}


# ─── Helpers ──────────────────────────────────────────────────────────────────

def eh_ticker_br(ticker: str) -> bool:
    return bool(re.match(r"^[A-Z]{4}[0-9]{1,2}[FBP]?$", ticker))


def ticker_yahoo(ticker: str) -> str:
    return f"{ticker}.SA" if eh_ticker_br(ticker) else ticker


def carregar_quant(hoje: str) -> dict | None:
    path = CACHE_DIR / f"quant_{hoje}.json"
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    # Tentar dias anteriores (até 3)
    from datetime import timedelta
    for d in range(1, 4):
        dt = (datetime.strptime(hoje, "%Y-%m-%d") - timedelta(days=d)).strftime("%Y-%m-%d")
        path = CACHE_DIR / f"quant_{dt}.json"
        if path.exists():
            print(f"Quant encontrado do dia {dt}.")
            return json.loads(path.read_text(encoding="utf-8"))
    return None


def parse_ips_limite(conteudo: str, pattern: str, default: float) -> float:
    """Extrai limite numérico do IPS ou retorna o default."""
    m = re.search(pattern, conteudo, re.IGNORECASE)
    if m:
        try:
            val = float(m.group(1).replace(",", ".").replace("%", "").strip())
            return val / 100 if val > 1 else val
        except ValueError:
            pass
    return default


def carregar_limites_ips() -> dict:
    if not IPS_PATH.exists():
        return IPS_DEFAULTS.copy()
    conteudo = IPS_PATH.read_text(encoding="utf-8")
    return {
        "var_maximo_pct": parse_ips_limite(
            conteudo, r"VaR[^:]*:\s*([\d,\.]+)", IPS_DEFAULTS["var_maximo_pct"]),
        "drawdown_maximo_pct": parse_ips_limite(
            conteudo, r"[Dd]rawdown[^:]*:\s*([\d,\.]+)", IPS_DEFAULTS["drawdown_maximo_pct"]),
        "concentracao_maxima_pct": parse_ips_limite(
            conteudo, r"[Cc]oncentra[çc][aã]o[^:]*:\s*([\d,\.]+)",
            IPS_DEFAULTS["concentracao_maxima_pct"]),
    }


def status_ips(valor: float, limite: float) -> str:
    if valor <= limite * 0.80:
        return "✅"
    if valor <= limite:
        return "⚠️"
    return "🚨"


def carregar_retornos_historicos(quant: dict) -> pd.DataFrame | None:
    """Reconstrói retornos diários via yfinance para cálculo de VaR."""
    tickers = list(quant.get("ativos", {}).keys())
    if not tickers:
        return None
    frames = {}
    for t in tickers:
        ty = ticker_yahoo(t)
        try:
            hist = yf.download(ty, period="1y", auto_adjust=True,
                               progress=False, threads=False)
            if hist.empty:
                continue
            close = hist["Close"]
            if isinstance(close, pd.DataFrame):
                close = close.iloc[:, 0]
            frames[t] = close.pct_change().dropna()
        except Exception:
            pass
    if not frames:
        return None
    return pd.DataFrame(frames).dropna()


# ─── Main ──────────────────────────────────────────────────────────────────────

def main():
    hoje = datetime.now().strftime("%Y-%m-%d")
    print(f"Risk Engineer — {hoje}")
    print("=" * 50)

    # Carregar Quant ou rodar
    quant = carregar_quant(hoje)
    if quant is None:
        print("Quant JSON não encontrado. Rodando run_quant.py...")
        rc = subprocess.run(
            [sys.executable,
             str(AGENTS_DIR / "quant-data-engineer" / "run_quant.py")],
            text=True,
        )
        if rc.returncode != 0:
            print("ERRO ao rodar Quant. Abortando.")
            sys.exit(1)
        quant = carregar_quant(hoje)
        if quant is None:
            print("ERRO: JSON Quant ainda indisponível.")
            sys.exit(1)

    limites = carregar_limites_ips()
    ativos_q = quant.get("ativos", {})
    cart_q = quant.get("carteira", {})
    num_ativos = cart_q.get("num_ativos", 0)

    # ── VaR e CVaR ────────────────────────────────────────────────────────────
    retornos_df = carregar_retornos_historicos(quant)
    vol_diaria = (cart_q.get("volatilidade_pct") or 0) / 100 / math.sqrt(252)

    var_hist_pct = None
    cvar_pct = None

    if retornos_df is not None and not retornos_df.empty:
        pesos = {t: 1.0 / num_ativos for t in retornos_df.columns} if num_ativos > 0 else {}
        if pesos:
            ret_cart = retornos_carteira_historicos(retornos_df, pesos)
            var_hist_pct = var_historico(ret_cart, 0.95)
            cvar_pct = cvar(ret_cart, 0.95)

    var_param_pct = var_parametrico(vol_diaria) if vol_diaria else None

    # ── Concentração ──────────────────────────────────────────────────────────
    conc_max_ticker = max(ativos_q, key=lambda t: ativos_q[t].get("peso_carteira_pct", 0),
                          default=None)
    conc_max_pct = (ativos_q[conc_max_ticker].get("peso_carteira_pct", 0) / 100
                    if conc_max_ticker else 0)
    hhi_val = cart_q.get("hhi", 0)

    # ── Drawdown atual ────────────────────────────────────────────────────────
    dd_atual_pct = cart_q.get("drawdown_maximo_pct") or 0
    dd_atual = dd_atual_pct / 100

    # ── Stress tests ──────────────────────────────────────────────────────────
    beta_cart = cart_q.get("beta_ibov") or 1.0
    stress = rodar_todos_cenarios(beta_cart, PATRIMONIO_NORMALIZADO)

    # ── Circuit breakers ──────────────────────────────────────────────────────
    cb_var = (var_hist_pct is None) or (var_hist_pct <= limites["var_maximo_pct"])
    cb_dd = abs(dd_atual) <= limites["drawdown_maximo_pct"]
    cb_conc = conc_max_pct <= limites["concentracao_maxima_pct"]
    cb_corr = True  # sem histórico de correlação para comparar

    circuit_breakers = {
        "var_ok": cb_var,
        "drawdown_ok": cb_dd,
        "concentracao_ok": cb_conc,
        "correlacao_ok": cb_corr,
    }

    # ── Flags para PM ─────────────────────────────────────────────────────────
    flags = []
    if not cb_var:
        flags.append(f"🚨 CRÍTICO — VaR {var_hist_pct*100:.2f}% acima do limite IPS {limites['var_maximo_pct']*100:.1f}%")
    if not cb_dd:
        flags.append(f"🚨 CRÍTICO — Drawdown {abs(dd_atual)*100:.2f}% acima do limite IPS {limites['drawdown_maximo_pct']*100:.1f}%")
    if not cb_conc:
        flags.append(f"⚠️ ALTO — {conc_max_ticker} concentração {conc_max_pct*100:.1f}% acima do limite {limites['concentracao_maxima_pct']*100:.1f}%")
    pares_corr = quant.get("pares_alta_correlacao", [])
    for par in pares_corr[:2]:
        flags.append(f"⚠️ MÉDIO — Alta correlação {par['ativo_a']}/{par['ativo_b']}: {par['correlacao']:.2f}")
    if not flags:
        flags.append("✅ Todos os circuit breakers dentro dos limites IPS.")

    # ── JSON de risco ─────────────────────────────────────────────────────────
    risk_json = {
        "data": hoje,
        "var_historico_95_pct": round(var_hist_pct * 100, 3) if var_hist_pct else None,
        "var_parametrico_95_pct": round(var_param_pct * 100, 3) if var_param_pct else None,
        "cvar_95_pct": round(cvar_pct * 100, 3) if cvar_pct else None,
        "drawdown_atual_pct": dd_atual_pct,
        "concentracao_maxima_pct": round(conc_max_pct * 100, 2),
        "concentracao_maxima_ticker": conc_max_ticker,
        "hhi": hhi_val,
        "sharpe_carteira": cart_q.get("sharpe"),
        "volatilidade_anual_pct": cart_q.get("volatilidade_pct"),
        "beta_ibov": beta_cart,
        "stress_tests": stress,
        "circuit_breakers": circuit_breakers,
        "flags_pm": flags,
    }

    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    risk_cache = CACHE_DIR / f"risk_{hoje}.json"
    import numpy as np

    class _NpEncoder(json.JSONEncoder):
        def default(self, o):
            if isinstance(o, (np.integer,)): return int(o)
            if isinstance(o, (np.floating,)): return float(o)
            if isinstance(o, (np.bool_,)): return bool(o)
            if isinstance(o, np.ndarray): return o.tolist()
            return super().default(o)

    risk_cache.write_text(json.dumps(risk_json, ensure_ascii=False, indent=2, cls=_NpEncoder), encoding="utf-8")
    print(f"JSON de risco salvo: {risk_cache}")
    # Síntese textual é feita pelo Claude Code ao ler o cache — não via API direta.

    def fmt_pct(v): return f"{v:.2f}%" if v is not None else "N/D"

    # Terminal summary
    print(f"\n{'═'*50}")
    print(f"  RISK SNAPSHOT — {hoje}")
    print(f"{'─'*50}")
    print(f"  VaR 95% hist:   {fmt_pct(var_hist_pct*100 if var_hist_pct else None)}")
    print(f"  CVaR 95%:       {fmt_pct(cvar_pct*100 if cvar_pct else None)}")
    print(f"  Drawdown atual: {fmt_pct(abs(dd_atual)*100)}")
    print(f"  Conc. máxima:   {conc_max_ticker} {conc_max_pct*100:.1f}%")
    print(f"  Circuit breakers: {'✅ OK' if all(circuit_breakers.values()) else '⚠️ VIOLAÇÕES'}")
    print(f"{'═'*50}\n")


if __name__ == "__main__":
    main()
