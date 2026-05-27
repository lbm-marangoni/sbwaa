"""
optimize_expansao.py — Análise de expansão de portfólio com watchlist.
Compara fronteira eficiente da carteira atual vs carteira + watchlist.
Uso: python sbwaa.py /otimizar-expansao

Salva: scripts/data/cache/optim_expansao_YYYY-MM-DD.json
"""

import os
import sys
import re
import json
import math
from datetime import datetime, date, timedelta
from pathlib import Path

os.environ["PYTHONUTF8"] = "1"
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

import numpy as np
import pandas as pd
import yfinance as yf

PROJECT_ROOT = Path(__file__).parent.parent.parent
VAULT_ROOT = PROJECT_ROOT / "vault"
CACHE_DIR = PROJECT_ROOT / "scripts" / "data" / "cache"
CARTEIRA_PATH = VAULT_ROOT / "00-portfolio" / "carteira.md"
ATIVOS_DIR = VAULT_ROOT / "01-ativos"

# Limpar cache de 'calculators' para evitar conflito com risk-engineer se carregado antes
for _k in list(sys.modules.keys()):
    if _k.startswith("calculators"):
        del sys.modules[_k]
_quant_path = str(PROJECT_ROOT / ".claude" / "agents" / "quant-data-engineer")
if _quant_path not in sys.path:
    sys.path.insert(0, _quant_path)
from calculators.optimization import otimizar_carteira

IBOV_TICKER = "^BVSP"
SELIC_PADRAO = 0.1275


# ─── Leitura de dados ─────────────────────────────────────────────────────────

def _eh_ticker_br(ticker: str) -> bool:
    return bool(re.match(r"^[A-Z]{4}[0-9]{1,2}[FBP]?$", ticker))


def _yahoo(ticker: str) -> str:
    return f"{ticker}.SA" if _eh_ticker_br(ticker) else ticker


def _carteira_tickers() -> list[str]:
    if not CARTEIRA_PATH.exists():
        return []
    tickers = []
    dentro = False
    for linha in CARTEIRA_PATH.read_text(encoding="utf-8").splitlines():
        s = linha.strip()
        if s.startswith("| Ticker"):
            dentro = True
            continue
        if dentro and s.startswith("|---"):
            continue
        if dentro and s.startswith("|"):
            cols = [c.strip() for c in s.split("|")[1:-1]]
            if cols and cols[0]:
                t = cols[0].replace("[[", "").replace("]]", "").split("|")[0].strip().upper()
                t = re.sub(r"01-ativos/([^/]+)/tese", r"\1", t)
                if t:
                    tickers.append(t)
        elif dentro:
            break
    return tickers


def _watchlist_tickers(carteira: list[str]) -> list[str]:
    """Ativos analisados que NÃO estão em carteira."""
    if not ATIVOS_DIR.exists():
        return []
    analisados = {p.name.upper() for p in ATIVOS_DIR.iterdir() if p.is_dir()}
    return sorted(analisados - set(carteira))


def _buscar_historico(ticker_yf: str) -> pd.Series | None:
    try:
        hist = yf.download(ticker_yf, period="1y", auto_adjust=True,
                           progress=False, threads=False)
        if hist.empty:
            return None
        close = hist["Close"]
        if isinstance(close, pd.DataFrame):
            close = close.iloc[:, 0]
        close = close.dropna()
        return close if len(close) >= 60 else None
    except Exception:
        return None


def _selic_do_cache() -> float:
    hoje = date.today().strftime("%Y-%m-%d")
    for d in range(7):
        dt = (date.today() - timedelta(days=d)).strftime("%Y-%m-%d")
        p = CACHE_DIR / f"quant_{dt}.json"
        if p.exists():
            try:
                return json.loads(p.read_text(encoding="utf-8")).get("selic_anual", SELIC_PADRAO)
            except Exception:
                pass
    return SELIC_PADRAO


def _retornos_do_cache_quant() -> dict[str, pd.Series]:
    """Reutiliza históricos já salvos no cache quant quando possível."""
    return {}  # extensão futura; por ora busca via yfinance


# ─── Cálculo de contribuição marginal ────────────────────────────────────────

def _sharpe_carteira(retornos_df: pd.DataFrame, pesos: np.ndarray,
                     selic: float) -> float:
    ret_anual = retornos_df.mean().values * 252
    cov_anual = retornos_df.cov().values * 252
    ret = float(np.dot(pesos, ret_anual))
    vol = float(np.sqrt(pesos @ cov_anual @ pesos))
    return (ret - selic) / vol if vol > 1e-9 else float("-inf")


