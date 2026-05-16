"""
comparar.py — Análise comparativa entre dois ativos.
Uso: python sbwaa.py /comparar PETR4 VALE3
"""

import sys
import json
import argparse
from datetime import datetime, timedelta
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
VAULT_ROOT = PROJECT_ROOT / "vault"
SCRIPTS_DATA = PROJECT_ROOT / "scripts" / "data"
CACHE_DIR = SCRIPTS_DATA / "cache"


def carregar_dcf(ticker: str) -> dict | None:
    hoje = datetime.now().strftime("%Y-%m-%d")
    for d in range(8):
        dt = (datetime.strptime(hoje, "%Y-%m-%d") - timedelta(days=d)).strftime("%Y-%m-%d")
        path = CACHE_DIR / f"dcf_{ticker}_{dt}.json"
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
    return None


def carregar_valuation(ticker: str) -> str:
    hoje = datetime.now().strftime("%Y-%m-%d")
    ativo_dir = VAULT_ROOT / "01-ativos" / ticker
    if not ativo_dir.exists():
        return ""
    for versao in ["longa", "curta"]:
        for d in range(8):
            dt = (datetime.strptime(hoje, "%Y-%m-%d") - timedelta(days=d)).strftime("%Y-%m-%d")
            path = ativo_dir / f"equity-research-{ticker}-{dt}-{versao}.md"
            if path.exists():
                return path.read_text(encoding="utf-8")[:2000]
    return ""


def resumir_ativo(ticker: str) -> str:
    dcf = carregar_dcf(ticker)
    val = carregar_valuation(ticker)

    resumo = f"=== {ticker} ===\n"

    if dcf:
        cen = dcf.get("cenarios", {})
        base = cen.get("base", {})
        pess = cen.get("pessimista", {})
        resumo += (
            f"Preço atual: R$ {dcf.get('preco_atual', 'N/D')}\n"
            f"Valor justo (base): R$ {base.get('valor_justo', 'N/D')} | Upside: {base.get('upside_pct', 'N/D')}%\n"
            f"Upside pessimista: {pess.get('upside_pct', 'N/D')}%\n"
            f"WACC: {dcf.get('wacc_base', 'N/D')}\n"
        )
    else:
        resumo += "DCF: não disponível (execute /analisar primeiro)\n"

    if val:
        resumo += f"Valuation:\n{val[:800]}\n"
    else:
        resumo += "Valuation: não disponível\n"

    return resumo


def main():
    parser = argparse.ArgumentParser(description="/comparar — SBWAA")
    parser.add_argument("ticker1")
    parser.add_argument("ticker2")
    args = parser.parse_args()

    t1 = args.ticker1.upper()
    t2 = args.ticker2.upper()
    hoje = datetime.now().strftime("%Y-%m-%d")

    print(f"\n{'═'*55}")
    print(f"  SBWAA — Comparar {t1} vs {t2} | {hoje}")
    print(f"{'═'*55}\n")

    dados_t1 = resumir_ativo(t1)
    dados_t2 = resumir_ativo(t2)

    if "não disponível" in dados_t1 and "não disponível" in dados_t2:
        print(f"⚠️  Sem dados para análise.")
        print(f"   Execute /analisar {t1} e /analisar {t2} antes de comparar.\n")
        return

    import anthropic
    client = anthropic.Anthropic()

    prompt = f"""DATA: {hoje}

Compare os dois ativos abaixo. Seja direto e use dados concretos.

{dados_t1}

{dados_t2}

Gere uma comparação estruturada:

## {t1} vs {t2} — Comparação | {hoje}

### Valuation
{{compare upside, valor justo, confiança}}

### Qualidade do Negócio
{{compare com base nos dados disponíveis}}

### Risco
{{compare WACC, sensibilidade, setor}}

### Veredicto Comparativo
{{qual prefere hoje e por quê — com dados}}

Links: [[pm-decisao-{hoje}]] (se existir)
"""

    print("Gerando comparação (claude-sonnet-4-6)...\n")
    print("─" * 55)
    output = ""
    with client.messages.stream(
        model="claude-sonnet-4-6",
        max_tokens=1500,
        messages=[{"role": "user", "content": prompt}],
    ) as stream:
        for text in stream.text_stream:
            print(text, end="", flush=True)
            output += text
    print(f"\n{'─'*55}\n")

    # Salvar
    comp_dir = VAULT_ROOT / "02-relatorios"
    comp_dir.mkdir(parents=True, exist_ok=True)
    out_path = comp_dir / f"comparar-{t1}-{t2}-{hoje}.md"
    md = f"""---
tags: [relatorio, comparacao, {t1.lower()}, {t2.lower()}]
cssclasses: [node-relatorio]
data: {hoje}
---

{output}

## Links
[[{t1.lower()}]] | [[{t2.lower()}]]
"""
    out_path.write_text(md, encoding="utf-8")
    print(f"  Salvo em: {out_path.relative_to(PROJECT_ROOT)}\n")


if __name__ == "__main__":
    main()
