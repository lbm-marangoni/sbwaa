"""
mundo_economico.py — Macro do dia focado em panorama econômico global.
Uso: python sbwaa.py /mundo-economico
"""

import sys
import subprocess
from datetime import datetime, timedelta
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
VAULT_ROOT = PROJECT_ROOT / "vault"
SCRIPTS_DATA = PROJECT_ROOT / "scripts" / "data"
AGENTS_DIR = PROJECT_ROOT / ".claude" / "agents"


def main():
    hoje = datetime.now().strftime("%Y-%m-%d")

    print(f"\n{'═'*55}")
    print(f"  SBWAA — Mundo Econômico | {hoje}")
    print(f"{'═'*55}\n")

    # Garantir snapshot atualizado
    print("[1/2] Atualizando snapshot de mercado...")
    subprocess.run([sys.executable, str(SCRIPTS_DATA / "market_snapshot.py")], text=True)

    # Market Researcher (usa cache se existir)
    mr_path = VAULT_ROOT / "03-macro" / f"market-researcher-{hoje}.md"
    if mr_path.exists():
        print("[2/2] Market Researcher (usando cache)...")
    else:
        print("[2/2] Market Researcher...")
        subprocess.run(
            [sys.executable, str(AGENTS_DIR / "market-researcher" / "run_market_researcher.py")],
            text=True,
        )

    if not mr_path.exists():
        print("\n⚠️  Market Researcher não gerou output. Verifique a API.\n")
        return

    conteudo = mr_path.read_text(encoding="utf-8")

    # Gerar nota focada em macro via Sonnet
    import anthropic
    client = anthropic.Anthropic()

    prompt = f"""Com base no relatório do Market Researcher abaixo, gere um panorama econômico global focado.
Formato obrigatório:

---
tags: [macro, mundo-economico]
cssclasses: [node-macro]
data: {hoje}
---

# Mundo Econômico — {hoje}

## 🌍 Panorama Global
{{3-4 temas macro mais relevantes do dia, com dados concretos}}

## 🇧🇷 Brasil
{{2-3 pontos específicos para o mercado BR}}

## 💱 Câmbio e Commodities
{{BRL/USD, Petróleo, Ouro — nível e tendência}}

## 📌 O que monitorar
{{Top 3 eventos ou dados a acompanhar nas próximas 48h}}

## Links
[[market-researcher-{hoje}]]

---
RELATÓRIO DO MARKET RESEARCHER:
{conteudo[:3000]}
"""

    print("\nGerando panorama econômico (claude-sonnet-4-6)...")
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1500,
        messages=[{"role": "user", "content": prompt}],
    )
    output_md = response.content[0].text

    # Salvar
    macro_dir = VAULT_ROOT / "03-macro"
    macro_dir.mkdir(parents=True, exist_ok=True)
    out_path = macro_dir / f"mundo-economico-{hoje}.md"
    out_path.write_text(output_md, encoding="utf-8")

    print(output_md)
    print(f"\n{'═'*55}")
    print(f"  Salvo em: {out_path.relative_to(PROJECT_ROOT)}")
    print(f"{'═'*55}\n")


if __name__ == "__main__":
    main()
