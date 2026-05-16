# _standby — Scripts com Anthropic API Key

Scripts originais que chamam `anthropic.Anthropic()` diretamente via API key.
Guardados aqui para reativação futura quando quiser usar a API paga.

**Modo atual do sistema:** Claude Code (sem API key)
**Modo destes scripts:** API key (`ANTHROPIC_API_KEY` no `.env`)

---

## Como reativar

1. Configure `.env` com sua `ANTHROPIC_API_KEY`
2. Copie os scripts de volta para os locais originais:

```powershell
# Runners dos agentes
Copy-Item "_standby/agents/market-researcher/run_market_researcher.py"   ".claude/agents/market-researcher/"
Copy-Item "_standby/agents/earnings-reviewer/run_earnings_reviewer.py"   ".claude/agents/earnings-reviewer/"
Copy-Item "_standby/agents/model-builder/run_model_builder.py"           ".claude/agents/model-builder/"
Copy-Item "_standby/agents/valuation-reviewer/run_valuation_reviewer.py" ".claude/agents/valuation-reviewer/"
Copy-Item "_standby/agents/quant-data-engineer/run_quant.py"             ".claude/agents/quant-data-engineer/"
Copy-Item "_standby/agents/risk-engineer/run_risk_engineer.py"           ".claude/agents/risk-engineer/"
Copy-Item "_standby/agents/portfolio-manager/run_pm.py"                  ".claude/agents/portfolio-manager/"
Copy-Item "_standby/agents/portfolio-manager/run_analisar.py"            ".claude/agents/portfolio-manager/"

# Commands
Copy-Item "_standby/commands/*.py" ".claude/commands/"

# Pipeline
Copy-Item "_standby/scripts/run_research_pipeline.py" "scripts/"
```

3. No `sbwaa.py`, altere `MODO_CLAUDE_CODE = True` para `False`

---

## Estrutura

| Arquivo | Agente / Função |
|---------|----------------|
| `agents/market-researcher/run_market_researcher.py` | Market Researcher — análise macro/setorial |
| `agents/earnings-reviewer/run_earnings_reviewer.py` | Earnings Reviewer — resultados trimestrais |
| `agents/model-builder/run_model_builder.py` | Model Builder — DCF e Gordon |
| `agents/valuation-reviewer/run_valuation_reviewer.py` | Valuation Reviewer — equity research |
| `agents/quant-data-engineer/run_quant.py` | Quant — métricas quantitativas + síntese |
| `agents/risk-engineer/run_risk_engineer.py` | Risk Engineer — VaR, CVaR, stress test + síntese |
| `agents/portfolio-manager/run_pm.py` | Portfolio Manager — decisão final |
| `agents/portfolio-manager/run_analisar.py` | Orquestrador — pipeline completo 8 etapas |
| `commands/morning_call.py` | /morning-call |
| `commands/mundo_economico.py` | /mundo-economico |
| `commands/investimento_do_dia.py` | /investimento-do-dia |
| `commands/relatorio_semanal.py` | /relatorio-semanal |
| `commands/relatorio_mensal.py` | /relatorio-mensal |
| `commands/comparar.py` | /comparar |
| `commands/tese.py` | /tese |
| `commands/rebalancear.py` | /rebalancear |
| `scripts/run_research_pipeline.py` | Pipeline integrado |
