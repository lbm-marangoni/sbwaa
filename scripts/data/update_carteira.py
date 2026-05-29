"""
update_carteira.py — Atualiza cotações e P&L na carteira.md.
Uso: python update_carteira.py
Nunca transmite dados privados (quantidade, preço médio) para fora.
"""

import re
import sys
import json
from datetime import datetime
from pathlib import Path

VAULT_ROOT = Path(__file__).parent.parent.parent / "vault"
CARTEIRA_PATH = VAULT_ROOT / "00-portfolio" / "carteira.md"
IPS_PATH      = VAULT_ROOT / "00-portfolio" / "ips.md"
SCRIPTS_DIR = Path(__file__).parent

sys.path.insert(0, str(SCRIPTS_DIR))
from fetch_fundamentals import buscar_ticker as brapi_buscar
from fetch_yahoo import buscar_ticker as yahoo_buscar

TICKERS_BR_SUFFIX = ".SA"

# Ticker reservado para a RF Oportunidade (Caixinha Nubank)
OPORT_TICKER  = "RF-OPRT"
RF_OPORT_PATH = VAULT_ROOT / "00-portfolio" / "rf-oportunidade.md"

# Mapeamento tipo → classe IPS (usa os labels com emoji gravados por add_ativo.py)
TIPO_CLASSE = {
    "🟦 AÇÃO ON":  "Ações BR",
    "🟦 AÇÃO PN":  "Ações BR",
    "🟩 FII":      "FIIs",
    "🟨 ETF BR":   "ETFs BR",
    "🟥 ETF INTL": "ETFs Internac.",
    "⬜ RF":       "Renda Fixa",
    "🟪 TD":       "Tesouro Direto",
    "🟫 DEB":      "Renda Fixa",
    "🟧 CRI/CRA":  "Renda Fixa",
    # fallbacks sem emoji (compatibilidade)
    "AÇÃO ON": "Ações BR", "AÇÃO PN": "Ações BR",
    "FII": "FIIs", "ETF BR": "ETFs BR", "ETF INTL": "ETFs Internac.",
    "RF": "Renda Fixa", "TD": "Tesouro Direto",
    "DEB": "Renda Fixa", "CRI/CRA": "Renda Fixa",
}

# Fallback quando ips.md não existe
CLASSE_IPS_PADRAO = {
    "Ações BR": 25.0, "FIIs": 35.0, "Renda Fixa": 20.0,
    "Tesouro Direto": 12.0, "ETFs Internac.": 8.0,
}


def cotacao_rf_oportunidade() -> float | None:
    """Lê o saldo_bruto da Caixinha como 'preço atual' do RF-OPRT."""
    if not RF_OPORT_PATH.exists():
        return None
    try:
        sys.path.insert(0, str(SCRIPTS_DIR))
        from rf_oportunidade import ler_estado
        saldo, _ = ler_estado()
        return saldo if saldo > 0 else None
    except Exception:
        return None


def cotacao_br(ticker: str) -> float | None:
    try:
        dados = brapi_buscar(ticker)
        return dados.get("cotacao")
    except Exception as e:
        print(f"  AVISO Yahoo Finance [{ticker}]: {e}")
    # fallback com sufixo .SA explícito
    try:
        dados = yahoo_buscar(ticker + TICKERS_BR_SUFFIX)
        return dados.get("cotacao_atual")
    except Exception as e:
        print(f"  AVISO Yahoo Finance [{ticker}.SA]: {e}")
    return None


def cotacao_intl(ticker: str) -> float | None:
    try:
        dados = yahoo_buscar(ticker)
        return dados.get("cotacao_atual")
    except Exception as e:
        print(f"  AVISO Yahoo [{ticker}]: {e}")
    return None


def parsear_tabela(conteudo: str) -> list[dict]:
    """Extrai linhas da tabela de posições do carteira.md."""
    linhas = []
    dentro = False
    cabecalho = []
    for linha in conteudo.splitlines():
        stripped = linha.strip()
        if stripped.startswith("| Ticker") or stripped.startswith("|Ticker"):
            cabecalho = [c.strip() for c in stripped.split("|")[1:-1]]
            dentro = True
            continue
        if dentro and stripped.startswith("|---"):
            continue
        if dentro and stripped.startswith("|"):
            celulas = [c.strip() for c in stripped.split("|")[1:-1]]
            if len(celulas) >= len(cabecalho[:5]):
                row = dict(zip(cabecalho, celulas + [""] * 10))
                linhas.append(row)
        elif dentro and stripped == "":
            break
    return linhas


