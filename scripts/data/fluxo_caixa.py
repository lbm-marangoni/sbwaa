"""
fluxo_caixa.py — Projeção de renda passiva mês a mês (12 meses).

Seção A — Renda Periódica (ações, FIIs, ETFs):
  - Dividendos históricos recebidos + declarados futuros + projetados
  - Tabela mês × ticker com status: ✅ recebido | 📢 declarado | ~ projetado

Seção B — Valorização RF (RF, TD, DEB, CRI/CRA):
  - Crescimento mensal estimado bruto + líquido (IR)
  - IOF = 0 (já expirado para posições ativas)

Alerta: projeção < meta_mensal de metas.md

Uso: python scripts/data/fluxo_caixa.py
"""

import calendar
import json
import re
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

PROJECT_ROOT  = Path(__file__).parent.parent.parent
VAULT_ROOT    = PROJECT_ROOT / "vault"
SCRIPTS_DIR   = Path(__file__).parent
COMMANDS_DIR  = PROJECT_ROOT / ".claude" / "commands"

METAS_PATH    = VAULT_ROOT / "00-portfolio" / "metas.md"
SAIDA_PATH    = VAULT_ROOT / "00-portfolio" / "fluxo-caixa.md"
CACHE_DIR     = SCRIPTS_DIR / "cache"

sys.path.insert(0, str(SCRIPTS_DIR))
sys.path.insert(0, str(COMMANDS_DIR))

from dividendos import (  # type: ignore
    parse_carteira, parse_historico,
    eh_ticker_br, ticker_yahoo,
    dados_br, dados_intl,
)

TIPOS_RF = {
    "⬜ RF", "🟪 TD", "🟫 DEB", "🟧 CRI/CRA",
    "RF", "TD", "DEB", "CRI/CRA",
}
TIPOS_CRI_CRA_ISENTO = {"🟧 CRI/CRA", "CRI/CRA"}

MESES_PT = {
    1:"Jan", 2:"Fev", 3:"Mar", 4:"Abr", 5:"Mai", 6:"Jun",
    7:"Jul", 8:"Ago", 9:"Set", 10:"Out", 11:"Nov", 12:"Dez",
}


# ── Leitura de meta ────────────────────────────────────────────────────────────

def ler_meta_mensal() -> float | None:
    """Lê alvo_mensal de vault/00-portfolio/metas.md."""
    if not METAS_PATH.exists():
        return None
    conteudo = METAS_PATH.read_text(encoding="utf-8")
    m = re.search(r"alvo_mensal:\s*([\d,.]+)", conteudo)
    if m:
        try:
            return float(m.group(1).replace(",", "."))
        except ValueError:
            pass
    return None


# ── BCB — taxa CDI mensal ──────────────────────────────────────────────────────

def _carregar_bcb() -> dict:
    hoje = date.today()
    for d in range(8):
        dt = (hoje - timedelta(days=d)).isoformat()
        p = CACHE_DIR / f"bcb_{dt}.json"
        if p.exists():
            try:
                return json.loads(p.read_text(encoding="utf-8"))
            except Exception:
                pass
    return {}


def cdi_mensal_atual(bcb: dict) -> float:
    """Última taxa mensal Selic acumulada (proxy CDI)."""
    try:
        hist = bcb["series"]["selic_acum_mes"]["historico"]
        if hist:
            return hist[-1]["valor"] / 100
    except (KeyError, TypeError):
        pass
    return (1 + 0.1475) ** (1 / 12) - 1   # fallback 14.75% a.a.


# ── Extensão do projetor para 12 meses ────────────────────────────────────────

def projetar_12m(ultima: date, intervalo: int, hoje: date) -> list[date]:
    """Gera todas as datas projetadas nos próximos 12 meses."""
    if not intervalo:
        return []
    fim = hoje + timedelta(days=366)
    prox = ultima
    while prox <= hoje:
        prox += timedelta(days=intervalo)
    datas = []
    while prox <= fim:
        datas.append(prox)
        prox += timedelta(days=intervalo)
    return datas


# ── Calendário de renda periódica ──────────────────────────────────────────────

def _mes_key(d: date) -> str:
    return d.strftime("%Y-%m")


