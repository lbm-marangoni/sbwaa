"""
add_ativo.py — Adiciona ou incrementa posição na carteira.
Se o ticker já existe, recalcula o preço médio ponderado e registra P&L antes.
Uso: python add_ativo.py --ticker PETR4 --tipo acao-pn --quantidade 100 --preco-medio 36.00 --setor energia
"""

import argparse
import sys
import time
from datetime import datetime
from pathlib import Path

VAULT_ROOT    = Path(__file__).parent.parent.parent / "vault"
CARTEIRA_PATH = VAULT_ROOT / "00-portfolio" / "carteira.md"
HISTORICO_PATH = VAULT_ROOT / "00-portfolio" / "historico-trades.md"
ATIVOS_DIR    = VAULT_ROOT / "01-ativos"

SCRIPTS_DIR = Path(__file__).parent
sys.path.insert(0, str(SCRIPTS_DIR))

TIPOS_VALIDOS = {
    "acao-on":    "🟦 AÇÃO ON",
    "acao-pn":    "🟦 AÇÃO PN",
    "fii":        "🟩 FII",
    "etf-br":     "🟨 ETF BR",
    "etf-intl":   "🟥 ETF INTL",
    "renda-fixa": "⬜ RF",
    "tesouro":    "🟪 TD",
    "debenture":  "🟫 DEB",
    "cri-cra":    "🟧 CRI/CRA",
}

# Tipos off-exchange: não têm cotação em bolsa — validação de API pulada automaticamente
TIPOS_OFF_EXCHANGE = {"renda-fixa", "tesouro", "debenture", "cri-cra"}

# Indexadores válidos para RF
INDEXADORES = ["CDI", "IPCA", "Selic", "PRE", "IGPM"]

HISTORICO_HEADER = "| Data | Ticker | Tipo | Operação | Qtd | Preço | Total R$ | PM ant. | P&L ant. |"
HISTORICO_SEP    = "|------|--------|------|----------|-----|-------|----------|---------|----------|"


# ── Validação e cotação ────────────────────────────────────────────────────────

def buscar_cotacao_atual(ticker: str, tipo: str) -> float | None:
    try:
        if tipo == "etf-intl":
            from fetch_yahoo import buscar_ticker
            return buscar_ticker(ticker).get("cotacao_atual")
        from fetch_fundamentals import buscar_ticker as brapi
        dados = brapi(ticker)
        if dados.get("cotacao"):
            return dados["cotacao"]
        time.sleep(0.3)
        from fetch_yahoo import buscar_ticker as yahoo
        r = yahoo(ticker + ".SA") or {}
        if r.get("cotacao_atual"):
            return r["cotacao_atual"]
        r2 = yahoo(ticker) or {}
        return r2.get("cotacao_atual")
    except Exception:
        return None


def validar_ticker(ticker: str, tipo: str) -> tuple[bool, float | None]:
    """Returns (válido, cotação_atual)."""
    print(f"  Validando {ticker} nas APIs...")
    preco = buscar_cotacao_atual(ticker, tipo)
    return preco is not None, preco


# ── Leitura da carteira ────────────────────────────────────────────────────────

def buscar_posicao(ticker: str) -> dict | None:
    """Retorna {'qtd', 'pm', 'tipo', 'setor'} se ticker já existe, else None."""
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
                return {"qtd": qtd, "pm": pm, "tipo": cols[1], "setor": cols[2]}
            except (ValueError, IndexError):
                pass
    return None


# ── Escrita na carteira ────────────────────────────────────────────────────────