def eh_ticker_br(ticker: str) -> bool:
    t = ticker.upper()
    return bool(re.match(r"^[A-Z]{4}[0-9]{1,2}[FBP]?$", t)) and not t.startswith("^")


def _ler_ips_alvo() -> dict:
    """Lê alocação alvo do IPS; retorna fallback padrão se não encontrar."""
    if not IPS_PATH.exists():
        return CLASSE_IPS_PADRAO.copy()
    conteudo = IPS_PATH.read_text(encoding="utf-8")
    resultado = {}
    dentro = False
    for linha in conteudo.splitlines():
        stripped = linha.strip()
        if stripped.startswith("| Classe"):
            dentro = True
            continue
        if dentro and stripped.startswith("|---"):
            continue
        if dentro and stripped.startswith("|"):
            cols = [c.strip() for c in stripped.split("|")[1:-1]]
            if len(cols) >= 2 and cols[0] and cols[1]:
                try:
                    resultado[cols[0]] = float(cols[1].replace("%", "").replace(",", "."))
                except ValueError:
                    pass
        elif dentro and not stripped.startswith("|"):
            break
    return resultado or CLASSE_IPS_PADRAO.copy()


def _barra(pct: float, maximo: float = 100.0, width: int = 20) -> str:
    """Gera barra visual com blocos █░ (compatível com Obsidian)."""
    if maximo <= 0:
        return "░" * width
    filled = min(int(pct / maximo * width), width)
    return "█" * filled + "░" * (width - filled)


def _secoes_visuais(linhas_novas: list[dict], total_atual: float) -> str:
    """
    Gera seções visuais de alocação para carteira.md.
    Retorna string markdown para ser appendada após ## Resumo.
    """
    if not linhas_novas or total_atual <= 0:
        return ""

    ips_alvo = _ler_ips_alvo()
    agora = datetime.now().strftime("%Y-%m-%d %H:%M")

    # ── Alocação por classe ───────────────────────────────────────────────────
    classe_val: dict[str, float] = {}
    for row in linhas_novas:
        tipo = row.get("Tipo", "").strip()
        classe = TIPO_CLASSE.get(tipo, "Outros")
        try:
            val = float(row.get("Valor (R$)", "0").replace(",", "").replace("+", ""))
        except Exception:
            val = 0.0
        classe_val[classe] = classe_val.get(classe, 0.0) + val

    # ── Seção: Alocação por Classe ───────────────────────────────────────────
    md = [
        "",
        "---",
        "",
        "## 📊 Alocação por Classe",
        "",
        f"*Atualizado em {agora} — gerado automaticamente pelo sistema*",
        "",
        "| Classe | Atual | Alvo IPS | Gap | Barra |",
        "|--------|-------|----------|-----|-------|",
    ]

    alertas = []
    todas_classes = sorted(
        set(list(ips_alvo.keys()) + list(classe_val.keys())),
        key=lambda c: -classe_val.get(c, 0.0),
    )
    for classe in todas_classes:
        val = classe_val.get(classe, 0.0)
        pct_atual = val / total_atual * 100
        alvo = ips_alvo.get(classe, 0.0)
        gap = pct_atual - alvo
        gap_str = f"`{gap:+.1f}%`" if alvo else "—"
        alvo_str = f"{alvo:.1f}%" if alvo else "—"
        barra = _barra(pct_atual, 100.0, 20)
        md.append(f"| {classe} | {pct_atual:.1f}% | {alvo_str} | {gap_str} | `{barra}` |")
        if alvo and abs(gap) >= 5:
            alertas.append((classe, gap))

    if alertas:
        md.append("")
        for classe, gap in alertas:
            tipo_alerta = "warning" if abs(gap) < 10 else "danger"
            sinal = "acima" if gap > 0 else "abaixo"
            md.append(f"> [!{tipo_alerta}] **{classe}** — {abs(gap):.1f}% {sinal} do alvo IPS")

    # ── Seção: Posições — Detalhes Visuais ───────────────────────────────────
    md += [
        "",
        "## 📈 Posições — Detalhes Visuais",
        "",
        "| Ticker | Tipo | P&L | % Carteira | % Classe | Barra (carteira) |",
        "|--------|------|-----|-----------|----------|-----------------|",
    ]

    # Ordenar por valor decrescente
    linhas_ord = sorted(
        linhas_novas,
        key=lambda r: float(r.get("Valor (R$)", "0").replace(",", "").replace("+", "") or 0),
        reverse=True,
    )

    for row in linhas_ord:
        ticker = row.get("Ticker", "")
        tipo   = row.get("Tipo", "")
        pl_pct = row.get("P&L (%)", "—")
        classe = TIPO_CLASSE.get(tipo, "Outros")
        classe_total = classe_val.get(classe, 0.0)

        try:
            val = float(row.get("Valor (R$)", "0").replace(",", "").replace("+", ""))
        except Exception:
            val = 0.0

        pct_total  = val / total_atual * 100 if total_atual > 0 else 0.0
        pct_classe = val / classe_total * 100 if classe_total > 0 else 0.0
        # Escala da barra: 25% = largura total (concentração máxima IPS)
        barra = _barra(pct_total, 25.0, 20)

        md.append(
            f"| {ticker} | {tipo} | {pl_pct} "
            f"| {pct_total:.1f}% | {pct_classe:.1f}% | `{barra}` |"
        )

    # Nota de concentração máxima
    if linhas_ord:
        try:
            max_val = float(linhas_ord[0].get("Valor (R$)", "0").replace(",", "").replace("+", ""))
            max_pct = max_val / total_atual * 100
            if max_pct > 20:
                md.append("")
                md.append(f"> [!warning] Concentração máxima: **{linhas_ord[0]['Ticker']}** em {max_pct:.1f}% (limite IPS: 20%)")
        except Exception:
            pass

    return "\n".join(md)


