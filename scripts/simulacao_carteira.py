"""
simulacao_carteira.py — Backtest histórico (Parte B) + Monte Carlo (Parte A)

Quando a carteira estiver vazia, usa proxies por classe de ativo conforme alocação IPS:
  Ações BR 25%  ->BOVA11.SA  (ETF IBOVESPA)
  FIIs 35%      ->KNRI11.SA  (FII representativo com histórico desde 2010)
  ETFs Internac 8% → IVVB11.SA (S&P 500 em BRL)
  Renda Fixa 20% → CDI diário (BCB série 12)
  Tesouro Direto 12% → IPCA + 5% a.a. (BCB série 433 + spread)

Uso:
  python scripts/simulacao_carteira.py
  python scripts/simulacao_carteira.py --patrimonio 50000
  python scripts/simulacao_carteira.py --patrimonio 50000 --aporte 1000
  python scripts/simulacao_carteira.py --anos 10 20 30 --historico 5
"""

import argparse
import io
import sys
import warnings
from datetime import date, timedelta

# Força UTF-8 no terminal Windows (evita UnicodeEncodeError com caracteres especiais)
if sys.platform == "win32" and hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace", line_buffering=True)
from pathlib import Path

warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd
import requests
import yfinance as yf

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from matplotlib.gridspec import GridSpec

PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = PROJECT_ROOT / "logs" / "simulacao"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

TODAY = date.today()
TODAY_STR = TODAY.isoformat()

# ─── Configuração IPS ────────────────────────────────────────────────────────
PROXY_CONFIG = [
    {"nome": "Ações BR",        "ticker": "BOVA11.SA",  "peso": 0.25, "tipo": "yfinance"},
    {"nome": "FIIs",            "ticker": "KNRI11.SA",  "peso": 0.35, "tipo": "yfinance"},
    {"nome": "ETFs Internac.",  "ticker": "IVVB11.SA",  "peso": 0.08, "tipo": "yfinance"},
    {"nome": "Renda Fixa",      "ticker": None,          "peso": 0.20, "tipo": "cdi"},
    {"nome": "Tesouro Direto",  "ticker": None,          "peso": 0.12, "tipo": "ipca_plus"},
]

IPCA_PLUS_SPREAD = 0.05   # 5% a.a. real acima do IPCA (Tesouro IPCA+)
SELIC_FALLBACK   = 0.1065 # usado se BCB indisponível

# ─── Tema ────────────────────────────────────────────────────────────────────
COR_FUNDO  = "#0f1117"
COR_GRADE  = "#2a2a3a"
COR_TEXTO  = "#e0e0e0"
COR_CART   = "#4CAF50"
COR_IBOV   = "#2196F3"
COR_CDI    = "#FF9800"
COR_PAINEL = "#161b27"


# ─── Coleta de dados ─────────────────────────────────────────────────────────

def _fetch_bcb(serie: int, anos: int) -> pd.Series:
    """Coleta série do BCB/SGS. Retorna série diária/mensal indexada por data."""
    inicio = (TODAY - timedelta(days=anos * 365 + 60)).strftime("%d/%m/%Y")
    fim = TODAY.strftime("%d/%m/%Y")
    url = (
        f"https://api.bcb.gov.br/dados/serie/bcdata.sgs.{serie}/dados"
        f"?formato=json&dataInicial={inicio}&dataFinal={fim}"
    )
    try:
        r = requests.get(url, timeout=20)
        r.raise_for_status()
        dados = r.json()
        registros = []
        for d in dados:
            val = d.get("valor")
            if val not in (None, "", "null"):
                try:
                    registros.append({
                        "data": pd.to_datetime(d["data"], format="%d/%m/%Y"),
                        "valor": float(str(val).replace(",", ".")) / 100,
                    })
                except (ValueError, TypeError):
                    pass
        if not registros:
            return pd.Series(dtype=float)
        return pd.DataFrame(registros).set_index("data")["valor"].sort_index()
    except Exception as e:
        print(f"    Aviso BCB série {serie}: {e}")
        return pd.Series(dtype=float)


def fetch_cdi(anos: int) -> pd.Series:
    print("  ->Renda Fixa (CDI — BCB série 12)")
    return _fetch_bcb(12, anos)


def fetch_ipca(anos: int) -> pd.Series:
    print("  ->Tesouro Direto (IPCA — BCB série 433)")
    return _fetch_bcb(433, anos)


