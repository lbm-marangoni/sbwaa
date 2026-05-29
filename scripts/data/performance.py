"""
performance.py — Benchmark automático de performance da carteira SBWAA.
Retorno da carteira vs IBOV, CDI, IPCA para MTD / YTD / 12m.
Alpha, beta, tracking error, Sharpe.
Salva série histórica em vault/02-relatorios/performance-historico.json.

Uso: python scripts/data/performance.py
"""

import re
import sys
import json
import math
from datetime import date, datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd
import yfinance as yf

PROJECT_ROOT  = Path(__file__).parent.parent.parent
VAULT_ROOT    = PROJECT_ROOT / "vault"
SCRIPTS_DATA  = PROJECT_ROOT / "scripts" / "data"
CACHE_DIR     = SCRIPTS_DATA / "cache"
CARTEIRA_PATH = VAULT_ROOT / "00-portfolio" / "carteira.md"
ATIVOS_DIR    = VAULT_ROOT / "01-ativos"
HISTORICO_PATH = VAULT_ROOT / "02-relatorios" / "performance-historico.json"

IBOV_TICKER = "^BVSP"

TIPOS_RF     = {"⬜ RF", "🟪 TD", "🟫 DEB", "🟧 CRI/CRA",
                "RF", "TD", "DEB", "CRI/CRA"}
TIPOS_EQUITY = {"🟦 AÇÃO ON", "🟦 AÇÃO PN", "🟩 FII",
                "🟨 ETF BR", "🟥 ETF INTL",
                "AÇÃO ON", "AÇÃO PN", "FII", "ETF BR", "ETF INTL"}

TIPO_CLASSE_MAP = {
    "🟦 AÇÃO ON":  "Ações BR",   "🟦 AÇÃO PN":  "Ações BR",
    "🟩 FII":      "FIIs",       "🟨 ETF BR":   "ETFs BR",
    "🟥 ETF INTL": "ETFs Intl",  "⬜ RF":       "Renda Fixa",
    "🟪 TD":       "Tesouro",    "🟫 DEB":      "Renda Fixa",
    "🟧 CRI/CRA":  "Renda Fixa",
}


# ── Helpers ────────────────────────────────────────────────────────────────────

def eh_ticker_br(t: str) -> bool:
    return bool(re.match(r"^[A-Z]{4}[0-9]{1,2}[FBP]?$", t))


def ticker_yf(t: str) -> str:
    return f"{t}.SA" if eh_ticker_br(t) else t


def _inicio_mes(d: date) -> date:
    return date(d.year, d.month, 1)


def _inicio_ano(d: date) -> date:
    return date(d.year, 1, 1)


def _inicio_12m(d: date) -> date:
    return d - timedelta(days=365)


def _fmt_pct(v: float | None, casas: int = 1) -> str:
    if v is None or math.isnan(v):
        return "  N/D  "
    return f"{v*100:+.{casas}f}%"


def _fmt_num(v: float | None, casas: int = 2) -> str:
    if v is None or math.isnan(v):
        return "  N/D"
    return f"{v:.{casas}f}"


# ── Leitura de carteira ────────────────────────────────────────────────────────

def extrair_posicoes() -> list[dict]:
    """Retorna lista de {ticker, tipo, setor, qtd, pm, classe} da carteira.md."""
    posicoes = []
    if not CARTEIRA_PATH.exists():
        return posicoes
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
            if len(cols) < 5:
                continue
            ticker_raw = cols[0].replace("[[", "").replace("]]", "").split("|")[0].strip()
            ticker_raw = re.sub(r"01-ativos/([^/]+)/tese", r"\1", ticker_raw).upper()
            if not ticker_raw:
                continue
            try:
                qtd = float(cols[3].replace(",", "."))
                pm  = float(cols[4].replace(",", ".").replace("R$", "").strip())
            except (ValueError, IndexError):
                continue
            tipo  = cols[1] if len(cols) > 1 else ""
            setor = cols[2] if len(cols) > 2 else ""
            posicoes.append({
                "ticker": ticker_raw,
                "tipo":   tipo,
                "setor":  setor,
                "qtd":    qtd,
                "pm":     pm,
                "classe": TIPO_CLASSE_MAP.get(tipo, "Outros"),
                "investido": qtd * pm,
                "eh_rf": tipo in TIPOS_RF,
            })
        elif dentro and not s.startswith("|"):
            break
    return posicoes


