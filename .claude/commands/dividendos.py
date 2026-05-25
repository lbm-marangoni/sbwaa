"""
dividendos.py — Proventos pagos, declarados e projetados da carteira.
Uso: python sbwaa.py /dividendos

Fontes:
  BR  (ações/FIIs): Brapi cashDividends — inclui declarados futuros quando disponível
  INTL (ETFs):      yfinance t.dividends — histórico + t.info exDividendDate declarado
  Projeção:         detecta frequência (mensal/trimestral/semestral/anual) pelo histórico
                    e estima próximas datas + valor médio dos últimos pagamentos
"""

import json
import re
import sys
from datetime import datetime, timedelta, date
from pathlib import Path

import yfinance as yf
import pandas as pd

PROJECT_ROOT   = Path(__file__).parent.parent.parent
VAULT_ROOT     = PROJECT_ROOT / "vault"
CARTEIRA_PATH  = VAULT_ROOT / "00-portfolio" / "carteira.md"
HISTORICO_PATH = VAULT_ROOT / "00-portfolio" / "historico-trades.md"
SCRIPTS_DIR    = PROJECT_ROOT / "scripts" / "data"
sys.path.insert(0, str(SCRIPTS_DIR))


def eh_ticker_br(ticker: str) -> bool:
    return bool(re.match(r"^[A-Z]{4}[0-9]{1,2}[FBP]?$", ticker))


def ticker_yahoo(ticker: str) -> str:
    return f"{ticker}.SA" if eh_ticker_br(ticker) else ticker


# ── Leitura de dados de portfólio ──────────────────────────────────────────────

def parse_historico() -> dict:
    """Retorna {ticker: data_primeira_compra}."""
    datas = {}
    if not HISTORICO_PATH.exists():
        return datas
    dentro = False
    for linha in HISTORICO_PATH.read_text(encoding="utf-8").splitlines():
        s = linha.strip()
        if s.startswith("| Data") or s.startswith("|Data"):
            dentro = True
            continue
        if dentro and s.startswith("|---"):
            continue
        if dentro and s.startswith("|"):
            cols = [c.strip() for c in s.split("|")[1:-1]]
            if len(cols) >= 4 and cols[0] and cols[3].upper() == "COMPRA":
                tk = cols[1].strip()
                try:
                    d = datetime.strptime(cols[0], "%Y-%m-%d")
                    if tk not in datas or d < datas[tk]:
                        datas[tk] = d
                except ValueError:
                    pass
        elif dentro and not s.startswith("|"):
            break
    return datas


def parse_carteira() -> list[dict]:
    if not CARTEIRA_PATH.exists():
        return []
    posicoes = []
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
            if len(cols) >= 5 and cols[0] and cols[0] not in ("", "Ticker"):
                try:
                    qtd = float(cols[3].replace(".", "").replace(",", ".") or 0)
                    pm  = float(re.sub(r"[^\d,.]", "", cols[4]).replace(",", ".") or 0)
                    if cols[0] and qtd > 0:
                        posicoes.append({"ticker": cols[0], "tipo": cols[1],
                                         "qtd": qtd, "pm": pm})
                except (ValueError, IndexError):
                    pass
        elif dentro and not s.startswith("|"):
            break
    return posicoes


# ── Análise de frequência e projeção ──────────────────────────────────────────

