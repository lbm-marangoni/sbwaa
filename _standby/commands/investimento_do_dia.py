"""
investimento_do_dia.py — Identifica oportunidades compatíveis com o IPS do usuário.
Uso: python sbwaa.py /investimento-do-dia
"""

import re
import json
import sys
import subprocess
from datetime import datetime, timedelta
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
VAULT_ROOT = PROJECT_ROOT / "vault"
SCRIPTS_DATA = PROJECT_ROOT / "scripts" / "data"
AGENTS_DIR = PROJECT_ROOT / ".claude" / "agents"
CACHE_DIR = SCRIPTS_DATA / "cache"
IPS_PATH = VAULT_ROOT / "00-portfolio" / "ips.md"
CARTEIRA_PATH = VAULT_ROOT / "00-portfolio" / "carteira.md"


def carregar_pesos_publicos() -> dict:
    """Lê carteira — retorna apenas tickers e pesos (seguro para API)."""
    if not CARTEIRA_PATH.exists():
        return {}
    conteudo = CARTEIRA_PATH.read_text(encoding="utf-8")
    tickers = []
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
                tickers.append(cols[0])
        elif dentro and not stripped.startswith("|"):
            break
    return {t: "na carteira" for t in tickers}


def main():
    hoje = datetime.now().strftime("%Y-%m-%d")

    print(f"\n{'═'*55}")
    print(f"  SBWAA — Investimento do Dia | {hoje}")
    print(f"{'═'*55}\n")

    # Garantir dados macro do dia
    mr_path = VAULT_ROOT / "03-macro" / f"market-researcher-{hoje}.md"
    if not mr_path.exists():
        print("Atualizando dados de mercado...")
        subprocess.run([sys.executable, str(SCRIPTS_DATA / "market_snapshot.py")], text=True)
        subprocess.run(
            [sys.executable, str(AGENTS_DIR / "market-researcher" / "run_market_researcher.py")],
            text=True,
        )

    ips_txt = IPS_PATH.read_text(encoding="utf-8")[:800] if IPS_PATH.exists() else "IPS não preenchido."
    mr_txt = mr_path.read_text(encoding="utf-8")[:2000] if mr_path.exists() else "Dados macro indisponíveis."
    carteira_atual = carregar_pesos_publicos()
    carteira_txt = json.dumps(carteira_atual, ensure_ascii=False) if carteira_atual else "Carteira vazia."

    import anthropic
    client = anthropic.Anthropic()

    prompt = f"""DATA: {hoje}

IPS DO USUÁRIO:
{ips_txt}

CARTEIRA ATUAL (tickers):
{carteira_txt}

CONTEXTO MACRO DO DIA:
{mr_txt}

Com base no perfil IPS, na composição atual da carteira e no cenário macro, identifique 1 ou 2 ativos
do mercado brasileiro que merecem atenção HOJE como ponto de partida para análise.

REGRAS:
- Sugerir apenas ativos compatíveis com o perfil de risco do IPS
- Priorizar classes com underweight vs alocação alvo do IPS
- Cruzar com setores favorecidos pelo macro do dia
- NÃO é recomendação de compra — é sugestão para /analisar
- Tom: direto, sem hype, com contexto concreto

FORMATO:
═══════════════════════════════════════════════
SBWAA — Investimento do Dia | {hoje}
═══════════════════════════════════════════════

Com base no seu IPS e no cenário de hoje:

🎯 EXPLORAR: {{TICKER1}}
   Tipo: {{tipo}} | Setor: {{setor}}
   Por quê hoje: {{1-2 linhas de contexto com dados}}
   → Execute: python sbwaa.py /analisar {{TICKER1}}

🎯 EXPLORAR: {{TICKER2}} (se houver)
   ...

⚠️  Esta sugestão é ponto de partida para análise,
    não recomendação de compra. Use /analisar para
    a análise completa antes de qualquer decisão.
═══════════════════════════════════════════════
"""

    print("Gerando sugestão (claude-sonnet-4-6)...")
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=800,
        messages=[{"role": "user", "content": prompt}],
    )
    output = response.content[0].text

    print(f"\n{output}\n")

    # Salvar no vault
    diario_dir = VAULT_ROOT / "02-relatorios" / "diarios"
    diario_dir.mkdir(parents=True, exist_ok=True)
    out_path = diario_dir / f"investimento-do-dia-{hoje}.md"
    md = f"""---
tags: [diario, investimento-do-dia]
cssclasses: [node-diario]
data: {hoje}
---

{output}

## Links
[[market-researcher-{hoje}]] | [[carteira]] | [[ips]]
"""
    out_path.write_text(md, encoding="utf-8")
    print(f"  Salvo em: {out_path.relative_to(PROJECT_ROOT)}\n")


if __name__ == "__main__":
    main()