def ler_rf_params(ticker: str) -> dict:
    """Lê indexador, taxa e data_entrada do frontmatter de tese.md."""
    params = {"indexador": "CDI", "taxa": "100%", "data_entrada": None}
    tese = ATIVOS_DIR / ticker / "tese.md"
    if not tese.exists():
        return params
    for linha in tese.read_text(encoding="utf-8").splitlines():
        if linha.startswith("---") and linha.strip() != "---":
            continue
        for chave in ("indexador", "taxa", "data_entrada"):
            if linha.lower().startswith(f"{chave}:"):
                val = linha.split(":", 1)[1].strip().strip('"').strip("'")
                if val:
                    params[chave] = val
    return params


# ── BCB — CDI e IPCA ──────────────────────────────────────────────────────────

def carregar_bcb() -> dict | None:
    """Carrega cache BCB mais recente (até 7 dias). Tenta fetch se ausente."""
    hoje = date.today()
    for d in range(8):
        dt = (hoje - timedelta(days=d)).isoformat()
        path = CACHE_DIR / f"bcb_{dt}.json"
        if path.exists():
            try:
                return json.loads(path.read_text(encoding="utf-8"))
            except Exception:
                pass
    # Tenta fetch ao vivo
    try:
        sys.path.insert(0, str(SCRIPTS_DATA))
        from fetch_bcb import main as bcb_main  # type: ignore
        print("  BCB: cache ausente — buscando ao vivo...")
        return bcb_main()
    except Exception as e:
        print(f"  BCB: falha ao buscar ({e})")
        return None


def _serie_mensal(bcb: dict, serie: str) -> list[dict]:
    """Extrai historico mensal de uma série BCB."""
    try:
        return bcb["series"][serie]["historico"]
    except (KeyError, TypeError):
        return []


def _acumular_mensal(historico: list[dict], inicio: date, fim: date) -> float:
    """Compõe taxas mensais entre inicio e fim (inclusive meses parcialmente cobertos)."""
    acum = 1.0
    for entry in historico:
        try:
            data_str = entry["data"]  # formato "DD/MM/YYYY"
            partes = data_str.split("/")
            mes_ano = date(int(partes[2]), int(partes[1]), 1)
        except Exception:
            continue
        # Considera o mês se seu início cai no período [inicio, fim]
        if inicio <= mes_ano <= fim:
            acum *= (1 + entry["valor"] / 100)
    return acum - 1


def cdi_acumulado(inicio: date, fim: date, bcb: dict) -> float:
    """CDI acumulado entre inicio e fim usando selic_acum_mes."""
    historico = _serie_mensal(bcb, "selic_acum_mes")
    if not historico:
        # Fallback: selic_diaria
        hist_diaria = _serie_mensal(bcb, "selic_diaria")
        acum = 1.0
        for entry in hist_diaria:
            try:
                partes = entry["data"].split("/")
                d = date(int(partes[2]), int(partes[1]), int(partes[0]))
                if inicio <= d <= fim:
                    acum *= (1 + entry["valor"] / 100)
            except Exception:
                pass
        return acum - 1
    return _acumular_mensal(historico, _inicio_mes(inicio), _inicio_mes(fim))


def ipca_acumulado(inicio: date, fim: date, bcb: dict) -> float:
    """IPCA acumulado entre inicio e fim."""
    historico = _serie_mensal(bcb, "ipca_mensal")
    if not historico:
        # Fallback: ipca15
        historico = _serie_mensal(bcb, "ipca15_mensal")
    return _acumular_mensal(historico, _inicio_mes(inicio), _inicio_mes(fim))