def atualizar_carteira():
    if not CARTEIRA_PATH.exists():
        print(f"Erro: {CARTEIRA_PATH} não encontrado.")
        sys.exit(1)

    conteudo = CARTEIRA_PATH.read_text(encoding="utf-8")
    posicoes = parsear_tabela(conteudo)

    posicoes_validas = [
        p for p in posicoes
        if p.get("Ticker", "").strip() and
           p.get("Qtd", "").strip() and
           p.get("Preço Médio", "").strip()
    ]

    if not posicoes_validas:
        print("Carteira sem posições preenchidas — nada a atualizar.")
        return

    total_investido = 0.0
    total_atual = 0.0
    linhas_novas = []

    for pos in posicoes_validas:
        ticker_raw = pos["Ticker"].strip().strip("[]").split("|")[0].replace("[[", "").strip()
        ticker = ticker_raw.upper()

        try:
            qtd = float(pos["Qtd"].replace(",", "."))
            pm = float(pos["Preço Médio"].replace(",", ".").replace("R$", "").strip())
        except ValueError:
            print(f"  AVISO: {ticker} — quantidade ou preço médio inválido, pulando.")
            continue

        tipo = pos.get("Tipo", "").strip()
        setor = pos.get("Setor", "").strip()

        print(f"  Atualizando {ticker}...")
        if ticker == OPORT_TICKER:
            preco_atual = cotacao_rf_oportunidade()
        elif eh_ticker_br(ticker):
            preco_atual = cotacao_br(ticker)
        else:
            preco_atual = cotacao_intl(ticker)

        if preco_atual is None:
            print(f"  AVISO: cotação não obtida para {ticker}, mantendo linha sem cálculo.")
            linhas_novas.append(pos)
            continue

        valor_pos = round(qtd * preco_atual, 2)
        pl_rs = round(valor_pos - qtd * pm, 2)
        pl_pct = round((preco_atual - pm) / pm * 100, 1) if pm else 0.0

        total_investido += qtd * pm
        total_atual += valor_pos

        ticker_display = ticker

        linhas_novas.append({
            "Ticker": ticker_display,
            "Tipo": tipo,
            "Setor": setor,
            "Qtd": str(int(qtd) if qtd.is_integer() else qtd),
            "Preço Médio": f"{pm:.2f}",
            "Preço Atual": f"{preco_atual:.2f}",
            "Valor (R$)": f"{valor_pos:,.2f}",
            "P&L (R$)": f"{pl_rs:+,.2f}",
            "P&L (%)": f"{pl_pct:+.1f}%",
            "Alocação (%)": "__ALLOC__",
        })

    # calcular alocação
    for row in linhas_novas:
        if row.get("Alocação (%)") == "__ALLOC__" and total_atual > 0:
            try:
                val = float(row["Valor (R$)"].replace(",", "").replace("+", ""))
                row["Alocação (%)"] = f"{val / total_atual * 100:.1f}%"
            except Exception:
                row["Alocação (%)"] = "—"

    pl_total = round(total_atual - total_investido, 2)
    pl_total_pct = round((total_atual - total_investido) / total_investido * 100, 1) if total_investido else 0.0
    agora = datetime.now().strftime("%Y-%m-%d %H:%M")

    cabecalho_tabela = "| Ticker | Tipo | Setor | Qtd | Preço Médio | Preço Atual | Valor (R$) | P&L (R$) | P&L (%) | Alocação (%) |"
    separador = "|--------|------|-------|-----|-------------|-------------|------------|----------|---------|--------------|"
    linhas_md = [cabecalho_tabela, separador]
    for row in linhas_novas:
        cols = [
            row.get("Ticker", ""), row.get("Tipo", ""), row.get("Setor", ""),
            row.get("Qtd", ""), row.get("Preço Médio", ""), row.get("Preço Atual", ""),
            row.get("Valor (R$)", ""), row.get("P&L (R$)", ""), row.get("P&L (%)", ""),
            row.get("Alocação (%)", ""),
        ]
        linhas_md.append("| " + " | ".join(cols) + " |")

    tabela_nova = "\n".join(linhas_md)

    resumo_novo = (
        f"- **Patrimônio Total:** R$ {total_atual:,.2f}\n"
        f"- **Total Investido:** R$ {total_investido:,.2f}\n"
        f"- **P&L Total:** R$ {pl_total:+,.2f} ({pl_total_pct:+.1f}%)\n"
        f"- **Última atualização:** {agora}"
    )

    # Substituir tabela e resumo no conteúdo original
    novo_conteudo = re.sub(
        r"\| Ticker \|.*?(?=\n##|\Z)", tabela_nova, conteudo, flags=re.DOTALL
    )
    novo_conteudo = re.sub(
        r"- \*\*Patrimônio Total:\*\*.*?- \*\*Última atualização:\*\*.*",
        resumo_novo, novo_conteudo, flags=re.DOTALL
    )

    # ── Seções visuais: adicionar/substituir após ## Resumo ──────────────────
    secoes = _secoes_visuais(linhas_novas, total_atual)
    if secoes:
        # Remover seções visuais anteriores se existirem (após o separador ---)
        novo_conteudo = re.sub(
            r"\n---\n\n## 📊 Alocação por Classe.*$",
            "", novo_conteudo, flags=re.DOTALL
        )
        novo_conteudo = novo_conteudo.rstrip() + "\n" + secoes + "\n"

    CARTEIRA_PATH.write_text(novo_conteudo, encoding="utf-8")
    print(f"\nCarteira atualizada em {agora}")
    print(f"  Patrimônio Total : R$ {total_atual:,.2f}")
    print(f"  Total Investido  : R$ {total_investido:,.2f}")
    print(f"  P&L Total        : R$ {pl_total:+,.2f} ({pl_total_pct:+.1f}%)")
    if linhas_novas and total_atual > 0:
        print(f"  📄 Visão visual    : vault/00-portfolio/carteira.md")

    # ── Bloco de renda (lê cache do /dividendos) ──────────────────────────────
    cache_path = VAULT_ROOT / "00-portfolio" / ".proventos-cache.json"
    if cache_path.exists():
        try:
            prov = json.loads(cache_path.read_text(encoding="utf-8"))
            dy   = prov.get("dy_ponderado_pct", 0.0)
            men  = prov.get("renda_mensal_est", 0.0)
            men_real = prov.get("renda_mensal_real", 0.0)
            ano  = prov.get("total_no_ano", 0.0)
            atua = prov.get("atualizado_em", "—")
            if dy or men or ano:
                print(f"\n  {'─'*46}")
                if dy:
                    print(f"  DY estimado      : {dy:.2f}% a.a.")
                if men:
                    print(f"  Renda mensal est.: R$ {men:,.2f}")
                if men_real:
                    print(f"  Renda mensal real: R$ {men_real:,.2f}  (média {datetime.now().year})")
                if ano:
                    print(f"  Recebido em {datetime.now().year}  : R$ {ano:,.2f}")
                print(f"  Fonte: /dividendos ({atua})")
                print(f"  {'─'*46}")
        except Exception:
            pass


if __name__ == "__main__":
    atualizar_carteira()