def inserir_linha_carteira(ticker: str, tipo: str, setor: str, qtd: float, pm: float):
    conteudo = CARTEIRA_PATH.read_text(encoding="utf-8")
    label    = TIPOS_VALIDOS.get(tipo, tipo)
    qtd_str  = str(int(qtd)) if qtd == int(qtd) else str(qtd)
    nova_linha = f"| {ticker} | {label} | {setor.capitalize()} | {qtd_str} | {pm:.2f} |  |  |  |  |"
    linhas = conteudo.splitlines()
    idx = None
    for i, l in enumerate(linhas):
        if l.strip().startswith("|---") and i > 0 and "Ticker" in linhas[i - 1]:
            idx = i + 1
    if idx is None:
        for i, l in enumerate(linhas):
            if "|-----" in l:
                idx = i + 1
                break
    if idx is None:
        conteudo += f"\n{nova_linha}"
    else:
        j = idx
        while j < len(linhas) and linhas[j].strip().startswith("|"):
            j += 1
        linhas.insert(j, nova_linha)
        conteudo = "\n".join(linhas)
    CARTEIRA_PATH.write_text(conteudo, encoding="utf-8")


def atualizar_posicao(ticker: str, nova_qtd: float, novo_pm: float):
    """Atualiza qtd e PM de linha existente; limpa campos calculados."""
    conteudo = CARTEIRA_PATH.read_text(encoding="utf-8")
    linhas   = conteudo.splitlines()
    for i, linha in enumerate(linhas):
        s = linha.strip()
        if not s.startswith("|") or s.startswith("| Ticker") or s.startswith("|---"):
            continue
        cols = [c.strip() for c in s.split("|")[1:-1]]
        if len(cols) >= 5 and cols[0].upper() == ticker.upper():
            qtd_str = str(int(nova_qtd)) if nova_qtd == int(nova_qtd) else str(nova_qtd)
            while len(cols) < 10:
                cols.append("")
            cols[3] = qtd_str
            cols[4] = f"{novo_pm:.2f}"
            cols[5] = cols[6] = cols[7] = cols[8] = cols[9] = ""
            linhas[i] = "| " + " | ".join(cols) + " |"
            break
    CARTEIRA_PATH.write_text("\n".join(linhas), encoding="utf-8")


# ── Histórico ──────────────────────────────────────────────────────────────────

def _garantir_header_historico():
    """Migra header do historico para versão com PM ant. / P&L ant. se necessário."""
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