def cdi_diario_series(inicio: date, fim: date, bcb: dict) -> pd.Series:
    """Retorna série de retornos diários CDI (para construção de série do portfólio)."""
    hist = _serie_mensal(bcb, "selic_diaria")
    datas, valores = [], []
    for entry in hist:
        try:
            partes = entry["data"].split("/")
            d = date(int(partes[2]), int(partes[1]), int(partes[0]))
            if inicio <= d <= fim:
                datas.append(pd.Timestamp(d))
                valores.append(entry["valor"] / 100)
        except Exception:
            pass
    if not datas:
        return pd.Series(dtype=float)
    return pd.Series(valores, index=datas)


# ── Retorno de ativos individuais ──────────────────────────────────────────────

def retorno_equity_periodo(ticker: str, inicio: date) -> float | None:
    """Retorno de um ativo equity via yfinance entre inicio e hoje."""
    try:
        hist = yf.download(
            ticker_yf(ticker),
            start=(inicio - timedelta(days=5)).isoformat(),
            auto_adjust=True,
            progress=False,
            threads=False,
        )
        if hist.empty:
            return None
        close = hist["Close"]
        if isinstance(close, pd.DataFrame):
            close = close.iloc[:, 0]
        close = close.dropna()
        if len(close) < 2:
            return None
        # Preço mais próximo do inicio e o mais recente
        close_filtrado = close[close.index.date >= inicio]
        if close_filtrado.empty:
            return None
        p_inicio = float(close_filtrado.iloc[0])
        p_fim    = float(close_filtrado.iloc[-1])
        return (p_fim / p_inicio) - 1
    except Exception:
        return None


def _parse_taxa(taxa_str: str, indexador: str) -> tuple[float, str]:
    """
    Retorna (fator, modo) onde:
      modo='pct_indexador' → taxa é % do indexador (ex: '110%' do CDI)
      modo='spread'        → taxa é spread sobre o indexador (ex: '+6%' IPCA)
      modo='pre'           → taxa fixa anual (ex: '13.5%')
    """
    s = taxa_str.strip().replace(",", ".")
    if s.startswith("+"):
        return float(s.replace("+", "").replace("%", "")) / 100, "spread"
    pct = float(s.replace("%", ""))
    if indexador in ("CDI", "Selic") and pct > 20:
        # Provavelmente é % do CDI (ex: 110%)
        return pct / 100, "pct_indexador"
    if pct > 2:
        # Taxa anual PRE (ex: 13.5%)
        return pct / 100, "pre"
    # Assume multiplicador do indexador
    return pct, "pct_indexador"


def estimar_retorno_rf(ticker: str, inicio: date, fim: date, bcb: dict) -> float:
    """Estima retorno RF para o período usando indexador/taxa de tese.md."""
    params = ler_rf_params(ticker)
    indexador = params.get("indexador", "CDI").upper()
    taxa_str  = params.get("taxa", "100%") or "100%"
    dias = max(1, (fim - inicio).days)

    try:
        fator, modo = _parse_taxa(taxa_str, indexador)
    except Exception:
        fator, modo = 1.0, "pct_indexador"

    if indexador in ("CDI", "SELIC"):
        cdi = cdi_acumulado(inicio, fim, bcb)
        if modo == "pct_indexador":
            return (1 + cdi) ** fator - 1 if fator != 1.0 else cdi
        elif modo == "spread":
            return cdi + fator * (dias / 252)
        else:
            return (1 + fator) ** (dias / 252) - 1

    elif indexador == "IPCA":
        ipca = ipca_acumulado(inicio, fim, bcb)
        if modo == "spread":
            return (1 + ipca) * (1 + fator * dias / 252) - 1
        else:
            return (1 + ipca) * fator - 1

    elif indexador in ("PRE", "IGPM"):
        return (1 + fator) ** (dias / 252) - 1

    # Fallback: CDI 100%
    return cdi_acumulado(inicio, fim, bcb)


# ── Retorno IBOV ───────────────────────────────────────────────────────────────

def retorno_ibov(inicio: date) -> float | None:
    return retorno_equity_periodo(IBOV_TICKER.replace(".SA", ""), inicio)