def construir_calendario(
    posicoes_income: list[dict],
    analises: dict,          # {ticker: analise_dict}
    datas_entrada: dict,     # {ticker: datetime}
    hoje: date,
) -> dict:
    """
    Retorna {mes_key: {ticker: {"valor": float, "status": str}}}
    para os próximos 12 meses.
    status: "recebido" | "declarado" | "projetado" | None
    """
    meses = {}
    fim = hoje + timedelta(days=366)
    d = date(hoje.year, hoje.month, 1)
    while d <= fim:
        meses[_mes_key(d)] = {}
        mes_seguinte_ano  = d.year + (d.month // 12)
        mes_seguinte_mes  = (d.month % 12) + 1
        d = date(mes_seguinte_ano, mes_seguinte_mes, 1)

    for pos in posicoes_income:
        tk  = pos["ticker"]
        qtd = pos["qtd"]
        a   = analises.get(tk)
        if not a or "erro" in a:
            continue

        entrada_d = datas_entrada.get(tk)
        entrada_d = entrada_d.date() if isinstance(entrada_d, datetime) else entrada_d

        val_medio   = a.get("valor_medio", 0.0)
        intervalo   = a.get("intervalo", 0)
        declarados  = {_mes_key(d["data"]): d["valor"] for d in a.get("declarados", [])
                       if d["data"] > hoje}

        # Pagamentos históricos já recebidos
        pagos_por_mes: dict[str, float] = {}
        for p in a.get("pagamentos", []):
            pd_ = p["data"]
            if isinstance(pd_, str):
                try:
                    pd_ = datetime.strptime(pd_[:10], "%Y-%m-%d").date()
                except Exception:
                    continue
            if entrada_d and pd_ < entrada_d:
                continue
            mk = _mes_key(pd_)
            pagos_por_mes[mk] = pagos_por_mes.get(mk, 0.0) + p["valor"] * qtd

        # Projeções para os próximos 12 meses
        projetados_por_mes: dict[str, float] = {}
        if intervalo and val_medio:
            datas_rec = sorted(p["data"] if isinstance(p["data"], date)
                               else datetime.strptime(str(p["data"])[:10], "%Y-%m-%d").date()
                               for p in a.get("pagamentos", []))
            if datas_rec:
                for pd_ in projetar_12m(datas_rec[-1], intervalo, hoje):
                    mk = _mes_key(pd_)
                    if mk not in declarados:  # declarado tem prioridade
                        projetados_por_mes[mk] = val_medio * qtd

        # Preenche o calendário
        for mk in meses:
            valor = None
            status = None
            mk_date = datetime.strptime(mk + "-01", "%Y-%m-%d").date()

            if mk < _mes_key(hoje):
                # Mês passado — só "recebido"
                if mk in pagos_por_mes:
                    valor = pagos_por_mes[mk]
                    status = "recebido"
            elif mk == _mes_key(hoje):
                # Mês atual — recebido ou declarado/projetado
                if mk in pagos_por_mes:
                    valor = pagos_por_mes[mk]
                    status = "recebido"
                elif mk in declarados:
                    valor = declarados[mk] * qtd
                    status = "declarado"
                elif mk in projetados_por_mes:
                    valor = projetados_por_mes[mk]
                    status = "projetado"
            else:
                # Mês futuro
                if mk in declarados:
                    valor = declarados[mk] * qtd
                    status = "declarado"
                elif mk in projetados_por_mes:
                    valor = projetados_por_mes[mk]
                    status = "projetado"

            if valor is not None and valor > 0:
                meses[mk][tk] = {"valor": round(valor, 2), "status": status}

    return meses


# ── Valorização mensal RF ──────────────────────────────────────────────────────

def _ler_rf_params(ticker: str) -> dict:
    tese = VAULT_ROOT / "01-ativos" / ticker / "tese.md"
    params = {"indexador": "CDI", "taxa": "100%", "data_entrada": None}
    if not tese.exists():
        return params
    for linha in tese.read_text(encoding="utf-8").splitlines():
        for chave in ("indexador", "taxa", "data_entrada"):
            if linha.lower().startswith(f"{chave}:"):
                val = linha.split(":", 1)[1].strip().strip('"').strip("'")
                if val:
                    params[chave] = val
    return params


def taxa_mensal_rf(params: dict, cdi_m: float) -> float:
    """Retorna taxa de crescimento mensal estimada."""
    indexador = (params.get("indexador") or "CDI").upper()
    taxa_str  = (params.get("taxa") or "100%").strip().replace(",", ".")

    try:
        if taxa_str.startswith("+"):
            spread = float(taxa_str.replace("+", "").replace("%", "")) / 100
            if indexador in ("CDI", "SELIC"):
                return cdi_m + spread / 12
            return cdi_m + spread / 12
        pct = float(taxa_str.replace("%", ""))
        if indexador in ("CDI", "SELIC"):
            fator = pct / 100 if pct > 2 else pct
            return cdi_m * fator
        if indexador == "IPCA":
            ipca_m = (1 + 0.05) ** (1 / 12) - 1  # fallback IPCA ~5%
            return ipca_m + (pct / 100 / 12 if pct < 20 else pct / 100 / 12)
        # PRE ou IGPM
        return (1 + pct / 100) ** (1 / 12) - 1
    except Exception:
        return cdi_m


def calcular_valorizacao_rf(
    posicoes_rf: list[dict],
    cdi_m: float,
    hoje: date,
    n_meses: int = 12,
) -> dict:
    """
    Retorna {mes_key: {ticker: {"bruto": float, "liquido": float}}}
    Para cada mês futuro: crescimento mensal estimado bruto + líquido.
    """
    sys.path.insert(0, str(SCRIPTS_DIR))
    from calculos_tributarios import aliquota_ir_rf  # type: ignore

    resultado: dict = {}

    for m in range(1, n_meses + 1):
        ano  = hoje.year  + (hoje.month + m - 1) // 12
        mes  = (hoje.month + m - 1) % 12 + 1
        mk   = f"{ano:04d}-{mes:02d}"
        fim_mes = date(ano, mes, calendar.monthrange(ano, mes)[1])
        resultado[mk] = {}

        for pos in posicoes_rf:
            tk  = pos["ticker"]
            qtd = pos["qtd"]
            pm  = pos["pm"]
            params = _ler_rf_params(tk)

            data_entrada_str = params.get("data_entrada")
            if data_entrada_str:
                try:
                    data_entrada = datetime.strptime(data_entrada_str, "%Y-%m-%d").date()
                    dias_ate_fim = max(0, (fim_mes - data_entrada).days)
                except Exception:
                    dias_ate_fim = max(0, m * 30)
            else:
                dias_ate_fim = max(0, m * 30)

            taxa_m = taxa_mensal_rf(params, cdi_m)
            principal = pm * qtd
            crescimento_bruto = round(principal * taxa_m, 2)

            # IR: aliquota sobre rendimento (realizado só no resgate, mas serve de estimativa)
            isento_ir = pos.get("tipo", "") in TIPOS_CRI_CRA_ISENTO
            if isento_ir:
                al_ir = 0.0
            else:
                al_ir = aliquota_ir_rf(dias_ate_fim) / 100

            crescimento_liquido = round(crescimento_bruto * (1 - al_ir), 2)

            resultado[mk][tk] = {
                "bruto":   crescimento_bruto,
                "liquido": crescimento_liquido,
            }

    return resultado


# ── Output Markdown ────────────────────────────────────────────────────────────

def _fmt_valor(v: float | None, status: str | None = None) -> str:
    if v is None or v == 0:
        return "—"
    s = f"R$ {v:,.2f}"
    if status in ("projetado",):
        return s + "~"
    return s


def gerar_md(
    hoje: date,
    posicoes_income: list[dict],
    posicoes_rf: list[dict],
    calendario: dict,
    valorizacao_rf: dict,
    meta_mensal: float | None,
):
    """Escreve vault/00-portfolio/fluxo-caixa.md."""
    tickers_income = [p["ticker"] for p in posicoes_income]
    tickers_rf     = [p["ticker"] for p in posicoes_rf]

    # Calcula totais por mês (income)
    totais_income = {}
    for mk, dados in calendario.items():
        totais_income[mk] = sum(v["valor"] for v in dados.values())

    # Status por mês (income)
    def status_mes(mk: str) -> str:
        if mk < _mes_key(hoje):
            return "✅"
        if mk == _mes_key(hoje):
            return "⏳"
        # Verifica se tem algum declarado
        if any(d.get("status") == "declarado" for d in calendario[mk].values()):
            return "📢"
        return "~"

    # Alerta vs meta
    meses_abaixo = 0
    media_projecao = 0.0
    meses_futuros = [mk for mk in calendario if mk >= _mes_key(hoje)]
    if meses_futuros and meta_mensal:
        for mk in meses_futuros:
            if totais_income.get(mk, 0) < meta_mensal:
                meses_abaixo += 1
        media_projecao = sum(totais_income.get(mk, 0) for mk in meses_futuros) / len(meses_futuros)

    # Totais RF por mês
    totais_rf_bruto = {mk: sum(v["bruto"] for v in d.values())
                       for mk, d in valorizacao_rf.items()}
    totais_rf_liq   = {mk: sum(v["liquido"] for v in d.values())
                       for mk, d in valorizacao_rf.items()}

    hoje_str = hoje.isoformat()
    linhas = [
        "---",
        "tags: [portfolio, fluxo-caixa, renda-passiva]",
        "cssclasses: [node-portfolio]",
        f"data: {hoje_str}",
        f"meta_mensal: {meta_mensal or 0}",
        "---",
        "",
        f"# Fluxo de Caixa — Renda Passiva",
        "",
        f"> Gerado em {hoje_str} — próximos 12 meses.",
        "",
    ]

    # Alerta
    if meta_mensal:
        gap = media_projecao - meta_mensal
        emoji = "✅" if gap >= 0 else "⚠️"
        linhas += [
            f"> [!{'tip' if gap >= 0 else 'warning'}] {emoji} Meta: **R$ {meta_mensal:,.0f}/mês** | "
            f"Projeção média: **R$ {media_projecao:,.0f}/mês** | "
            f"Gap: **R$ {gap:+,.0f}/mês**"
            + (f" | {meses_abaixo} de {len(meses_futuros)} meses abaixo da meta" if meses_abaixo > 0 else " | Todos os meses acima da meta"),
            "",
        ]

    # ── Seção A: Renda Periódica ──────────────────────────────────────────────
    linhas += [
        "---",
        "",
        "## 📅 Renda Periódica — Ações, FIIs e ETFs",
        "",
    ]

    if tickers_income:
        # Wikilinks nos cabeçalhos
        cabecalho_tickers = " | ".join(f"[[{tk}]]" for tk in tickers_income)
        linhas += [
            f"| Mês | Status | Total | {cabecalho_tickers} |",
            "|-----|--------|-------|" + "|".join("-------" for _ in tickers_income) + "|",
        ]

        for mk in sorted(calendario.keys()):
            ano, mes = int(mk[:4]), int(mk[5:])
            label = f"{MESES_PT[mes]}/{str(ano)[2:]}"
            total = totais_income.get(mk, 0)
            st    = status_mes(mk)
            total_s = _fmt_valor(total, "projetado" if mk > _mes_key(hoje) else None)

            celulas = []
            for tk in tickers_income:
                d = calendario[mk].get(tk)
                if d:
                    celulas.append(_fmt_valor(d["valor"], d.get("status")))
                else:
                    celulas.append("—")

            linhas.append(f"| {label} | {st} | {total_s} | " + " | ".join(celulas) + " |")

        linhas.append("")
        linhas += [
            "> ✅ recebido  |  📢 declarado  |  ~ projetado  |  ⏳ mês atual",
            "",
        ]
    else:
        linhas += ["> Nenhum ativo gerador de renda periódica na carteira.", ""]

    # ── Seção B: Valorização RF ───────────────────────────────────────────────
    linhas += [
        "---",
        "",
        "## 📈 Valorização Mensal — Renda Fixa / Tesouro",
        "",
        "> Crescimento mensal estimado sobre o capital investido. "
        "IR calculado sobre a alíquota vigente no mês de referência.",
        "> IOF = zero (posições com mais de 30 dias de aplicação).",
        "",
    ]

    if tickers_rf and valorizacao_rf:
        # Colunas: para cada ticker RF: bruto | líquido
        cab_rf = " | ".join(
            f"[[{tk}]] bruto | [[{tk}]] líq." for tk in tickers_rf
        )
        sep_rf = "|".join("-------|-------" for _ in tickers_rf)
        linhas += [
            f"| Mês | Total bruto | Total líq. | {cab_rf} |",
            f"|-----|------------|------------|{sep_rf}|",
        ]

        for mk in sorted(valorizacao_rf.keys()):
            ano, mes = int(mk[:4]), int(mk[5:])
            label = f"{MESES_PT[mes]}/{str(ano)[2:]}"
            tb = totais_rf_bruto.get(mk, 0)
            tl = totais_rf_liq.get(mk, 0)

            celulas_rf = []
            for tk in tickers_rf:
                d = valorizacao_rf[mk].get(tk)
                if d:
                    celulas_rf.append(f"R$ {d['bruto']:,.2f}~ | R$ {d['liquido']:,.2f}~")
                else:
                    celulas_rf.append("— | —")

            linhas.append(
                f"| {label} | R$ {tb:,.2f}~ | R$ {tl:,.2f}~ | "
                + " | ".join(celulas_rf) + " |"
            )
        linhas.append("")
    else:
        linhas += ["> Nenhuma posição RF/TD/DEB/CRI-CRA na carteira.", ""]

    # ── Seção C: Resumo ───────────────────────────────────────────────────────
    total_income_12m = sum(totais_income.values())
    total_rf_bruto_12m = sum(totais_rf_bruto.values())
    total_rf_liq_12m   = sum(totais_rf_liq.values())
    total_renda_12m    = total_income_12m + total_rf_liq_12m

    linhas += [
        "---",
        "",
        "## 📊 Resumo — 12 Meses",
        "",
        "| Métrica | Valor |",
        "|---------|-------|",
    ]
    if meta_mensal:
        linhas.append(f"| Meta mensal IPS | R$ {meta_mensal:,.0f}/mês |")
        linhas.append(f"| Projeção média (renda periódica) | R$ {media_projecao:,.0f}/mês~ |")
        if meses_abaixo > 0:
            linhas.append(f"| Meses abaixo da meta | {meses_abaixo} de {len(meses_futuros)} |")
    linhas.append(f"| Total renda periódica 12m | R$ {total_income_12m:,.2f}~ |")
    linhas.append(f"| Total valorização RF 12m (bruto) | R$ {total_rf_bruto_12m:,.2f}~ |")
    linhas.append(f"| Total valorização RF 12m (líquido) | R$ {total_rf_liq_12m:,.2f}~ |")
    linhas.append(f"| **Renda total estimada 12m** | **R$ {total_renda_12m:,.2f}~** |")
    linhas += [
        "",
        "---",
        "",
        "## Links",
        "",
        "[[carteira]] | [[ips]] | [[metas]] | [[dividendos]]",
        "",
    ]

    SAIDA_PATH.parent.mkdir(parents=True, exist_ok=True)
    SAIDA_PATH.write_text("\n".join(linhas), encoding="utf-8")
    print(f"  Salvo: {SAIDA_PATH}")


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    hoje = date.today()
    print(f"\nSBWAA Fluxo de Caixa — {hoje.isoformat()}")
    print("=" * 60)

    posicoes = parse_carteira()
    if not posicoes:
        print("  Carteira vazia.")
        return

    datas_entrada = parse_historico()
    meta_mensal   = ler_meta_mensal()
    bcb           = _carregar_bcb()
    cdi_m         = cdi_mensal_atual(bcb)

    posicoes_income = [p for p in posicoes if p["tipo"] not in TIPOS_RF]
    posicoes_rf     = [p for p in posicoes if p["tipo"] in TIPOS_RF]

    print(f"  Income: {len(posicoes_income)} ativos | RF: {len(posicoes_rf)} ativos")
    if meta_mensal:
        print(f"  Meta mensal IPS: R$ {meta_mensal:,.0f}/mês")

    # Busca dados de dividendos para ativos de renda
    analises = {}
    for pos in posicoes_income:
        tk = pos["ticker"]
        de = datas_entrada.get(tk)
        print(f"  Buscando {tk}...", end="", flush=True)
        if eh_ticker_br(tk):
            analises[tk] = dados_br(tk, datetime.now(), de)
        else:
            analises[tk] = dados_intl(ticker_yahoo(tk), datetime.now(), de)
        ok = "erro" not in analises[tk]
        print(" ok" if ok else f" falhou: {analises[tk].get('erro', '?')}")

    # Calendário 12 meses
    print("  Construindo calendário...")
    calendario = construir_calendario(posicoes_income, analises, datas_entrada, hoje)

    # Valorização RF
    val_rf = {}
    if posicoes_rf:
        print("  Calculando valorização RF...")
        val_rf = calcular_valorizacao_rf(posicoes_rf, cdi_m, hoje)

    # Output
    gerar_md(hoje, posicoes_income, posicoes_rf, calendario, val_rf, meta_mensal)

    # Resumo terminal
    totais = {mk: sum(v["valor"] for v in d.values()) for mk, d in calendario.items()}
    meses_futuros = [mk for mk in calendario if mk >= _mes_key(hoje)]
    media = sum(totais.get(mk, 0) for mk in meses_futuros) / len(meses_futuros) if meses_futuros else 0

    print(f"\n  Projeção média mensal (renda periódica): R$ {media:,.0f}~")
    if meta_mensal:
        gap = media - meta_mensal
        emoji = "✅" if gap >= 0 else "⚠️"
        print(f"  {emoji} Meta: R$ {meta_mensal:,.0f}/mês | Gap: R$ {gap:+,.0f}/mês")
    print(f"\n{'='*60}\n")


if __name__ == "__main__":
    main()
