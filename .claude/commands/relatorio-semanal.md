---
description: Relatório semanal de performance — P&L, métricas e outlook
---

# /relatorio-semanal

## Passo 1 — Coletar dados

```powershell
$env:PYTHONUTF8 = "1"; cd "C:\Users\lbmma\Downloads\Local\SBWAA"
python scripts/data/update_carteira.py
python .claude/agents/quant-data-engineer/run_quant.py
python .claude/agents/risk-engineer/run_risk_engineer.py
```

Leia:
- `vault/00-portfolio/carteira.md`
- `scripts/data/cache/quant_*.json` (mais recente)
- `scripts/data/cache/risk_*.json` (mais recente)
- `vault/02-relatorios/diarios/` — notes da semana (últimos 5 dias úteis)

## Passo 2 — Relatório

Leia `.claude/agents/portfolio-manager/SKILL.md`.

Gere o relatório semanal com:

**Sumário da Semana**
- Performance da carteira vs IBOV na semana
- Retorno absoluto estimado (normalizado R$ 100k — privacidade)

**Performance por Ativo**
Tabela: Ticker | Retorno 1S | Contribuição | Destaque

**Top 3 Melhores / Piores**
- 3 ativos que mais contribuíram positivamente
- 3 ativos que mais pesaram (se carteira tiver ≥ 3)

**Métricas HF da Semana**
- Sharpe, volatilidade, drawdown máximo, VaR atual
- Circuit breakers: todos OK?

**Dividendos Recebidos**
Se houver registro em `vault/00-portfolio/historico-trades.md`

**Outlook Próxima Semana**
- 2-3 eventos/dados a acompanhar
- Algum ativo da carteira com catalisador próximo?

## Passo 3 — Salvar

Salve em `vault/02-relatorios/semanais/semana-YYYY-WNN.md` com wikilinks para todos os ativos mencionados, `[[carteira]]` e `[[ips]]`.