def hist_ibov_diario(inicio: date) -> pd.Series | None:
    """Série diária de retornos do IBOV."""
    try:
        hist = yf.download(
            IBOV_TICKER,
            start=inicio.isoformat(),
            auto_adjust=True,
            progress=False,
            threads=False,
        )
        if hist.empty:
            return None
        close = hist["Close"]
        if isinstance(close, pd.DataFrame):
            close = close.iloc[:, 0]
        return close.pct_change().dropna()
    except Exception:
        return None


# ── Retorno da carteira ────────────────────────────────────────────────────────

def calcular_retorno_carteira(
    posicoes: list[dict],
    inicio: date,
    bcb: dict,
) -> tuple[float | None, dict]:
    """
    Retorno ponderado por capital investido.
    Retorna (retorno_total, {classe: retorno_classe}).
    """
    total_investido = sum(p["investido"] for p in posicoes)
    if total_investido <= 0:
        return None, {}

    retornos_classe: dict[str, list] = {}
    pesos_classe: dict[str, float] = {}

    retorno_total_cart = 0.0
    cobertura = 0.0  # peso coberto por dados válidos

    for pos in posicoes:
        ticker   = pos["ticker"]
        peso     = pos["investido"] / total_investido
        classe   = pos["classe"]

        if pos["eh_rf"]:
            ret = estimar_retorno_rf(ticker, inicio, date.today(), bcb)
        else:
            ret = retorno_equity_periodo(ticker, inicio)
            if ret is None:
                continue  # pula ticker sem dados

        retorno_total_cart += peso * ret
        cobertura += peso
        retornos_classe.setdefault(classe, []).append((peso, ret))
        pesos_classe[classe] = pesos_classe.get(classe, 0) + peso

    if cobertura < 0.01:
        return None, {}

    # Normaliza pelo que foi coberto (caso alguns tickers falharam)
    if cobertura < 0.99:
        retorno_total_cart = retorno_total_cart / cobertura

    # Retorno por classe
    ret_por_classe = {}
    for classe, lista in retornos_classe.items():
        peso_total_classe = sum(p for p, _ in lista)
        if peso_total_classe > 0:
            ret_por_classe[classe] = sum(p * r for p, r in lista) / peso_total_classe

    return retorno_total_cart, ret_por_classe


# ── Métricas de risco ──────────────────────────────────────────────────────────

