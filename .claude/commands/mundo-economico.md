---
description: Análise macro do dia — cenário global e impacto no Brasil
---

# /mundo-economico

## Passo 1 — Coletar dados

```powershell
$env:PYTHONUTF8 = "1"; cd "C:\Users\lbmma\Downloads\Local\SBWAA"
python scripts/data/fetch_yahoo.py --macro
python scripts/data/market_snapshot.py
```

Leia todos os `scripts/data/cache/yahoo_*.json` do dia.

## Passo 2 — Análise

Leia `.claude/agents/market-researcher/SKILL.md` e produza:

**Mercados Globais** — tabela com variações do dia: IBOV, S&P500, Nasdaq, DXY, BRL/USD, petróleo, ouro, juros EUA 10Y.

**Narrativa Macro** — 3-4 parágrafos curtos:
1. O que está movendo os mercados hoje
2. Posição do Brasil no contexto global
3. Commodities e câmbio: implicações para empresas brasileiras
4. O que acompanhar nas próximas 24-48h

**Termômetro de Risco**
- Risk-on ou Risk-off? Justificar em 1 frase.
- Impacto nos setores da carteira (`vault/00-portfolio/carteira.md`)

Salve em `vault/03-macro/mundo-economico-YYYY-MM-DD.md` com wikilinks.
