"""
vender_ativo.py — Registra venda (parcial ou total) de um ativo na carteira.

Renda Variável:
    python vender_ativo.py --ticker PETR4 --quantidade 50 --preco 45.00

Renda Fixa / Tesouro (resgate pelo valor total):
    python vender_ativo.py --ticker CDB001 --quantidade 1 --valor 5500.00
    python vender_ativo.py --ticker NTNB35 --quantidade 1 --valor 3800.00

Resgate parcial (ex: 60% de uma posição RF com qtd=1):
    python vender_ativo.py --ticker CDB001 --quantidade 0.6 --valor 3300.00

Flag opcional para data de entrada (se não encontrada em tese.md):
    python vender_ativo.py --ticker CDB001 --quantidade 1 --valor 5500 --data-entrada 2025-01-10
"""

import argparse
import sys
import re
from datetime import datetime
from pathlib import Path

VAULT_ROOT     = Path(__file__).parent.parent.parent / "vault"
CARTEIRA_PATH  = VAULT_ROOT / "00-portfolio" / "carteira.md"
HISTORICO_PATH = VAULT_ROOT / "00-portfolio" / "historico-trades.md"
ATIVOS_DIR     = VAULT_ROOT / "01-ativos"

SCRIPTS_DIR = Path(__file__).parent
sys.path.insert(0, str(SCRIPTS_DIR))

HISTORICO_HEADER = "| Data | Ticker | Tipo | Operação | Qtd | Preço | Total R$ | PM ant. | P&L ant. |"
HISTORICO_SEP    = "|------|--------|------|----------|-----|-------|----------|---------|----------|"

# Tipos RF e seus rótulos
TIPOS_RF_TRIBUTADO = {"renda-fixa", "tesouro", "debenture"}
TIPOS_RF_ISENTO    = {"cri-cra"}   # IR isento para PF (Lei 12.431/2011)
TIPOS_RF            = TIPOS_RF_TRIBUTADO | TIPOS_RF_ISENTO

LABEL_UNIDADE = {
    "renda-fixa": "unidades",
    "tesouro":    "títulos",
    "debenture":  "unidades",
    "cri-cra":    "unidades",
}


# ── Leitura da carteira ────────────────────────────────────────────────────────

def buscar_posicao(ticker: str) -> dict | None:
    if not CARTEIRA_PATH.exists():
        return None
    for linha in CARTEIRA_PATH.read_text(encoding="utf-8").splitlines():
        s = linha.strip()
        if not s.startswith("|") or s.startswith("| Ticker") or s.startswith("|---"):
            continue
        cols = [c.strip() for c in s.split("|")[1:-1]]
        if len(cols) >= 5 and cols[0].upper() == ticker.upper():
            try:
                qtd = float(cols[3].replace(",", "."))
                pm  = float(cols[4].replace(",", ".").replace("R$", "").strip())
                return {"qtd": qtd, "pm": pm, "tipo": cols[1], "setor": cols[2], "cols": cols}
            except (ValueError, IndexError):
                pass
    return None


def ler_data_entrada(ticker: str) -> str | None:
    """Lê data_entrada do frontmatter de vault/01-ativos/TICKER/tese.md."""
    tese = ATIVOS_DIR / ticker.upper() / "tese.md"
    if not tese.exists():
        return None
    for linha in tese.read_text(encoding="utf-8").splitlines():
        if linha.strip().startswith("data_entrada:"):
            val = linha.split(":", 1)[1].strip()
            if re.match(r"\d{4}-\d{2}-\d{2}", val):
                return val
    return None


# ── Escrita na carteira ────────────────────────────────────────────────────────

def remover_linha_carteira(ticker: str):
    conteudo = CARTEIRA_PATH.read_text(encoding="utf-8")
    novas = []
    for linha in conteudo.splitlines():
        s = linha.strip()
        if s.startswith("|") and not s.startswith("| Ticker") and not s.startswith("|---"):
            cols = [c.strip() for c in s.split("|")[1:-1]]
            if cols and cols[0].upper() == ticker.upper():
                continue
        novas.append(linha)
    CARTEIRA_PATH.write_text("\n".join(novas), encoding="utf-8")