def calcular_metricas_risco(
    posicoes: list[dict],
    bcb: dict,
    inicio_12m: date,
) -> dict:
    """Calcula beta, tracking error, Sharpe, volatilidade (base: 12m)."""
    metricas = {
        "beta":            float("nan"),
        "tracking_error":  float("nan"),
        "sharpe":          float("nan"),
        "volatilidade":    float("nan"),
        "max_drawdown":    float("nan"),
    }

    hoje = date.today()
    total_investido = sum(p["investido"] for p in posicoes)
    if total_investido <= 0:
        return metricas

    # Série diária do IBOV
    ibov_daily = hist_ibov_diario(inicio_12m)
    if ibov_daily is None or len(ibov_daily) < 30:
        return metricas

    # Construir série diária do portfólio
    # Equities: yfinance; RF: CDI diário (série suave)
    series_equities: list[tuple[float, pd.Series]] = []
    peso_rf_total = 0.0

    for pos in posicoes:
        ticker = pos["ticker"]
        peso   = pos["investido"] / total_investido

        if pos["eh_rf"]:
            peso_rf_total += peso
        else:
            try:
                hist = yf.download(
                    ticker_yf(ticker),
                    start=inicio_12m.isoformat(),
                    auto_adjust=True, progress=False, threads=False,
                )
                if hist.empty:
                    continue
                close = hist["Close"]
                if isinstance(close, pd.DataFrame):
                    close = close.iloc[:, 0]
                ret_diario = close.pct_change().dropna()
                if len(ret_diario) >= 20:
                    series_equities.append((peso, ret_diario))
            except Exception:
                continue

    if not series_equities and peso_rf_total < 0.1:
        return metricas

    # Índice de referência: datas do IBOV
    idx = ibov_daily.index

    # Série do portfólio equity (ponderada)
    port_eq = pd.Series(0.0, index=idx)
    peso_equity_coberto = 0.0
    for peso, s in series_equities:
        s_alinhado = s.reindex(idx).fillna(0)
        port_eq += peso * s_alinhado
        peso_equity_coberto += peso

    # Adicionar contribuição RF (CDI diário suave)
    cdi_daily = cdi_diario_series(inicio_12m, hoje, bcb)
    if not cdi_daily.empty and peso_rf_total > 0:
        cdi_alinhado = cdi_daily.reindex(idx).fillna(cdi_daily.mean() if len(cdi_daily) > 0 else 0)
        port_eq += peso_rf_total * cdi_alinhado

    # Normaliza se cobertura parcial
    peso_total_coberto = peso_equity_coberto + peso_rf_total
    if peso_total_coberto > 0.1:
        port_eq = port_eq / peso_total_coberto

    if len(port_eq) < 30:
        return metricas

    # Beta
    try:
        df = pd.concat([port_eq, ibov_daily], axis=1).dropna()
        df.columns = ["port", "ibov"]
        cov_mat = np.cov(df["port"], df["ibov"])
        var_ibov = cov_mat[1][1]
        metricas["beta"] = float(cov_mat[0][1] / var_ibov) if var_ibov > 0 else float("nan")
    except Exception:
        pass

    # Tracking Error
    try:
        df_te = pd.concat([port_eq, ibov_daily], axis=1).dropna()
        diff = df_te.iloc[:, 0] - df_te.iloc[:, 1]
        metricas["tracking_error"] = float(diff.std() * math.sqrt(252))
    except Exception:
        pass

    # Volatilidade e Sharpe
    try:
        vol = float(port_eq.std() * math.sqrt(252))
        metricas["volatilidade"] = vol
        # CDI 12m como risk-free
        cdi_12m = cdi_acumulado(inicio_12m, hoje, bcb)
        ret_12m, _ = calcular_retorno_carteira(posicoes, inicio_12m, bcb)
        if ret_12m is not None and vol > 0:
            ret_anual = (1 + ret_12m) - 1  # já é 12m ≈ anual
            metricas["sharpe"] = (ret_anual - cdi_12m) / vol
    except Exception:
        pass

    # Max Drawdown
    try:
        curva = (1 + port_eq).cumprod()
        rolling_max = curva.cummax()
        dd = (curva / rolling_max - 1).min()
        metricas["max_drawdown"] = float(dd)
    except Exception:
        pass

    return metricas


# ── Histórico ──────────────────────────────────────────────────────────────────

def atualizar_historico(snapshot: dict):
    """Insere ou atualiza snapshot mensal em performance-historico.json."""
    dados: dict = {"ultima_atualizacao": date.today().isoformat(), "historico": []}
    HISTORICO_PATH.parent.mkdir(parents=True, exist_ok=True)

    if HISTORICO_PATH.exists():
        try:
            dados = json.loads(HISTORICO_PATH.read_text(encoding="utf-8"))
        except Exception:
            pass

    mes_ref = snapshot["mes_ref"]
    historico = dados.get("historico", [])
    # Substitui entrada existente do mesmo mês ou insere nova
    historico = [h for h in historico if h.get("mes_ref") != mes_ref]
    historico.append(snapshot)
    historico.sort(key=lambda h: h["mes_ref"])

    dados["ultima_atualizacao"] = date.today().isoformat()
    dados["historico"] = historico
    HISTORICO_PATH.write_text(json.dumps(dados, ensure_ascii=False, indent=2), encoding="utf-8")


# ── Exibição ───────────────────────────────────────────────────────────────────