def adicionar_historico(ticker: str, tipo: str, qtd: float, pm: float,
                        data: str, pm_anterior: float | None = None,
                        pl_antes: str = "—"):
    _garantir_header_historico()
    conteudo = HISTORICO_PATH.read_text(encoding="utf-8")
    total    = round(qtd * pm, 2)
    qtd_str  = str(int(qtd)) if qtd == int(qtd) else str(qtd)
    pm_ant_s = f"{pm_anterior:.2f}" if pm_anterior else "—"
    nova_linha = (
        f"| {data} | {ticker} | {tipo} | COMPRA | {qtd_str} | "
        f"{pm:.2f} | {total:,.2f} | {pm_ant_s} | {pl_antes} |"
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


# ── Nota do ativo ──────────────────────────────────────────────────────────────

def criar_nota_ativo(ticker: str, tipo: str, setor: str, data_entrada: str,
                     nome: str | None = None, indexador: str | None = None,
                     taxa: str | None = None, vencimento: str | None = None):
    pasta = ATIVOS_DIR / ticker
    pasta.mkdir(parents=True, exist_ok=True)
    tese_path = pasta / "tese.md"
    if tese_path.exists():
        print(f"  Nota {tese_path} já existe — não sobrescrevendo.")
        return

    eh_rf = tipo in TIPOS_OFF_EXCHANGE
    titulo = nome if nome else ticker

    # Frontmatter extra para RF/TD/DEB/CRI-CRA
    extra_front = ""
    if eh_rf:
        if indexador:
            extra_front += f"indexador: {indexador}\n"
        if taxa:
            extra_front += f"taxa: \"{taxa}\"\n"
        if vencimento:
            extra_front += f"vencimento: {vencimento}\n"
        extra_front += f"emissor: {setor}\n"

    # Descrição legível para RF
    descricao_rf = ""
    if eh_rf:
        partes = []
        if indexador and taxa:
            partes.append(f"{indexador} {taxa}")
        elif indexador:
            partes.append(indexador)
        elif taxa:
            partes.append(taxa)
        if vencimento:
            partes.append(f"venc. {vencimento}")
        if partes:
            descricao_rf = f"\n**{' | '.join(partes)}**\n"

    if eh_rf:
        corpo = f"""> Ativo de renda fixa — sem pipeline de análise de ações.
{descricao_rf}
## Detalhes

| Campo      | Valor           |
|------------|-----------------|
| Emissor    | {setor}         |
| Indexador  | {indexador or '—'} |
| Taxa       | {taxa or '—'}   |
| Vencimento | {vencimento or '—'} |
| Entrada    | {data_entrada}  |

## Links
- [[carteira]] — posição atual
- [[ips]] — adequação ao perfil
"""
    else:
        corpo = f"""> Análise pendente. Execute `/analisar {ticker}` para gerar.

## Links
- [[carteira]] — posição atual
- [[ips]] — adequação ao perfil
"""

    conteudo = f"""---
tags: [ativo, {tipo}, {ticker.lower()}]
cssclasses: [node-{tipo}]
ticker: {ticker}
nome: "{titulo}"
tipo: {tipo}
setor: {setor}
data_entrada: {data_entrada}
{extra_front}status: {"ativo" if eh_rf else "aguardando-analise"}
---

# {titulo}

{corpo}"""
    tese_path.write_text(conteudo, encoding="utf-8")


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Adiciona ou incrementa ativo na carteira SBWAA")
    parser.add_argument("--ticker",      required=True)
    parser.add_argument("--tipo",        required=True, choices=list(TIPOS_VALIDOS.keys()))
    parser.add_argument("--quantidade",  required=True, type=float)
    parser.add_argument("--preco-medio", required=True, type=float, dest="preco_medio")
    parser.add_argument("--setor",       required=True,
                        help="Setor (ações/FIIs) ou Emissor (RF/TD/DEB/CRI-CRA: ex. XP, BTG, Nubank)")
    parser.add_argument("--skip-validacao", action="store_true",
                        help="Pular validação de ticker nas APIs (automático para RF/TD/DEB/CRI-CRA)")
    parser.add_argument("--data",        default=None,
                        help="Data de entrada YYYY-MM-DD (padrão: hoje)")
    # Flags exclusivas de renda fixa
    parser.add_argument("--nome",        default=None,
                        help="Nome do produto (ex: 'CDB XP 110%% CDI'). Opcional.")
    parser.add_argument("--indexador",   default=None, choices=INDEXADORES,
                        help="Indexador: CDI | IPCA | Selic | PRE | IGPM")
    parser.add_argument("--taxa",        default=None,
                        help="Taxa (ex: '110%%' para CDI, '+6%%' para IPCA, '13.5%%' para PRE)")
    parser.add_argument("--vencimento",  default=None,
                        help="Data de vencimento YYYY-MM-DD (ex: 2029-01-01)")
    args = parser.parse_args()

    ticker = args.ticker.upper()
    eh_rf  = args.tipo in TIPOS_OFF_EXCHANGE

    # Validação de data de entrada
    if args.data:
        try:
            datetime.strptime(args.data, "%Y-%m-%d")
            data_entrada = args.data
        except ValueError:
            print("Erro: --data deve estar no formato YYYY-MM-DD (ex: 2024-01-15)")
            sys.exit(1)
    else:
        data_entrada = datetime.now().strftime("%Y-%m-%d")

    # Validação de vencimento
    if args.vencimento:
        try:
            datetime.strptime(args.vencimento, "%Y-%m-%d")
        except ValueError:
            print("Erro: --vencimento deve estar no formato YYYY-MM-DD (ex: 2029-01-01)")
            sys.exit(1)

    # Aviso se flags de RF usadas em tipos de renda variável
    if not eh_rf and any([args.nome, args.indexador, args.taxa, args.vencimento]):
        print("Aviso: --nome/--indexador/--taxa/--vencimento são para RF/TD/DEB/CRI-CRA.")

    # Busca posição existente
    posicao_atual = buscar_posicao(ticker)

    # Cotação — RF não tem cotação em bolsa: usa preco_medio como valor atual
    preco_atual = None
    if eh_rf or args.skip_validacao:
        if eh_rf:
            print(f"  Tipo {args.tipo} — off-exchange, validacao de API pulada.")
        preco_atual = args.preco_medio  # valor de face = custo de aquisição
    else:
        valido, preco_atual = validar_ticker(ticker, args.tipo)
        if not valido:
            print(f"Erro: ticker {ticker} não encontrado na Brapi nem no Yahoo Finance.")
            print("Use --skip-validacao para adicionar mesmo assim.")
            sys.exit(1)
        print(f"  Ticker {ticker} validado.  Cotação atual: R$ {preco_atual:.2f}" if preco_atual else f"  Ticker {ticker} validado.")

    if posicao_atual:
        # ── Compra adicional / aporte em RF ──────────────────────────────────
        qtd_ant = posicao_atual["qtd"]
        pm_ant  = posicao_atual["pm"]

        pl_antes_str = "—"
        if preco_atual and pm_ant > 0 and not eh_rf:
            pl_pct       = (preco_atual - pm_ant) / pm_ant * 100
            pl_rs        = round((preco_atual - pm_ant) * qtd_ant, 2)
            pl_antes_str = f"{pl_pct:+.1f}%"

        nova_qtd = qtd_ant + args.quantidade
        novo_pm  = (qtd_ant * pm_ant + args.quantidade * args.preco_medio) / nova_qtd

        label_qtd = "unidades" if eh_rf else "ações"
        print(f"\n  [{'APORTE' if eh_rf else 'COMPRA ADICIONAL'}] {ticker}")
        print(f"  {'─'*48}")
        print(f"  Posição anterior : {int(qtd_ant) if qtd_ant == int(qtd_ant) else qtd_ant} {label_qtd} @ P.M. R$ {pm_ant:.2f}")
        if preco_atual and not eh_rf:
            pl_pct_disp = (preco_atual - pm_ant) / pm_ant * 100
            pl_rs_disp  = round((preco_atual - pm_ant) * qtd_ant, 2)
            print(f"  Cotação atual    : R$ {preco_atual:.2f}  ->  P&L antes: {pl_pct_disp:+.1f}%  (R$ {pl_rs_disp:+,.2f})")
        print(f"  Este aporte      : {int(args.quantidade) if args.quantidade == int(args.quantidade) else args.quantidade} {label_qtd} @ R$ {args.preco_medio:.2f}")
        print(f"  {'─'*48}")
        print(f"  Novo P. Médio    : R$ {novo_pm:.2f}")
        print(f"  Nova quantidade  : {int(nova_qtd) if nova_qtd == int(nova_qtd) else nova_qtd} {label_qtd}")

        atualizar_posicao(ticker, nova_qtd, novo_pm)
        adicionar_historico(ticker, args.tipo, args.quantidade, args.preco_medio,
                            data_entrada, pm_ant, pl_antes_str)
        print(f"\n[OK] Posição de {ticker} atualizada.")

    else:
        # ── Primeira entrada ──────────────────────────────────────────────────
        label_qtd = "unidades" if eh_rf else "ações"
        nome_display = args.nome or ticker
        print(f"\n  [NOVA POSIÇÃO] {nome_display}")

        # Para RF: mostrar resumo do produto
        if eh_rf:
            partes = []
            if args.indexador and args.taxa:
                partes.append(f"{args.indexador} {args.taxa}")
            elif args.indexador:
                partes.append(args.indexador)
            elif args.taxa:
                partes.append(args.taxa)
            if args.vencimento:
                partes.append(f"venc. {args.vencimento}")
            if partes:
                print(f"  {' | '.join(partes)}")
            print(f"  Emissor: {args.setor}")

        inserir_linha_carteira(ticker, args.tipo, args.setor,
                               args.quantidade, args.preco_medio)
        adicionar_historico(ticker, args.tipo, args.quantidade, args.preco_medio,
                            data_entrada, None, "—")
        criar_nota_ativo(ticker, args.tipo, args.setor, data_entrada,
                         nome=args.nome, indexador=args.indexador,
                         taxa=args.taxa, vencimento=args.vencimento)
        print(f"\n[OK] {nome_display} adicionado. Pasta: vault/01-ativos/{ticker}/")


if __name__ == "__main__":
    main()
