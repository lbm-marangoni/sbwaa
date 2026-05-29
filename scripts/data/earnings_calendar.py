"""
earnings_calendar.py — Calendário de resultados trimestrais da carteira.

Fontes por tipo de ativo:
  Ações (AÇÃO ON/PN):
    1. yfinance calendar['Earnings Date']  → data oficial quando disponível
    2. Fallback: earnings_dates histórico  → última data + 91d  (tipo: estimado)
  FIIs (FII):
    Estimativa baseada no calendário CVM padrão (~45 dias após fechamento)
    Tipo: estimado (FII)
  ETFs, RF, TD, DEB, CRI/CRA: ignorados

Saídas:
  - vault/00-portfolio/earnings-calendar.json  (lido por check_alerts.py)
  - vault/00-portfolio/earnings-calendar.md    (visualização Obsidian)
  - vault/01-ativos/TICKER/earnings-TICKER-TRIMESTRE.md  (stub por resultado)

Uso: python scripts/data/earnings_calendar.py
"""

import json
import re
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

import yfinance as yf

PROJECT_ROOT  = Path(__file__).parent.parent.parent
VAULT_ROOT    = PROJECT_ROOT / "vault"
SCRIPTS_DIR   = Path(__file__).parent
CARTEIRA_PATH = VAULT_ROOT / "00-portfolio" / "carteira.md"
CAL_JSON      = VAULT_ROOT / "00-portfolio" / "earnings-calendar.json"
CAL_MD        = VAULT_ROOT / "00-portfolio" / "earnings-calendar.md"
ATIVOS_DIR    = VAULT_ROOT / "01-ativos"

TIPOS_ACAO = {"🟦 AÇÃO ON", "🟦 AÇÃO PN", "AÇÃO ON", "AÇÃO PN"}
TIPOS_FII  = {"🟩 FII", "FII"}
TIPOS_RF   = {"⬜ RF", "🟪 TD", "🟫 DEB", "🟧 CRI/CRA", "RF", "TD", "DEB", "CRI/CRA"}

MESES_PT = {
    1:"Jan", 2:"Fev", 3:"Mar", 4:"Abr", 5:"Mai", 6:"Jun",
    7:"Jul", 8:"Ago", 9:"Set", 10:"Out", 11:"Nov", 12:"Dez",
}


# ── Carteira ───────────────────────────────────────────────────────────────────

def parse_carteira() -> list[dict]:
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
            if len(cols) >= 5 and cols[0]:
                posicoes.append({"ticker": cols[0], "tipo": cols[1] if len(cols) > 1 else ""})
        elif dentro and s and not s.startswith("|"):
            break
    return posicoes


def eh_ticker_br(t: str) -> bool:
    return bool(re.match(r"^[A-Z]{4}[0-9]{1,2}[FBP]?$", t))


# ── Trimestre ──────────────────────────────────────────────────────────────────

def trimestre_de_data(d: date) -> str:
    """Infere o trimestre que uma data de earnings cobre.
    Ex: resultado divulgado em mai/2026 → Q1-2026 (jan-mar)
    """
    m, a = d.month, d.year
    if m in (1, 2, 3):    return f"Q4-{a-1}"   # Q4 do ano anterior
    if m in (4, 5, 6):    return f"Q1-{a}"
    if m in (7, 8, 9):    return f"Q2-{a}"
    return                        f"Q3-{a}"


# ── Ações — busca earnings ─────────────────────────────────────────────────────

def buscar_earnings_acao(ticker: str) -> tuple[date | None, str, str]:
    """
    Retorna (data, trimestre, tipo) onde tipo = 'confirmado' | 'estimado'.
    """
    tk = f"{ticker}.SA" if eh_ticker_br(ticker) else ticker
    hoje = date.today()

    # 1. Tentativa direta via calendar
    try:
        t = yf.Ticker(tk)
        cal = t.calendar or {}
        datas = cal.get("Earnings Date", [])
        if isinstance(datas, date):
            datas = [datas]
        futuras = [d for d in datas if isinstance(d, date) and d > hoje]
        if futuras:
            d = min(futuras)
            return d, trimestre_de_data(d), "confirmado"
    except Exception:
        pass

    # 2. Fallback: histórico earnings_dates → última + 91 dias
    try:
        t = yf.Ticker(tk)
        hist = t.earnings_dates
        if hist is not None and not hist.empty:
            passadas = [ts.date() for ts in hist.index if ts.date() <= hoje]
            if passadas:
                ultima = max(passadas)
                proxima = ultima + timedelta(days=91)
                if proxima > hoje:
                    return proxima, trimestre_de_data(proxima), "estimado"
    except Exception:
        pass

    return None, "", ""


