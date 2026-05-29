"""
extract_targets.py — Extrai preços-alvo de vault/01-ativos/ e popula alertas.json.
Chamado automaticamente após /analisar, /tese e /pm.

Uso:
    python scripts/alerts/extract_targets.py --ticker PETR4
    python scripts/alerts/extract_targets.py --todos
"""

import re
import sys
import json
import argparse
from datetime import date
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
VAULT_ATIVOS = PROJECT_ROOT / "vault" / "01-ativos"
ALERTAS_JSON = PROJECT_ROOT / "vault" / "00-portfolio" / "alertas.json"

# (regex, tipo, direcao, descricao)
# Mais específicos primeiro para evitar captura errada
PADROES = [
    (r"\*\*Preço teto \([^)]+\):\*\*\s*R\$\s*([\d,.]+)",     "teto",          "acima",  "Preço teto — revisar posição"),
    (r"\*\*Preço[ -]teto:\*\*\s*R\$\s*([\d,.]+)",             "teto",          "acima",  "Preço teto — revisar posição"),
    (r"\*\*Preço[ -]alvo:\*\*\s*R\$\s*([\d,.]+)",             "alvo",          "acima",  "Preço-alvo atingido"),
    (r"\*\*Valor justo \(base\):\*\*\s*R\$\s*([\d,.]+)",      "valor_justo",   "acima",  "Valor justo atingido — avaliar saída"),
    (r"\*\*Preço chão \([^)]+\):\*\*\s*R\$\s*([\d,.]+)",      "chao",          "abaixo", "Preço chão — zona de compra"),
    (r"\*\*Nível de entrada:\*\*\s*R\$\s*([\d,.]+)",          "entrada",       "abaixo", "Nível de entrada — avaliar compra"),
    (r"\*\*Stop:\*\*\s*R\$\s*([\d,.]+)",                      "stop",          "abaixo", "Stop atingido — revisar tese"),
    (r"\*\*Valor justo \(pessimista\):\*\*\s*R\$\s*([\d,.]+)", "pessimista",   "abaixo", "Downside pessimista atingido"),
]

FM_PRECO_ALVO = re.compile(r"^preco-alvo:\s*([\d,.]+)", re.MULTILINE)


def _parse_preco(s: str) -> float | None:
    try:
        return float(s.strip().replace(".", "").replace(",", "."))
    except (ValueError, AttributeError):
        return None


def extrair_precos_arquivo(path: Path) -> list[dict]:
    texto = path.read_text(encoding="utf-8")
    resultado = []
    vistos = set()

    m = FM_PRECO_ALVO.search(texto)
    if m:
        preco = _parse_preco(m.group(1))
        if preco and preco > 0:
            resultado.append({"tipo": "alvo", "preco": preco, "direcao": "acima", "descricao": "Preço-alvo atingido"})
            vistos.add("alvo")

    for pattern, tipo, direcao, descricao in PADROES:
        if tipo in vistos:
            continue
        m = re.search(pattern, texto)
        if m:
            preco = _parse_preco(m.group(1))
            if preco and preco > 0:
                resultado.append({"tipo": tipo, "preco": preco, "direcao": direcao, "descricao": descricao})
                vistos.add(tipo)

    return resultado


def arquivos_ticker(ticker: str) -> list[Path]:
    pasta = VAULT_ATIVOS / ticker
    if not pasta.exists():
        return []
    ordem_prefixos = ["analise-", "pm-decisao-", "tese-rapida-", "tese-"]
    arquivos: list[Path] = []
    vistos: set[Path] = set()
    for prefixo in ordem_prefixos:
        for f in sorted(pasta.glob(f"{prefixo}*.md"), key=lambda x: x.stem, reverse=True):
            if f not in vistos:
                arquivos.append(f)
                vistos.add(f)
    for f in sorted(pasta.glob("*.md"), key=lambda x: x.stem, reverse=True):
        if f not in vistos:
            arquivos.append(f)
    return arquivos


def registrar_alertas(ticker: str, novos: list[dict]):
    dados: dict = {"alertas": []}
    if ALERTAS_JSON.exists():
        try:
            dados = json.loads(ALERTAS_JSON.read_text(encoding="utf-8"))
        except Exception:
            dados = {"alertas": []}

    dados["alertas"] = [a for a in dados.get("alertas", []) if a.get("ticker") != ticker]

    hoje = date.today().isoformat()
    for a in novos:
        dados["alertas"].append({
            "id":             f"{ticker}-{a['tipo']}-{hoje}",
            "ticker":         ticker,
            "tipo":           a["tipo"],
            "preco":          a["preco"],
            "direcao":        a["direcao"],
            "descricao":      a["descricao"],
            "acao_sugerida":  f"/pm {ticker}",
            "fonte":          a.get("fonte", "?"),
            "data_criacao":   hoje,
        })

    ALERTAS_JSON.parent.mkdir(parents=True, exist_ok=True)
    ALERTAS_JSON.write_text(json.dumps(dados, ensure_ascii=False, indent=2), encoding="utf-8")


def processar_ticker(ticker: str) -> list[dict]:
    ticker = ticker.upper()
    arquivos = arquivos_ticker(ticker)
    if not arquivos:
        print(f"  [{ticker}] Nenhum arquivo de análise encontrado em vault/01-ativos/{ticker}/.")
        return []

    todos: list[dict] = []
    tipos_vistos: set[str] = set()
    for arq in arquivos:
        try:
            for p in extrair_precos_arquivo(arq):
                if p["tipo"] not in tipos_vistos:
                    p["fonte"] = arq.name
                    todos.append(p)
                    tipos_vistos.add(p["tipo"])
        except Exception as e:
            print(f"  [{ticker}] Erro ao ler {arq.name}: {e}")

    if not todos:
        print(f"  [{ticker}] Nenhum preço-alvo encontrado.")
        return []

    registrar_alertas(ticker, todos)
    print(f"  [{ticker}] {len(todos)} alerta(s) registrado(s):")
    for a in todos:
        sinal = "↑" if a["direcao"] == "acima" else "↓"
        print(f"    {sinal} {a['tipo']:<14}  R$ {a['preco']:.2f}  ← {a.get('fonte', '?')}")
    return todos


def processar_todos():
    if not VAULT_ATIVOS.exists():
        print("vault/01-ativos/ não encontrado.")
        return
    tickers = sorted(p.name for p in VAULT_ATIVOS.iterdir() if p.is_dir())
    if not tickers:
        print("Nenhum ativo em vault/01-ativos/.")
        return
    print(f"Processando {len(tickers)} ticker(s)...\n")
    total = sum(len(processar_ticker(t)) for t in tickers)
    print(f"\nTotal: {total} alerta(s) em {ALERTAS_JSON}")


def main():
    parser = argparse.ArgumentParser(description="Extrai preços-alvo de análises para alertas.json")
    grp = parser.add_mutually_exclusive_group(required=True)
    grp.add_argument("--ticker", metavar="TICKER", help="Ticker específico")
    grp.add_argument("--todos", action="store_true", help="Todos os tickers em vault/01-ativos/")
    args = parser.parse_args()
    if args.todos:
        processar_todos()
    else:
        processar_ticker(args.ticker)


if __name__ == "__main__":
    main()