def exibir_relatorio(
    hoje: date,
    ret: dict,
    bench: dict,
    metricas: dict,
    por_classe: dict,
):
    W = 62
    sep = "═" * W

    print(f"\n{sep}")
    print(f"  SBWAA — PERFORMANCE vs BENCHMARKS  ({hoje.isoformat()})")
    print(f"{sep}")
    print(f"\n  {'':20s} {'MTD':>8} {'YTD':>8} {'12M':>8}")
    print(f"  {'─'*50}")

    linhas = [
        ("Carteira",  ret.get("mtd"), ret.get("ytd"), ret.get("12m")),
        ("IBOV",      bench.get("ibov_mtd"), bench.get("ibov_ytd"), bench.get("ibov_12m")),
        ("CDI",       bench.get("cdi_mtd"),  bench.get("cdi_ytd"),  bench.get("cdi_12m")),
        ("IPCA",      bench.get("ipca_mtd"), bench.get("ipca_ytd"), bench.get("ipca_12m")),
    ]
    for label, mtd, ytd, m12 in linhas:
        print(f"  {label:<20s} {_fmt_pct(mtd):>8} {_fmt_pct(ytd):>8} {_fmt_pct(m12):>8}")

    print(f"  {'─'*50}")

    def alpha(cart, bm):
        if cart is None or bm is None:
            return None
        if math.isnan(cart) or math.isnan(bm):
            return None
        return cart - bm

    alpha_ibov_mtd = alpha(ret.get("mtd"), bench.get("ibov_mtd"))
    alpha_ibov_12m = alpha(ret.get("12m"), bench.get("ibov_12m"))
    alpha_cdi_mtd  = alpha(ret.get("mtd"), bench.get("cdi_mtd"))
    alpha_cdi_12m  = alpha(ret.get("12m"), bench.get("cdi_12m"))

    print(f"  {'Alpha vs IBOV':<20s} {_fmt_pct(alpha_ibov_mtd):>8} {'':>8} {_fmt_pct(alpha_ibov_12m):>8}")
    print(f"  {'Alpha vs CDI':<20s} {_fmt_pct(alpha_cdi_mtd):>8} {'':>8} {_fmt_pct(alpha_cdi_12m):>8}")

    print(f"\n{sep}")
    print(f"  MÉTRICAS DE RISCO (12m)")
    print(f"{sep}\n")
    print(f"  Beta vs IBOV        {_fmt_num(metricas.get('beta')):>8}")
    print(f"  Tracking Error      {_fmt_pct(metricas.get('tracking_error'), 1):>8} a.a.")
    print(f"  Sharpe              {_fmt_num(metricas.get('sharpe')):>8}")
    print(f"  Volatilidade        {_fmt_pct(metricas.get('volatilidade'), 1):>8} a.a.")
    print(f"  Max Drawdown        {_fmt_pct(metricas.get('max_drawdown'), 1):>8}")

    if por_classe:
        print(f"\n{sep}")
        print(f"  DECOMPOSIÇÃO MTD POR CLASSE")
        print(f"{sep}")
        print(f"\n  {'Classe':<18} {'Peso':>6}  {'Ret MTD':>8}  {'Contrib':>8}")
        print(f"  {'─'*48}")
        total_invest = sum(v for v in _pesos_classe_cache.values()) if _pesos_classe_cache else 1
        for classe, ret_c in sorted(por_classe.items()):
            peso_c = _pesos_classe_cache.get(classe, 0)
            contrib = peso_c * ret_c if ret_c is not None else None
            peso_str = f"{peso_c*100:.0f}%" if peso_c > 0 else "—"
            print(f"  {classe:<18} {peso_str:>6}  {_fmt_pct(ret_c):>8}  {_fmt_pct(contrib):>8}")

    print(f"\n  Histórico: {HISTORICO_PATH}")
    print(f"{sep}\n")


