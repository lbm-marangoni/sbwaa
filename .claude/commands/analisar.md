---
description: Pipeline completo de análise de ativo (8 etapas) sem API key — usa Claude Code como agente. Aceita um ou mais tickers separados por espaço.
---

# /analisar $ARGUMENTS

Execute o pipeline completo de análise para: **$ARGUMENTS**

## DETECÇÃO DE MODO

Antes de iniciar, identifique quantos tickers estão em `$ARGUMENTS`:
- **1 ticker** (ex: `PETR4`): executar pipeline único — comportamento idêntico ao original.
- **2+ tickers** (ex: `PETR4 VALE3 XPML11`): executar pipeline completo e isolado para **cada ticker em sequência**. Ao final de todos, gerar tabela comparativa.

Para múltiplos tickers: informe no início quais serão analisados e em qual ordem, com o formato:
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ANÁLISE EM BATCH — {N} ativos
Ordem: TICKER1 → TICKER2 → TICKER3
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## PIPELINE POR TICKER

Execute as etapas abaixo integralmente para cada ticker antes de passar ao próximo.
Ao iniciar cada ativo em batch, exibir um cabeçalho de progresso:
```
══════════════════════════════════════════════
[1/2] ANALISANDO: TICKER1
══════════════════════════════════════════════
```

---

### ETAPA 0 — Preparação

Defina ROOT como `C:\Users\lbmma\Downloads\Local\SBWAA` e execute com `$env:PYTHONUTF8 = "1"`.

Rode em sequência:
```powershell
$env:PYTHONUTF8 = "1"; cd "C:\Users\lbmma\Downloads\Local\SBWAA"
python scripts/data/fetch_brapi.py {TICKER}
python scripts/data/fetch_yahoo.py --macro
python scripts/data/fetch_consensus.py {TICKER}
python scripts/data/update_carteira.py
```

> Em batch: `fetch_yahoo.py --macro` roda apenas uma vez para o primeiro ticker. Os demais aproveitam o cache do dia.

Leia os arquivos de cache gerados:
- `scripts/data/cache/brapi_{TICKER}_*.json` — dados fundamentalistas BR
- `scripts/data/cache/yahoo_*.json` — macro global (todos os arquivos do dia)
- `scripts/data/cache/consensus_{TICKER}_*.json` — consenso de analistas (disponível quando houver cobertura)

---

### ETAPA 1 — Market Researcher

Leia `.claude/agents/market-researcher/SKILL.md` e execute a análise de mercado para **{TICKER}**:
- Contexto macro (dados dos caches Yahoo)
- Setor e posicionamento competitivo
- Catalisadores e riscos macro relevantes hoje

> Em batch: o contexto macro global é compartilhado entre todos os ativos — foque na análise setorial e nos catalisadores específicos de cada ticker.

---

### ETAPA 2 — Earnings Reviewer

Leia `.claude/agents/earnings-reviewer/SKILL.md` e execute a revisão de resultados para **{TICKER}**:
- Use os dados do cache Brapi (P/L, P/VP, margem, ROE, dívida líquida/EBITDA)
- Qualidade dos resultados, tendência, surpresas vs estimativas

---

### ETAPA 3 — Model Builder (DCF)

Leia `.claude/agents/model-builder/SKILL.md` e execute a modelagem para **{TICKER}**:
- Se ação: modelo DCF com premissas explícitas (WACC, g, projeção de FCL)
- Se FII: modelo de Gordon (DY sustentável, cap rate, crescimento de aluguéis)
- Output: preço-alvo, upside/downside vs cotação atual, margem de segurança

---

### ETAPA 4 — Valuation Reviewer

Leia `.claude/agents/valuation-reviewer/SKILL.md` e execute a revisão de valuation para **{TICKER}**:
- Crítica ao modelo DCF construído acima
- Múltiplos comparáveis (P/L, EV/EBITDA, P/VP setorial)
- Preço teto/chão: Graham (ações) ou Bazin (FIIs)
- Veredicto de valuation: BARATO / JUSTO / CARO com justificativa

---

### ETAPA 5 — Quant / Data Engineer

Execute os scripts quantitativos (não precisam de API):
```powershell
python .claude/agents/quant-data-engineer/run_quant.py
```

Leia o cache gerado `scripts/data/cache/quant_*.json` e apresente as métricas chave:
- Sharpe, volatilidade anualizada, drawdown máximo, beta IBOV
- Correlação com outros ativos da carteira

---

### ETAPA 6 — Risk Engineer

Execute os scripts de risco (não precisam de API):
```powershell
python .claude/agents/risk-engineer/run_risk_engineer.py
```

Leia o cache gerado `scripts/data/cache/risk_*.json` e avalie:
- VaR 95% histórico e paramétrico
- CVaR, drawdown atual
- Circuit breakers do IPS: estão dentro dos limites?

---

### ETAPA 7 — Portfolio Manager (Decisão Final)

Leia `.claude/agents/portfolio-manager/SKILL.md` e tome a decisão final sobre **{TICKER}**:
- Consolide os outputs das etapas anteriores
- Verifique adequação ao IPS (`vault/00-portfolio/ips.md`)
- Verifique posição atual em `vault/00-portfolio/carteira.md`
- Emita veredicto: **COMPRAR / AGUARDAR / EVITAR** com sizing sugerido
- Justificativa em no máximo 5 bullets com dados concretos

---

### ETAPA 8 — Salvar Output

Salve a nota de análise em `vault/01-ativos/{TICKER}/analise-{TICKER}-YYYY-MM-DD.md` com:
- Frontmatter YAML (tags, data, veredicto, preço-alvo)
- Seções de cada etapa resumidas
- Wikilinks para: `[[carteira]]`, `[[ips]]`, todos os ativos relacionados mencionados
- Use os labels de tipo de ativo definidos no CLAUDE.md

---

## TABELA COMPARATIVA FINAL (somente em batch — 2+ tickers)

Após concluir o pipeline de todos os tickers, gerar obrigatoriamente:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
RESUMO COMPARATIVO — {DATA}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Ticker  Tipo         Veredicto  Valuation  Upside DCF  P. Teto    Cotação   Sizing
──────────────────────────────────────────────────────────────────────────────────
TICK1   🟦 AÇÃO PN   COMPRAR    BARATO     +28%        R$ 48,00   R$ 38,00  8%
TICK2   🟩 FII       AGUARDAR   JUSTO      +9%         R$ 115,00  R$ 106,00 —

──────────────────────────────────────────────────────────────────────────────────
Prioridade de aporte (PM): TICK1 > TICK2
```

Colunas obrigatórias: Ticker | Tipo | Veredicto PM | Valuation Reviewer | Upside DCF | Preço Teto (Graham ou Bazin) | Cotação atual | Sizing sugerido

Linha "Prioridade de aporte": ordenar os ativos com veredicto COMPRAR por upside DCF decrescente. Ativos AGUARDAR/EVITAR ficam fora da ordenação de prioridade.