def atualizar_qtd_carteira(ticker: str, nova_qtd: float):
    conteudo = CARTEIRA_PATH.read_text(encoding="utf-8")
    linhas   = conteudo.splitlines()
    for i, linha in enumerate(linhas):
        s = linha.strip()
        if not s.startswith("|") or s.startswith("| Ticker") or s.startswith("|---"):
            continue
        cols = [c.strip() for c in s.split("|")[1:-1]]
        if len(cols) >= 5 and cols[0].upper() == ticker.upper():
            while len(cols) < 10:
                cols.append("")
            cols[3] = str(int(nova_qtd)) if nova_qtd == int(nova_qtd) else f"{nova_qtd:.4f}".rstrip("0").rstrip(".")
            cols[5] = cols[6] = cols[7] = cols[8] = cols[9] = ""
            linhas[i] = "| " + " | ".join(cols) + " |"
            break
    CARTEIRA_PATH.write_text("\n".join(linhas), encoding="utf-8")


# ── Histórico ──────────────────────────────────────────────────────────────────

def _garantir_header_historico():
    conteudo = HISTORICO_PATH.read_text(encoding="utf-8")
    if "PM ant." not in conteudo:
        conteudo = conteudo.replace(
            "| Data | Ticker | Tipo | Operação | Qtd | Preço | Total R$ |",
            HISTORICO_HEADER,
        ).replace(
            "|------|--------|------|----------|-----|-------|----------|",
            HISTORICO_SEP,
        )
        HISTORICO_PATH.write_text(conteudo, encoding="utf-8")


def adicionar_historico_venda(ticker: str, tipo: str, qtd: float, preco: float,
                               data: str, pm_pos: float, pl_realizado: str):
    _garantir_header_historico()
    conteudo   = HISTORICO_PATH.read_text(encoding="utf-8")
    total      = round(qtd * preco, 2)
    qtd_str    = str(int(qtd)) if qtd == int(qtd) else f"{qtd:.4f}".rstrip("0").rstrip(".")
    nova_linha = (
        f"| {data} | {ticker} | {tipo} | VENDA | {qtd_str} | "
        f"{preco:.2f} | {total:,.2f} | {pm_pos:.2f} | {pl_realizado} |"
    )
    linhas = conteudo.splitlines()
    j = len(linhas)
    for i, l in enumerate(linhas):
        if "|-----" in l or "|------" in l:
            j = i + 1
            while j < len(linhas) and linhas[j].strip().startswith("|"):
                j += 1
            break
    linhas.insert(j, nova_linha)
    HISTORICO_PATH.write_text("\n".join(linhas), encoding="utf-8")


# ── Tributação RF ──────────────────────────────────────────────────────────────

