"""
vender_ativo.py — Registra venda (parcial ou total) de um ativo na carteira.
Uso: python vender_ativo.py --ticker PETR4 --quantidade 50 --preco 45.00
"""

import argparse
import sys
from datetime import datetime
from pathlib import Path

VAULT_ROOT     = Path(__file__).parent.parent.parent / "vault"
CARTEIRA_PATH  = VAULT_ROOT / "00-portfolio" / "carteira.md"
HISTORICO_PATH = VAULT_ROOT / "00-portfolio" / "historico-trades.md"

SCRIPTS_DIR = Path(__file__).parent
sys.path.insert(0, str(SCRIPTS_DIR))

HISTORICO_HEADER = "| Data | Ticker | Tipo | Operação | Qtd | Preço | Total R$ | PM ant. | P&L ant. |"
HISTORICO_SEP    = "|------|--------|------|----------|-----|-------|----------|---------|----------|"


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


def remover_linha_carteira(ticker: str):
    conteudo = CARTEIRA_PATH.read_text(encoding="utf-8")
    linhas   = conteudo.splitlines()
    novas    = []
    for linha in linhas:
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
            cols[3] = str(int(nova_qtd)) if nova_qtd == int(nova_qtd) else str(nova_qtd)
            cols[5] = cols[6] = cols[7] = cols[8] = cols[9] = ""
            linhas[i] = "| " + " | ".join(cols) + " |"
            break
    CARTEIRA_PATH.write_text("\n".join(linhas), encoding="utf-8")


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
    qtd_str    = str(int(qtd)) if qtd == int(qtd) else str(qtd)
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


def main():
    parser = argparse.ArgumentParser(description="Registra venda de ativo na carteira SBWAA")
    parser.add_argument("--ticker",     required=True)
    parser.add_argument("--quantidade", required=True, type=float)
    parser.add_argument("--preco",      required=True, type=float,
                        help="Preço de venda por ação/cota")
    parser.add_argument("--data",       default=None,
                        help="Data da venda YYYY-MM-DD (padrão: hoje)")
    args = parser.parse_args()

    ticker = args.ticker.upper()

    if args.data:
        try:
            datetime.strptime(args.data, "%Y-%m-%d")
            data_venda = args.data
        except ValueError:
            print("Erro: --data deve estar no formato YYYY-MM-DD (ex: 2024-01-15)")
            sys.exit(1)
    else:
        data_venda = datetime.now().strftime("%Y-%m-%d")

    posicao = buscar_posicao(ticker)
    if not posicao:
        print(f"Erro: {ticker} não encontrado na carteira.")
        sys.exit(1)

    qtd_atual = posicao["qtd"]
    pm        = posicao["pm"]
    tipo      = posicao["tipo"]

    if args.quantidade > qtd_atual:
        print(f"Erro: tentando vender {args.quantidade} mas posição é de apenas {qtd_atual}.")
        sys.exit(1)

    # Cálculos
    pl_rs_unit  = args.preco - pm
    pl_pct      = (args.preco - pm) / pm * 100 if pm else 0.0
    pl_rs_total = round(pl_rs_unit * args.quantidade, 2)
    receita     = round(args.quantidade * args.preco, 2)
    qtd_restante = qtd_atual - args.quantidade

    print(f"\n  [VENDA] {ticker}")
    print(f"  {'─'*48}")
    print(f"  Posição atual    : {int(qtd_atual) if qtd_atual == int(qtd_atual) else qtd_atual} ações @ P.M. R$ {pm:.2f}")
    print(f"  Vendendo         : {int(args.quantidade) if args.quantidade == int(args.quantidade) else args.quantidade} ações @ R$ {args.preco:.2f}")
    print(f"  Receita bruta    : R$ {receita:,.2f}")
    print(f"  P&L realizado    : R$ {pl_rs_total:+,.2f}  ({pl_pct:+.1f}%)")
    print(f"  {'─'*48}")

    pl_realizado_str = f"{pl_pct:+.1f}%"
    adicionar_historico_venda(ticker, tipo, args.quantidade, args.preco,
                              data_venda, pm, pl_realizado_str)

    if qtd_restante <= 0:
        remover_linha_carteira(ticker)
        print(f"  Posição zerada   : {ticker} removido da carteira.")
    else:
        atualizar_qtd_carteira(ticker, qtd_restante)
        print(f"  Posição restante : {int(qtd_restante) if qtd_restante == int(qtd_restante) else qtd_restante} ações @ P.M. R$ {pm:.2f}")
        print(f"  (P.M. inalterado — custo das ações restantes não muda com a venda)")

    print(f"\n[OK] Venda de {ticker} registrada em {data_venda}.")


if __name__ == "__main__":
    main()
