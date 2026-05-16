---
description: Relatório mensal completo — performance, análise de risco e revisão de teses
---

# /relatorio-mensal

## Passo 1 — Coletar dados

```powershell
$env:PYTHONUTF8 = "1"; cd "C:\Users\lbmma\Downloads\Local\SBWAA"
python scripts/data/update_carteira.py
python .claude/agents/quant-data-engineer/run_quant.py
python .claude/agents/risk-engineer/run_risk_engineer.py
```

Leia:
- `vault/00-portfolio/carteira.md`
- `vault/00-portfolio/ips.md`
- `vault/00-portfolio/historico-trades.md`
- `scripts/data/cache/quant_*.json` (mais recente)
- `scripts/data/cache/risk_*.json` (mais recente)
- `vault/02-relatorios/semanais/` — relatórios das últimas 4 semanas
- `vault/01-ativos/` — teses e análises recentes de cada ativo

## Passo 2 — Relatório

Leia `.claude/agents/portfolio-manager/SKILL.md`.

Gere o relatório mensal com as seções:

**1. Performance do Mês**
- Retorno da carteira vs IBOV (normalizado R$ 100k)
- Retorno acumulado no ano (se houver dados históricos)
- Tabela por ativo: retorno no mês, contribuição, posição atual

**2. Análise de Risco**
- VaR, CVaR, drawdown máximo do mês
- Evolução da volatilidade vs mês anterior
- Circuit breakers violados? Ações tomadas?

**3. Movimentações do Mês**
Com base em `historico-trades.md`: compras, vendas, dividendos recebidos

**4. Revisão de Teses**
Para cada ativo da carteira: tese continua válida? (Sim / Atenção / Reavaliar)
Basear nos dados disponíveis em `vault/01-ativos/`

**5. Alocação vs IPS**
Tabela: Classe | Alvo % | Atual % | Desvio | Ação sugerida

**6. Outlook Próximo Mês**
- Agenda macro relevante (Fed, COPOM, resultados)
- Oportunidades ou riscos específicos para a carteira
- 1 ação prioritária para o próximo mês

## Passo 3 — Salvar

Salve em `vault/02-relatorios/mensais/relatorio-YYYY-MM.md` com wikilinks completos.