# ── FIIs — datas estimadas ─────────────────────────────────────────────────────

def proximas_dfs_fii(hoje: date) -> list[tuple[date, str]]:
    """
    Retorna lista de (data estimada, trimestre) para DFs trimestrais de FII
    nos próximos 180 dias. Base: CVM ~45 dias após fechamento do trimestre.
    """
    ano = hoje.year
    # Datas estimadas de publicação das DFs (meados do mês seguinte ao prazo CVM)
    candidatos = [
        (date(ano,     2, 15), f"Q4-{ano-1}"),
        (date(ano,     5, 15), f"Q1-{ano}"),
        (date(ano,     8, 15), f"Q2-{ano}"),
        (date(ano,    11, 15), f"Q3-{ano}"),
        (date(ano+1,   2, 15), f"Q4-{ano}"),
    ]
    return [(d, t) for d, t in candidatos if hoje < d <= hoje + timedelta(days=180)]


# ── Stub note no vault ─────────────────────────────────────────────────────────

def criar_stub_earnings(ticker: str, trimestre: str, data: date, tipo: str) -> Path:
    pasta = ATIVOS_DIR / ticker
    pasta.mkdir(parents=True, exist_ok=True)
    path = pasta / f"earnings-{ticker}-{trimestre}.md"
    if path.exists():
        return path

    estimado_str = " *(data estimada)*" if tipo != "confirmado" else ""
    fii_str = " (FII — Demonstração Financeira Trimestral)" if "fii" in tipo else ""

    conteudo = f"""---
tags: [earnings, {ticker.lower()}, {trimestre.lower().replace("-", "")}]
ticker: {ticker}
trimestre: {trimestre}
data_prevista: {data.isoformat()}
tipo: {tipo}
status: pendente
agente: earnings-reviewer
---

# Earnings — {ticker} {trimestre}{estimado_str}{fii_str}

> **Data prevista:** {data.strftime('%d/%m/%Y')}{estimado_str}
> Quando os resultados forem divulgados, execute `/earnings {ticker}`.

## Números do Trimestre

| Métrica | {trimestre} | Trim. Anterior | QoQ | YoY |
|---------|-------------|----------------|-----|-----|
| Receita Líquida | | | | |
| EBITDA | | | | |
| Margem EBITDA | | | | |
| Lucro Líquido | | | | |
| Dívida Líq./EBITDA | | | | |

## Links
- [[carteira]] | [[ips]]
"""
    path.write_text(conteudo, encoding="utf-8")
    return path


# ── JSON + Markdown ────────────────────────────────────────────────────────────

def salvar_json(eventos: list[dict]):
    dados = {
        "ultima_atualizacao": date.today().isoformat(),
        "eventos": sorted(eventos, key=lambda e: e["data"]),
    }
    CAL_JSON.parent.mkdir(parents=True, exist_ok=True)
    CAL_JSON.write_text(json.dumps(dados, ensure_ascii=False, indent=2), encoding="utf-8")


