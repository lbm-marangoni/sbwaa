"""
rebalancear.py — PM analisa alocação atual vs IPS e sugere ajustes.
Uso: python sbwaa.py /rebalancear
"""

import re
import json
from datetime import datetime, timedelta
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
VAULT_ROOT = PROJECT_ROOT / "vault"
SCRIPTS_DATA = PROJECT_ROOT / "scripts" / "data"
CACHE_DIR = SCRIPTS_DATA / "cache"
CARTEIRA_PATH = VAULT_ROOT / "00-portfolio" / "carteira.md"
IPS_PATH = VAULT_ROOT / "00-portfolio" / "ips.md"


def carregar_json_cache(prefixo: str) -> dict | None:
    hoje = datetime.now().strftime("%Y-%m-%d")
    for d in range(4):
        dt = (datetime.strptime(hoje, "%Y-%m-%d") - timedelta(days=d)).strftime("%Y-%m-%d")
        path = CACHE_DIR / f"{prefixo}_{dt}.json"
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
    return None


def parse_carteira_publica() -> dict:
    """Tickers e tipos — sem valores absolutos."""
    if not CARTEIRA_PATH.exists():
        return {}
    conteudo = CARTEIRA_PATH.read_text(encoding="utf-8")
    resultado = {}
    dentro = False
    for linha in conteudo.splitlines():
        stripped = linha.strip()
        if stripped.startswith("| Ticker"):
            dentro = True
            continue
        if dentro and stripped.startswith("|---"):
            continue
        if dentro and stripped.startswith("|"):
            cols = [c.strip() for c in stripped.split("|")[1:-1]]
            if cols and cols[0] and cols[0] not in ("", "Ticker"):
                resultado[cols[0]] = cols[1] if len(cols) > 1 else ""
        elif dentro and not stripped.startswith("|"):
            break
    return resultado


def main():
    hoje = datetime.now().strftime("%Y-%m-%d")

    print(f"\n{'═'*55}")
    print(f"  SBWAA — Rebalanceamento | {hoje}")
    print(f"{'═'*55}\n")

    ips_txt = IPS_PATH.read_text(encoding="utf-8") if IPS_PATH.exists() else ""
    carteira = parse_carteira_publica()
    quant = carregar_json_cache("quant")
    risk = carregar_json_cache("risk")

    if not ips_txt:
        print("⚠️  IPS não preenchido. Execute /ips --editar para configurar.\n")
        return

    if not carteira:
        print("⚠️  Carteira vazia. Use /adicionar para incluir ativos.\n")
        return

    cart_txt = json.dumps(carteira, ensure_ascii=False)
    quant_txt = json.dumps(quant.get("carteira", {}), ensure_ascii=False) if quant else "Sem dados Quant."
    risk_txt = json.dumps({k: v for k, v in (risk or {}).items()
                           if k != "stress_tests"}, ensure_ascii=False) if risk else "Sem dados Risk."

    import anthropic
    client = anthropic.Anthropic()

    prompt = f"""DATA: {hoje}

IPS DO USUÁRIO:
{ips_txt[:800]}

CARTEIRA ATUAL (tickers e tipos — sem valores absolutos):
{cart_txt}

MÉTRICAS QUANTITATIVAS:
{quant_txt}

MÉTRICAS DE RISCO:
{risk_txt}

Você é o Portfolio Manager. Analise o desvio da carteira atual vs alocação alvo do IPS.

Gere um relatório de rebalanceamento com:
1. Desvios por classe de ativo (atual% vs alvo%)
2. Sugestão concreta: o que reduzir, o que aumentar, em que ordem
3. Impacto estimado no Sharpe e VaR após rebalanceamento
4. Prioridade (urgente / moderado / pode aguardar)

REGRAS:
- Tom: gestor sênior, direto, sem condescendência
- Se a carteira estiver dentro dos limites: dizer claramente
- Se houver violação: dizer o que viola e a consequência
- Sugestão = recomendação, não ordem. O usuário decide.
- NÃO usar "depende" sem especificar do quê
"""

    print("Gerando análise de rebalanceamento (claude-sonnet-4-6)...\n")
    print("─" * 55)

    import anthropic
    client = anthropic.Anthropic()
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

    # Salvar no vault
    portfolio_dir = VAULT_ROOT / "00-portfolio"
    out_path = portfolio_dir / f"rebalanceamento-{hoje}.md"
    md = f"""---
tags: [portfolio, rebalanceamento]
cssclasses: [node-portfolio]
data: {hoje}
agente: portfolio-manager
---

# Rebalanceamento — {hoje}

{output}

## Links
[[carteira]] | [[ips]] | [[risk-{hoje}]]
"""
    out_path.write_text(md, encoding="utf-8")
    print(f"  Salvo em: {out_path.relative_to(PROJECT_ROOT)}\n")


if __name__ == "__main__":
    main()