def calcular_e_exibir_tributacao_rf(
    ticker: str,
    tipo: str,
    principal: float,
    rendimento: float,
    dias: int,
    data_entrada: str,
):
    """Calcula IR + IOF e exibe o bloco tributário para RF/TD/DEB/CRI-CRA."""
    sys.path.insert(0, str(Path(__file__).parent))
    from calculos_tributarios import calcular_tributario_rf, aliquota_ir_rf, aliquota_iof_rf

    isento_ir = tipo in TIPOS_RF_ISENTO   # CRI/CRA: isento IR para PF

    if rendimento <= 0:
        print(f"  Rendimento       : R$ {rendimento:,.2f}  (sem ganho — sem tributos)")
        liquido = principal + rendimento
        print(f"  Líquido estimado : R$ {liquido:,.2f}")
        return round(liquido, 2)

    trib = calcular_tributario_rf(principal, rendimento, dias)

    al_iof = trib.iof_aliquota_pct
    al_ir  = 0.0 if isento_ir else trib.ir_aliquota_pct
    iof_v  = trib.iof_valor
    ir_v   = 0.0 if isento_ir else trib.ir_valor
    rend_apos_iof = rendimento - iof_v
    liquido = round(principal + rend_apos_iof - ir_v, 2)

    iof_str = f"✅ zerado" if iof_v == 0 else f"⚠️  R$ {iof_v:,.2f} ({al_iof:.0f}%)"
    ir_str  = f"isento — CRI/CRA (Lei 12.431)" if isento_ir else f"R$ {ir_v:,.2f} ({al_ir:.1f}%)"

    print(f"  {'─'*48}")
    print(f"  TRIBUTAÇÃO  ({dias} dias corridos desde {data_entrada})")
    print(f"  {'─'*48}")
    print(f"  Principal           : R$ {principal:>10,.2f}")
    print(f"  Rendimento bruto    : R$ {rendimento:>10,.2f}")
    print(f"  IOF estimado        : {iof_str}")
    print(f"  IR estimado         : {ir_str}")
    print(f"  {'─'*48}")
    print(f"  Líquido estimado    : R$ {liquido:>10,.2f}")

    if tipo == "debenture":
        print(f"  ⚠️  DEB simples: verificar se é incentivada (isenção IR) no seu extrato.")

    return liquido


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Registra resgate/venda de ativo na carteira SBWAA")
    parser.add_argument("--ticker",       required=True)
    parser.add_argument("--quantidade",   required=True, type=float)
    parser.add_argument("--preco",        type=float, default=None,
                        help="Preço de venda por ação/cota (RV) ou por unidade (RF)")
    parser.add_argument("--valor",        type=float, default=None,
                        help="Valor total bruto do resgate em R$ (RF/TD — alternativa a --preco)")
    parser.add_argument("--data",         default=None,
                        help="Data da venda/resgate YYYY-MM-DD (padrão: hoje)")
    parser.add_argument("--data-entrada", default=None, dest="data_entrada",
                        help="Data da aplicação YYYY-MM-DD para cálculo IR/IOF (RF/TD). "
                             "Se omitida, lê de vault/01-ativos/TICKER/tese.md automaticamente.")
    args = parser.parse_args()

    ticker = args.ticker.upper()

    # Validação: precisa de --preco ou --valor
    if args.preco is None and args.valor is None:
        print("Erro: informe --preco (por unidade) ou --valor (total bruto do resgate).")
        sys.exit(1)

    # Data da venda
    if args.data:
        try:
            datetime.strptime(args.data, "%Y-%m-%d")
            data_venda = args.data
        except ValueError:
            print("Erro: --data deve estar no formato YYYY-MM-DD")
            sys.exit(1)
    else:
        data_venda = datetime.now().strftime("%Y-%m-%d")

    posicao = buscar_posicao(ticker)
    if not posicao:
        print(f"Erro: {ticker} não encontrado na carteira.")
        sys.exit(1)

    qtd_atual = posicao["qtd"]
    pm        = posicao["pm"]
    tipo_raw  = posicao["tipo"]   # ex: "🟩 FII" ou "⬜ RF"

    # Normaliza tipo para comparação (ex: "⬜ RF" → "renda-fixa")
    TIPO_LABEL_PARA_KEY = {
        "🟦 AÇÃO ON":  "acao-on",
        "🟦 AÇÃO PN":  "acao-pn",
        "🟩 FII":      "fii",
        "🟨 ETF BR":   "etf-br",
        "🟥 ETF INTL": "etf-intl",
        "⬜ RF":       "renda-fixa",
        "🟪 TD":       "tesouro",
        "🟫 DEB":      "debenture",
        "🟧 CRI/CRA":  "cri-cra",
    }
    tipo_key = TIPO_LABEL_PARA_KEY.get(tipo_raw, tipo_raw.lower())
    eh_rf    = tipo_key in TIPOS_RF

    # Derivar preco_unit
    if args.valor is not None:
        preco_unit = round(args.valor / args.quantidade, 6)
    else:
        preco_unit = args.preco

    if args.quantidade > qtd_atual + 1e-9:
        print(f"Erro: tentando resgatar {args.quantidade} mas posição é de apenas {qtd_atual}.")
        sys.exit(1)

    # Cálculos base
    receita_bruta   = round(preco_unit * args.quantidade, 2)
    principal_venda = round(pm * args.quantidade, 2)
    pl_rs_total     = round(receita_bruta - principal_venda, 2)
    pl_pct          = (preco_unit - pm) / pm * 100 if pm else 0.0
    qtd_restante    = round(qtd_atual - args.quantidade, 8)

    # Rótulo de unidade
    label_unid = LABEL_UNIDADE.get(tipo_key, "ações")

    # ── Exibição ──────────────────────────────────────────────────────────────
    if eh_rf:
        titulo_op = "RESGATE TOTAL" if qtd_restante < 1e-9 else "RESGATE PARCIAL"
    else:
        titulo_op = "VENDA"

    print(f"\n  [{titulo_op}] {ticker}  ({tipo_raw})")
    print(f"  {'─'*48}")

    qtd_disp     = str(int(args.quantidade)) if args.quantidade == int(args.quantidade) else f"{args.quantidade:.4f}".rstrip("0").rstrip(".")
    qtd_ant_disp = str(int(qtd_atual))        if qtd_atual     == int(qtd_atual)        else f"{qtd_atual:.4f}".rstrip("0").rstrip(".")

    print(f"  Posição atual    : {qtd_ant_disp} {label_unid} @ P.M. R$ {pm:.2f}")
    if eh_rf:
        print(f"  Resgatando       : {qtd_disp} {label_unid}  →  R$ {receita_bruta:,.2f} bruto")
    else:
        print(f"  Vendendo         : {qtd_disp} {label_unid} @ R$ {preco_unit:.2f}")
        print(f"  Receita bruta    : R$ {receita_bruta:,.2f}")
    print(f"  P&L bruto        : R$ {pl_rs_total:+,.2f}  ({pl_pct:+.1f}%)")

    # ── Tributação RF ─────────────────────────────────────────────────────────
    liquido_rf = None
    if eh_rf:
        # Resolver data de entrada
        data_entrada_str = args.data_entrada or ler_data_entrada(ticker)

        if data_entrada_str:
            try:
                d_entrada = datetime.strptime(data_entrada_str, "%Y-%m-%d")
                d_venda   = datetime.strptime(data_venda, "%Y-%m-%d")
                dias      = max(0, (d_venda - d_entrada).days)
            except ValueError:
                dias = 0
                data_entrada_str = "data inválida"
        else:
            dias = 0
            data_entrada_str = "desconhecida"
            print(f"\n  ⚠️  Data de entrada não encontrada em tese.md.")
            print(f"     Use --data-entrada YYYY-MM-DD para cálculo correto de IR/IOF.")

        rendimento = max(0.0, pl_rs_total)
        liquido_rf = calcular_e_exibir_tributacao_rf(
            ticker, tipo_key,
            principal_venda, rendimento,
            dias, data_entrada_str,
        )

    # ── Tributação RV ─────────────────────────────────────────────────────────
    elif pl_rs_total > 0:
        try:
            from calculos_tributarios import calcular_ir_renda_variavel
            trib_rv = calcular_ir_renda_variavel(ticker, tipo_key, pl_rs_total)
            print(f"  IR estimado      : {trib_rv.linha_resumo()}")
        except Exception:
            pass

    print(f"  {'─'*48}")

    # ── Registro ──────────────────────────────────────────────────────────────
    pl_str = f"{pl_pct:+.1f}%"
    if eh_rf and liquido_rf is not None:
        pl_liquido = round(liquido_rf - principal_venda, 2)
        pl_liq_pct = pl_liquido / principal_venda * 100 if principal_venda else 0
        pl_str = f"{pl_pct:+.1f}% bruto / {pl_liq_pct:+.1f}% líq."

    adicionar_historico_venda(ticker, tipo_raw, args.quantidade, preco_unit,
                              data_venda, pm, pl_str)

    if qtd_restante < 1e-9:
        remover_linha_carteira(ticker)
        print(f"  Posição zerada   : {ticker} removido da carteira.")
    else:
        atualizar_qtd_carteira(ticker, qtd_restante)
        qtd_rest_disp = str(int(qtd_restante)) if abs(qtd_restante - round(qtd_restante)) < 1e-9 else f"{qtd_restante:.4f}".rstrip("0").rstrip(".")
        print(f"  Posição restante : {qtd_rest_disp} {label_unid} @ P.M. R$ {pm:.2f}")
        if not eh_rf:
            print(f"  (P.M. inalterado — custo das {label_unid} restantes não muda com a venda)")

    if eh_rf and liquido_rf is not None:
        print(f"\n[OK] Resgate de {ticker} registrado em {data_venda}.")
        print(f"     Líquido estimado: R$ {liquido_rf:,.2f}  (verifique na corretora o valor exato).")
    else:
        print(f"\n[OK] Venda de {ticker} registrada em {data_venda}.")


if __name__ == "__main__":
    main()