def fetch_yf_returns(ticker: str, anos: int) -> pd.Series:
    inicio = (TODAY - timedelta(days=anos * 365 + 60)).strftime("%Y-%m-%d")
    try:
        hist = yf.download(ticker, start=inicio, progress=False, auto_adjust=True)
        if hist.empty or len(hist) < 100:
            return pd.Series(dtype=float, name=ticker)
        close = hist["Close"]
        if isinstance(close, pd.DataFrame):
            close = close.iloc[:, 0]
        returns = close.pct_change().dropna()
        returns.name = ticker
        return returns
    except Exception as e:
        print(f"    Aviso yfinance {ticker}: {e}")
        return pd.Series(dtype=float, name=ticker)


# ─── Construção da carteira ──────────────────────────────────────────────────

def build_portfolio_returns(anos: int) -> tuple[pd.Series, dict]:
    """
    Monta série de retornos diários ponderados conforme PROXY_CONFIG.
    Retorna (retornos_carteira, dict de componentes).
    """
    print("\nBaixando dados históricos...")

    # 1. Tickers yfinance
    yf_retornos: dict[str, pd.Series] = {}
    for cfg in PROXY_CONFIG:
        if cfg["tipo"] == "yfinance":
            print(f"  ->{cfg['nome']} ({cfg['ticker']})")
            r = fetch_yf_returns(cfg["ticker"], anos)
            if not r.empty:
                yf_retornos[cfg["nome"]] = r
            else:
                print(f"    Sem dados. Usando CDI como fallback.")

    # 2. Índice de datas comuns entre tickers com dados
    series_validas = [s for s in yf_retornos.values() if not s.empty]
    if not series_validas:
        raise ValueError("Sem dados históricos disponíveis.")
    idx = series_validas[0].index
    for s in series_validas[1:]:
        idx = idx.intersection(s.index)
    idx = pd.DatetimeIndex(sorted(idx))

    # 3. BCB
    cdi  = fetch_cdi(anos)
    ipca = fetch_ipca(anos)

    # 4. Construir série por componente
    componentes: dict[str, pd.Series] = {}
    for cfg in PROXY_CONFIG:
        nome = cfg["nome"]
        if cfg["tipo"] == "yfinance":
            if nome in yf_retornos:
                componentes[nome] = yf_retornos[nome].reindex(idx).fillna(0.0)
            else:
                componentes[nome] = _cdi_fallback(cdi, idx)
        elif cfg["tipo"] == "cdi":
            componentes[nome] = _cdi_fallback(cdi, idx)
        elif cfg["tipo"] == "ipca_plus":
            componentes[nome] = _ipca_plus_daily(ipca, IPCA_PLUS_SPREAD, idx)

    # 5. Retorno ponderado
    df = pd.DataFrame(componentes)
    ret_cart = sum(df[n] * cfg["peso"] for cfg in PROXY_CONFIG if (n := cfg["nome"]) in df.columns)
    ret_cart.name = "Carteira IPS"

    return ret_cart, componentes


def _cdi_fallback(cdi: pd.Series, idx: pd.DatetimeIndex) -> pd.Series:
    if not cdi.empty:
        return cdi.reindex(idx, method="ffill").fillna((1 + SELIC_FALLBACK) ** (1 / 252) - 1)
    fallback_diario = (1 + SELIC_FALLBACK) ** (1 / 252) - 1
    return pd.Series(fallback_diario, index=idx)


def _ipca_plus_daily(ipca: pd.Series, spread: float, idx: pd.DatetimeIndex) -> pd.Series:
    spread_diario = (1 + spread) ** (1 / 252) - 1
    if ipca.empty:
        ipca_anual = 0.05
        ret = (1 + ipca_anual) ** (1 / 252) - 1 + spread_diario
        return pd.Series(ret, index=idx)
    ipca_al = ipca.reindex(idx, method="ffill").fillna(ipca.mean())
    ipca_diario = (1 + ipca_al) ** (1 / 22) - 1  # mensal → diário útil
    return ipca_diario + spread_diario


# ─── Monte Carlo ─────────────────────────────────────────────────────────────

