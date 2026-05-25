---
description: Análise comparativa lado a lado de dois ativos
---

# /comparar $ARGUMENTS

Compare os dois ativos informados. Formato esperado: `/comparar PETR4 VALE3`

Extraia os dois tickers de $ARGUMENTS (primeiro e segundo).

## Passo 1 — Coletar dados dos dois ativos

```powershell
$env:PYTHONUTF8 = "1"; cd "C:\Users\lbmma\Downloads\Local\SBWAA"
python scripts/data/fetch_fundamentals.py TICKER1 TICKER2
python scripts/data/fetch_yahoo.py --macro
```

Leia os dois arquivos de cache `scripts/data/cache/fundamentals_TICKER*_*.json`.
Se algum tiver nota de análise prévia em `vault/01-ativos/TICKER/`, leia também.

## Passo 2 — Comparação

Leia `.claude/agents/valuation-reviewer/SKILL.md` e `.claude/agents/portfolio-manager/SKILL.md`.

Produza uma tabela comparativa com:

| Critério | TICKER1 | TICKER2 |
|---|---|---|
| Tipo / Setor | | |
| Cotação atual | | |
| P/L | | |
| P/VP | | |
| DY (%) | | |
| Dívida líq./EBITDA | | |
| ROE (%) | | |
| Crescimento receita | | |
| Upside estimado | | |
| Risco principal | | |

**Análise qualitativa:**
- Qual tem melhor qualidade de resultados e por quê
- Qual está mais barato no momento e por quê
- Correlação entre os dois: diversificam ou concentram?

**Veredicto comparativo:**
Leia `vault/00-portfolio/carteira.md` e `vault/00-portfolio/ips.md`.
Qual dos dois se encaixa melhor na carteira atual e no IPS? Por quê?

## Passo 3 — Salvar

Salve em `vault/01-ativos/comparacoes/comparar-TICKER1-TICKER2-YYYY-MM-DD.md` com wikilinks para ambos os ativos.