def _correlacao_com_carteira(ativo_ret: pd.Series,
                              carteira_ret: pd.Series) -> float:
    """Correlação do ativo com o retorno ponderado da carteira."""
    combined = pd.concat([ativo_ret, carteira_ret], axis=1).dropna()
    if len(combined) < 20:
        return float("nan")
    return float(combined.corr().iloc[0, 1])


def _sharpe_marginal(ticker: str, ret_serie: pd.Series,
                     retornos_base: pd.DataFrame, pesos_base: np.ndarray,
                     selic: float, peso_teste: float = 0.05) -> float:
    """
    Sharpe do portfólio base com o ativo adicionado a peso_teste%
    (pesos base reduzidos proporcionalmente) menos Sharpe base.
    """
    pesos_adj = pesos_base * (1 - peso_teste)
    retornos_exp = retornos_base.copy()
    retornos_exp[ticker] = ret_serie
    cols = list(retornos_base.columns) + [ticker]
    pesos_exp = np.append(pesos_adj, peso_teste)
    df = retornos_exp[cols].dropna()
    if len(df) < 20:
        return float("nan")
    sh_exp = _sharpe_carteira(df, pesos_exp, selic)
    sh_base = _sharpe_carteira(retornos_base.dropna(), pesos_base, selic)
    return round(sh_exp - sh_base, 4) if math.isfinite(sh_exp) and math.isfinite(sh_base) else float("nan")


# ─── Output ──────────────────────────────────────────────────────────────────

def _fmt(v, sufixo="", ndigits=3):
    if v is None or (isinstance(v, float) and not math.isfinite(v)):
        return "N/D"
    return f"{round(v, ndigits)}{sufixo}"


def _classificar(peso_otimo: float, delta_sharpe: float) -> str:
    if peso_otimo >= 0.02 and (math.isnan(delta_sharpe) or delta_sharpe >= 0):
        return "MELHORA"
    if peso_otimo < 0.01 and not math.isnan(delta_sharpe) and delta_sharpe < -0.01:
        return "PIORA"
    return "NEUTRO"


def _icone(classif: str) -> str:
    return {"MELHORA": "✅", "NEUTRO": "⚠️ ", "PIORA": "🔴"}.get(classif, "—")