def monte_carlo(
    retornos: pd.Series,
    anos_lista: list[int],
    n_sim: int,
    patrimonio: float,
    aporte_mensal: float = 0.0,
) -> tuple[dict, float, float]:
    """
    GBM paramétrico com aporte mensal opcional.
    Drift ajustado: μ - σ²/2 (correção Itô).
    """
    mu    = retornos.mean()
    sigma = retornos.std()
    drift = mu - 0.5 * sigma ** 2

    resultados: dict[int, np.ndarray] = {}
    rng = np.random.default_rng(seed=42)

    for anos in anos_lista:
        dias = int(anos * 252)
        Z = rng.standard_normal((n_sim, dias))

        wealth = np.full(n_sim, patrimonio, dtype=np.float64)
        paths  = np.zeros((n_sim, dias), dtype=np.float64)

        for d in range(dias):
            wealth *= np.exp(drift + sigma * Z[:, d])
            if aporte_mensal > 0 and (d + 1) % 22 == 0:
                wealth += aporte_mensal
            paths[:, d] = wealth

        resultados[anos] = paths

    return resultados, mu, sigma


# ─── Gráficos ────────────────────────────────────────────────────────────────

def _ax_style(ax):
    ax.set_facecolor(COR_PAINEL)
    ax.tick_params(colors=COR_TEXTO, labelsize=8)
    ax.grid(True, color=COR_GRADE, alpha=0.5, linewidth=0.6)
    for sp in ax.spines.values():
        sp.set_color(COR_GRADE)


def plot_backtest(
    ret_cart: pd.Series,
    cdi: pd.Series,
    ibov_ret: pd.Series,
    output_path: Path,
):
    fig = plt.figure(figsize=(14, 9), facecolor=COR_FUNDO)
    fig.suptitle(
        "Parte B — Backtest Histórico  |  Carteira IPS vs Benchmarks",
        color="white", fontsize=13, fontweight="bold", y=0.99,
    )

    gs = GridSpec(3, 1, figure=fig, hspace=0.45, height_ratios=[3, 1.5, 1.5])

    idx = ret_cart.index

    # Alinha benchmarks ao mesmo índice
    cdi_al  = (_cdi_fallback(cdi, idx) if cdi.empty
               else cdi.reindex(idx, method="ffill").fillna(cdi.mean()))
    ibov_al = (ibov_ret.reindex(idx).fillna(0.0) if not ibov_ret.empty
               else pd.Series(0.0, index=idx))

    cum_cart = (1 + ret_cart).cumprod() * 100 - 100
    cum_cdi  = (1 + cdi_al).cumprod()  * 100 - 100
    cum_ibov = (1 + ibov_al).cumprod() * 100 - 100

    # ── Painel 1: retorno acumulado ──────────────────────────────────────────
    ax1 = fig.add_subplot(gs[0])
    _ax_style(ax1)
    ax1.plot(cum_cart.index, cum_cart, color=COR_CART,  lw=2.2, label="Carteira IPS", zorder=3)
    ax1.plot(cum_ibov.index, cum_ibov, color=COR_IBOV,  lw=1.6, alpha=0.85, label="IBOVESPA")
    ax1.plot(cum_cdi.index,  cum_cdi,  color=COR_CDI,   lw=1.6, alpha=0.85, label="CDI")
    ax1.axhline(0, color="#555", lw=0.6, linestyle="--")
    ax1.set_ylabel("Retorno acumulado (%)", color=COR_TEXTO, fontsize=9)
    ax1.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:.0f}%"))
    ax1.legend(loc="upper left", facecolor="#1a1a2e", labelcolor=COR_TEXTO, fontsize=9,
               framealpha=0.8)
    ax1.set_title("Retorno Acumulado", color=COR_TEXTO, fontsize=10, pad=5)

    # ── Painel 2: rolling 12m ────────────────────────────────────────────────
    ax2 = fig.add_subplot(gs[1])
    _ax_style(ax2)
    r12_cart = (1 + ret_cart).rolling(252).apply(np.prod, raw=True) - 1
    r12_ibov = (1 + ibov_al).rolling(252).apply(np.prod, raw=True) - 1
    ax2.plot(r12_cart.index, r12_cart * 100, color=COR_CART, lw=1.5, label="Carteira IPS")
    ax2.plot(r12_ibov.index, r12_ibov * 100, color=COR_IBOV, lw=1.2, alpha=0.7, label="IBOV")
    ax2.axhline(0, color="#555", lw=0.6, linestyle="--")
    ax2.set_ylabel("Retorno 12m (%)", color=COR_TEXTO, fontsize=9)
    ax2.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:.0f}%"))
    ax2.legend(loc="upper left", facecolor="#1a1a2e", labelcolor=COR_TEXTO, fontsize=8,
               framealpha=0.8)
    ax2.set_title("Retorno Rolling 12 meses", color=COR_TEXTO, fontsize=10, pad=5)

    # ── Painel 3: drawdown ───────────────────────────────────────────────────
    ax3 = fig.add_subplot(gs[2])
    _ax_style(ax3)
    cum_price = (1 + ret_cart).cumprod()
    dd = (cum_price / cum_price.cummax() - 1) * 100
    ax3.fill_between(dd.index, dd, 0, color="#ef5350", alpha=0.45)
    ax3.plot(dd.index, dd, color="#ef5350", lw=1.2)
    ax3.axhline(-18, color=COR_CDI, lw=1, linestyle="--", alpha=0.75,
                label="Limite IPS (−18%)")
    ax3.set_ylabel("Drawdown (%)", color=COR_TEXTO, fontsize=9)
    ax3.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:.0f}%"))
    ax3.legend(loc="lower left", facecolor="#1a1a2e", labelcolor=COR_TEXTO, fontsize=8,
               framealpha=0.8)
    ax3.set_title("Drawdown", color=COR_TEXTO, fontsize=10, pad=5)

    # ── Métricas no rodapé ───────────────────────────────────────────────────
    ret_a = (1 + ret_cart.mean()) ** 252 - 1
    vol_a = ret_cart.std() * np.sqrt(252)
    sharpe = (ret_a - SELIC_FALLBACK) / vol_a if vol_a > 0 else 0
    dd_max = dd.min()
    periodo = f"{ret_cart.index[0].strftime('%Y-%m')} → {ret_cart.index[-1].strftime('%Y-%m')}"

    fig.text(
        0.5, 0.003,
        f"Período: {periodo}   |   Ret. anual: {ret_a*100:.1f}%   |   "
        f"Vol: {vol_a*100:.1f}%   |   Sharpe: {sharpe:.2f}   |   Max DD: {dd_max:.1f}%",
        ha="center", color="#aaa", fontsize=9,
    )

    plt.savefig(output_path, dpi=150, bbox_inches="tight", facecolor=COR_FUNDO)
    plt.close(fig)
    print(f"  OK:Backtest salvo: {output_path}")


