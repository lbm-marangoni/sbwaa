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

Salve em `vault/02-relatorios/semanais/semana-YYYY-WNN.md` com:
- Frontmatter: `tags: [relatorio, semanal]`, `data:`, `semana:` (ex: 2026-W22)
- Todo o conteúdo gerado acima
- Wikilinks para todos os ativos mencionados, `[[carteira]]` e `[[ips]]`

## Passo 4 — Risk Snapshot semanal

Com base nos dados de `scripts/data/cache/risk_*.json` (mais recente), salve em `vault/05-risk/snapshots/risk-YYYY-MM-DD.md`:

```yaml
---
tags: [risk, snapshot]
data: YYYY-MM-DD
semana: YYYY-WNN
---
```

| Métrica | Valor | Limite IPS | Status |
|---------|-------|------------|--------|
| VaR 95% (histórico) | X% | 2% | ✅/⚠️ |
| VaR 95% (paramétrico) | X% | 2% | ✅/⚠️ |
| CVaR 95% | X% | — | — |
| Drawdown atual | X% | 18% | ✅/⚠️ |
| Volatilidade anualizada | X% | — | — |
| Sharpe | X | — | — |
| Concentração máxima | X% | 20% | ✅/⚠️ |

**Circuit breakers:** todos OK? Se não, qual foi acionado e qual ação tomada.

Wikilinks: `[[carteira]]`, `[[ips]]`, e o arquivo `semana-YYYY-WNN` recém-salvo.