_pesos_classe_cache: dict[str, float] = {}


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    hoje = date.today()
    print(f"\nSBWAA Performance — {hoje.isoformat()}")
    print("=" * 50)

    posicoes = extrair_posicoes()
    if not posicoes:
        print("Carteira vazia ou não encontrada.")
        return

    total_investido = sum(p["investido"] for p in posicoes)
    print(f"  {len(posicoes)} posições | capital investido: R$ {total_investido:,.2f}")

    # Pesos por classe (para exibição)
    global _pesos_classe_cache
    for pos in posicoes:
        c = pos["classe"]
        _pesos_classe_cache[c] = _pesos_classe_cache.get(c, 0) + pos["investido"] / total_investido

    # Períodos
    inicio_mtd = _inicio_mes(hoje)
    inicio_ytd = _inicio_ano(hoje)
    inicio_12m = _inicio_12m(hoje)

    # BCB
    print("  Carregando benchmarks BCB...")
    bcb = carregar_bcb()
    if not bcb:
        print("  AVISO: dados BCB indisponíveis — CDI/IPCA estimados podem ser imprecisos.")
        bcb = {"series": {}}

    # Benchmarks IBOV
    print("  Carregando IBOV...")
    bench = {
        "ibov_mtd": retorno_ibov(inicio_mtd),
        "ibov_ytd": retorno_ibov(inicio_ytd),
        "ibov_12m": retorno_ibov(inicio_12m),
        "cdi_mtd":  cdi_acumulado(inicio_mtd, hoje, bcb),
        "cdi_ytd":  cdi_acumulado(inicio_ytd, hoje, bcb),
        "cdi_12m":  cdi_acumulado(inicio_12m, hoje, bcb),
        "ipca_mtd": ipca_acumulado(inicio_mtd, hoje, bcb),
        "ipca_ytd": ipca_acumulado(inicio_ytd, hoje, bcb),
        "ipca_12m": ipca_acumulado(inicio_12m, hoje, bcb),
    }

    # Retorno carteira
    print("  Calculando retorno da carteira...")
    ret_mtd, por_classe_mtd = calcular_retorno_carteira(posicoes, inicio_mtd, bcb)
    ret_ytd, _              = calcular_retorno_carteira(posicoes, inicio_ytd, bcb)
    ret_12m, _              = calcular_retorno_carteira(posicoes, inicio_12m, bcb)

    ret = {"mtd": ret_mtd, "ytd": ret_ytd, "12m": ret_12m}

    # Métricas de risco
    print("  Calculando métricas de risco (12m)...")
    metricas = calcular_metricas_risco(posicoes, bcb, inicio_12m)

    # Exibir
    exibir_relatorio(hoje, ret, bench, metricas, por_classe_mtd)

    # Snapshot para histórico
    def _s(v): return round(v, 6) if v is not None and not math.isnan(v) else None

    snapshot = {
        "data":               hoje.isoformat(),
        "mes_ref":            hoje.strftime("%Y-%m"),
        "retorno_carteira_mtd": _s(ret_mtd),
        "retorno_carteira_ytd": _s(ret_ytd),
        "retorno_carteira_12m": _s(ret_12m),
        "retorno_ibov_mtd":   _s(bench["ibov_mtd"]),
        "retorno_ibov_ytd":   _s(bench["ibov_ytd"]),
        "retorno_ibov_12m":   _s(bench["ibov_12m"]),
        "retorno_cdi_mtd":    _s(bench["cdi_mtd"]),
        "retorno_cdi_ytd":    _s(bench["cdi_ytd"]),
        "retorno_cdi_12m":    _s(bench["cdi_12m"]),
        "retorno_ipca_mtd":   _s(bench["ipca_mtd"]),
        "retorno_ipca_ytd":   _s(bench["ipca_ytd"]),
        "retorno_ipca_12m":   _s(bench["ipca_12m"]),
        "alpha_ibov_mtd":     _s((ret_mtd or 0) - (bench["ibov_mtd"] or 0)) if ret_mtd and bench["ibov_mtd"] else None,
        "alpha_ibov_12m":     _s((ret_12m or 0) - (bench["ibov_12m"] or 0)) if ret_12m and bench["ibov_12m"] else None,
        "alpha_cdi_mtd":      _s((ret_mtd or 0) - (bench["cdi_mtd"] or 0)) if ret_mtd and bench["cdi_mtd"] else None,
        "alpha_cdi_12m":      _s((ret_12m or 0) - (bench["cdi_12m"] or 0)) if ret_12m and bench["cdi_12m"] else None,
        "beta":               _s(metricas.get("beta")),
        "tracking_error_12m": _s(metricas.get("tracking_error")),
        "sharpe_12m":         _s(metricas.get("sharpe")),
        "volatilidade_12m":   _s(metricas.get("volatilidade")),
        "max_drawdown_12m":   _s(metricas.get("max_drawdown")),
    }

    atualizar_historico(snapshot)
    print(f"  Snapshot {snapshot['mes_ref']} salvo em performance-historico.json\n")


if __name__ == "__main__":
    main()