def plot_montecarlo(
    resultados: dict,
    anos_lista: list[int],
    patrimonio: float,
    aporte_mensal: float,
    output_path: Path,
    mu_anual: float,
    sigma_anual: float,
):
    n = len(anos_lista)
    fig, axes = plt.subplots(1, n, figsize=(6 * n, 8), facecolor=COR_FUNDO)
    if n == 1:
        axes = [axes]

    titulo_aporte = f"   |   Aporte mensal: R$ {aporte_mensal:,.0f}" if aporte_mensal > 0 else ""
    fig.suptitle(
        f"Parte A — Monte Carlo  |  {len(resultados[anos_lista[0]]):,} simulações\n"
        f"Patrimônio inicial: R$ {patrimonio:,.0f}{titulo_aporte}   |   "
        f"μ anual: {mu_anual*100:.1f}%   σ anual: {sigma_anual*100:.1f}%",
        color="white", fontsize=11, fontweight="bold",
    )

    PERCENTIS = [5, 25, 50, 75, 95]

    for i, anos in enumerate(anos_lista):
        ax = axes[i]
        _ax_style(ax)

        matriz = resultados[anos]
        dias_total = matriz.shape[1]
        eixo_x = np.linspace(0, anos, dias_total + 1)

        # inclui ponto inicial
        inicio_col = np.full((matriz.shape[0], 1), patrimonio)
        m_full = np.hstack([inicio_col, matriz])

        pct = {p: np.percentile(m_full, p, axis=0) for p in PERCENTIS}

        # Fan chart
        ax.fill_between(eixo_x, pct[5],  pct[95], color="#0d2b4a", alpha=0.55, label="P5–P95")
        ax.fill_between(eixo_x, pct[25], pct[75], color="#1565C0", alpha=0.50, label="P25–P75")
        ax.plot(eixo_x, pct[50], color="#42A5F5", lw=2.5, label="Mediana (P50)", zorder=3)
        ax.plot(eixo_x, pct[95], color="#90CAF9", lw=0.9, linestyle="--", alpha=0.65)
        ax.plot(eixo_x, pct[5],  color="#90CAF9", lw=0.9, linestyle="--", alpha=0.65)
        ax.axhline(patrimonio, color=COR_CDI, lw=1, linestyle=":", alpha=0.55,
                   label="Patrimônio inicial")

        # Anotação final
        def _fmt(v: float) -> str:
            if v >= 1e6:
                return f"R$ {v/1e6:.2f}M"
            if v >= 1e3:
                return f"R$ {v/1e3:.0f}k"
            return f"R$ {v:,.0f}"

        p50_final = pct[50][-1]
        ax.annotate(
            f"Mediana\n{_fmt(p50_final)}",
            xy=(anos, p50_final),
            xytext=(-70, 14),
            textcoords="offset points",
            color="#42A5F5", fontsize=8,
            arrowprops=dict(arrowstyle="->", color="#42A5F5", lw=0.9),
        )

        # Tabela de percentis no canto
        tabela_linhas = [
            f"P95: {_fmt(pct[95][-1])}",
            f"P75: {_fmt(pct[75][-1])}",
            f"P50: {_fmt(pct[50][-1])}",
            f"P25: {_fmt(pct[25][-1])}",
            f"P5:  {_fmt(pct[5][-1])}",
        ]
        ax.text(
            0.03, 0.97, "\n".join(tabela_linhas),
            transform=ax.transAxes,
            color=COR_TEXTO, fontsize=7.5,
            verticalalignment="top",
            fontfamily="monospace",
            bbox=dict(facecolor="#1a1a2e", alpha=0.75, boxstyle="round,pad=0.4"),
        )

        ax.set_xlabel("Anos", color=COR_TEXTO, fontsize=10)
        ax.set_ylabel("Patrimônio", color=COR_TEXTO, fontsize=10)
        ax.set_title(f"Horizonte: {anos} anos", color=COR_TEXTO, fontsize=11,
                     fontweight="bold")
        ax.yaxis.set_major_formatter(mticker.FuncFormatter(
            lambda x, _: f"R${x/1e6:.1f}M" if x >= 1e6 else f"R${x/1e3:.0f}k"
        ))
        ax.legend(loc="lower right", facecolor="#1a1a2e", labelcolor=COR_TEXTO,
                  fontsize=8, framealpha=0.8)
        ax.set_xlim(0, anos)
        ax.set_ylim(bottom=0)

    plt.tight_layout(rect=[0, 0, 1, 0.90])
    plt.savefig(output_path, dpi=150, bbox_inches="tight", facecolor=COR_FUNDO)
    plt.close(fig)
    print(f"  OK:Monte Carlo salvo: {output_path}")