def _detectar_freq(datas: list[date]) -> tuple[str, int]:
    """Retorna (nome_frequencia, intervalo_em_dias) pelo histórico de datas."""
    if len(datas) < 2:
        return "desconhecida", 0
    intervals = sorted([(datas[i+1] - datas[i]).days for i in range(len(datas) - 1)])
    med = intervals[len(intervals) // 2]
    if med <= 40:   return "mensal",      30
    if med <= 100:  return "trimestral",  91
    if med <= 200:  return "semestral",  182
    return "anual", 365


def _projeta_proximas(ultima: date, intervalo: int, hoje: date,
                      janela: int = 90, n: int = 3) -> list[date]:
    """Gera até n datas futuras dentro da janela, a partir da última data paga."""
    prox = ultima
    while True:
        prox = date.fromordinal(prox.toordinal() + intervalo)
        if prox > hoje:
            break
    datas = []
    for i in range(n):
        d = date.fromordinal(prox.toordinal() + intervalo * i)
        if (d - hoje).days <= janela:
            datas.append(d)
    return datas


def analisar_serie(pagamentos: list[dict],
                   data_entrada: datetime | None,
                   hoje: datetime) -> dict:
    """
    Recebe lista de {'data': date, 'valor': float} (histórico já pago, cronológico).
    Retorna dict com projeção, totais e frequência.
    """
    hoje_d    = hoje.date()
    ano_inicio = date(hoje.year, 1, 1)

    # Totais desde entrada
    entrada_d = data_entrada.date() if data_entrada else None
    total_desde_entrada = sum(
        p["valor"] for p in pagamentos
        if entrada_d is None or p["data"] >= entrada_d
    )

    # Totais no ano (a partir da entrada ou jan/1, o que vier depois)
    corte_ano = max(ano_inicio, entrada_d) if entrada_d else ano_inicio
    total_no_ano = sum(p["valor"] for p in pagamentos if p["data"] >= corte_ano)

    if len(pagamentos) < 2:
        return {"frequencia": "desconhecida", "intervalo": 0, "valor_medio": 0.0,
                "proximas_datas": [], "declarados": [],
                "total_no_ano": total_no_ano,
                "total_desde_entrada": total_desde_entrada}

    # Frequência pelos últimos 18 meses
    cutoff = hoje_d - timedelta(days=548)
    recentes = [p for p in pagamentos if p["data"] >= cutoff]
    datas_rec = sorted(p["data"] for p in recentes)

    freq_nome, intervalo = _detectar_freq(datas_rec)

    # Valor médio dos últimos min(6, n) pagamentos
    n_rec = min(6, len(recentes))
    valor_medio = sum(p["valor"] for p in pagamentos[-n_rec:]) / n_rec if n_rec else 0.0

    proximas = []
    if intervalo and datas_rec:
        proximas = _projeta_proximas(datas_rec[-1], intervalo, hoje_d)

    return {
        "frequencia": freq_nome,
        "intervalo":  intervalo,
        "valor_medio": valor_medio,
        "proximas_datas": proximas,
        "declarados": [],  # preenchido pelo caller para BR
        "total_no_ano": total_no_ano,
        "total_desde_entrada": total_desde_entrada,
    }


# ── Fontes de dados ────────────────────────────────────────────────────────────

def _parse_date(s: str) -> date | None:
    if not s:
        return None
    try:
        return datetime.strptime(s[:10], "%Y-%m-%d").date()
    except ValueError:
        return None


def dados_br(ticker: str, hoje: datetime, data_entrada: datetime | None) -> dict:
    """
    Busca dividendos de ativo BR via Brapi.
    Distingue automaticamente declarados futuros (data > hoje) de pagos (data <= hoje).
    """
    try:
        from fetch_fundamentals import buscar_ticker
        brapi = buscar_ticker(ticker)
    except Exception as e:
        return {"erro": str(e), "pagamentos": [], "declarados": [],
                "total_no_ano": 0.0, "total_desde_entrada": 0.0,
                "frequencia": "—", "valor_medio": 0.0, "proximas_datas": []}

    historico_raw = brapi.get("dividendos_historico") or []
    hoje_d = hoje.date()

    pagamentos = []
    declarados = []
    for entry in historico_raw:
        d = _parse_date(entry.get("data", ""))
        v = entry.get("valor", 0) or 0
        if not d or not v:
            continue
        if d > hoje_d:
            declarados.append({"data": d, "valor": v})
        else:
            pagamentos.append({"data": d, "valor": v})

    analise = analisar_serie(pagamentos, data_entrada, hoje)
    analise["declarados"] = sorted(declarados, key=lambda x: x["data"])

    # YoC via brapi dy
    dy = brapi.get("dy")
    preco = brapi.get("cotacao")
    analise["dy_brapi"] = dy
    analise["preco"]    = preco
    return analise


def dados_intl(ticker: str, hoje: datetime, data_entrada: datetime | None) -> dict:
    """Busca dividendos de ETF internacional via yfinance."""
    try:
        t    = yf.Ticker(ticker)
        divs = t.dividends
        info = t.info or {}

        if divs is None or divs.empty:
            return {"pagamentos": [], "declarados": [],
                    "total_no_ano": 0.0, "total_desde_entrada": 0.0,
                    "frequencia": "—", "valor_medio": 0.0, "proximas_datas": [],
                    "dy_yf": None, "preco": None}

        if divs.index.tz is not None:
            divs.index = divs.index.tz_convert(None)

        hoje_d = hoje.date()
        pagamentos = [
            {"data": ts.date(), "valor": float(v)}
            for ts, v in divs.items()
            if ts.date() <= hoje_d
        ]
        pagamentos.sort(key=lambda x: x["data"])

        analise = analisar_serie(pagamentos, data_entrada, hoje)

        # Dividendo declarado pelo yfinance (exDividendDate no futuro)
        declarados = []
        ex_ts = info.get("exDividendDate")
        if ex_ts:
            ex_d = datetime.fromtimestamp(ex_ts).date()
            if ex_d > hoje_d:
                v = info.get("lastDividendValue") or analise["valor_medio"]
                declarados.append({"data": ex_d, "valor": v})
        analise["declarados"] = declarados

        dy    = info.get("dividendYield") or info.get("trailingAnnualDividendYield")
        preco = info.get("regularMarketPrice") or info.get("previousClose")
        analise["dy_yf"] = dy
        analise["preco"] = preco
        return analise

    except Exception as e:
        return {"erro": str(e), "pagamentos": [], "declarados": [],
                "total_no_ano": 0.0, "total_desde_entrada": 0.0,
                "frequencia": "—", "valor_medio": 0.0, "proximas_datas": []}


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    hoje    = datetime.now()
    hoje_d  = hoje.date()
    JANELA  = 90  # dias à frente para mostrar próximos pagamentos

    posicoes = parse_carteira()
    if not posicoes:
        print("\n  Carteira vazia. Use /adicionar para incluir ativos.\n")
        return

    datas_entrada = parse_historico()

    print(f"\n{'═'*64}")
    print(f"  SBWAA — Dividendos & Proventos  |  {hoje.strftime('%Y-%m-%d')}")
    print(f"{'═'*64}\n")

    # Acumula dados por ticker
    proximos_todos: list[dict] = []     # {ticker, data, valor, total_est, fonte, freq}
    pagos_ano:      dict[str, float] = {}
    total_recebido: dict[str, float] = {}
    yoc_data:       dict[str, float] = {}
    freq_map:       dict[str, str]   = {}

    for pos in posicoes:
        tk  = pos["ticker"]
        qtd = pos["qtd"]
        pm  = pos["pm"]
        data_entrada = datas_entrada.get(tk)
        br = eh_ticker_br(tk)

        print(f"  Processando {tk}...", end="", flush=True)

        if br:
            analise = dados_br(tk, hoje, data_entrada)
        else:
            analise = dados_intl(ticker_yahoo(tk), hoje, data_entrada)

        if "erro" in analise:
            print(f"  ⚠️  {tk}: {analise['erro']}")
            continue

        print(" ok")

        freq       = analise.get("frequencia", "—")
        val_medio  = analise.get("valor_medio", 0.0)
        freq_map[tk] = freq

        # Totais acumulados
        pagos_ano[tk]      = round(analise.get("total_no_ano", 0.0) * qtd, 2)
        total_recebido[tk] = round(analise.get("total_desde_entrada", 0.0) * qtd, 2)

        # YoC
        dy    = analise.get("dy_brapi") or analise.get("dy_yf")
        preco = analise.get("preco") or pm
        if pm > 0:
            if dy:
                yoc_data[tk] = round(float(dy) * 100, 2)
            elif val_medio and analise.get("intervalo", 0):
                pagamentos_ano = 365 / analise["intervalo"]
                yoc_data[tk] = round(val_medio * pagamentos_ano / pm * 100, 2)

        # Declarados (futuros já anunciados)
        for d in analise.get("declarados", []):
            dias = (d["data"] - hoje_d).days
            if 0 < dias <= JANELA:
                proximos_todos.append({
                    "ticker": tk, "data": d["data"], "valor": d["valor"],
                    "total_est": round(d["valor"] * qtd, 2),
                    "fonte": "✓ declarado", "freq": freq,
                })

        # Projetados a partir do histórico
        for proj_d in analise.get("proximas_datas", []):
            # não duplicar se já temos declarado próxima essa data (±7 dias)
            ja_tem = any(
                abs((p["data"] - proj_d).days) <= 7 and p["ticker"] == tk
                for p in proximos_todos
            )
            if ja_tem:
                continue
            dias = (proj_d - hoje_d).days
            if 0 < dias <= JANELA:
                proximos_todos.append({
                    "ticker": tk, "data": proj_d, "valor": val_medio,
                    "total_est": round(val_medio * qtd, 2) if val_medio else None,
                    "fonte": "~ projetado", "freq": freq,
                })

    proximos_todos.sort(key=lambda x: x["data"])

    # ── Seção 1: Próximos pagamentos ────────────────────────────────────────────
    print(f"\n  PRÓXIMOS PAGAMENTOS (próximos {JANELA} dias)")
    print(f"  {'─'*60}")
    if proximos_todos:
        print(f"  {'Ticker':<8} {'Data':<12} {'Valor/cota':>11} {'Total est.':>13}  Fonte")
        print(f"  {'─'*60}")
        total_prox = 0.0
        for p in proximos_todos:
            val_s   = f"R$ {p['valor']:.4f}" if p["valor"] else "  N/D    "
            tot_s   = f"R$ {p['total_est']:>8,.2f}" if p["total_est"] else "  N/D    "
            dias    = (p["data"] - hoje_d).days
            print(f"  {p['ticker']:<8} {str(p['data']):<12} {val_s:>11} {tot_s:>13}  "
                  f"[{p['fonte']}]  ({dias}d)  {p['freq']}")
            total_prox += p["total_est"] or 0
        print(f"  {'─'*60}")
        print(f"  {'TOTAL EST.':<34} R$ {total_prox:>10,.2f}")
    else:
        print(f"  Nenhum pagamento encontrado nos próximos {JANELA} dias.")
        print(f"  Ativos com histórico insuficiente (<2 pagamentos) não geram projeção.")

    # ── Seção 2: Pagos no ano ────────────────────────────────────────────────────
    total_ano = sum(pagos_ano.values())
    print(f"\n  DIVIDENDOS PAGOS EM {hoje.year}  (a partir da data de entrada)")
    print(f"  {'─'*60}")
    for tk, total in sorted(pagos_ano.items(), key=lambda x: -x[1]):
        de = datas_entrada.get(tk)
        de_s = f"  entrada: {de.strftime('%Y-%m-%d')}" if de else ""
        freq = freq_map.get(tk, "—")
        print(f"  {tk:<8} R$ {total:>10,.2f}   {freq:<14}{de_s}")
    print(f"  {'─'*60}")
    print(f"  {'TOTAL':<8} R$ {total_ano:>10,.2f}")

    # ── Seção 3: Total recebido desde a entrada ──────────────────────────────────
    total_hist = sum(total_recebido.values())
    print(f"\n  TOTAL RECEBIDO DESDE A ENTRADA")
    print(f"  {'─'*60}")
    for tk, total in sorted(total_recebido.items(), key=lambda x: -x[1]):
        de = datas_entrada.get(tk)
        de_s = de.strftime('%Y-%m-%d') if de else "—"
        print(f"  {tk:<8} R$ {total:>10,.2f}   desde {de_s}")
    print(f"  {'─'*60}")
    print(f"  {'TOTAL':<8} R$ {total_hist:>10,.2f}")
    print(f"\n  ℹ  Patrimônio na carteira = valor de mercado das posições.")
    print(f"     Proventos recebidos acima representam retorno adicional (total return).")

    # ── Seção 4: Yield on Cost ───────────────────────────────────────────────────
    if yoc_data:
        print(f"\n  YIELD ON COST")
        print(f"  {'─'*60}")
        for tk, yoc in sorted(yoc_data.items(), key=lambda x: -x[1]):
            print(f"  {tk:<8} {yoc:>6.2f}% a.a.")

    # ── Cache para /carteira ─────────────────────────────────────────────────────
    cache = {
        "total_recebido": round(total_hist, 2),
        "total_no_ano":   round(total_ano, 2),
        "atualizado_em":  hoje.strftime("%Y-%m-%d %H:%M"),
    }
    cache_path = VAULT_ROOT / "00-portfolio" / ".proventos-cache.json"
    try:
        cache_path.write_text(json.dumps(cache, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass

    print(f"\n{'═'*64}\n")


if __name__ == "__main__":
    main()
