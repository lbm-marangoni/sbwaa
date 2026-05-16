---
description: Sugestão de 1-2 ativos para explorar análise hoje, com base no IPS e no cenário macro
---

# /investimento-do-dia

## Passo 1 — Coletar contexto

```powershell
$env:PYTHONUTF8 = "1"; cd "C:\Users\lbmma\Downloads\Local\SBWAA"
python scripts/data/fetch_yahoo.py --macro
```

Leia:
- Todos os `scripts/data/cache/yahoo_*.json` do dia
- `vault/00-portfolio/ips.md`
- `vault/00-portfolio/carteira.md`

## Passo 2 — Sugestão

Leia `.claude/agents/market-researcher/SKILL.md`.

Com base no cenário macro do dia e no perfil do IPS, sugira **1 ou 2 ativos** para explorar análise — não é recomendação de compra, é uma indicação de onde vale a pena gastar atenção hoje.

Para cada sugestão:
- **Ticker** e tipo (🟦 AÇÃO / 🟩 FII / 🟥 ETF INTL etc.)
- **Setor**
- **Por que hoje** — 2 linhas conectando o cenário macro à oportunidade
- **Pré-condição** — o que você precisaria ver nos dados para considerar a entrada

Termine com:
> Execute `/tese TICKER` para análise rápida ou `/analisar TICKER` para pipeline completo.

Não salva arquivo — resposta direta no chat.