def salvar_md(eventos: list[dict], hoje: date):
    hoje_str = hoje.isoformat()
    linhas = [
        "---",
        "tags: [portfolio, earnings, calendario]",
        "cssclasses: [node-portfolio]",
        f"data: {hoje_str}",
        "---",
        "",
        f"# 📅 Calendário de Resultados",
        "",
        f"> Atualizado em {hoje_str} — próximos 180 dias. Alertas automáticos: D-7 e D-1.",
        "",
        "---",
        "",
        "| Data | Ticker | Trimestre | Status | Nota | Ação |",
        "|------|--------|-----------|--------|------|------|",
    ]
    for e in eventos:
        d = datetime.strptime(e["data"], "%Y-%m-%d").date()
        dias = (d - hoje).days
        dias_str = f"({dias}d)" if dias > 0 else "hoje"
        status = "✅ confirmado" if e["tipo"] == "confirmado" else ("~ estimado (FII)" if "fii" in e["tipo"] else "~ estimado")
        nota_link = f"[[earnings-{e['ticker']}-{e['trimestre']}]]" if e.get("nota_vault") else "—"
        acao = f"`/earnings {e['ticker']}`" if "fii" not in e["tipo"] else "—"
        linhas.append(
            f"| {d.strftime('%d/%m/%y')} {dias_str} | [[{e['ticker']}]] | {e['trimestre']} "
            f"| {status} | {nota_link} | {acao} |"
        )
    linhas += [
        "",
        "---",
        "",
        "## Links",
        "",
        "[[carteira]] | [[ips]] | [[dividendos]]",
        "",
    ]
    CAL_MD.write_text("\n".join(linhas), encoding="utf-8")


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    hoje = date.today()
    print(f"\nSBWAA Earnings Calendar — {hoje.isoformat()}")
    print("=" * 60)

    posicoes = parse_carteira()
    acoes = [p for p in posicoes if p["tipo"] in TIPOS_ACAO]
    fiis  = [p for p in posicoes if p["tipo"] in TIPOS_FII]

    print(f"  Ações: {len(acoes)} | FIIs: {len(fiis)}")

    eventos: list[dict] = []
    notas_criadas = 0

    # ── Ações ─────────────────────────────────────────────────────────────────
    for pos in acoes:
        ticker = pos["ticker"]
        print(f"  Buscando {ticker}...", end="", flush=True)
        data, trimestre, tipo = buscar_earnings_acao(ticker)
        if data is None:
            print(" sem data")
            continue
        dias = (data - hoje).days
        tipo_str = "✅" if tipo == "confirmado" else "~"
        print(f" {tipo_str} {trimestre} em {data.strftime('%d/%m')} ({dias}d)")

        nota = criar_stub_earnings(ticker, trimestre, data, tipo)
        notas_criadas += 1

        eventos.append({
            "ticker":     ticker,
            "tipo_ativo": pos["tipo"],
            "trimestre":  trimestre,
            "data":       data.isoformat(),
            "tipo":       tipo,
            "fonte":      "yfinance",
            "nota_vault": str(nota.relative_to(PROJECT_ROOT)).replace("\\", "/"),
        })

    # ── FIIs ──────────────────────────────────────────────────────────────────
    dfs_fii = proximas_dfs_fii(hoje)
    for pos in fiis:
        ticker = pos["ticker"]
        for data, trimestre in dfs_fii:
            nota = criar_stub_earnings(ticker, trimestre, data, "estimado-fii")
            notas_criadas += 1
            eventos.append({
                "ticker":     ticker,
                "tipo_ativo": pos["tipo"],
                "trimestre":  trimestre,
                "data":       data.isoformat(),
                "tipo":       "estimado-fii",
                "fonte":      "estimativa-cvm",
                "nota_vault": str(nota.relative_to(PROJECT_ROOT)).replace("\\", "/"),
            })

    # ── Salvar ────────────────────────────────────────────────────────────────
    eventos_sorted = sorted(eventos, key=lambda e: e["data"])
    salvar_json(eventos_sorted)
    salvar_md(eventos_sorted, hoje)
    print(f"\n  {len(eventos_sorted)} evento(s) | {notas_criadas} nota(s) criada(s)")
    print(f"  JSON: {CAL_JSON}")
    print(f"  MD:   {CAL_MD}")

    # ── Resumo terminal ───────────────────────────────────────────────────────
    proximos = [e for e in eventos_sorted if (datetime.strptime(e["data"], "%Y-%m-%d").date() - hoje).days <= 90]
    if proximos:
        print(f"\n  Próximos 90 dias:")
        for e in proximos:
            d = datetime.strptime(e["data"], "%Y-%m-%d").date()
            dias = (d - hoje).days
            tipo_str = "✅" if e["tipo"] == "confirmado" else "~"
            acao = f"→ /earnings {e['ticker']}" if "fii" not in e["tipo"] else "(FII)"
            print(f"    {tipo_str} {d.strftime('%d/%m/%y')} [{dias:>3}d]  {e['ticker']:<8} {e['trimestre']}  {acao}")
    print(f"\n{'='*60}\n")


if __name__ == "__main__":
    main()