def _imprimir_resultado(resultado: dict):
    hoje = resultado["data_calculo"]
    cart_t = resultado["carteira_tickers"]
    wl_t = resultado["watchlist_tickers"]

    print(f"\n{'═'*70}")
    print(f"  SBWAA — Análise de Expansão  |  {hoje}")
    print(f"  Carteira: {len(cart_t)} ativos  |  Watchlist: {len(wl_t)} candidatos")
    print(f"{'═'*70}\n")

    fb = resultado.get("fronteira_base", {})
    fe = resultado.get("fronteira_expandida", {})

    def _sh(d): return _fmt(d.get("max_sharpe", {}).get("sharpe") if d else None)
    def _vol(d): return _fmt(d.get("max_sharpe", {}).get("volatilidade_pct") if d else None, "%")
    def _mv(d): return _fmt(d.get("min_vol", {}).get("volatilidade_pct") if d else None, "%")

    ganho = resultado.get("ganho_sharpe_expansao")
    ganho_str = f"  (+{ganho:.3f})" if ganho and ganho > 0 else ("  (sem melhora)" if ganho is not None else "")

    print(f"  {'FRONTEIRA':<32} {'BASE':>10}   {'EXPANDIDA':>12}")
    print(f"  {'─'*58}")
    print(f"  {'Sharpe Máximo (Max Sharpe)':<32} {_sh(fb):>10}   {_sh(fe):>12}{ganho_str}")
    print(f"  {'Volatilidade @ Max Sharpe':<32} {_vol(fb):>10}   {_vol(fe):>12}")
    print(f"  {'Volatilidade Mínima (Min Vol)':<32} {_mv(fb):>10}   {_mv(fe):>12}")

    candidatos = resultado.get("candidatos", [])
    if not candidatos:
        print("\n  Nenhum ativo da watchlist com histórico suficiente.\n")
        return

    print(f"\n  {'─'*68}")
    print(f"  CANDIDATOS DA WATCHLIST — Ranking por impacto no portfólio")
    print(f"  {'─'*68}")
    print(f"  {'Ticker':<10} {'Sharpe':<8} {'Corr.Cart':<11} {'ΔSharpe':<10} {'Peso Ótimo':<12} {'Status'}")
    print(f"  {'─'*68}")

    for c in candidatos:
        ticker     = c["ticker"]
        sh_prop    = _fmt(c.get("sharpe_proprio"))
        corr       = _fmt(c.get("correlacao_carteira"))
        delta      = c.get("delta_sharpe_marginal")
        delta_str  = f"{delta:+.3f}" if delta is not None and math.isfinite(delta) else "N/D"
        peso_o     = c.get("peso_no_otimo_expandido", 0)
        peso_str   = f"{peso_o*100:.1f}%" if peso_o else "  0%"
        classif    = c.get("classificacao", "NEUTRO")
        icone      = _icone(classif)
        print(f"  {ticker:<10} {sh_prop:<8} {corr:<11} {delta_str:<10} {peso_str:<12} {icone} {classif}")

    # Pesos sugeridos no ótimo expandido (apenas ativos com peso relevante)
    pesos_exp = resultado.get("pesos_otimo_expandido", {})
    novos = {t: p for t, p in pesos_exp.items() if t not in cart_t and p >= 0.01}
    alterados = {t: p for t, p in pesos_exp.items() if t in cart_t}

    if novos:
        print(f"\n  {'─'*68}")
        print(f"  COMPOSIÇÃO DO ÓTIMO EXPANDIDO — ativos da watchlist que entrariam:")
        for t, p in sorted(novos.items(), key=lambda x: -x[1]):
            print(f"    + {t:<10}  {p*100:.1f}%")

    if alterados:
        # Compara com pesos atuais (iguais por simplificação — pesos reais viriam do quant cache)
        n_cart = len(cart_t)
        peso_atual_ref = 1.0 / n_cart if n_cart else 0
        print(f"\n  Ativos da carteira com pesos ajustados no ótimo expandido:")
        for t, p in sorted(alterados.items(), key=lambda x: -abs(x[1] - peso_atual_ref)):
            delta_p = (p - peso_atual_ref) * 100
            seta = "▲" if delta_p > 0 else "▼"
            print(f"    {seta} {t:<10}  {p*100:.1f}%  ({delta_p:+.1f}% vs peso atual)")

    print(f"\n  Legenda:  ✅ melhora Sharpe  ⚠️  neutro/marginal  🔴 piora ou não entra")
    print(f"  Dica: /analisar TICKER para analisar candidato ✅ antes de decidir")
    print(f"{'═'*70}\n")


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    hoje = date.today().strftime("%Y-%m-%d")
    print(f"\nAnálise de Expansão — {hoje}")
    print("=" * 50)

    cart_tickers = _carteira_tickers()
    wl_tickers = _watchlist_tickers(cart_tickers)
    selic = _selic_do_cache()

    if not cart_tickers:
        print("Carteira vazia. Adicione ativos com /adicionar.")
        sys.exit(1)

    print(f"Carteira: {cart_tickers}")
    print(f"Watchlist: {wl_tickers if wl_tickers else '(vazia)'}")
    print(f"Selic: {selic*100:.2f}%\n")

    # ── Buscar históricos ────────────────────────────────────────────────────
    historicos: dict[str, pd.Series] = {}

    print("Carregando históricos da carteira...")
    for t in cart_tickers:
        h = _buscar_historico(_yahoo(t))
        if h is not None:
            historicos[t] = h
            print(f"  ✓ {t}")
        else:
            print(f"  ✗ {t} — histórico insuficiente")

    print("\nCarregando históricos da watchlist...")
    wl_com_hist = []
    for t in wl_tickers:
        h = _buscar_historico(_yahoo(t))
        if h is not None:
            historicos[t] = h
            wl_com_hist.append(t)
            print(f"  ✓ {t}")
        else:
            print(f"  ✗ {t} — histórico insuficiente (excluído)")

    cart_validos = [t for t in cart_tickers if t in historicos]
    if len(cart_validos) < 2:
        print("\nHistórico insuficiente para calcular fronteira.")
        sys.exit(1)

    # ── Retornos diários ─────────────────────────────────────────────────────
    todos_com_hist = cart_validos + wl_com_hist
    retornos_raw = {t: historicos[t].pct_change().dropna() for t in todos_com_hist}
    retornos_df_all = pd.DataFrame(retornos_raw).dropna()

    retornos_base = retornos_df_all[cart_validos].copy()
    n_cart = len(cart_validos)
    pesos_eq = np.array([1.0 / n_cart] * n_cart)

    # ── Fronteira base ───────────────────────────────────────────────────────
    print("\nCalculando fronteira base (carteira atual)...")
    pesos_base_dict = {t: 1.0 / n_cart for t in cart_validos}
    optim_base = otimizar_carteira(
        tickers=cart_validos,
        retornos_df=retornos_base,
        pesos_atual=pesos_base_dict,
        selic=selic,
        n_sim=8_000,
    )

    # ── Fronteira expandida ──────────────────────────────────────────────────
    resultado_expansao = None
    pesos_exp_dict_final: dict[str, float] = {}
    candidatos: list[dict] = []

    if wl_com_hist:
        print("Calculando fronteira expandida (carteira + watchlist)...")
        n_todos = len(todos_com_hist)
        pesos_todos_dict = {t: 1.0 / n_todos for t in todos_com_hist}
        optim_exp = otimizar_carteira(
            tickers=todos_com_hist,
            retornos_df=retornos_df_all,
            pesos_atual=pesos_todos_dict,
            selic=selic,
            n_sim=8_000,
        )
        resultado_expansao = optim_exp

        # Pesos no ótimo expandido por ticker
        ms_exp = (optim_exp.get("max_sharpe") or {})
        if ms_exp and ms_exp.get("pesos"):
            pesos_exp_dict_final = {
                t: round(float(p), 4)
                for t, p in zip(todos_com_hist, ms_exp["pesos"])
            }

        # ── Por candidato da watchlist ────────────────────────────────────
        print("Calculando contribuição marginal de cada ativo da watchlist...")
        retorno_carteira_ponderado = (retornos_base * pesos_eq).sum(axis=1)

        for t in wl_com_hist:
            ret_serie = retornos_df_all[t]
            ret_serie_alinhado = ret_serie.reindex(retornos_base.index).dropna()

            # Sharpe próprio
            ret_anual_t = float(ret_serie.mean() * 252)
            vol_t = float(ret_serie.std() * np.sqrt(252))
            sh_proprio = round((ret_anual_t - selic) / vol_t, 3) if vol_t > 1e-9 else None

            # Correlação com a carteira
            corr = _correlacao_com_carteira(ret_serie_alinhado, retorno_carteira_ponderado)

            # Delta Sharpe marginal (adiciona a 5% da carteira)
            delta = _sharpe_marginal(t, ret_serie, retornos_base, pesos_eq, selic, 0.05)

            # Peso que recebe no ótimo expandido
            peso_otimo = pesos_exp_dict_final.get(t, 0.0)

            classif = _classificar(peso_otimo, delta if math.isfinite(delta) else float("nan"))

            candidatos.append({
                "ticker": t,
                "sharpe_proprio": sh_proprio,
                "correlacao_carteira": round(corr, 3) if math.isfinite(corr) else None,
                "delta_sharpe_marginal": round(delta, 4) if math.isfinite(delta) else None,
                "peso_no_otimo_expandido": peso_otimo,
                "classificacao": classif,
            })

        # Ordenar: MELHORA primeiro, depois NEUTRO, depois PIORA; dentro de cada grupo por delta
        ordem = {"MELHORA": 0, "NEUTRO": 1, "PIORA": 2}
        candidatos.sort(key=lambda x: (
            ordem.get(x["classificacao"], 1),
            -(x["delta_sharpe_marginal"] or 0)
        ))

    # ── Ganho de Sharpe ──────────────────────────────────────────────────────
    sh_base = (optim_base.get("max_sharpe") or {}).get("sharpe")
    sh_exp  = (resultado_expansao.get("max_sharpe") or {}).get("sharpe") if resultado_expansao else None
    ganho = round(sh_exp - sh_base, 4) if sh_base and sh_exp else None

    # ── Montar resultado final ───────────────────────────────────────────────
    resultado = {
        "data_calculo": hoje,
        "carteira_tickers": cart_validos,
        "watchlist_tickers": wl_com_hist,
        "selic_anual": selic,
        "fronteira_base": {
            "max_sharpe": optim_base.get("max_sharpe"),
            "min_vol":    optim_base.get("min_vol"),
        },
        "fronteira_expandida": {
            "max_sharpe": (resultado_expansao or {}).get("max_sharpe"),
            "min_vol":    (resultado_expansao or {}).get("min_vol"),
        } if resultado_expansao else None,
        "ganho_sharpe_expansao": ganho,
        "candidatos": candidatos,
        "pesos_otimo_expandido": pesos_exp_dict_final,
    }

    # ── Salvar cache ─────────────────────────────────────────────────────────
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_path = CACHE_DIR / f"optim_expansao_{hoje}.json"
    cache_path.write_text(json.dumps(resultado, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nJSON salvo: {cache_path}")

    _imprimir_resultado(resultado)
    return resultado


if __name__ == "__main__":
    main()