# ─── Resumo terminal ─────────────────────────────────────────────────────────

def print_summary(
    ret_cart: pd.Series,
    mc_resultados: dict,
    anos_lista: list[int],
    patrimonio: float,
    aporte_mensal: float,
):
    mu    = ret_cart.mean()
    sigma = ret_cart.std()
    ret_a = (1 + mu) ** 252 - 1
    vol_a = sigma * np.sqrt(252)
    sharpe = (ret_a - SELIC_FALLBACK) / vol_a if vol_a > 0 else 0
    cum = (1 + ret_cart).cumprod()
    dd_max = (cum / cum.cummax() - 1).min()

    print("\n" + "=" * 62)
    print("  BACKTEST -- METRICAS HISTORICAS (ALOCACAO IPS)")
    print("=" * 62)
    print(f"  Retorno anualizado  : {ret_a*100:.1f}%")
    print(f"  Volatilidade anual  : {vol_a*100:.1f}%")
    print(f"  Sharpe ratio        : {sharpe:.2f}  (Selic fallback {SELIC_FALLBACK*100:.1f}%)")
    print(f"  Max Drawdown        : {dd_max*100:.1f}%")
    print(f"  Periodo             : {ret_cart.index[0].strftime('%Y-%m-%d')} a "
          f"{ret_cart.index[-1].strftime('%Y-%m-%d')}")

    def _fmt(v: float) -> str:
        return f"R${v/1e6:.2f}M" if v >= 1e6 else f"R${v/1e3:.0f}k"

    print("\n" + "=" * 62)
    print("  MONTE CARLO -- PROJECAO DE PATRIMONIO")
    print("=" * 62)
    print(f"  Patrimonio inicial  : R$ {patrimonio:,.2f}")
    if aporte_mensal > 0:
        print(f"  Aporte mensal       : R$ {aporte_mensal:,.2f}")
    print(f"  Simulacoes          : {len(mc_resultados[anos_lista[0]]):,}")
    print()
    header = f"  {'Anos':<7} {'P5':>12} {'P25':>12} {'P50 (mediana)':>15} {'P75':>12} {'P95':>12}"
    print(header)
    print("  " + "-" * 67)
    for anos in anos_lista:
        finais = mc_resultados[anos][:, -1]
        p = {k: np.percentile(finais, k) for k in [5, 25, 50, 75, 95]}
        print(f"  {anos:<7} {_fmt(p[5]):>12} {_fmt(p[25]):>12} "
              f"{_fmt(p[50]):>15} {_fmt(p[75]):>12} {_fmt(p[95]):>12}")
    print("=" * 62)


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Backtest histórico + Monte Carlo — Carteira IPS SBWAA"
    )
    parser.add_argument("--patrimonio",  type=float, default=10_000,
                        help="Patrimônio inicial para Monte Carlo (R$) [padrão: 10000]")
    parser.add_argument("--aporte",      type=float, default=0.0,
                        help="Aporte mensal no Monte Carlo (R$) [padrão: 0]")
    parser.add_argument("--anos",        type=int, nargs="+", default=[10, 20, 30],
                        help="Horizontes Monte Carlo em anos [padrão: 10 20 30]")
    parser.add_argument("--historico",   type=int, default=5,
                        help="Anos de histórico para backtest [padrão: 5]")
    parser.add_argument("--simulacoes",  type=int, default=10_000,
                        help="Número de simulações [padrão: 10000]")
    parser.add_argument("--no-graficos", action="store_true",
                        help="Apenas terminal, sem gerar PNGs")
    args = parser.parse_args()

    print("=" * 62)
    print("  SBWAA — Simulação de Carteira")
    print("  Parte A: Monte Carlo  |  Parte B: Backtest Histórico")
    print("=" * 62)
    print("\n  Alocação IPS (proxies por classe de ativo):")
    for cfg in PROXY_CONFIG:
        label = cfg["ticker"] or cfg["tipo"].upper()
        print(f"    {cfg['nome']:<20}  {cfg['peso']*100:.0f}%   [{label}]")

    # Dados históricos
    ret_cart, _ = build_portfolio_returns(args.historico)

    print("\n  ->Benchmark IBOV (^BVSP)")
    ibov_ret = fetch_yf_returns("^BVSP", args.historico)

    print("  ->CDI benchmark (BCB série 12)")
    cdi = fetch_cdi(args.historico)

    # Monte Carlo
    print(f"\nRodando Monte Carlo ({args.simulacoes:,} simulações)...")
    mc_resultados, mu, sigma = monte_carlo(
        ret_cart, args.anos, args.simulacoes, args.patrimonio, args.aporte
    )
    mu_anual    = (1 + mu) ** 252 - 1
    sigma_anual = sigma * np.sqrt(252)

    # Resumo no terminal
    print_summary(ret_cart, mc_resultados, args.anos, args.patrimonio, args.aporte)

    # Salva parâmetros em cache para /carteira usar sem refazer o download
    import json as _json
    params_cache = {
        "mu_anual":       mu_anual,
        "sigma_anual":    sigma_anual,
        "data":           TODAY_STR,
        "historico_anos": args.historico,
    }
    (OUTPUT_DIR / "params_cache.json").write_text(
        _json.dumps(params_cache, indent=2), encoding="utf-8"
    )

    if args.no_graficos:
        print(f"\nOK: Simulacao concluida (sem graficos). Cache salvo em {OUTPUT_DIR}")
        return

    # Gráficos
    print("\nGerando gráficos...")
    path_bt = OUTPUT_DIR / f"backtest_{TODAY_STR}.png"
    path_mc = OUTPUT_DIR / f"montecarlo_{TODAY_STR}.png"

    plot_backtest(ret_cart, cdi, ibov_ret, path_bt)
    plot_montecarlo(
        mc_resultados, args.anos, args.patrimonio, args.aporte,
        path_mc, mu_anual, sigma_anual,
    )

    print(f"\nOK:Arquivos salvos em: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
