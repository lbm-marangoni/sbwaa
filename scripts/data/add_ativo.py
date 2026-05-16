"""
add_ativo.py — Adiciona um ativo à carteira e cria estrutura no vault.
Uso: python add_ativo.py --ticker PETR4 --tipo acao-pn --quantidade 100 --preco-medio 36.00 --setor energia
"""

import argparse
import sys
import time
from datetime import datetime
from pathlib import Path

VAULT_ROOT = Path(__file__).parent.parent.parent / "vault"
CARTEIRA_PATH = VAULT_ROOT / "00-portfolio" / "carteira.md"
HISTORICO_PATH = VAULT_ROOT / "00-portfolio" / "historico-trades.md"
ATIVOS_DIR = VAULT_ROOT / "01-ativos"

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


def validar_ticker_brapi(ticker: str) -> bool:
    try:
        from fetch_brapi import buscar_ticker
        dados = buscar_ticker(ticker)
        return dados.get("cotacao") is not None
    except BaseException:
        return False


def validar_ticker_yahoo(ticker: str) -> bool:
    try:
        from fetch_yahoo import buscar_ticker
        dados = buscar_ticker(ticker)
        return dados.get("cotacao_atual") is not None
    except BaseException:
        return False


def validar_ticker(ticker: str, tipo: str) -> bool:
    print(f"  Validando {ticker} nas APIs...")
    if tipo in ("etf-intl",):
        return validar_ticker_yahoo(ticker)
    # Tenta Brapi primeiro, fallback Yahoo
    if validar_ticker_brapi(ticker):
        return True
    time.sleep(0.5)
    return validar_ticker_yahoo(ticker + ".SA") or validar_ticker_yahoo(ticker)


def adicionar_linha_carteira(ticker: str, tipo: str, setor: str, qtd: float, pm: float):
    conteudo = CARTEIRA_PATH.read_text(encoding="utf-8")
    label = TIPOS_VALIDOS.get(tipo, tipo)
    qtd_str = str(int(qtd)) if qtd == int(qtd) else str(qtd)
    nova_linha = f"| {ticker} | {label} | {setor.capitalize()} | {qtd_str} | {pm:.2f} |  |  |  |  |"
    # inserir antes da linha de resumo ou no fim da tabela
    linhas = conteudo.splitlines()
    idx_inserir = None
    for i, l in enumerate(linhas):
        if l.strip().startswith("|---") and "Ticker" in linhas[i - 1] if i > 0 else False:
            idx_inserir = i + 1
    if idx_inserir is None:
        # Procura o separador da tabela
        for i, l in enumerate(linhas):
            if "|-----" in l:
                idx_inserir = i + 1
                break
    if idx_inserir is None:
        conteudo += f"\n{nova_linha}"
    else:
        # Avança até o fim da tabela
        j = idx_inserir
        while j < len(linhas) and linhas[j].strip().startswith("|"):
            j += 1
        linhas.insert(j, nova_linha)
        conteudo = "\n".join(linhas)
    CARTEIRA_PATH.write_text(conteudo, encoding="utf-8")


def adicionar_historico(ticker: str, tipo: str, qtd: float, pm: float):
    conteudo = HISTORICO_PATH.read_text(encoding="utf-8")
    hoje = datetime.now().strftime("%Y-%m-%d")
    total = round(qtd * pm, 2)
    qtd_str = str(int(qtd)) if qtd == int(qtd) else str(qtd)
    nova_linha = f"| {hoje} | {ticker} | {tipo} | COMPRA | {qtd_str} | {pm:.2f} | {total:,.2f} |"
    linhas = conteudo.splitlines()
    j = len(linhas)
    for i, l in enumerate(linhas):
        if "|-----" in l:
            j = i + 1
            while j < len(linhas) and linhas[j].strip().startswith("|"):
                j += 1
            break
    linhas.insert(j, nova_linha)
    HISTORICO_PATH.write_text("\n".join(linhas), encoding="utf-8")


def criar_nota_ativo(ticker: str, tipo: str, setor: str):
    pasta = ATIVOS_DIR / ticker
    pasta.mkdir(parents=True, exist_ok=True)
    tese_path = pasta / "tese.md"
    if tese_path.exists():
        print(f"  Nota {tese_path} já existe — não sobrescrevendo.")
        return
    conteudo = f"""---
tags: [ativo, {tipo}, {ticker.lower()}]
cssclasses: [node-{tipo}]
ticker: {ticker}
tipo: {tipo}
setor: {setor}
status: aguardando-analise
---

# {ticker} — Tese de Investimento

> Análise pendente. Execute `/analisar {ticker}` para gerar.

## Links
- [[carteira]] — posição atual
- [[ips]] — adequação ao perfil
"""
    tese_path.write_text(conteudo, encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="Adiciona ativo à carteira SBWAA")
    parser.add_argument("--ticker", required=True)
    parser.add_argument("--tipo", required=True, choices=list(TIPOS_VALIDOS.keys()))
    parser.add_argument("--quantidade", required=True, type=float)
    parser.add_argument("--preco-medio", required=True, type=float, dest="preco_medio")
    parser.add_argument("--setor", required=True)
    parser.add_argument("--skip-validacao", action="store_true", help="Pular validação de ticker nas APIs")
    args = parser.parse_args()

    ticker = args.ticker.upper()

    if not args.skip_validacao:
        if not validar_ticker(ticker, args.tipo):
            print(f"Erro: ticker {ticker} não encontrado na Brapi nem no Yahoo Finance.")
            print("Use --skip-validacao para adicionar mesmo assim.")
            sys.exit(1)
        print(f"  Ticker {ticker} validado.")

    adicionar_linha_carteira(ticker, args.tipo, args.setor, args.quantidade, args.preco_medio)
    adicionar_historico(ticker, args.tipo, args.quantidade, args.preco_medio)
    criar_nota_ativo(ticker, args.tipo, args.setor)

    print(f"\n[OK] {ticker} adicionado a carteira. Pasta criada em vault/01-ativos/{ticker}/")


if __name__ == "__main__":
    main()
