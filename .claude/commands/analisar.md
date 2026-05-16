---
description: Pipeline completo de análise de ativo (8 etapas) sem API key — usa Claude Code como agente
---

# /analisar $ARGUMENTS

Execute o pipeline completo de análise para o ticker **$ARGUMENTS**.

## ETAPA 0 — Preparação

Defina ROOT como `C:\Users\lbmma\Downloads\Local\SBWAA` e execute com `$env:PYTHONUTF8 = "1"`.

Rode em sequência:
```powershell
$env:PYTHONUTF8 = "1"; cd "C:\Users\lbmma\Downloads\Local\SBWAA"
python scripts/data/fetch_brapi.py $ARGUMENTS
python scripts/data/fetch_yahoo.py --macro
python scripts/data/update_carteira.py
```

Leia os arquivos de cache gerados:
- `scripts/data/cache/brapi_$ARGUMENTS_*.json` — dados fundamentalistas BR
- `scripts/data/cache/yahoo_*.json` — macro global (todos os arquivos do dia)

---

## ETAPA 1 — Market Researcher

Leia `.claude/agents/market-researcher/SKILL.md` e execute a análise de mercado para **$ARGUMENTS**:
- Contexto macro (dados dos caches Yahoo)
- Setor e posicionamento competitivo
- Catalisadores e riscos macro relevantes hoje

---

## ETAPA 2 — Earnings Reviewer

Leia `.claude/agents/earnings-reviewer/SKILL.md` e execute a revisão de resultados para **$ARGUMENTS**:
- Use os dados do cache Brapi (P/L, P/VP, margem, ROE, dívida líquida/EBITDA)
- Qualidade dos resultados, tendência, surpresas vs estimativas

---

## ETAPA 3 — Model Builder (DCF)

Leia `.claude/agents/model-builder/SKILL.md` e execute a modelagem para **$ARGUMENTS**:
- Se ação: modelo DCF com premissas explícitas (WACC, g, projeção de FCL)
- Se FII: modelo de Gordon (DY sustentável, cap rate, crescimento de aluguéis)
- Output: preço-alvo, upside/downside vs cotação atual, margem de segurança

---

## ETAPA 4 — Valuation Reviewer

Leia `.claude/agents/valuation-reviewer/SKILL.md` e execute a revisão de valuation para **$ARGUMENTS**:
- Crítica ao modelo DCF construído acima
- Múltiplos comparáveis (P/L, EV/EBITDA, P/VP setorial)
- Veredicto de valuation: BARATO / JUSTO / CARO com justificativa

---

## ETAPA 5 — Quant / Data Engineer

Execute os scripts quantitativos (não precisam de API):
```powershell
python .claude/agents/quant-data-engineer/run_quant.py
```

Leia o cache gerado `scripts/data/cache/quant_*.json` e apresente as métricas chave:
- Sharpe, volatilidade anualizada, drawdown máximo, beta IBOV
- Correlação com outros ativos da carteira

---

## ETAPA 6 — Risk Engineer

Execute os scripts de risco (não precisam de API):
```powershell
python .claude/agents/risk-engineer/run_risk_engineer.py
```

Leia o cache gerado `scripts/data/cache/risk_*.json` e avalie:
- VaR 95% histórico e paramétrico
- CVaR, drawdown atual
- Circuit breakers do IPS: estão dentro dos limites?

---

## ETAPA 7 — Portfolio Manager (Decisão Final)

Leia `.claude/agents/portfolio-manager/SKILL.md` e tome a decisão final sobre **$ARGUMENTS**:
- Consolide os outputs das etapas anteriores
- Verifique adequação ao IPS (`vault/00-portfolio/ips.md`)
- Verifique posição atual em `vault/00-portfolio/carteira.md`
- Emita veredicto: **COMPRAR / AGUARDAR / EVITAR** com sizing sugerido
- Justificativa em no máximo 5 bullets com dados concretos

---

## ETAPA 8 — Salvar Output

Salve a nota de análise em `vault/01-ativos/$ARGUMENTS/analise-$ARGUMENTS-YYYY-MM-DD.md` com:
- Frontmatter YAML (tags, data, veredicto, preço-alvo)
- Seções de cada etapa resumidas
- Wikilinks para: `[[carteira]]`, `[[ips]]`, todos os ativos relacionados mencionados
- Use os labels de tipo de ativo definidos no CLAUDE.md
